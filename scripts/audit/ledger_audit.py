#!/usr/bin/env python3
"""lhg-money-plan 确定性审计：扫描目标目录下的账本/预算/目标/报告文件。

检查：
  LED-SCHEMA-001  ledger.csv 必填列缺失（blocker）
  LED-AMT-001     ledger.csv 金额非法（blocker）
  LED-DATE-001    ledger.csv 日期格式不规范（warning）
  BUD-ALLOC-001   budget.json 分类比例合计 != 100%（blocker）
  BUD-SAVE-001    budget.json 无储蓄类目（warning）
  TGT-MATH-001    goals.json 月均储蓄与（目标-已存）/期限月对不上（blocker）
  ADV-KEYWORD-001 报告 .md 含投资建议关键词（blocker）
  CMP-DISC-001    报告 .md 缺少合规声明（blocker）

用法：
    python3 ledger_audit.py --target <目录> [--format json|text] [--fail-on blocker|warning]

exit code：0=无命中（按 --fail-on 口径），2=有 blocker，1=仅 warning（且 --fail-on=warning）。
零第三方依赖。规则文案均为本项目原创。
"""

import argparse
import csv
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-money-plan/ledger-audit"

REQUIRED_LEDGER_COLS = ["日期", "分类", "金额", "方向"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
COMPLIANCE_STMT = "不构成任何投资建议"
ADVICE_KEYWORDS = [
    "买入", "加仓", "必涨", "抄底", "重仓", "满仓",
    "推荐买", "强烈看好", "肯定涨", "稳赚", "保本",
    "闭眼买", "翻倍", "十倍股", "梭哈",
]
SAVE_HINTS = ["储蓄", "应急金", "存钱", "目标"]


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file", "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line, snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {"rule_id": self.rule_id, "severity": self.severity,
                "category": self.category, "title": self.title,
                "file": self.file, "line": self.line,
                "snippet": self.snippet, "detail": self.detail}


findings = []


def add(rule_id, severity, category, title, file, line=0, snippet="", detail=""):
    findings.append(Finding(rule_id, severity, category, title, file, line, snippet, detail))


def read_text(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read()


# ---------------------------------------------------------------- 账本

def check_ledger(path):
    try:
        rows = list(csv.DictReader(read_text(path).splitlines()))
    except Exception as e:
        add("LED-SCHEMA-001", "blocker", "账本", "账本 CSV 无法解析",
            path, detail=str(e))
        return
    if not rows:
        add("LED-SCHEMA-001", "blocker", "账本", "账本 CSV 为空",
            path, detail="无数据行")
        return
    cols = rows[0].keys()
    missing = [c for c in REQUIRED_LEDGER_COLS if c not in cols]
    if missing:
        add("LED-SCHEMA-001", "blocker", "账本", "账本缺少必填列",
            path, detail="缺少列：%s；必填：%s" % ("、".join(missing), "、".join(REQUIRED_LEDGER_COLS)))
    for i, r in enumerate(rows, start=2):
        amt = (r.get("金额") or "").strip()
        try:
            v = float(amt)
            if v <= 0:
                raise ValueError
        except Exception:
            add("LED-AMT-001", "blocker", "账本", "金额非法（须为正数）",
                path, line=i, snippet=amt,
                detail="第 %d 行金额=%r；金额列须为正数，方向用“方向”列表示" % (i, amt))
        d = (r.get("日期") or "").strip()
        if d and not DATE_RE.match(d):
            add("LED-DATE-001", "warning", "账本", "日期格式不规范",
                path, line=i, snippet=d, detail="第 %d 行日期=%r，应为 YYYY-MM-DD" % (i, d))
        direct = (r.get("方向") or "").strip()
        if direct and direct not in ("收入", "支出"):
            add("LED-SCHEMA-001", "blocker", "账本", "方向列取值非法",
                path, line=i, snippet=direct,
                detail="第 %d 行方向=%r，只能是“收入”或“支出”" % (i, direct))


# ---------------------------------------------------------------- 预算

def check_budget(path):
    try:
        d = json.loads(read_text(path))
    except Exception as e:
        add("BUD-ALLOC-001", "blocker", "预算", "budget.json 无法解析",
            path, detail=str(e))
        return
    cats = d.get("categories")
    if not isinstance(cats, dict) or not cats:
        add("BUD-ALLOC-001", "blocker", "预算", "budget.json 缺少 categories",
            path, detail="categories 须为“分类名: 占比%”的字典")
        return
    try:
        total = sum(float(v) for v in cats.values())
    except Exception:
        add("BUD-ALLOC-001", "blocker", "预算", "预算比例含非数字",
            path, detail=str(cats))
        return
    if abs(total - 100) > 0.5:
        add("BUD-ALLOC-001", "blocker", "预算", "预算分配合计不是 100%",
            path, snippet="合计 %.1f%%" % total,
            detail="各分类占比合计 %.1f%%，与 100%% 偏差超过 ±0.5%%；请调整后使合计为 100" % total)
    if not any(any(h in k for h in SAVE_HINTS) for k in cats.keys()):
        add("BUD-SAVE-001", "warning", "预算", "预算中没有储蓄类目",
            path, detail="未发现含“储蓄/应急金/存钱/目标”字样的分类；建议储蓄占比不低于 10%")


# ---------------------------------------------------------------- 目标

def check_goals(path):
    try:
        goals = json.loads(read_text(path))
    except Exception as e:
        add("TGT-MATH-001", "blocker", "目标", "goals.json 无法解析",
            path, detail=str(e))
        return
    if not isinstance(goals, list):
        goals = [goals]
    for g in goals:
        name = g.get("名称", "?")
        try:
            target = float(g["目标金额"])
            saved = float(g.get("已存金额", 0))
            months = float(g["期限月"])
            monthly = float(g["月均储蓄"])
        except Exception:
            add("TGT-MATH-001", "blocker", "目标", "目标字段缺失或非数字",
                path, snippet=str(name), detail="目标 %r 缺少 目标金额/期限月/月均储蓄 或取值非法" % name)
            continue
        if months <= 0:
            add("TGT-MATH-001", "blocker", "目标", "期限月非法",
                path, snippet=str(name), detail="目标 %r 期限月须为正数" % name)
            continue
        expect = (target - saved) / months
        if abs(monthly - expect) > max(abs(expect) * 0.01, 0.01):
            add("TGT-MATH-001", "blocker", "目标", "月均储蓄测算对不上",
                path, snippet=str(name),
                detail="目标 %r：月均储蓄填写 %.2f，但（目标金额−已存）/期限月 = %.2f" % (name, monthly, expect))


# ---------------------------------------------------------------- 报告合规

def check_report(path):
    text = read_text(path)
    for kw in ADVICE_KEYWORDS:
        idx = text.find(kw)
        if idx >= 0:
            line = text.count("\n", 0, idx) + 1
            add("ADV-KEYWORD-001", "blocker", "合规", "报告含投资建议关键词",
                path, line=line, snippet=kw,
                detail="第 %d 行命中关键词“%s”；本插件不输出投资建议，请改写该句" % (line, kw))
            break  # 每文件报一次即可
    if COMPLIANCE_STMT not in text:
        add("CMP-DISC-001", "blocker", "合规", "报告缺少合规声明",
            path, detail="报告末尾须原样附带合规声明块（含“%s”）" % COMPLIANCE_STMT)


# ---------------------------------------------------------------- 主流程

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--format", default="json", choices=["json", "text"])
    ap.add_argument("--fail-on", default="blocker", choices=["blocker", "warning"])
    args = ap.parse_args()

    target = os.path.abspath(args.target)
    if os.path.isdir(target):
        files = [os.path.join(target, f) for f in sorted(os.listdir(target))]
    else:
        files = [target]

    for p in files:
        base = os.path.basename(p)
        if not os.path.isfile(p):
            continue
        if base == "ledger.csv":
            check_ledger(p)
        elif base == "budget.json":
            check_budget(p)
        elif base == "goals.json":
            check_goals(p)
        elif base.endswith(".md"):
            check_report(p)

    n_blocker = sum(1 for f in findings if f.severity == "blocker")
    n_warning = sum(1 for f in findings if f.severity == "warning")
    summary = {"tool": TOOL, "version": VERSION, "target": target,
               "blocker": n_blocker, "warning": n_warning,
               "total": len(findings)}

    if args.format == "json":
        out = {"summary": summary,
               "findings": [f.to_dict() for f in findings]}
        sys.stdout.write(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        lines = ["[%s] %s blocker=%d warning=%d" % (TOOL, target, n_blocker, n_warning)]
        for f in findings:
            lines.append("%s %s %s:%s %s" % (f.severity.upper(), f.rule_id, f.file, f.line, f.title))
            if f.detail:
                lines.append("    " + f.detail)
        sys.stdout.write("\n".join(lines) + "\n")

    if n_blocker:
        return 2
    if n_warning and args.fail_on == "warning":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
