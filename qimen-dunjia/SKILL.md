---
name: qimen-dunjia
description: >
  奇门遁甲排盘、解盘、择时、方位判断与理论教学技能。用户明确提到奇门遁甲、时家奇门、
  奇门排盘、奇门解盘、奇门择吉、方位选择、趋吉避凶，或要求“用奇门”分析一件具体事情时，
  必须使用本技能。正式排盘前先做结构化访谈，再调用脚本完成固定计算，最后再做解读与建议。
  即使问题很短（只问某个时辰的局），也必须用本技能并运行脚本，不要心算。
compatibility: Requires Python 3.11+, lunar_python, and tzdata; run scripts/qimen_cli.py for all fixed calculations.
---

# 奇门遁甲技能

本技能面向普通求测者，默认使用 `mainline-cn-v1` 规则集。工作方式是：

1. 先访谈，确认用户到底要看什么、看哪一刻、想判断什么。
2. 再用脚本做固定计算，不靠心算排盘。
3. 最后再用奇门规则做解读、建议和风险提醒。

不要跳过访谈，不要在信息不完整时硬算，也不要把完整内部推理链直接展示给用户。

## 触发范围

以下场景应使用本技能：

- 用户要求正式奇门排盘或解盘。
- 用户要求用奇门判断一件具体事情能不能成、何时动、往哪边走、避开什么。
- 用户要求奇门择时、方位选择、趋吉避凶建议。
- 用户要求讲解奇门理论、格局、用神、盘例。

以下场景不要直接进入正式排盘：

- 用户只是在闲聊玄学，没有明确要用奇门。
- 用户信息太少，连事情类型和时间都没给。
- 用户要求其他流派，而当前规则集不支持。

## 总原则

- 默认规则集固定为 `mainline-cn-v1`，不要在正式排盘路径里混用其他流派。
- 正式排盘前必须先访谈。
- 固定计算一律调用 `scripts/qimen_cli.py`。
- 不展示完整推理链，只展示关键依据和必要计算结果。
- 重大决策、疾病、法律、投资等高风险主题，必须附现实建议。
- 不用恐吓式语言，不说“必败”“必死”“无救”。
- `references/` 中各节注明了古籍出处；标「未核对古籍」或「部分」的内容是现代整理，向用户转述时要说明这是现代说法、不是古籍原文，不要说成古法定论。

## 默认规则

当前内置规则固定如下：

- 体系：时家转盘奇门
- 默认时区：`Asia/Shanghai`
- 默认适用区域：中国大陆优先
- 定局：拆补法（按起局时刻所处节气取局，现代软件通行）。《奇门遁甲统宗》《遁甲演义》用超神接气置闰，符头与节气错开的日子局数可能不同；用户的软件或老师用置闰法时要说明差异。
- 中宫/寄宫：中宫相关判断一律寄坤处理

详细规则见 `references/ruleset-mainline.md`。

如果用户明确要求别的流派：

1. 先直说当前技能默认使用 `mainline-cn-v1`。
2. 问用户是否接受先按这套规则排。
3. 如果不接受，不进入正式排盘，只做理论讨论或说明当前版本不支持。

## 工作流

### 第 1 步：先访谈

正式排盘前，必须先做两段式访谈。

先问第一轮核心问题，语言要直白：

1. 你要看什么事？一句话说清。
2. 事情对应的时间是什么？如果就是现在，直接说“现在”。
3. 你人在哪个城市？如果不在中国大陆，请直接说国家/城市。
4. 你最想判断什么？比如能不能成、什么时候动、选哪边、要避开什么。
5. 这件事现在进展到哪一步了？
6. 你要“直接结论”还是“详细讲解”？

第二轮按条件追问：

- 只有日期，没有具体时辰：补问具体小时，至少补到时辰。
- 给的是农历：补问是否闰月。
- 人在海外：补问时区或城市。
- 问题太泛：补问“你最想判断哪一个结果”。
- 高风险主题：补问是否也需要现实建议，并提醒医生、律师、财务顾问等专业帮助。

访谈模板见 `references/interview.md`。

### 第 2 步：决定是否进入正式排盘

只有在以下信息确认后，才进入正式排盘：

- 事项类型明确
- 时间明确
- 地点或时区明确到可计算
- 判断目标明确

如果没收齐，只继续追问，不要先排盘。

如果用户只是想学习理论：

- 先问他想学什么。
- 不直接进入正式排盘。
- 可以结合 `references/examples.md` 做教学。

### 第 3 步：调用脚本做固定计算

**前置：确认依赖已安装**

执行正式排盘前先检查依赖。如果未安装，先运行：

```bash
python3 -m pip install -r "<skill_dir>/scripts/requirements.txt"
```

**执行脚本**

脚本路径以本 skill 目录为基准，记为 `<skill_dir>`（本 SKILL.md 所在目录；作为 Claude Code 插件安装时，即加载本 skill 时给出的 base directory）：

```bash
python3 "<skill_dir>/scripts/qimen_cli.py" \
  --input "tmp/qimen_input.json" \
  --output "tmp/qimen_output.json"
```

**写入与运行（必须照做）**：用 Write 工具在当前工作目录下创建 `tmp/qimen_input.json`（Write 需要绝对路径，即 `<当前工作目录>/tmp/qimen_input.json`；下面命令里的相对路径 `tmp/...` 指向同一文件）；不要用 shell heredoc、`echo >`、`mkdir && ...` 等组合命令写文件。然后单独运行上面那一条 `python3` 命令（不加 `cd`、`&&` 或管道），再用 Read 读取输出文件。这样用户只需授权一条 python3 命令；命令被拒绝时，告诉用户需要允许运行该 python 脚本，不要改为手算。命令用 `python3`；只有 `python3` 不存在（如部分 Windows）时才改用 `python`。`python3` 能运行脚本即说明依赖已装好，不要再去安装。

输入 JSON 最低字段：

```json
{
  "question_type": "",
  "question_goal": "",
  "time_input": "",
  "calendar_type": "solar|lunar|now",
  "location": {
    "country": "",
    "city": "",
    "timezone": "",
    "longitude": null
  },
  "true_solar_time": false,
  "calendar_locale": "cn|vn",
  "ruleset": "mainline-cn-v1"
}
```

- `calendar_locale` 默认 `cn`；越南用户用阴历报时间时传 `vn`。只影响农历输入换算与输出的农历日期，起局按节气与干支，不受影响。
- `true_solar_time` 可选，默认按所给时区的钟表时间起局。用户要求按真太阳时起局时传 `true`，并给 `location.longitude`（东经为正）；明细见输出 `normalized_input.true_solar_time`，口径见 `ruleset.time_rule`。

使用要求：

- 由你把访谈结果整理成输入 JSON。
- 固定计算必须以脚本输出为准。
- 如果脚本不可用，不要手算顶替；要明确告诉用户当前版本需要脚本才能正式排盘。

### 第 4 步：阅读脚本输出

重点读取以下字段：

| 字段 | 用途 |
|------|------|
| `normalized_input` | 确认时间、时区、事项被正确解析 |
| `calendar` | 公历/农历对照、当前节气（二十四节气，含中气） |
| `ganzhi` | 年月日时干支、日旬、时旬（用于定旬首/旬空） |
| `chart.dun_type` | 阴遁/阳遁 |
| `chart.yuan` | 上元/中元/下元 |
| `chart.ju_number` | 局数（1-9）|
| `chart.xunshou` | 旬首（如"甲子"）|
| `chart.hidden_yi` | 旬首奇仪（寄宫的隐干，如"戊"）——**不可遗漏** |
| `chart.kongwang` | 时旬空地支（如["寅","卯"]），影响当前时辰 |
| `chart.kongwang_palaces` | 时旬空对应宫位编号 |
| `chart.day_kongwang` | 日旬空地支，影响整日大环境 |
| `chart.day_kongwang_palaces` | 日旬空对应宫位编号 |
| `chart.time_stem_visible` | 时干（代表所问之事/当前动态，**取用神的关键参考**）|
| `chart.day_stem` | 日干落宫：`{ stem, palace, note }`（代表求测者本人）|
| `chart.year_stem` | 年干落宫：`{ stem, palace, note }`（代表上级/大环境）|
| `chart.month_stem` | 月干落宫：`{ stem, palace, note }`（代表同事/同龄竞争者）|
| `chart.hour_yima` | 时马：`{ branch, palace, source_branch }`，按时支取（出行/变动类问题优先看）|
| `chart.day_yima` | 日马：`{ branch, palace, source_branch }`，按日支取（看整日的变动）|
| `chart.zhifu` | 值符：`{ palace, star }`，随时干落宫 |
| `chart.zhishi` | 值使：`{ palace, door, raw_palace, hours_from_xunshou }`，从旬首宫逐时移宫，**与值符分别落宫** |
| `chart.center_hosting` | 中宫随转：`{ hosted_star: 天禽, center_stem, earth_host_palace: 2, sky_palace, follows_star: 天芮 }` |
| `chart.door_index` | 门→宫反查字典，如 `{"开门": 7, "生门": 1, ...}`——**按用神直接定位** |
| `chart.star_index` | 星→宫反查字典，如 `{"天心": 7, "天芮": 9, "天禽": 9, ...}`（天禽与天芮同宫）|
| `chart.detected_patterns` | 格局自动检测结果数组，每项含 `name`、`palace`、`detail`、`nature(吉/凶/中)` |
| `chart.palaces` | 9 宫完整数组（详见下方） |
| `warnings` | 边界提醒、寄宫提醒等 |

**`chart.palaces` 每宫字段：**

| 字段 | 说明 |
|------|------|
| `palace` | 宫号（1-9）|
| `name` / `direction` / `trigram` / `element` | 宫名/方位/卦/五行 |
| `earth_stem` / `sky_stem` | 地盘干 / 天盘干 |
| `sky_stems` | 该宫全部天盘干；天芮所落之宫会多一个随转来的中五地盘干 |
| `hosted_sky_stem` / `hosted_stem_relation` | 随天芮转来的中五地盘干 / 它与本宫地盘干的关系 |
| `stem_relation` | 天地盘干五行关系：比和/天生地/地生天/天克地/地克天 |
| `star` / `star_element` / `star_palace_relation` | 星名 / 星五行 / 星与宫的五行关系（生/被生/克/被克/比和）|
| `hosted_star` | 随天芮转来的天禽，只在天芮所落之宫为 `天禽` |
| `door` / `door_element` / `door_palace_relation` | 门名 / 门五行 / 门与宫的五行关系——**门迫 = 门克宫（`克`），宫克门（`被克`）是门受制** |
| `god` | 八神名 |
| `is_center` / `hosts_center` / `hosts_center_sky` / `hosting_note` | 中宫标记：`hosts_center` 是地盘寄坤（坤二），`hosts_center_sky` 是天禽与中干随天芮落宫 |

**注意事项：**

- `chart.palaces` 中 5 号宫（中宫）`star`、`door`、`god` 都为 `null`，天禽已随天芮转出，不参与常规用神判断。
- 2 号宫（坤宫）`hosts_center: true`，承载中五地盘干；天禽和中干在天盘上落在 `chart.center_hosting.sky_palace`。
- 值符、值使各自移宫，通常不同宫；不要默认两者同落时干宫。
- 驿马分时马、日马两个字段，解读时说明用的是哪一个。
- `chart.time_stem_visible` 是时干的明干（显干），用于判断所问之事在盘中的代表位置。
- `chart.day_stem.palace` 是日干落宫，代表求测者本人的位置。
- `chart.door_index` 可直接用 `chart.door_index["开门"]` 快速找到事业用神所在宫。
- `chart.detected_patterns` 中 `nature: "凶"` 的格局（伏吟、反吟、门反吟、门迫、吉门受制）需要在解读中重点提示。反吟、门反吟是整盘翻转，八宫会同时出现，解读时合并成一句说。
- 八神阳遁顺布、阴遁逆布，`god` 字段已按此排好。
- 如果 `warnings` 里出现边界提示、中宫寄宫提示，要在解读里明确说明。

### 第 5 步：解读与输出

正式排盘响应统一按这个结构：

1. 已确认信息
2. 使用规则与默认项
3. 盘面摘要
4. 用神与关键依据
5. 核心判断
6. 方位 / 时机 / 行动建议
7. 风险提醒与免责声明

#### 已确认信息

用直白语言复述：

- 看什么事
- 起局时间
- 地点 / 时区
- 想判断什么
- 输出偏好（直接结论 / 详细讲解）

#### 使用规则与默认项

必须写明：

- 当前使用 `mainline-cn-v1`
- 时区是否默认 `Asia/Shanghai`
- 是否按“现在”起局
- 如果有寄宫、中宫、边界提醒，也写明

#### 盘面摘要

只讲关键计算结果，不堆砌无意义术语：

- 阴遁 / 阳遁
- 局数
- 旬首
- 旬空
- 值符
- 值使

必要时可列出简洁宫位摘要，不要求把每一步内部推演全展示出来。

#### 用神与关键依据

按事项取用神，优先参考 `references/yongshen.md`。

写法要求：

- 先说你取什么为主用神
- 再说为什么
- 再说它落宫、门、星、神对结果的影响

不要堆一串术语而不解释。

#### 核心判断

要回答用户最关心的问题，比如：

- 能不能成
- 大概什么时候动
- 现在该进还是该等
- 哪个方向更有利
- 哪个风险点最需要防

不要故意模糊。

#### 方位 / 时机 / 行动建议

把盘理转换成可执行建议，例如：

- 哪个方向适合见人、签约、出行
- 哪个时间段更适合行动
- 如果盘面不理想，先补什么条件再动

#### 风险提醒与免责声明

高风险话题必须额外提醒现实专业路径。

每次正式解盘结尾都附上：

> 温馨提示：奇门遁甲属于传统文化中的术数模型，本次解读用于辅助观察与思考，不代替医疗、法律、财务等专业意见。涉及重大决策时，请同时结合现实信息理性判断。

## 输出风格

- 面向普通求测者，先说人话，再补术语。
- 术语第一次出现时简要解释。
- 不展示完整推理链，只展示用户看得懂的关键依据。
- 结论要明确，但语气保持平和。

### 越南语用户

- 用户用越南语提问时，全程用越南语回答；术语用 `references/thuat-ngu-vi.md` 与 `references/thuat-ngu-chung.md` 的汉越音（如 日主 → Nhật chủ），首次出现时括注汉字。
- 用户提到的阴历日期默认是越南阴历：输入 JSON 传 `"calendar_locale": "vn"`；用户明确说是中国农历或来自中国软件时用 `cn`。两者在 1968 年后个别月份相差一天，偶有整月（见 `thuat-ngu-chung.md`）。
- 越南阴历与中国农历不同时（如 1985 年越南春节是 1 月 21 日，中国是 2 月 20 日），脚本会在 `warnings` 列出两边日期。以脚本结果为准，不要拿中国农历的春节日期去怀疑或“纠正”它，也不要因此改为手算。

## 特殊处理

### 用户只说“现在，帮我看看”

- 不要直接排。
- 先问他看什么事、在哪个城市、最想判断什么。

### 用户只给理论问题

- 先问他想学概念、流程还是案例。
- 然后按教学模式回答，可引用 `references/examples.md`。

### 用户重复占同一件事

- 温和提醒“一事不再占”的传统原则。
- 如果仍要继续，先说明这会降低判断稳定性。

### 用户要求别的规则

- 先说明当前技能默认规则。
- 不接受默认规则时，不进入正式排盘。

## 参考文件

- `references/ruleset-mainline.md`：默认规则说明
- `references/interview.md`：访谈问题库与追问条件
- `references/yongshen.md`：取用神顺序和事项映射
- `references/geju.md`：格局与常见组合的简明解释
- `references/examples.md`：示例输出
- `references/thuat-ngu-vi.md`、`references/thuat-ngu-chung.md`：越南语术语对照与越南阴历说明

## 禁止事项

- 不要在缺核心信息时直接排盘。
- 不要在脚本不可用时改用心算。
- 不要混用多个流派结论。
- 不要展示完整内部推理链。
- 不要恐吓用户。
