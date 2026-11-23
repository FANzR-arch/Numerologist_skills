# Source audit plan

Started 2026-11-22. Status (2026-11-23): phases A0–A7 done; results per phase in section 8, open items in section 10.

## Goal

Every calculation rule and every interpretation passage in the repository should trace back to at least two authoritative sources (classic texts, scholarly commentary, calendar standards), with the edition and page recorded. Blogs are only leads for finding sources, never evidence.

The end result is a machine-readable rule registry. CI checks the registry, and each rule links to tests built from worked examples printed in the books.

## 1. State after the audit

Entries in `audit/rules.json` by outcome (run `python3 tools/audit.py check` for the latest table):

| Area | Checked against | Main result | Still missing |
|---|---|---|---|
| Calendar (`core/`) | Aslaksen, Hong Kong Observatory tables, NOAA, tzdb, Ho Ngoc Duc | 6 `confirmed`; 1 `conflict` (Vietnamese lunar calendar before 1967) | full text of GB/T 33661 |
| Liu Yao | 京氏易傳, 增刪卜易, 火珠林, 黃宗羲 | 12 `confirmed` (64 hexagrams, 8 palaces, shi/ying, najia, six relations, six spirits) | coin-face convention; King Wen order (one source) |
| Bazi | 淵海子平, 三命通會, 神峰通考, 滴天髓闡微 | 3 `confirmed`; hidden stems and ten gods sourced and tested | year/month change at solar terms, late Zi hour (no source sentence yet) |
| Qimen | 煙波釣叟歌, 奇門遁甲統宗, 遁甲演義 | 8 `confirmed`; 1 `conflict` (拆補 vs 置閏) | eight gods and star/door home palaces only partly have two sources |
| Zi Wei | 紫微斗數全書 | star placement, brightness, five-element bureau match the book, but only one source lineage | a second book (全集, 王亭之, Thai Thu Lang) |
| Numerology | Phillips, Decoz (previews) | arrow names, `phillips` rule; 1 `conflict` (maturity number) | meaning of each number, the Y rule; every source is T3 |
| Interpretation (`references/`) | the books above | every section labelled with a source, "partial", or "not checked" | most detailed explanations |

## 2. Source tiers

| Tier | Kind | Examples | Used to |
|---|---|---|---|
| T1 | Classics, original texts, official standards | 《京氏易传》, 《渊海子平》, 《紫微斗数全书》, GB/T 33661-2017 | Establish a rule |
| T2 | Scholarly commentary, reputable authors with clear editions, mathematical/astronomical work | 徐乐吾《子平真诠评注》, Reingold & Dershowitz *Calendrical Calculations*, Aslaksen *The Mathematics of the Chinese Calendar* | Explain and choose between variants |
| T3 | Popular practice books with an ISBN | Vietnamese translations, Japanese and English books | Record the convention common in each market |
| T4 | Independent software | iztro, Ho Ngoc Duc's lunar calendar program | Cross-check cases; the code lineage must be stated |
| — | Blogs, forums, videos, AI-generated content | | Leads only |

Acceptance rules:

- A rule is "confirmed" when it has at least one T1 or T2 source plus one other independent source from T1–T3.
- Two programs of the same lineage count as one source. For example, `lunar_python`, `lunar-javascript`, `lunar-typescript` and iztro (which uses `lunar-typescript`) are one lineage.
- When sources disagree, nothing is chosen silently. The rule becomes a parameter with a default (like `late_zi_rule`), and the registry records why the default was chosen with sources for each side.

## 3. Sources to find, by system and language

Legend: ✓ means the work certainly exists; edition, ISBN and pages still need checking with the book in hand. (?) means the title is uncertain and must be verified before entering the registry.

### Calendar (shared)

- ✓ GB/T 33661-2017《农历的编算和颁行》: rules for the Chinese lunar calendar, including new moons, solar terms and leap months.
- ✓ Helmer Aslaksen, *The Mathematics of the Chinese Calendar*: includes a section on the Vietnamese calendar and the "2033 problem".
- ✓ Edward Reingold, Nachum Dershowitz, *Calendrical Calculations*: chapter on the Chinese calendar with an independent algorithm.
- ✓ Ho Ngoc Duc, articles and program on the Vietnamese lunar calendar (UTC+7, the 1967–1968 change).
- ✓ Hong Kong Observatory (香港天文台) solar–lunar conversion tables. ✓ National Astronomical Observatory of Japan (国立天文台 暦計算室): times of the 24 solar terms. Both serve as test cases for solar terms.

### Bazi

- T1: ✓《渊海子平》, ✓《三命通会》 (万民英), ✓《子平真诠》 (沈孝瞻), ✓《滴天髓》, ✓《穷通宝鉴》.
- T2: ✓ 徐乐吾《子平真诠评注》 and《滴天髓补注》. ✓ 任铁樵's commentary《滴天髓阐微》.
- Vietnamese: translations of 邵伟华 (Thieu Vi Hoa), such as《四柱预测学》, Vietnamese title "Dự đoán theo tứ trụ" (?).
- Japanese: ✓ 阿部泰山 (the Japanese 四柱推命 tradition).
- English: ✓ Joey Yap, BaZi books (T3, commercial).
- Check: hidden stems, ten gods, twelve stages, luck periods at "3 days = 1 year", the period before the first luck period, the Zi hour rule (早子/夜子).

### Zi Wei

- T1: ✓《紫微斗数全书》, ✓《紫微斗数全集》.
- T2: ✓ 王亭之 (Zhongzhou school 中州派).
- Vietnamese: ✓ Vân Đằng Thái Thứ Lang, *Tử Vi Đẩu Số Tân Biên*. ✓ Thiên Lương, *Tử Vi Nghiệm Lý*. These underpin the "Vietnamese school" (Tuan, Triet…).
- Japanese: ✓ 鮑黎明 (Zi Wei books in Japanese).
- Check: the 14 major stars, minor stars, four transformations by year stem, leap-month handling, five-element bureau, life and body lords.

### Qimen

- T1: ✓《烟波钓叟歌》, ✓《奇门遁甲统宗》, ✓《御定奇门宝鉴》.
- T2: ✓ 张志春《神奇之门》.
- Japanese: ✓ 黒門 (Qimen Dunjia books).
- Check: ju determination (置闰 vs 拆补), placing zhifu and zhishi, center-palace handling (寄坤 and alternatives), definitions of the patterns the script detects (fuyin, fanyin, men po…).

### Liu Yao

- T1: ✓《京氏易传》 (origin of the eight palaces, shi/ying, najia). ✓《火珠林》.
- T2: ✓《增删卜易》 (野鹤老人). ✓《卜筮正宗》 (王洪绪). ✓《易冒》.
- Vietnamese: translations "Tăng San Bốc Dịch" and "Bốc Phệ Chính Tông" (?). Translator and publisher must be verified.
- Check: all of `HEXAGRAMS`, `NAJIA`, `GENERATIONS`, six spirits by day stem, the hidden-spirit rule, the use-god table.

### Numerology

- T2/T3: ✓ David A. Phillips, *The Complete Book of Numerology*. Said to be the origin of the method popular in Vietnam (birth chart, arrows); to be confirmed.
- T2/T3: ✓ Hans Decoz, *Numerology: Key to Your Inner Self*. ✓ Matthew Oliver Goodwin, *Numerology: The Complete Guide*. ✓ Juno Jordan, *The Romance in Your Name*. These represent the Western "classic" method.
- Vietnamese: the translation of Phillips sold in Vietnam (?). Title, translator and publisher must be verified.
- Check: the `vn` and `classic` reductions, the `digits` and `components` methods, arrow names and definitions, pinnacles and challenges, the Y rule, all of `y-nghia-so.md`.

## 4. Audit unit: the rule registry

The `audit/` directory:

```
audit/
  sources.json      # source catalogue
  rules.json        # one entry per rule
  cases/            # golden cases copied from book examples (input, expected output, citation)
```

(JSON instead of YAML to avoid a dependency; the tool is one file, `tools/audit.py`, with `sync` and `check`.)

`sources.json`, one entry per source (shown as YAML for readability):

```yaml
- id: jingshi-yizhuan
  title: 京氏易传
  author: 京房
  language: zh
  tier: T1
  edition: "<publisher, year, ISBN>"
  access: "ctext.org / print copy / photos supplied by the maintainer"
```

`rules.json`, one entry per rule:

```yaml
- id: liuyao.palace.generations
  engine: liuyao
  code: liuyao/scripts/liuyao_cli.py:GENERATIONS
  claim: "Eight palaces: shi line of the pure hexagram at line 6, first to fifth generation at lines 1-5, wandering soul at line 4, returning soul at line 3"
  sources:
    - {id: jingshi-yizhuan, locator: "vol. 上, p. …", stance: agree}
    - {id: zengshan-buyi, locator: "…", stance: agree}
  verdict: confirmed        # confirmed | variant | conflict | unverified
  tests: [liuyao/scripts/tests/test_liuyao_cli.py::TestPalaces]
```

- `verdict: variant` is used when sources disagree. The rule must then be a script parameter, and the entry records the sources for each side.
- Citations record only the location (volume, page) and a very short quote when truly needed. No long quotations and no scans in the repository. Explanations are in our own words.

## 5. Golden cases from books

Worked examples printed in books are the strongest oracle, because they are independent of both the code and the model. Examples: sample charts in 《紫微斗数全书》, sample hexagrams in《增删卜易》, cases in《子平真诠评注》, sample tables in Phillips.

- Each case goes in `audit/cases/<engine>/<id>.json`: input, expected output fields, and `source` (id + page).
- One parametrised test reads all of `audit/cases/` and runs each case through the engine's `build_output`.
- A failing case is never edited to match. Trace whether the cause is the code, a variant, or a misprint in the book, and record the finding in `rules.json`.

## 6. Process for each rule

1. **Extract**: list rules automatically from the code (constant tables, `ruleset` fields) with `python3 tools/audit.py sync`. Never by hand.
2. **Find sources**:
   - Public-domain classics: search ctext.org and zh.wikisource, record the location.
   - Copyrighted books: the maintainer supplies photos of the relevant pages; the contributor reads, compares and records the location.
3. **Compare**: cell by cell for tables, not just the general idea.
4. **Record the verdict** in `rules.json`. On disagreement: make the rule a parameter, or record the default with reasons.
5. **Add golden cases** when the book has examples.
6. **Review**: a different reviewer checks the citations against the same document, not from memory. Each engine also gets a review by someone who knows the system.

## 7. Tools and automated checks

- `tools/audit.py sync`: builds the rule list from the code. `check` reports rules in the code that the registry lacks.
- `tools/audit.py check` (run in CI):
  - Every rule has a `verdict`.
  - `confirmed` rules have a T1 or T2 source plus an independent source.
  - Every source `id` exists in `sources.json`.
  - Every referenced test exists.
- Coverage report: share of `confirmed` / `variant` / `conflict` / `unverified` rules per engine, printed in CI.
- Reuse what exists: arithmetic oracle tests, the iztro cross-check (recorded as T4, same lineage as `lunar_python`), and the eval suite.

## 8. Phases and results

| Phase | Scope | Result |
|---|---|---|
| A0. Framework ✅ | `audit/`, `tools/audit.py sync/check`, golden-case loader, CI | 231 units (tables, functions, `ruleset` fields, docs) extracted automatically; 19 `not_applicable` with reasons; the rest `unverified`; 37 sources in `sources.json` (editions not yet verified) |
| A1. Calendar (public sources ✅) | Read in full: Aslaksen (2010 draft), Hong Kong Observatory tables 1985/2007/2024/2033, ytliu0 (per GB/T 33661), NOAA, tzdb 2026f, Ho Ngoc Duc calrules_en.html (2008 Wayback copy). Not readable: GB/T 33661 full text, NAOJ tables | core: 6 `confirmed` (month numbering, leap month, new-moon day, solar terms, cn and vn conversion from 1967), 1 `conflict` (Vietnamese calendar before 1967: Aslaksen says the Beijing meridian, the code uses 120°E; Ho Ngoc Duc is silent on this period), the rest `unverified`; 19 golden cases. Fixed: equation of time per NOAA (366 days in leap years, UTC); the South Vietnam warning ends on 13 June 1975 per tzdb |
| A2. Numerology (previews ✅) | Read Google Books previews: Phillips (Hay House 2005) chapters 6–7 and excerpts of chapters 11, 13; Decoz (Perigee 2001) pp. 6, 20–21, 220, 262–263. Not read: Goodwin, Jordan, Vietnamese translations, Phillips's chapters on number meanings | Arrow names sourced (Phillips). Added the `phillips` rule (33 counts as 6; first pinnacle age 36 − 10/11). 21 golden cases. 1 `conflict` (maturity number: Decoz reduces to one digit). Nothing `confirmed` because numerology has no T1/T2 source. Still unsourced: number meanings, personal year, the Y rule, the `vn` rule keeping 33 |
| A3. Liu Yao (tables ✅) | Read in full on Wikisource: 京氏易傳 (四庫), 增刪卜易 (ch. 1–7, 11, 12, 18, 28, 八宮圖), 火珠林, 黃宗羲《易學象數論・占課》, 序卦傳. Not read: 卜筮正宗, 易冒 | 12 `confirmed`: the 64-hexagram table, 8 palaces and shi/ying (all 64 hexagrams compared automatically with both 增刪 and 京氏), najia, six relations, six spirits. 13 golden cases. Still `unverified`: King Wen order (only 序卦傳), coin-face convention (possibly the reverse of 單拆重交), xunkong/month break, Vietnamese hexagram names, `yongshen.md` |
| A4. Bazi (calculation rules ✅) | Read in full on Wikisource: 淵海子平, 三命通會 vols. 1–4, 神峰通考, 滴天髓闡微, 穷通宝鉴. Not read: 子平真詮 (not on Wikisource), 徐乐吾's commentary | 3 `confirmed`: heavenly stems, stem elements, luck-period rule. Hidden stems (as sets) and ten gods match 淵海 + 神峰, with a test; they live in a doc unit, handled in A7. 416 of 502 stem-branch runs in 滴天髓闡微 have luck periods adjacent to the month pillar (filtered by script). 5 golden cases rebuilt from luck-period examples (三命通會, 神峰通考). No source sentence yet: year change at Lichun, month change at solar terms, late Zi hour, elements of the six combinations |
| A5. Zi Wei (全書 ✅) | Read in full: 紫微斗數全書 vols. 1–3 on Wikisource. The 續道藏《紫微斗數》 is a different system. Not read: 全集, 王亭之, Thai Thu Lang | Matches 全書: 14 major stars, minor stars, brightness table (168/168 cells), five-element bureau (58/60 nayin), life and body lords; 6 golden cases. Not confirmed: only one source lineage. 1 `conflict`: Ren-year transformation (全書: Tianfu takes hua ke; code: Zuofu). Variants to decide: leap month (全書 counts it as the next month), Kui/Yue for Bing/Ding and Xin, where the first decade starts |
| A6. Qimen (ju and plate setup ✅) | Read in full on Wikisource: 煙波釣叟歌, 奇門遁甲統宗, 遁甲演義 (四庫). Not read: 御定奇門寶鑑, 神奇之門 | 8 `confirmed`: yang/yin dun by solar term, earth plate, six yi, star elements, three qi, three yuan. Eight gods and star/door home palaces only partly have two sources. Ju numbers match 統宗 for all 24 terms (one source). 3 golden cases from 遁甲演義 examples. 1 `conflict`: the code uses 拆補 on its own; both books teach 超神接氣置閏. Variants recorded: 勾陈/朱雀 vs 白虎/玄武; whether the center palace lodges with Kun or Gen |
| A7. Interpretation (labels ✅) | `SKILL.md` and `references/` of all five systems. The maintainer chose (2026-11-23) to keep the content and label it rather than remove it | Every section in references is labelled with a specific source (出处), "partial" (部分), or "not checked against the classics" (未核对古籍 / chưa đối chiếu sách); each SKILL.md tells the model to say so when it uses unsourced material. Also found: the 北斗/南斗 grouping in stars.md differs from 全書; 全書's verdict on 命無正曜 is harsher than the docs. Remaining: most detailed explanations are unsourced and need printed books or experts |

Order of work: calendar first because every engine depends on it; numerology and Liu Yao next because they had no book sources at the start.

## 9. Roles

- **Contributor** (a person or an AI tool):
  - Extracts rules from the code with `tools/audit.py sync`.
  - Finds public-domain classics on ctext.org and Wikisource.
  - Reads page photos of copyrighted books supplied by the maintainer.
  - Fills in the registry, writes tests and golden cases; compares tables cell by cell.
  - Never records a citation location they have not actually read.
- **Reviewer**: checks citations against the cited document itself, not from memory.
- **Maintainer / expert**:
  - Buys or borrows copyrighted books and photographs the needed pages.
  - Settles defaults when schools differ.
  - Reviews the Vietnamese interpretation text.

## 10. Open items

1. Default lunar calendar for Vietnamese-speaking users: still `calendar_locale: cn`; SKILL.md tells the model to pass `vn` when the user gives a date in the Vietnamese lunar calendar.
2. Vietnamese Zi Wei school (placing Tuan, Triet…): not done.
3. Printed books still missing: 紫微斗數全集, 王亭之's books, Thai Thu Lang, 子平真詮, the full Phillips, Vietnamese translations.
4. No expert in each system has reviewed the conclusions yet; so far only book sources and cross-review.
5. Unfixed `conflict` entries: the Vietnamese lunar calendar before 1967, the maturity number (numerology). The Liu Yao coin-face convention is still `unverified`.
