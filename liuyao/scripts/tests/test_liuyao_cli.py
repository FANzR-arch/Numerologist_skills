"""liuyao_cli.py 测试：八宫世应、纳甲、六亲、六神、伏神对照传统定式；日辰用纯算术核对。"""
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from liuyao_cli import HEXAGRAMS, build_output

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
TRIGRAM_LINES = {"乾": "111", "兑": "110", "离": "101", "震": "100", "巽": "011", "坎": "010", "艮": "001", "坤": "000"}


def _lines(upper, lower, moving=()):
    """由上下卦得到自下而上的六爻数值；moving 中的爻位（1-6）取老阴/老阳。"""
    bits = TRIGRAM_LINES[lower] + TRIGRAM_LINES[upper]
    return [(9 if b == "1" else 6) if i + 1 in moving else (7 if b == "1" else 8) for i, b in enumerate(bits)]


def _cast(upper, lower, moving=(), time="2026-11-22 10:00", **extra):
    return build_output({"lines": _lines(upper, lower, moving), "time": time, **extra})


class TestPalaces:
    def test_64_unique(self):
        assert len(HEXAGRAMS) == 64
        assert len({h["name"] for h in HEXAGRAMS.values()}) == 64
        assert sorted(h["number"] for h in HEXAGRAMS.values()) == list(range(1, 65))

    # 京房八宫定式：(上卦, 下卦) → (卦名, 宫, 世代, 世爻)
    @pytest.mark.parametrize("upper,lower,name,palace,generation,shi", [
        ("乾", "乾", "乾为天", "乾", "本宫", 6),
        ("乾", "巽", "天风姤", "乾", "一世", 1),
        ("乾", "坤", "天地否", "乾", "三世", 3),
        ("离", "坤", "火地晋", "乾", "游魂", 4),
        ("离", "乾", "火天大有", "乾", "归魂", 3),
        ("坤", "乾", "地天泰", "坤", "三世", 3),
        ("坎", "坤", "水地比", "坤", "归魂", 3),
        ("坎", "离", "水火既济", "坎", "三世", 3),
        ("离", "坎", "火水未济", "离", "三世", 3),
        ("乾", "坎", "天水讼", "离", "游魂", 4),
        ("艮", "震", "山雷颐", "巽", "游魂", 4),
        ("兑", "巽", "泽风大过", "震", "游魂", 4),
        ("震", "兑", "雷泽归妹", "兑", "归魂", 3),
        ("巽", "艮", "风山渐", "艮", "归魂", 3),
        ("兑", "坎", "泽水困", "兑", "一世", 1),
    ])
    def test_known(self, upper, lower, name, palace, generation, shi):
        hexagram = _cast(upper, lower)["hexagram"]
        assert (hexagram["name"], hexagram["palace"], hexagram["generation"], hexagram["shi"]) == (name, palace, generation, shi)
        assert hexagram["ying"] == (shi + 2) % 6 + 1

    def test_numbers_and_vietnamese_names(self):
        out = _cast("坤", "乾")["hexagram"]
        assert (out["number"], out["name_vi"]) == (11, "Địa Thiên Thái")
        assert _cast("离", "坎")["hexagram"]["number"] == 64


class TestNajiaAndLiuqin:
    def test_gou(self):
        # 天风姤（乾宫金）：内巽 辛丑 辛亥 辛酉，外乾 壬午 壬申 壬戌
        lines = _cast("乾", "巽")["lines"]
        assert [l["ganzhi"] for l in lines] == ["辛丑", "辛亥", "辛酉", "壬午", "壬申", "壬戌"]
        assert [l["liuqin"] for l in lines] == ["父母", "子孙", "兄弟", "官鬼", "兄弟", "父母"]
        assert [l["role"] for l in lines] == ["世", None, None, "应", None, None]

    def test_fushen(self):
        # 姤卦缺妻财：取乾为天二爻寅木妻财，伏于二爻亥水之下
        out = _cast("乾", "巽")
        assert out["missing_liuqin"] == ["妻财"]
        hidden = {l["position"]: l["fushen"] for l in out["lines"] if l["fushen"]}
        assert hidden == {2: {"ganzhi": "甲寅", "liuqin": "妻财", "element": "木"}}

    @pytest.mark.parametrize("trigram,inner,outer", [
        ("乾", "甲子 甲寅 甲辰", "壬午 壬申 壬戌"),
        ("坤", "乙未 乙巳 乙卯", "癸丑 癸亥 癸酉"),
        ("震", "庚子 庚寅 庚辰", "庚午 庚申 庚戌"),
        ("巽", "辛丑 辛亥 辛酉", "辛未 辛巳 辛卯"),
        ("坎", "戊寅 戊辰 戊午", "戊申 戊戌 戊子"),
        ("离", "己卯 己丑 己亥", "己酉 己未 己巳"),
        ("艮", "丙辰 丙午 丙申", "丙戌 丙子 丙寅"),
        ("兑", "丁巳 丁卯 丁丑", "丁亥 丁酉 丁未"),
    ])
    def test_pure_najia(self, trigram, inner, outer):
        lines = _cast(trigram, trigram)["lines"]
        assert " ".join(l["ganzhi"] for l in lines) == f"{inner} {outer}"

    def test_pure_hexagram_has_all_liuqin(self):
        for trigram in TRIGRAM_LINES:
            out = _cast(trigram, trigram)
            assert out["missing_liuqin"] == []
            assert not any(l["fushen"] for l in out["lines"])


class TestMoving:
    def test_changed_hexagram(self):
        out = _cast("乾", "乾", moving=(1,))
        assert out["changed"]["name"] == "天风姤"
        first = out["lines"][0]
        assert first["moving"] and first["changed"] == {"ganzhi": "辛丑", "liuqin": "父母", "element": "土"}  # 六亲按本卦宫
        assert not out["lines"][1]["moving"] and out["lines"][1]["changed"] is None

    def test_changed_liuqin_uses_original_palace(self):
        # 乾为天上爻动 → 泽天夬（坤宫土）；变爻丁未土对乾宫金是父母（若按坤宫会算成兄弟）
        out = _cast("乾", "乾", moving=(6,))
        assert (out["changed"]["name"], out["changed"]["palace"]) == ("泽天夬", "坤")
        assert out["lines"][5]["changed"] == {"ganzhi": "丁未", "liuqin": "父母", "element": "土"}

    def test_static_has_no_changed(self):
        assert _cast("乾", "乾")["changed"] is None


class TestCalendar:
    def test_day_and_month(self):
        # 2026-11-22：立冬后为亥月；丙午年 → 寅月庚寅 → 亥月己亥。日柱按 1949-10-01 甲子推
        cal = _cast("乾", "乾")["calendar"]
        idx = (date(2026, 11, 22) - date(1949, 10, 1)).days % 60
        assert cal["day_ganzhi"] == STEMS[idx % 10] + BRANCHES[idx % 12]
        assert cal["month_ganzhi"] == "己亥"
        start = idx - idx % 10
        assert cal["day_xunkong"] == BRANCHES[(start + 10) % 12] + BRANCHES[(start + 11) % 12]

    @pytest.mark.parametrize("rule,offset", [("next_day", 1), ("same_day", 0)])
    def test_late_zi(self, rule, offset):
        # 23:30 起卦：next_day 日辰取次日，same_day（夜子时）仍取当日
        idx = (date(2026, 11, 22) - date(1949, 10, 1)).days + offset
        cal = _cast("乾", "乾", time="2026-11-22 23:30", late_zi_rule=rule)["calendar"]
        assert cal["day_ganzhi"] == STEMS[idx % 10] + BRANCHES[idx % 12]

    @pytest.mark.parametrize("stem_day,first", [("甲", "青龙"), ("丙", "朱雀"), ("戊", "勾陈"), ("己", "螣蛇"), ("庚", "白虎"), ("壬", "玄武")])
    def test_liushen(self, stem_day, first):
        d = date(2026, 1, 1)
        while True:
            idx = (d - date(1949, 10, 1)).days % 60
            if STEMS[idx % 10] == stem_day:
                break
            d = date.fromordinal(d.toordinal() + 1)
        lines = _cast("乾", "乾", time=f"{d.isoformat()} 10:00")["lines"]
        order = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
        start = order.index(first)
        assert [l["liushen"] for l in lines] == [order[(start + i) % 6] for i in range(6)]

    def test_flags(self):
        out = _cast("乾", "乾")
        month_branch, kong = out["calendar"]["month_ganzhi"][1], out["calendar"]["day_xunkong"]
        clash = {b: BRANCHES[(BRANCHES.index(b) + 6) % 12] for b in BRANCHES}
        for line in out["lines"]:
            branch = line["ganzhi"][1]
            assert line["month_break"] == (clash[branch] == month_branch)
            assert line["xunkong"] == (branch in kong)


class TestInput:
    def test_cast_with_coins(self):
        out = build_output({"cast": True, "time": "2026-11-22 10:00"})
        assert len(out["lines"]) == 6
        assert all(l["value"] in (6, 7, 8, 9) for l in out["lines"])
        coins = out["normalized_input"]["coins"]
        assert all(len(c) == 3 and set(c) <= {2, 3} for c in coins)
        assert [sum(c) for c in coins] == out["normalized_input"]["lines"] == [l["value"] for l in out["lines"]]

    @pytest.mark.parametrize("payload,message", [
        ({"time": "2026-11-22 10:00"}, "lines"),
        ({"lines": [7, 7, 7], "time": "2026-11-22 10:00"}, "6"),
        ({"lines": [7, 7, 7, 7, 7, 5], "time": "2026-11-22 10:00"}, "6、7、8、9"),
        ({"lines": [7, 7, 7, 7, 7, 7]}, "time"),
        ({"lines": [7, 7, 7, 7, 7, 7], "cast": True, "time": "2026-11-22 10:00"}, "cast"),
        ({"lines": [7, 7, 7.0, 7, 7, 7], "time": "2026-11-22 10:00"}, "6、7、8、9"),
        ({"cast": "false", "time": "2026-11-22 10:00"}, "cast"),
    ])
    def test_rejects(self, payload, message):
        with pytest.raises(ValueError, match=message):
            build_output(payload)

    def test_now(self):
        from zoneinfo import ZoneInfo
        out = build_output({"lines": [7, 8, 7, 8, 7, 8], "time": "now", "location": {"timezone": "Asia/Ho_Chi_Minh"}})
        expected = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).replace(tzinfo=None)
        assert abs((datetime.fromisoformat(out["calendar"]["datetime"]) - expected).total_seconds()) < 120


def test_vietnamese_glossary_covers_output_terms():
    glossary = (Path(__file__).resolve().parents[2] / "references" / "thuat-ngu-vi.md").read_text(encoding="utf-8")
    out = _cast("乾", "巽", moving=(2,))
    terms = {out["hexagram"]["generation"]} | {l["liuqin"] for l in out["lines"]} | {"青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"}
    terms |= {"本宫", "一世", "二世", "三世", "四世", "五世", "游魂", "归魂", "世", "应", "伏神", "飞神", "月破", "旬空", "妻财"}
    assert [t for t in sorted(terms) if t not in glossary] == []
