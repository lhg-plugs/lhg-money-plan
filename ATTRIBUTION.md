# 灵感来源与致谢（Attribution）

本插件的**方法论灵感**来自以下项目，**所有实现代码、检测规则与文案均为原创**，未复制任何第三方的原文案或代码。

| 项目 | 作者 / 组织 | 许可（2026-10-11 核实） | 链接 | 借鉴了什么思路 |
|---|---|---|---|---|
| personal-finance（Agent Skill） | orchune | **Proprietary 专有许可**（其 README 明确标注；star 数未披露） | https://github.com/orchune/personal-finance | 仅借鉴"记账→预算→储蓄目标"三段式结构的高层思路；**该 skill 的原文案、提示词、代码一律未复制**，且本插件不依赖其 MCP 服务 |
| claude-skills（finance 域：budgeting） | felaris | MIT | https://github.com/felaris/claude-skills | 仅借鉴"预算按框架落地"的高层思路；文案与实现均为原创 |
| 50/30/20 预算法则 | Elizabeth Warren（通用理财常识） | 公共知识 | — | 预算分配框架（本插件的方法论表述为原创） |
| 六罐子理财法 | T. Harv Eker（通用理财常识） | 公共知识 | — | 预算分配备选框架（本插件的方法论表述为原创） |

## 声明

1. **借鉴思路，实现与文案均为原创**：以上项目的具体文案、提示词原文、代码实现均未被复制。本插件的 skill 方法论文案、审计规则、命令流程均为独立撰写。特别说明：orchune/personal-finance 为专有许可，本插件与其无任何代码或文案上的派生关系，也不调用其服务。
2. **许可合规**：felaris/claude-skills 为 MIT 宽松许可；本插件审计脚本仅使用 Python 标准库，未捆绑任何第三方包。
3. **商标与归属**：各项目名称与作者署名归其各自所有者所有。
4. **合规定位**：本插件仅为记账与预算规划助手，不构成任何投资建议；涉及投资决策请咨询持牌专业人士。

## 本插件自身的许可

本插件原创部分采用 MIT 许可（见 `LICENSE` 文件），版权所有：刘洪光（https://github.com/lhg-skills）。
