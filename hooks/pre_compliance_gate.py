#!/usr/bin/env python3
"""lhg-money-plan 硬门：投资建议关键词拦截。

触发：PreToolUse / Edit|Write。扫描本次写入/编辑的文件内容，
若命中投资建议关键词（买入/加仓/必涨/抄底/重仓/满仓/推荐买等），
以 exit code 2 拦截该操作，并给出改写指引。

逃生方式（按推荐度排序）：
  1. LHG_MONEYPLAN_COMPLY_OFF=1（环境变量，当前会话有效；关闭后
     关键词拦截不再触发，但审计脚本的 ADV-KEYWORD-001 仍会在
     money-audit 时报 blocker）。
  2. /plugin disable lhg-money-plan（整个插件停用，hooks 不再触发）。

设计原则：只有"命中关键词"才拦截；内部出错一律 fail-open
（直接放行，不报错）；零第三方依赖。

注意：本 hook 只做关键词层面的硬拦截，真正的合规判断
（上下文、语气）仍由 agent 按 skill 规范负责。
"""

import json
import os
import sys

# 投资建议关键词表（原创整理：常见荐股/荐基话术）
ADVICE_KEYWORDS = [
    "买入", "加仓", "必涨", "抄底", "重仓", "满仓",
    "推荐买", "强烈看好", "肯定涨", "稳赚", "保本",
    "闭眼买", "翻倍", "十倍股", "梭哈", "清仓买入",
]

REWRITE_GUIDE = (
    "改写指引：删除具体品种推荐与涨跌断言；只保留记账/预算/目标规划内容；"
    "如需提及投资方向，用标准话术替代："
    "“本工具仅为记账与预算规划助手，不构成任何投资建议；"
    "涉及投资决策请咨询持牌专业人士。”"
)


def extract_text(tool_input):
    """从 Edit/Write 的输入中抽取待写入文本。"""
    parts = []
    for key in ("content", "new_string", "old_string", "file_text"):
        v = tool_input.get(key)
        if isinstance(v, str) and v:
            parts.append(v)
    return "\n".join(parts)


def find_hits(text):
    hits = []
    for kw in ADVICE_KEYWORDS:
        if kw in text:
            hits.append(kw)
    return hits


def main() -> int:
    if os.environ.get("LHG_MONEYPLAN_COMPLY_OFF") == "1":
        return 0  # 逃生开关

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # 输入解析失败：fail-open

    tool_input = payload.get("tool_input", {}) or {}
    text = extract_text(tool_input)
    if not text:
        return 0

    try:
        hits = find_hits(text)
    except Exception:
        return 0  # 内部错误：fail-open

    if not hits:
        return 0

    msg = (
        "⛔ 合规硬门（lhg-money-plan）：本次写入内容命中投资建议关键词：%s。\n"
        "本插件仅为记账与预算规划助手，不输出投资建议。\n%s\n"
        "确认为合规内容但被误拦：export LHG_MONEYPLAN_COMPLY_OFF=1 后重试。"
        % ("、".join(hits), REWRITE_GUIDE)
    )
    sys.stderr.write(msg + "\n")
    return 2  # exit 2 = 拦截本次工具调用


if __name__ == "__main__":
    sys.exit(main())
