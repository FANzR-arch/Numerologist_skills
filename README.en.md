# Numerologist Skills

[中文](README.md) | English | [Tiếng Việt](README.vi.md)

AI skills for traditional divination systems, built as auditable, reusable engineering modules. The goal is not to make the model "better at metaphysics" but to cut hallucination in chart calculation, school conventions, step order and the reasoning behind each reading.

## Skills

| Directory | System | Main use | Calculation |
|---|---|---|---|
| `qimen-dunjia/` | Qimen Dunjia | Single-question judgement, timing, direction | Python CLI: `scripts/qimen_cli.py` |
| `ziwei-doushu/` | Zi Wei Dou Shu | Natal chart structure, palaces, decade and annual periods | Python CLI: `scripts/ziwei_cli.py` |
| `bazi/` | Four Pillars (Bazi) | Day master strength, structure, ten gods, luck periods | Python CLI: `scripts/bazi_cli.py` |
| `liuyao/` | Liu Yao | One question per hexagram, use god, shi/ying, moving lines | Python CLI: `scripts/liuyao_cli.py` |
| `numerology/` | Pythagorean numerology (Thần số học, Vietnamese) | Life path, birth chart, pinnacles, personal year | Python CLI: `scripts/numerology_cli.py` |

User guide: [docs/user-guide.md](docs/user-guide.md) (Vietnamese: [docs/user-guide.vi.md](docs/user-guide.vi.md)).

## Repository layout

- `SKILL.md`: skill description, triggers, workflow and output rules
- `references/`: rule sets, glossaries, examples and conventions; each section is labelled with its source or marked as not yet checked against the classics
- `scripts/`: deterministic calculation scripts (all five skills)
- `core/calendar_core.py`: shared input parsing, true solar time and the Vietnamese lunar calendar (`calendar_locale: vn`). `core/thuat-ngu-chung.md`: shared Vietnamese glossary. Each skill's `scripts/calendar_core.py` and `references/thuat-ngu-chung.md` are generated copies so every skill can be installed alone; edit `core/` only, then run `python3 tools/sync_core.py`. CI checks the copies with `--check`.
- `audit/`: registry that checks each rule against books and standards, with golden cases taken from worked examples in those books (see [audit/README.md](audit/README.md) and [docs/source-audit-plan.md](docs/source-audit-plan.md))

## Design principles

1. Ask first, then answer: when information is missing, ask for it instead of forcing a chart.
2. Hand deterministic work to scripts: calendar conversion, chart layout and other fixed calculations run in scripts, never by hand.
3. State the convention before the conclusion: school, day rollover, leap-month handling and defaults are always spelled out.
4. Structured reference only: health, legal and financial questions never replace professional advice.

## Install as a Claude Code plugin

```bash
/plugin install numerologist-skills --marketplace FANzR-arch/Numerologist_skills
```

Claude Code earlier than 2.1.275 needs two steps:

```bash
/plugin marketplace add FANzR-arch/Numerologist_skills
/plugin install numerologist-skills@numerologist-skills
```

The skills load automatically in conversation when relevant. The scripts need Python 3.11+ with `lunar_python` and `tzdata` (numerology needs only the standard library); on first use the skill asks before running `pip install -r <skill dir>/scripts/requirements.txt`. If you use a fork, replace `FANzR-arch/Numerologist_skills` with your repository.

Try it locally for one session without changing global settings:

```bash
claude --plugin-dir /path/to/Numerologist_skills
```

## Use as an MCP server

`mcp-server/server.py` exposes the five scripts as MCP tools: `bazi_chart`, `ziwei_chart`, `qimen_chart`, `liuyao_chart`, `numerology_chart`. Parameters match each skill's input JSON and the tools return the script output. Useful for clients such as Claude Desktop that cannot run scripts.

```bash
python3 -m pip install -r mcp-server/requirements.txt
claude mcp add numerologist -- python3 /path/to/Numerologist_skills/mcp-server/server.py
```

For Claude Desktop, add to `mcpServers` in `claude_desktop_config.json`:

```json
"numerologist": {"command": "python3", "args": ["/path/to/Numerologist_skills/mcp-server/server.py"]}
```

## Evals

`evals/` holds `claude plugin eval` cases that check whether the model runs the script instead of calculating by hand, whether key values and conventions are right, and whether it keeps to safety limits (no fatalistic claims; real-world advice for health, legal and financial questions). Each case also runs a baseline without the plugin and reports the score difference.

```bash
claude plugin eval . --model haiku --runs 2 --allow-tools 'Bash(python:*)' 'Bash(python3:*)' Write --no-publish
```

`python3` must be able to import `lunar_python` (except for numerology), or the bazi, liuyao and ziwei cases fail because the scripts cannot run.

## Quick start

```bash
python3 -m pip install -r bazi/scripts/requirements.txt
python3 bazi/scripts/bazi_cli.py --input tmp/bazi_input.json --output tmp/bazi_output.json
```

The other scripts work the same way: `qimen-dunjia/scripts/qimen_cli.py`, `ziwei-doushu/scripts/ziwei_cli.py`, `liuyao/scripts/liuyao_cli.py`, `numerology/scripts/numerology_cli.py`. Input fields are listed in each `SKILL.md`.

Run all tests:

```bash
python3 -m pip install -r requirements-dev.txt
pytest -q
```

## Disclaimer

This repository explores engineering for traditional divination and constraints on AI output. It is not medical, legal, financial or any other real-world decision advice.
