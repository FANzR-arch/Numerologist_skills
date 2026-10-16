"""
紫微斗数排盘脚本 ziwei_cli.py 回归测试

期望值来源分四类，每类都可独立核对：

1. 文档表：直接解析 references/calculation.md、sihua.md、stars.md 里的表，
   断言脚本常量与文档逐格一致（文档就是口径）。
2. 安星诀推导：文档中的口诀与示例（命宫示例、宫干示例、五行局示例），
   以及由口诀推出的结构约束（issue #5：紫微七杀同宫只可能在巳、亥）。
3. 独立实现：五行局与 lunar_python 的六十甲子纳音五行逐一对照；
   全盘结果（含主星庙旺利陷）与开源排盘库 iztro 2.6.2 的输出逐星对照（fixtures/iztro_cases.json，
   可用 fixtures/gen_iztro_cases.cjs 重新生成核对）。
4. 手排盘例：test_hand_derived_chart 的 docstring 逐步写出了按口诀手排的过程。
"""

import json
import re
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from lunar_python.util import LunarUtil

import ziwei_cli as z
from ziwei_cli import BRANCHES, STEMS, build_output

REFERENCES = Path(__file__).resolve().parents[2] / "references"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def read_ref(name: str) -> str:
    return (REFERENCES / name).read_text(encoding="utf-8")


def table_rows(text: str) -> dict[str, list[str]]:
    """把 markdown 表格行解析成 {首列: 其余列}，同名行后者覆盖前者。"""
    rows = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= {"|", "-", " "}:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows[cells[0]] = cells[1:]
    return rows


def section(text: str, start: str, end: str) -> str:
    return text[text.index(start):text.index(end, text.index(start))]


def run(birth_time: str, gender: str = "男", **extra) -> dict:
    return build_output({"calendar_type": "solar", "birth_time": birth_time, "gender": gender, **extra})


def palace_of(output: dict, name: str) -> dict:
    return next(p for p in output["chart"]["palaces"] if p["name"] == name)


# ============================================================
# 1. 脚本常量与文档表逐格一致
# ============================================================

class TestMatchesDocTables:
    calc = read_ref("calculation.md")

    @pytest.mark.parametrize("ju_name,ju_number", [("水二局", 2), ("木三局", 3), ("金四局", 4), ("土五局", 5), ("火六局", 6)])
    def test_ziwei_table(self, ju_name, ju_number):
        start = self.calc.index(f"**{ju_name}**")
        block = self.calc[start:start + 1500]
        cells = []
        for line in block.splitlines():
            if line.startswith("| 紫微 |"):
                cells += [c.strip() for c in line.strip("|").split("|")][1:]
            if len(cells) == 30:
                break
        assert len(cells) == 30
        for day, expected in enumerate(cells, start=1):
            assert BRANCHES[z.ziwei_position(ju_number, day)] == expected, f"{ju_name} 初{day}"

    def test_tianfu_table(self):
        rows = table_rows(section(self.calc, "| 紫微落宫 | 天府落宫 |", "### 7.3"))
        mapping = {k: v[0] for k, v in rows.items() if k in BRANCHES}
        assert len(mapping) == 12
        for zw, tf in mapping.items():
            assert BRANCHES[z.tianfu_position(BRANCHES.index(zw))] == tf

    def test_hour_tables(self):
        rows = table_rows(section(self.calc, "### 文昌、文曲", "### 左辅、右弼"))
        rows.update(table_rows(section(self.calc, "### 地空、地劫", "### 天马")))
        for h in range(12):
            stars = z.place_minor_stars("甲", "子", 1, h)
            for star in ["文昌", "文曲", "地空", "地劫"]:
                assert BRANCHES[stars[star]] == rows[star][h], f"{star} {BRANCHES[h]}时"

    def test_month_tables(self):
        rows = table_rows(section(self.calc, "### 左辅、右弼", "### 天魁"))
        for m in range(1, 13):
            stars = z.place_minor_stars("甲", "子", m, 0)
            assert BRANCHES[stars["左辅"]] == rows["左辅"][m - 1]
            assert BRANCHES[stars["右弼"]] == rows["右弼"][m - 1]

    def test_kui_yue_table(self):
        rows = table_rows(section(self.calc, "### 天魁、天钺", "### 禄存"))
        for i, stem in enumerate(STEMS):
            stars = z.place_minor_stars(stem, "子", 1, 0)
            assert BRANCHES[stars["天魁"]] == rows["天魁"][i], stem
            assert BRANCHES[stars["天钺"]] == rows["天钺"][i], stem

    def test_kui_yue_follows_classic_verse(self):
        # 甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸兔蛇藏，六辛逢马虎
        verse = {"甲戊庚": "丑未", "乙己": "子申", "丙丁": "亥酉", "壬癸": "卯巳", "辛": "午寅"}
        for stems, (kui, yue) in verse.items():
            for stem in stems:
                assert z.KUI_YUE[stem] == (kui, yue)

    def test_lucun_yang_tuo_table(self):
        rows = table_rows(section(self.calc, "### 禄存、擎羊、陀罗", "### 火星、铃星"))
        header = rows["年干"]
        for col, stems in enumerate(header):
            for stem in stems.split("/"):
                stars = z.place_minor_stars(stem, "子", 1, 0)
                for star in ["禄存", "擎羊", "陀罗"]:
                    assert BRANCHES[stars[star]] == rows[star][col], f"{stem} {star}"

    def test_huo_ling_and_tianma(self):
        huo = table_rows(section(self.calc, "### 火星、铃星", "规则："))
        ma = table_rows(section(self.calc, "### 天马", "## 9."))
        for col, group in enumerate(huo["年支组"]):
            for year_branch, h in product(group, range(12)):
                stars = z.place_minor_stars("甲", year_branch, 1, h)
                # 以起点宫起子时，顺数到生时
                assert stars["火星"] == (BRANCHES.index(huo["火星起点"][col]) + h) % 12
                assert stars["铃星"] == (BRANCHES.index(huo["铃星起点"][col]) + h) % 12
                assert BRANCHES[stars["天马"]] == ma["天马"][col]

    def test_ming_zhu_shen_zhu(self):
        rows = table_rows(section(self.calc, "## 11. 命主与身主", "## 12."))
        assert z.MING_ZHU == rows["命主星"]
        assert z.SHEN_ZHU == rows["身主星"]

    def test_decadal_start_ages(self):
        text = section(self.calc, "### 起限年龄", "### 顺逆规则")
        for name, age in re.findall(r"- (\S+局)：(\d+) 岁", text):
            assert any(v == (name, int(age)) for v in z.JU_BY_REMAINDER.values())

    def test_sihua_table(self):
        rows = table_rows(section(read_ref("sihua.md"), "### 生年四化", "## 四化入宫"))
        for stem in STEMS:
            assert list(z.SIHUA[stem]) == rows[stem], stem

    def test_brightness_table(self):
        rows = table_rows(section(read_ref("stars.md"), "### 十四主星庙旺利平陷", "出处："))
        assert rows["主星"] == BRANCHES
        for star in z.MAJOR_STARS:
            assert z.BRIGHTNESS[star] == rows[star], star

    def test_brightness_follows_quanshu_text(self):
        """《紫微斗數全書》卷三逐星原文旁证卷二总表：紫微「庙丑未午 旺寅申卯酉巳亥 平子 无陷」，
        七杀「平巳亥 无陷」，天同「庙巳亥」，天府「庙子丑未寅辰戌」。"""
        def at(star, branches):
            return {z.BRIGHTNESS[star][BRANCHES.index(b)] for b in branches}
        assert at("紫微", "丑未午") == {"庙"}
        assert at("紫微", "寅申卯酉巳亥") == {"旺"}
        assert at("紫微", "子") == {"平"}
        assert "落陷" not in z.BRIGHTNESS["紫微"]
        assert at("七杀", "巳亥") == {"平"} and "落陷" not in z.BRIGHTNESS["七杀"]
        assert at("天同", "巳亥") == {"庙"}
        assert at("天府", "子丑未寅辰戌") == {"庙"}


# ============================================================
# 2. 安星诀推导：文档示例与结构约束
# ============================================================

class TestVerseDerived:
    def test_doc_ming_gong_example(self):
        """calculation.md §2 示例：农历三月午时，命宫在戌。"""
        out = build_output({"calendar_type": "lunar", "birth_time": "2001-03-10 12:00", "gender": "男"})
        assert out["calendar"]["chart_month"] == 3
        assert out["chart"]["ming_gong"]["branch"] == "戌"
        # 身宫：辰宫起子顺数到午 → 戌（午时命身同宫）
        assert out["chart"]["shen_gong"]["branch"] == "戌"

    def test_doc_palace_order_example(self):
        """calculation.md §3 示例：命宫在午时十二宫的位置。"""
        expected = dict(zip("午巳辰卯寅丑子亥戌酉申未", z.PALACE_NAMES))
        # 农历正月卯时：寅起正月，逆数到卯 → 寅=子 丑=丑 子=寅 亥=卯
        # 需要命宫在午：农历五月(午)子时
        out = build_output({"calendar_type": "lunar", "birth_time": "2001-05-10 00:30", "gender": "男"})
        assert out["chart"]["ming_gong"]["branch"] == "午"
        for p in out["chart"]["palaces"]:
            assert expected[p["branch"]] == p["name"]

    def test_doc_palace_stem_example(self):
        """calculation.md §4 示例：甲年生人寅=丙寅 … 丑=丁丑。"""
        expected = "寅丙 卯丁 辰戊 巳己 午庚 未辛 申壬 酉癸 戌甲 亥乙 子丙 丑丁".split()
        for item in expected:
            assert z.palace_stem("甲", BRANCHES.index(item[0])) == item[1]

    @pytest.mark.parametrize("year_stems,yin_stem", [("甲己", "丙"), ("乙庚", "戊"), ("丙辛", "庚"), ("丁壬", "壬"), ("戊癸", "甲")])
    def test_wuhu_dun(self, year_stems, yin_stem):
        for stem in year_stems:
            assert z.palace_stem(stem, BRANCHES.index("寅")) == yin_stem

    @pytest.mark.parametrize("ganzhi,ju", [("丙子", "水二局"), ("辛未", "土五局"), ("庚申", "木三局")])
    def test_doc_wuxing_ju_examples(self, ganzhi, ju):
        assert z.wuxing_ju(ganzhi[0], ganzhi[1])[0] == ju

    def test_wuxing_ju_matches_nayin(self):
        """五行局诀与六十甲子纳音五行应一致（lunar_python 纳音表为独立来源）。"""
        element_of_ju = {"水二局": "水", "木三局": "木", "金四局": "金", "土五局": "土", "火六局": "火"}
        for i in range(60):
            gz = STEMS[i % 10] + BRANCHES[i % 12]
            nayin = LunarUtil.NAYIN[gz]
            assert element_of_ju[z.wuxing_ju(gz[0], gz[1])[0]] == nayin[-1], gz

    @pytest.mark.parametrize("ju", [2, 3, 4, 5, 6])
    def test_ziwei_quotient_property(self, ju):
        """日数恰为局数 k 倍时没有不足数，紫微落在从寅起数的第 k 宫。"""
        for k in range(1, 31 // ju + 1):
            assert z.ziwei_position(ju, k * ju) == (2 + k - 1) % 12

    @pytest.mark.parametrize("ziwei", range(12))
    def test_fourteen_stars_complete(self, ziwei):
        positions = z.place_major_stars(ziwei)
        assert sorted(positions) == sorted(z.MAJOR_STARS)
        assert len(positions) == 14

    def test_ziwei_pairs_only_in_allowed_branches(self):
        """issue #5：紫微七杀同宫只在巳亥；其余紫微双星组合同理（calculation.md §7.4）。
        穷举五局 × 三十日，所有紫微落宫都检查一遍。"""
        seen = {}
        for ju, day in product([2, 3, 4, 5, 6], range(1, 31)):
            positions = z.place_major_stars(z.ziwei_position(ju, day))
            zw = positions["紫微"]
            partners = [s for s, idx in positions.items() if idx == zw and s != "紫微"]
            assert len(partners) <= 1
            if partners:
                assert BRANCHES[zw] in z.ZIWEI_PAIR_BRANCHES[partners[0]]
                seen.setdefault(partners[0], set()).add(BRANCHES[zw])
            else:
                assert BRANCHES[zw] in {"子", "午"}  # 紫微独坐只在子午
        assert seen["七杀"] == {"巳", "亥"}
        assert seen == z.ZIWEI_PAIR_BRANCHES

    @pytest.mark.parametrize("birth_time,lunar_text,branch", [
        # 金四局初六：6/4 商 2 不足 2，寅起数 2 → 卯，偶数顺 2 → 巳
        ("1990-01-02 09:00", "己巳年腊月初六", "巳"),
        # 金四局三十：30/4 商 8 不足 2，寅起数 8 → 酉，偶数顺 2 → 亥
        ("1990-01-26 09:00", "己巳年腊月三十", "亥"),
    ])
    def test_issue5_zisha_end_to_end(self, birth_time, lunar_text, branch):
        out = run(birth_time)
        assert out["calendar"]["lunar_text"] == lunar_text
        assert out["chart"]["wuxing_ju"]["name"] == "金四局"
        assert out["chart"]["star_index"]["紫微"] == branch
        assert out["chart"]["star_index"]["七杀"] == branch
        assert out["chart"]["self_check"]["ziwei_partner"] == "七杀"

    def test_self_check_rejects_wrong_zisha(self, monkeypatch):
        """若安星出错导致紫杀落未宫（issue #5 的错盘），自检必须报错而不是输出。"""
        real = z.place_major_stars

        def broken(ziwei_idx):
            positions = real(ziwei_idx)
            positions["紫微"] = positions["七杀"] = BRANCHES.index("未")
            return positions

        monkeypatch.setattr(z, "place_major_stars", broken)
        with pytest.raises(AssertionError, match="紫微七杀同宫出现在未"):
            run("1990-01-02 09:00")

    @pytest.mark.parametrize("stem,gender,direction", [("甲", "男", 1), ("甲", "女", -1), ("乙", "男", -1), ("乙", "女", 1)])
    def test_decadal_direction(self, stem, gender, direction):
        assert z.decadal_direction(stem, gender) == direction


# ============================================================
# 3. 手排盘例
# ============================================================

def test_hand_derived_chart():
    """公历 2000-08-16 14:30 女，按口诀手排：

    - 农历庚辰年七月十七，未时；庚为阳年，阳女大限逆行。
    - 寅起正月顺数到七月 → 申；申起子时逆数到未时 → 丑，命宫丑；顺数到未时 → 卯，身宫卯。
    - 乙庚年起戊寅：寅戊 卯己 … 子戊 丑己，命宫己丑；己3 + 丑1 = 4 → 火六局，起限 6 岁。
    - 火六局十七日：17/6 商 3 不足 1，寅起数 3 → 辰，奇数逆 1 → 卯，紫微在卯。
    - 紫微卯：天机寅、太阳子、武曲亥、天同戌、廉贞未；天府丑：太阴寅、贪狼卯、巨门辰、
      天相巳、天梁午、七杀未、破军亥。
    - 庚年四化：太阳禄、武曲权、太阴科、天同忌。
    - 庚年魁丑钺未，禄存申、擎羊酉、陀罗未；辰年属申子辰：火星寅起子顺到未 → 酉，
      铃星戌起子顺到未 → 巳，天马寅；未时：文昌卯、文曲亥、地空辰、地劫午；
      七月：左辅戌、右弼辰、天刑卯、天姚未；辰年：红鸾亥、天喜巳、天哭寅、天虚戌。
    - 命主（命宫丑）巨门；身主（年支辰）文昌。
    """
    out = run("2000-08-16 14:30", "女")
    chart = out["chart"]
    assert out["calendar"]["lunar_text"] == "庚辰年七月十七"
    assert out["calendar"]["hour_branch"] == "未时"
    assert chart["ming_gong"] == {"branch": "丑", "ganzhi": "己丑"}
    assert chart["shen_gong"] == {"branch": "卯", "palace": "福德"}
    assert chart["wuxing_ju"] == {"name": "火六局", "number": 6}
    assert chart["decadal_direction"] == "逆行"
    assert (chart["ming_zhu"], chart["shen_zhu"]) == ("巨门", "文昌")
    expected = {
        "紫微": "卯", "天机": "寅", "太阳": "子", "武曲": "亥", "天同": "戌", "廉贞": "未",
        "天府": "丑", "太阴": "寅", "贪狼": "卯", "巨门": "辰", "天相": "巳", "天梁": "午", "七杀": "未", "破军": "亥",
        "天魁": "丑", "天钺": "未", "禄存": "申", "擎羊": "酉", "陀罗": "未",
        "火星": "酉", "铃星": "巳", "天马": "寅",
        "文昌": "卯", "文曲": "亥", "地空": "辰", "地劫": "午",
        "左辅": "戌", "右弼": "辰", "天刑": "卯", "天姚": "未",
        "红鸾": "亥", "天喜": "巳", "天哭": "寅", "天虚": "戌",
    }
    assert chart["star_index"] == expected
    assert [(s["type"], s["star"]) for s in chart["year_sihua"]] == [
        ("化禄", "太阳"), ("化权", "武曲"), ("化科", "太阴"), ("化忌", "天同"),
    ]
    assert palace_of(out, "命宫")["decadal"] == {"start_age": 6, "end_age": 15}
    assert palace_of(out, "兄弟")["decadal"] == {"start_age": 16, "end_age": 25}  # 逆行：丑 → 子


def test_horoscope_layers():
    """2026 丙午年：虚岁 27，落在 26-35 岁大限（亥宫丁亥，丁干四化）；流年命宫在午。"""
    out = run("2000-08-16 14:30", "女", query_year=2026)
    h = out["horoscope"]
    assert h["nominal_age"] == 27
    assert h["decadal"]["ganzhi"] == "丁亥"
    assert h["decadal"]["natal_palace"] == "夫妻"
    assert [s["star"] for s in h["decadal"]["sihua"]] == list(z.SIHUA["丁"])
    assert h["yearly"]["ganzhi"] == "丙午"
    assert h["yearly"]["ming_branch"] == "午"
    assert h["yearly"]["ming_on_natal_palace"] == "交友"
    assert [s["star"] for s in h["yearly"]["sihua"]] == list(z.SIHUA["丙"])


# ============================================================
# 4. 与独立实现 iztro 2.6.2 逐星对照
# ============================================================

IZTRO_CASES = json.loads((FIXTURES / "iztro_cases.json").read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", IZTRO_CASES, ids=lambda c: f"{c['input']['birth_time']}-{c['input']['gender']}")
def test_matches_iztro(case):
    out = build_output({"calendar_type": "solar", "leap_month_rule": "split_15", **case["input"]})
    chart = out["chart"]
    ref = case["iztro"]
    assert chart["ming_gong"]["branch"] == ref["ming"]
    assert chart["shen_gong"]["branch"] == ref["shen"]
    assert chart["wuxing_ju"]["name"] == ref["ju"]
    assert (chart["ming_zhu"], chart["shen_zhu"]) == (ref["ming_zhu"], ref["shen_zhu"])
    assert {k: chart["star_index"][k] for k in ref["stars"]} == ref["stars"]
    assert {s["star"]: s["type"][1] for s in chart["year_sihua"]} == ref["sihua"]
    by_branch = {p["branch"]: p for p in chart["palaces"]}
    assert "".join(by_branch[b]["stem"] for b in BRANCHES) == ref["stems"]
    assert [by_branch[b]["decadal"]["start_age"] for b in BRANCHES] == ref["decadal_starts"]
    brightness = {s["name"]: s["brightness"] for p in chart["palaces"] for s in p["major_stars"]}
    assert brightness == ref["brightness"]


# ============================================================
# 5. 历法口径：子时换日、闰月、输入校验
# ============================================================

class TestCalendarRules:
    def test_late_zi_next_day(self):
        """calculation.md §1：23:00 后视为次日子时。"""
        late = run("2000-08-16 23:30")
        next_early = run("2000-08-17 00:30")
        assert late["calendar"]["day_rollover_applied"] is True
        assert late["calendar"]["lunar_day"] == 18
        assert late["chart"]["star_index"] == next_early["chart"]["star_index"]

    def test_late_zi_same_day_option(self):
        out = run("2000-08-16 23:30", late_zi_rule="same_day")
        assert out["calendar"]["day_rollover_applied"] is False
        assert out["calendar"]["lunar_day"] == 17
        assert out["calendar"]["hour_branch"] == "子时"

    def test_late_zi_on_new_years_eve_changes_year(self):
        """除夕 23 点后换到次日，即农历正月初一，年干支随之换年。"""
        eve = run("2024-02-09 23:10")  # 癸卯年除夕
        assert eve["calendar"]["year_ganzhi"] == "甲辰"
        assert (eve["calendar"]["lunar_month"], eve["calendar"]["lunar_day"]) == (1, 1)

    def test_year_changes_at_lunar_new_year_not_lichun(self):
        """2024 立春是 2 月 4 日，春节是 2 月 10 日；2 月 5 日仍是癸卯年。"""
        assert run("2024-02-05 10:00")["calendar"]["year_ganzhi"] == "癸卯"
        assert run("2024-02-10 10:00")["calendar"]["year_ganzhi"] == "甲辰"

    # 农历 2023 闰二月：初一 = 公历 3-22，十五 = 4-05，十六 = 4-06，二十九（月末）= 4-19
    @pytest.mark.parametrize("day,lunar_day,month", [
        ("2023-03-22", 1, 2), ("2023-04-05", 15, 2),
        ("2023-04-06", 16, 3), ("2023-04-19", 29, 3),
    ])
    def test_leap_month_default_split_15(self, day, lunar_day, month):
        """未传 leap_month_rule 时默认 split_15：闰月十五日及以前按本月，十六日起按下月。"""
        out = run(f"{day} 10:00")
        assert out["calendar"]["is_leap_month"] is True
        assert out["calendar"]["lunar_day"] == lunar_day
        assert out["calendar"]["chart_month"] == month
        assert out["normalized_input"]["leap_month_rule"] == "split_15"
        assert out["normalized_input"]["leap_month_rule_source"] == "default"
        assert out["ruleset"]["leap_month_rule"] == {
            "id": "split_15", "source": "default",
            "description": z.LEAP_MONTH_RULES["split_15"], "applied": True,
        }
        assert any("split_15（默认算法" in w for w in out["warnings"])

    @pytest.mark.parametrize("rule,day,month", [
        ("current", "2023-03-22", 2), ("current", "2023-04-19", 2),
        ("next", "2023-03-22", 3), ("next", "2023-04-19", 3),
        ("split_15", "2023-04-05", 2), ("split_15", "2023-04-06", 3),
    ])
    def test_leap_month_explicit_rules(self, rule, day, month):
        out = run(f"{day} 10:00", leap_month_rule=rule)
        assert out["calendar"]["is_leap_month"] is True
        assert out["calendar"]["chart_month"] == month
        assert out["normalized_input"]["leap_month_rule"] == rule
        assert out["normalized_input"]["leap_month_rule_source"] == "explicit"
        assert any(f"{rule}（调用方指定" in w for w in out["warnings"])

    def test_leap_month_rule_changes_month_based_stars(self):
        """current 与 next 相差一个月：按月安的命宫、左辅随之移动，按年干安的禄存不变。"""
        cur = run("2023-04-19 10:00", leap_month_rule="current")["chart"]
        nxt = run("2023-04-19 10:00", leap_month_rule="next")["chart"]
        assert cur["ming_gong"]["branch"] != nxt["ming_gong"]["branch"]
        assert (BRANCHES.index(nxt["star_index"]["左辅"]) - BRANCHES.index(cur["star_index"]["左辅"])) % 12 == 1
        assert cur["star_index"]["禄存"] == nxt["star_index"]["禄存"]  # 按年干

    def test_non_leap_birth_marks_rule_not_applied(self):
        out = run("2000-08-16 14:30", "女")
        assert out["normalized_input"]["leap_month_rule_source"] == "default"
        assert out["ruleset"]["leap_month_rule"]["applied"] is False
        assert not any("闰" in w for w in out["warnings"])

    def test_invalid_leap_month_rule(self):
        with pytest.raises(ValueError, match="leap_month_rule"):
            run("2023-04-19 10:00", leap_month_rule="half")

    def test_lunar_input_equals_solar_input(self):
        solar = run("2000-08-16 14:30", "女")
        lunar = build_output({"calendar_type": "lunar", "birth_time": "2000-07-17 14:30", "gender": "女"})
        assert lunar["chart"] == solar["chart"]

    def test_lunar_leap_input(self):
        out = build_output({
            "calendar_type": "lunar", "gender": "男", "leap_month_rule": "current",
            "birth_time": {"year": 2023, "month": 2, "day": 20, "hour": 10, "is_leap_month": True},
        })
        assert out["calendar"]["chart_solar_date"] == "2023-04-10"

    def test_lunar_leap_input_rejects_missing_leap_month(self):
        with pytest.raises(ValueError, match="没有闰3月"):
            build_output({"calendar_type": "lunar", "gender": "男",
                          "birth_time": {"year": 2023, "month": 3, "day": 1, "hour": 10, "is_leap_month": True}})

    def test_missing_gender(self):
        with pytest.raises(ValueError, match="gender"):
            build_output({"calendar_type": "solar", "birth_time": "2000-08-16 14:30"})

    def test_missing_time(self):
        with pytest.raises(ValueError, match="出生时间"):
            build_output({"calendar_type": "solar", "birth_time": "2000-08-16", "gender": "男"})

    def test_hour_boundary_warning(self):
        assert any("时辰交界" in w for w in run("2000-08-16 14:55")["warnings"])
        assert not any("时辰交界" in w for w in run("2000-08-16 14:00")["warnings"])

    @pytest.mark.parametrize("hour,branch", [(0, "子"), (1, "丑"), (2, "丑"), (3, "寅"), (12, "午"), (13, "未"), (22, "亥"), (23, "子")])
    def test_hour_branch(self, hour, branch):
        assert BRANCHES[z.hour_branch_index(hour)] == branch


def test_cli_roundtrip(tmp_path):
    src = tmp_path / "in.json"
    dst = tmp_path / "out.json"
    src.write_text(json.dumps({"calendar_type": "solar", "birth_time": "2000-08-16 14:30", "gender": "女"}), encoding="utf-8")
    sys.argv = ["ziwei_cli.py", "--input", str(src), "--output", str(dst)]
    assert z.main() == 0
    assert json.loads(dst.read_text(encoding="utf-8"))["chart"]["ming_gong"]["branch"] == "丑"

    src.write_text(json.dumps({"calendar_type": "solar", "birth_time": "2000-08-16 14:30"}), encoding="utf-8")
    assert z.main() == 1
    assert "gender" in json.loads(dst.read_text(encoding="utf-8"))["error"]
