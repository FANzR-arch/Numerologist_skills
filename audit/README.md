# Source audit registry

Overall plan: [docs/source-audit-plan.md](../docs/source-audit-plan.md).

| File | Contents | Who edits |
|---|---|---|
| `rules.json` | One entry per audit unit: constant table, function, `ruleset` field, doc file | `tools/audit.py sync` creates the skeleton; contributors fill in `claim`, `sources`, `verdict`, `notes`, `tests` |
| `sources.json` | Source catalogue: tier T1–T4, language, `lineage`, edition | Contributors |
| `cases/<engine>/<id>.json` | Golden cases copied from worked examples printed in books | Contributors |

## Commands

```bash
python3 tools/audit.py sync
```

Run after every change to code or docs in a skill. It adds new units, removes units that no longer exist, and updates locations and fingerprints. Human-entered fields are kept.

```bash
python3 tools/audit.py check
```

CI runs this. It fails when the registry is out of sync with the code or malformed. It prints a coverage table per engine and lists `stale` entries: audited, but the code changed since, so they need re-auditing. After re-auditing, set `stale` to `false` in `rules.json`. Moving lines does not count as a change.

Renaming a function or constant creates a new unit; the old unit is removed and listed under `removed` by `sync`. If the old unit was audited, copy its fields to the new id.

## Filling in an entry

```json
{
  "id": "liuyao.table.NAJIA",
  "claim": "Jing Fang najia: Qian inner 甲子 甲寅 甲辰, outer 壬午 壬申 壬戌; …",
  "sources": [
    {"id": "jingshi-yizhuan", "locator": "<edition>, vol. …, p. …", "stance": "agree"},
    {"id": "zengshan-buyi", "locator": "<edition>, ch. …, p. …", "stance": "agree"}
  ],
  "verdict": "confirmed",
  "notes": "",
  "tests": ["liuyao/scripts/tests/test_liuyao_cli.py::TestNajiaAndLiuqin"]
}
```

`verdict`:

- `unverified`: not yet checked. The default.
- `confirmed`: needs at least one T1/T2 source and two sources of different `lineage`.
- `variant`: sources disagree. The rule must be a script parameter; `sources` lists the sources for each side.
- `conflict`: the code differs from the sources and has not been changed. Explain in `notes`.
- `not_applicable`: not a divination rule (input parsing, I/O). `notes` is required.

Rules:

- Record a `locator` (edition, volume, page) only for a page you actually read.
- No long quotations and no scans in the repository.
- Blogs are not sources.
- Once a specific edition is in hand, fill in `edition` and `access` in `sources.json` and set `verified: true`.

Write `claim`, `notes` and `locator` in English; keep proper names and quoted classical text as in the source.

## Golden cases

```json
{
  "source": {"id": "zengshan-buyi", "locator": "<edition>, p. …, example …"},
  "input": {"time": "…", "lines": [7, 8, 9, 7, 6, 8]},
  "expect": {"hexagram.name": "雷火丰", "lines.1.liuqin": "官鬼"}
}
```

`expect` uses dotted field paths, with list items numbered from 0. `audit/tests/test_golden_cases.py` runs every case. When a case fails, trace the cause: a code bug, a variant, or a misprint. Never edit a case to match the code.
