# User guide

English | [Tiếng Việt](user-guide.vi.md)

The plugin covers five systems: Bazi (`bazi`), Zi Wei Dou Shu (`ziwei-doushu`), Qimen Dunjia (`qimen-dunjia`), Liu Yao (`liuyao`) and Pythagorean numerology, "Thần số học" (`numerology`). Each system has a Python script that does the calculation; the model only asks for information and interprets the result.

Results are for reference only and do not replace medical, legal or financial advice.

## 1. Installation

You need Python 3.11 or later (`python3 --version`). Numerology needs only Python; the other four systems also need `lunar_python` and `tzdata`.

### Option A: Claude Code plugin (recommended)

In Claude Code:

```bash
/plugin install numerologist-skills --marketplace <owner>/Numerologist_skills
```

`<owner>` is the GitHub account that holds the repository (your fork). On Claude Code earlier than 2.1.275, install in two steps:

```bash
/plugin marketplace add <owner>/Numerologist_skills
```

```bash
/plugin install numerologist-skills@numerologist-skills
```

Install the Python libraries once (the path is the installed plugin directory, or the repository if you use a local copy):

```bash
python3 -m pip install -r bazi/scripts/requirements.txt
```

The first time a skill runs a script, Claude Code asks for permission to run `python3 ...`. Allow it. If you refuse, the skill stops and says so; it does not calculate by hand instead.

### Option B: try it from the repository without installing

```bash
claude --plugin-dir /path/to/Numerologist_skills
```

This applies to that session only and does not change global settings.

### Option C: MCP server (Claude Desktop and other MCP clients)

```bash
python3 -m pip install -r mcp-server/requirements.txt
```

```bash
claude mcp add numerologist -- python3 /path/to/Numerologist_skills/mcp-server/server.py
```

Claude Desktop: add to `mcpServers` in `claude_desktop_config.json`:

```json
"numerologist": {"command": "python3", "args": ["/path/to/Numerologist_skills/mcp-server/server.py"]}
```

The server has five tools: `bazi_chart`, `ziwei_chart`, `qimen_chart`, `liuyao_chart`, `numerology_chart`.

## 2. How to ask

Ask in plain language, in Vietnamese, Chinese or English. The skill asks for anything missing (gender, birth time, the question at hand…). Giving everything up front is faster.

| System | What to give | Example question |
|---|---|---|
| Bazi | birth date and time, gender, birthplace | "Draw a Bazi chart for a woman born 10:00 on 15 May 1990 (solar calendar) in Hanoi. How is the current luck period?" |
| Zi Wei | birth date and time, gender; for a lunar date, say whether it is a leap month | "Zi Wei chart for a man born 14:30 on 16 Aug 2000 (solar). Look at the Career palace and the year 2027." |
| Qimen | a specific matter, the time of asking, where you are | "Use Qimen: is signing a contract to the east at 15:00 this afternoon favourable?" |
| Liu Yao | one specific matter; the six coin tosses from bottom to top, or ask the script to toss | "I tossed 7, 8, 9, 7, 6, 8 (bottom up) at 10:00 today; will I pass the interview?" |
| Numerology | solar birth date, full birth name | "Numerology for Nguyen Van An, born 15 May 1990: life path, birth chart, personal year 2026." |

Liu Yao coin toss: toss 3 coins, count the inscribed face as 3 and the back as 2, and add them (this convention has not been checked against the classics; some books count the other way). 6 and 9 are moving lines. Record 6 tosses from the bottom up. Without coins, say "toss for me"; the script tosses with a secure random generator and returns each toss.

## 3. Calculation options

Schools differ on some points. The scripts have defaults and record the method used in the result's `ruleset`. To change one, tell Claude, for example "use true solar time".

| Option | Applies to | Default | When to change |
|---|---|---|---|
| Vietnamese / Chinese lunar calendar (`calendar_locale`) | Bazi, Zi Wei, Qimen | `cn` | For a date in the Vietnamese lunar calendar, say "Vietnamese lunar calendar". The two differ by a day in a few months per decade, occasionally by a whole month (Tet 1985: Vietnam 21 Jan, China 20 Feb). When they differ on that date, the result warns and lists both. |
| Zi hour (`late_zi_rule`) | Bazi, Zi Wei, Liu Yao | 23:00 starts the next day | Your teacher or software uses "night Zi" (23:00–24:00 stays on the same day). |
| True solar time (`true_solar_time`) | Bazi, Zi Wei, Qimen | off | Birthplace far from the time-zone meridian (north-west Vietnam, Xinjiang…) or your teacher asks for it; needs the birthplace longitude. |
| Leap month (`leap_month_rule`) | Zi Wei | days 1–15 count as this month, 16 onward as the next | Match the software you compare with. The Ziwei Doushu Quanshu counts the whole leap month as the next month (`next`). |
| Ren-year transformation (`sihua_rule`) | Zi Wei | `zuofu`: Zuofu takes hua ke | `quanshu` to follow the Ziwei Doushu Quanshu (Tianfu takes hua ke). |
| Life path reduction (`life_path_rule`) | Numerology | `vn`: 2–11, 22/4, 33/6 | `classic` for Western books (1–9, 11, 22, 33); `phillips` to follow Phillips exactly (33 counts as 6; first pinnacle age 36 − 10 or 11). |
| Summing method (`life_path_method`) | Numerology | add every digit | If results differ from another app, try reducing day, month and year separately. |

Common warnings in results (Claude will relay them):

- Birth time within ±15 minutes of a shichen boundary: check both shichen.
- Birth within ±24 hours of a solar term: the month pillar, sometimes the year pillar, may change if the birth time is off.
- Birth during daylight saving time (China 1986–1991): clocks were one hour ahead.
- Birth in South Vietnam between 1968 and 13 June 1975: clocks there ran on UTC+8 and lunar dates followed the traditional calendar (Tet 1968: South 30 Jan, North 29 Jan).

## 4. Run the scripts directly (without Claude)

Each script reads one JSON file and writes one JSON file:

```bash
python3 bazi/scripts/bazi_cli.py --input input.json --output output.json
```

Example `input.json` for Bazi:

```json
{"birth_time": "1990-05-15 10:00", "gender": "女", "calendar_locale": "vn", "query_year": 2026}
```

The input fields of each system are in its `SKILL.md` (the section on calling the script). Input errors appear in the `error` field of the output.

## 5. Troubleshooting

| Symptom | Fix |
|---|---|
| `command not found: python` | Use `python3`; the skills already call `python3`, only commands you type yourself need changing. |
| `ModuleNotFoundError: lunar_python` or the error "缺少依赖 lunar_python" | `python3 -m pip install -r <skill>/scripts/requirements.txt`. A Homebrew Python may also need `--break-system-packages`, or use a venv. |
| Claude calculates by hand instead of running the script | Say "use the … skill and run the script". Check that you allowed the `python3` command. |
| Results differ from other software or a teacher | Ask which method they use (Vietnamese or Chinese lunar calendar, Zi hour, true solar time, leap month) and ask for a recalculation with that method. |
| Zi Wei chart has no Tuan or Triet | The script follows the Chinese San He school and does not yet place the stars specific to Vietnamese Zi Wei. |

## 6. For developers

```bash
python3 -m pip install -r requirements-dev.txt
```

```bash
pytest -q
```

- Edit shared code only in `core/`, then run `python3 tools/sync_core.py`. CI checks with `python3 tools/sync_core.py --check`.
- Measure interpretation quality (paid, about $0.45 per run with Haiku, 3 runs per case):

```bash
claude plugin eval . --model haiku --runs 3 --allow-tools 'Bash(python:*)' 'Bash(python3:*)' Write --no-publish
```

  The machine's `python3` must be able to import `lunar_python`, or the Bazi, Zi Wei and Liu Yao cases fail.
