# Numerologist Skills (你的赛博命理师)

中文 | [English](README.en.md) | [Tiếng Việt](README.vi.md)

本项目把传统术数相关的 AI skill 拆成可审计、可复用、可逐步扩展的工程模块。目标不是把模型包装成“更会玄学”，而是尽量减少它在排盘、流派口径、步骤顺序和解释链路上的幻觉。

## 当前包含的 Skills

| 目录 | 体系 | 主要用途 | 固定计算 / 依赖 |
|---|---|---|---|
| `qimen-dunjia/` | 奇门遁甲 | 单事判断、择时、方位、趋吉避凶 | Python CLI：`scripts/qimen_cli.py` |
| `ziwei-doushu/` | 紫微斗数 | 本命盘结构解读、宫位分析、大限流年 | Python CLI：`scripts/ziwei_cli.py` |
| `bazi/` | 四柱八字 | 日主强弱、格局、十神、大运流年 | Python CLI：`scripts/bazi_cli.py` |
| `liuyao/` | 六爻 | 一事一卦、用神、世应、动变 | Python CLI：`scripts/liuyao_cli.py` |
| `numerology/` | Thần số học（毕达哥拉斯数字学，越南语） | số chủ đạo、biểu đồ ngày sinh、đỉnh cao、năm cá nhân | Python CLI：`scripts/numerology_cli.py` |

## 仓库结构

- `SKILL.md`：主技能说明、触发条件、工作流、输出约束
- `references/`：规则集、术语表、示例、口径说明
- `scripts/`：需要刚性计算时使用的外部脚本（五个 skill 均包含）
- `core/calendar_core.py`：五个脚本共用的输入解析、真太阳时换算与越南阴历（`calendar_locale: vn`）。`core/thuat-ngu-chung.md`：越南语通用术语表。各 skill 的 `scripts/calendar_core.py`（五个 skill）、`references/thuat-ngu-chung.md`（四个中国术数 skill）是生成的副本（每个 skill 可单独安装），只改 `core/`，再运行 `python tools/sync_core.py`；CI 用 `--check` 检查副本一致

## 设计原则

1. 先追问，再输出：信息不全时，优先补参数，不硬排盘。
2. 确定性计算外包：凡是历法换算、固定排盘、结构化计算，优先交给脚本或可信排盘结果。
3. 先声明口径，再做结论：流派、换日规则、闰月归属、默认规则都要说清楚。
4. 只给结构化参考：健康、法律、财务等高风险场景不替代现实专业建议。

使用说明见 [docs/user-guide.md](docs/user-guide.md)（英文，越南语版见 [docs/user-guide.vi.md](docs/user-guide.vi.md)）；按权威文献审校逻辑的计划见 [docs/source-audit-plan.md](docs/source-audit-plan.md)，登记表与工具见 [audit/README.md](audit/README.md)。

## 作为 Claude Code 插件安装

```bash
/plugin install numerologist-skills --marketplace FANzR-arch/Numerologist_skills
```

Claude Code 2.1.275 以前的版本分两步：

```bash
/plugin marketplace add FANzR-arch/Numerologist_skills
/plugin install numerologist-skills@numerologist-skills
```

装好后，五个 skill 在对话中按需自动加载。排盘脚本依赖 Python 3.11+ 与 `lunar_python`、`tzdata`（Thần số học只需 Python 标准库）；首次排盘缺依赖时，skill 会请你确认后运行 `pip install -r <skill 目录>/scripts/requirements.txt`。fork 后请把命令里的 `FANzR-arch/Numerologist_skills` 换成你的仓库。

本地试用（只对当前会话生效，不改全局配置）：

```bash
claude --plugin-dir /path/to/Numerologist_skills
```

## 作为 MCP server 使用

`mcp-server/server.py` 把五个计算脚本暴露为 MCP tool：`bazi_chart`、`ziwei_chart`、`qimen_chart`、`liuyao_chart`、`numerology_chart`，参数与各 skill 的输入 JSON 相同，返回脚本输出。适合 Claude Desktop 等不能直接运行脚本的客户端。

```bash
python3 -m pip install -r mcp-server/requirements.txt
claude mcp add numerologist -- python3 /path/to/Numerologist_skills/mcp-server/server.py
```

Claude Desktop 在 `claude_desktop_config.json` 的 `mcpServers` 中加入：

```json
"numerologist": {"command": "python3", "args": ["/path/to/Numerologist_skills/mcp-server/server.py"]}
```

## 解读质量评测（eval）

`evals/` 下是 `claude plugin eval` 用例：检查模型是否调用脚本而不是手算、关键数值与口径是否正确、是否守住安全边界（不下宿命断语、健康/法律/财务类附现实建议）。每个用例同时跑一个不加载插件的对照组，报告分数差 Δ。

```bash
claude plugin eval . --model haiku --runs 2 --allow-tools 'Bash(python:*)' 'Bash(python3:*)' Write --no-publish
```

运行环境里 `python3` 需要能 import `lunar_python`（Thần số học除外），否则八字、六爻、紫微等用例会因脚本无法运行而失分。

## 快速上手

如果你要运行奇门遁甲的固定计算脚本：

```bash
python3 -m pip install -r qimen-dunjia/scripts/requirements.txt
python3 qimen-dunjia/scripts/qimen_cli.py --input tmp/qimen_input.json --output tmp/qimen_output.json
```

如果你要运行紫微斗数的排盘脚本：

```bash
python3 -m pip install -r ziwei-doushu/scripts/requirements.txt
python3 ziwei-doushu/scripts/ziwei_cli.py --input tmp/ziwei_input.json --output tmp/ziwei_output.json
```

如果你要运行八字的排盘脚本：

```bash
python3 -m pip install -r bazi/scripts/requirements.txt
python3 bazi/scripts/bazi_cli.py --input tmp/bazi_input.json --output tmp/bazi_output.json
```

运行全部测试：

```bash
python3 -m pip install -r requirements-dev.txt
pytest -q
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
