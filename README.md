<!-- About 简介（推送后填写到仓库 About 栏）：
理财规划助手：收支记账→预算分配→储蓄目标规划 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-money-plan
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, personal-finance, budgeting, money-management -->

# lhg-money-plan：理财规划助手，记账预算目标一条龙

> ⚠️ **合规声明（首屏置顶）**：本工具仅为**记账与预算规划助手**，**不构成任何投资建议**；涉及投资决策请咨询持牌专业人士。
>
> **一句话介绍**：给 AI 编程助手装上"理财规划助手"——收支记账整理 → 预算分配（50/30/20）→ 储蓄目标规划 → 输出带合规声明的计划报告；**确定性审计 + 写入硬门双保险，投资建议表述出现即拦截**。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-money-plan
> /plugin install lhg-money-plan@lhg-plugs
> ```

## 它是什么

`lhg-money-plan` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **4 个命令**（小白入口）：`money-plan` 理财规划一条龙，`money-budget` 预算分配，`money-goal` 储蓄目标规划，`money-audit` 记账预算体检
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：记账五步法、预算三框架、目标规划四步法、月度复盘四问
- **2 个专家 agent**：记账助理、复盘审计专家
- **1 个合规硬门 hook**：写入文件命中投资建议关键词（买入/加仓/必涨/抄底/重仓/满仓/推荐买等）直接拦截，可一键关闭
- **8 条确定性审计规则**：纯 Python 标准库、零第三方依赖，含预算合计校验、目标测算一致性、关键词拦截、合规声明检查

## 合规设计：三层防护

1. **声明置顶**：README 首屏、每个 SKILL.md 开头、每条命令输出末尾，都有显著的合规声明。
2. **写入硬门**：hook 在文件写入前扫描投资建议关键词，命中即拦截（exit 2）；`LHG_MONEYPLAN_COMPLY_OFF=1` 可关闭。
3. **审计兜底**：`ledger_audit.py` 的 ADV-KEYWORD-001（关键词）与 CMP-DISC-001（声明缺失）是 blocker，`money-audit` 命令逐条清零。

## 4 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-money-plan:money-plan` | 记账→预算→目标一条龙，输出计划报告 | `/lhg-money-plan:money-plan "税后18000"` |
| `/lhg-money-plan:money-budget` | 按 50/30/20（或六罐子/零基）分配月预算 | `/lhg-money-plan:money-budget 18000` |
| `/lhg-money-plan:money-goal` | 储蓄目标：缺口测算→与预算对账 | `/lhg-money-plan:money-goal "应急金10万，12个月"` |
| `/lhg-money-plan:money-audit` | 体检：文件完整性+测算一致性+合规 | `/lhg-money-plan:money-audit ./我的账本` |

## 目录结构

```
lhg-money-plan/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 4 个命令：money-plan / money-budget / money-goal / money-audit
├── skills/                  # 4 个平台中立 skill（记账/预算/目标/复盘，合规声明置顶）
├── agents/                  # 2 个专家 agent（tracker / reviewer）
├── hooks/                   # 投资建议关键词拦截 hook（fail-open，可一键关闭）
├── scripts/audit/           # 确定性审计：ledger_audit.py（零第三方依赖）
├── fixtures/                # 好/坏对照用例
├── smoke_test.py            # 冒烟测试
├── ATTRIBUTION.md           # 灵感来源声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**Q：它能推荐买什么基金/股票吗？**
A：不能，这是设计红线。本插件只做记账、预算、储蓄目标规划三件事；任何投资品种推荐都会被 hook 与审计脚本拦截。需要投资建议请咨询持牌专业人士。

**Q：和记账 App（随手记/鲨鱼记账）有什么区别？**
A：记账 App 负责"记"，本插件负责"算和规划"：基于你的账本自动出预算分配、储蓄目标缺口测算、月度复盘归因。你可以把 App 导出的 CSV 直接丢给它。

**Q：收入不稳定（自由职业）能用吗？**
A：能。记账 skill 里有专门口径：取近 6 个月平均 ×0.8 做保守基数，预算按这个基数做。

**Q：一定要用 Claude Code 吗？**
A：`skills/` 下的方法论是平台中立的纯 Markdown，可直接搬到豆包、Workbuddy 等 agent 平台用。只有 commands/agents/hooks 需要 Claude Code。

**Q：我的账本数据安全吗？**
A：账本只存在你的本地工作目录，插件不上传任何数据到外部服务。合规硬门只做本地关键词扫描。

**Q：hook 把我正常的内容拦了怎么办？**
A：两种处理：① 确认内容确实合规后，`export LHG_MONEYPLAN_COMPLY_OFF=1` 关闭本次拦截；② 到本仓库提 issue（标题前缀 `[hook]`），我们优化关键词表。

## 自迭代

- 每个 skill 末尾有「自检与反馈」节：质检门 + 标准冒烟用例 + 一键提 issue。
- 发现规则误报/漏报、方法论不合理：到本仓库提 issue（标题带对应 skill 前缀，如 `[lhg-mp-track]`），附输入数据特征与期望行为。

## 出品：刘洪光

刘洪光（https://github.com/lhg-skills）出品，lhg-plugs「小白专家插件」系列之一。
灵感来源见 [ATTRIBUTION.md](./ATTRIBUTION.md)（借鉴思路，实现与文案均为原创）。

---
⚠️ 合规声明：本工具仅为记账与预算规划助手，**不构成任何投资建议**；涉及投资决策请咨询持牌专业人士。
