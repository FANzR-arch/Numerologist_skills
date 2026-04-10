# Numerologist Skills (AI 术数工程化)

本项目把传统术数相关的 AI skill 拆成可审计、可复用、可逐步扩展的工程模块。目标不是把模型包装成“更会玄学”，而是尽量减少它在排盘、流派口径、步骤顺序和解释链路上的幻觉。

## 当前包含的 Skills

| 目录 | 体系 | 主要用途 | 固定计算 / 依赖 |
|---|---|---|---|
| `qimen-dunjia/` | 奇门遁甲 | 单事判断、择时、方位、趋吉避凶 | Python CLI：`scripts/qimen_cli.py` |
| `ziwei-doushu/` | 紫微斗数 | 本命盘结构解读、宫位分析、大限流年 | 规则与 references 驱动 |
| `bazi/` | 四柱八字 | 日主强弱、格局、十神、大运流年 | 规则与 references 驱动 |

## 仓库结构

- `SKILL.md`：主技能说明、触发条件、工作流、输出约束
- `references/`：规则集、术语表、示例、口径说明
- `scripts/`：需要刚性计算时使用的外部脚本（当前仅奇门遁甲包含）

## 设计原则

1. 先追问，再输出：信息不全时，优先补参数，不硬排盘。
2. 确定性计算外包：凡是历法换算、固定排盘、结构化计算，优先交给脚本或可信排盘结果。
3. 先声明口径，再做结论：流派、换日规则、闰月归属、默认规则都要说清楚。
4. 只给结构化参考：健康、法律、财务等高风险场景不替代现实专业建议。

## 快速上手

如果你要运行奇门遁甲的固定计算脚本：

```bash
pip install -r qimen-dunjia/scripts/requirements.txt
python qimen-dunjia/scripts/qimen_cli.py --input tmp/qimen_input.json --output tmp/qimen_output.json
```

## Why This Repo

与其让 LLM 在“似懂非懂”的状态里硬着头皮往下说，不如把关键步骤拆开：

- 用 Prompt 约束控制提问顺序和输出边界
- 用 References 固定术语、口径和判断顺序
- 用外部脚本承接刚性计算

这样至少能让过程更透明，错误更容易暴露，版本边界也更清楚。

## Disclaimer

本仓库内容用于传统术数的工程化表达与 AI 约束实验，不构成医疗、法律、财务或其他现实决策建议。

---
*Created as part of the AI Engineering of Traditional Divination (AI 术数工程化) initiative.*
