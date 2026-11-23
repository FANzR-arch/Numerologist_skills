---
name: liuyao
description: >
  六爻纳甲筮法排卦与断卦技能（Lục Hào / Kinh Dịch bói quẻ）。用户提到六爻、摇卦、起卦、铜钱卦、
  纳甲、世应、六亲、用神、动爻、变卦、伏神，或要求用六爻 / Lục Hào / gieo quẻ 判断一件具体事情时触发。
  排卦调用脚本完成固定计算，模型只负责问事、取用神与解读。
  即使问题很短（只问卦名或用神），也必须用本技能并运行脚本，不要心算。
compatibility: Requires Python 3.11+, lunar_python, and tzdata; run scripts/liuyao_cli.py for all fixed calculations.
---

# 六爻技能

Read:

- `references/yongshen.md`
- `references/thuat-ngu-vi.md`、`references/thuat-ngu-chung.md`（越南语用户）

## 总原则

- 一事一卦：先问清要判断的具体事情，不为笼统的"运势如何"起卦。
- 本卦、变卦、世应、纳甲、六亲、六神、伏神、月建日辰、旬空月破一律以脚本输出为准，不手排，不改盘。
- 卦象给出倾向与条件，不说"必死""必败""无解"；健康、法律、投资等重大事项附现实建议。
- 不展示完整推理链，只给关键依据：用神、旺衰、动变、空破、世应。
- `references/` 中各节注明了古籍出处；标「未核对古籍」或「部分」的内容是现代整理，向用户转述时要说明这是现代说法、不是古籍原文，不要说成古法定论。

## 第一步：问事

确认：

1. 要判断的具体事情，以及问卦者与事情的关系（自己的工作、配偶的病、朋友的借款……），据此在 `references/yongshen.md` 中取用神。
2. 起卦时间（默认现在）。
3. 卦从哪里来：
   - 用户自己摇卦：三枚铜钱摇六次，自下而上记录每次结果。三个背（或约定的一面）= 6 老阴（动），一字两背 = 7 少阳，两字一背 = 8 少阴，三字 = 9 老阳（动）。先说清字、背各算 3 和 2，再让用户报数。
   - 用户请你代摇：传 `cast: true`，脚本用安全随机数模拟三枚铜钱，并在输出中给出每次的铜钱结果。

## 第二步：调用脚本

脚本以本 skill 目录为基准，记为 `<skill_dir>`（本 SKILL.md 所在目录；作为 Claude Code 插件安装时即 skill 的 base directory）。缺依赖时征得用户同意后运行：

```bash
python3 -m pip install -r "<skill_dir>/scripts/requirements.txt"
```

```bash
python3 "<skill_dir>/scripts/liuyao_cli.py" \
  --input "tmp/liuyao_input.json" \
  --output "tmp/liuyao_output.json"
```

**写入与运行（必须照做）**：用 Write 工具在当前工作目录下创建 `tmp/liuyao_input.json`（Write 需要绝对路径，即 `<当前工作目录>/tmp/liuyao_input.json`；下面命令里的相对路径 `tmp/...` 指向同一文件）；不要用 shell heredoc、`echo >`、`mkdir && ...` 等组合命令写文件。然后单独运行上面那一条 `python3` 命令（不加 `cd`、`&&` 或管道），再用 Read 读取输出文件。这样用户只需授权一条 python3 命令；命令被拒绝时，告诉用户需要允许运行该 python 脚本，不要改为手算。命令用 `python3`；只有 `python3` 不存在（如部分 Windows）时才改用 `python`。`python3` 能运行脚本即说明依赖已装好，不要再去安装。

输入 JSON：

```json
{
  "question": "这次面试能否录取",
  "lines": [7, 8, 9, 7, 6, 8],
  "time": "2026-11-22 10:00",
  "late_zi_rule": "next_day|same_day"
}
```

- `lines` 自下而上六个数；代摇时去掉 `lines`，改传 `"cast": true`。
- `time` 填起卦时刻，或 `"now"`（按 `location.timezone`，默认 Asia/Shanghai）。
- 输出有 `error` 字段时按提示向用户补问，不要手排。

## 第三步：读取输出

| 字段 | 用途 |
|---|---|
| `calendar` | 月建 `month_ganzhi`、日辰 `day_ganzhi`、旬空 `day_xunkong` |
| `hexagram` | 本卦：卦名、越南语名 `name_vi`、卦序、上下卦、所属宫与宫五行、世代、世爻 `shi`、应爻 `ying` |
| `changed` | 变卦（静卦为 null） |
| `lines` | 自下而上六爻：干支、五行、六亲、六神、世/应、动、变爻（干支与六亲，六亲按本卦宫）、伏神、旬空、月破、日冲 |
| `missing_liuqin` | 本卦缺的六亲（其伏神见对应爻的 `fushen`） |
| `normalized_input` | 爻值、是否脚本代摇及铜钱结果、起卦时间 |

## 第四步：断卦

1. 取用神，指出它在第几爻（或伏于第几爻之下）、五行、六神。
2. 看月建、日辰对用神的生克，定旺衰；注明旬空、月破、日冲。
3. 看动爻：哪些动爻生克用神；变爻对动爻是回头生还是回头克。
4. 看世应关系与原神、忌神。
5. 结论：倾向、关键条件、需要注意的时间点（如出空、冲实之日），以及现实中能做的事。

## 输出风格

- 先说结论，再说依据；术语第一次出现时用一句话解释。
- 结论明确但语气平和，凶象转译成风险与应对。

### 越南语用户

- 用户用越南语提问时全程用越南语回答；卦名用输出里的 `name_vi`，术语用 `references/thuat-ngu-vi.md` 与 `references/thuat-ngu-chung.md` 的汉越音，首次出现时括注汉字。

## 结尾提醒

凡是给出卦象结果或任何解读的回复（包括只排卦、初步判断），都在结尾附上下面这段，不要省略；用户用越南语时附越南语译文：

> 六爻属于传统文化中的占问方法，本次解读用于辅助思考，不代替医疗、法律、财务等专业意见。

> Lưu ý: Lục Hào là phép xem quẻ truyền thống; phần luận giải này chỉ để tham khảo khi suy nghĩ, không thay cho ý kiến chuyên môn về y tế, pháp lý, tài chính.
