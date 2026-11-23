"""bazi_cli.py 测试。

四柱用独立的纯算术推算（六十甲子序数、五虎遁、五鼠遁、甲子日基准）核对，
不调用 lunar_python；藏干与十神核对 references/tiangan-dizhi.md，确保脚本与参考表一致。
"""
import random
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from bazi_cli import build_output

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
REFERENCE = (Path(__file__).resolve().parents[2] / "references" / "tiangan-dizhi.md").read_text(encoding="utf-8")

# 十二节的公历日期（1900-2100 年间实际日期在此 ±1 天内），值为该节起始的月支
NOMINAL_JIE = [(1, 6, "丑"), (2, 4, "寅"), (3, 6, "卯"), (4, 5, "辰"), (5, 6, "巳"), (6, 6, "午"),
               (7, 7, "未"), (8, 8, "申"), (9, 8, "酉"), (10, 8, "戌"), (11, 7, "亥"), (12, 7, "子")]
JIAZI_DAY = date(1949, 10, 1)  # 甲子日


def _chart(birth_time, gender="男", **extra):
    return build_output({"birth_time": birth_time, "gender": gender, **extra})


def _ganzhi(index):
    return STEMS[index % 10] + BRANCHES[index % 12]


def _sexagenary(gz):
    return next(i for i in range(60) if _ganzhi(i) == gz)


def _near_jie(d):
    return any(abs((d - date(d.year, m, day)).days) <= 3 for m, day, _ in NOMINAL_JIE)


def _expected_pillars(dt, late_zi_rule="next_day"):
    """纯算术四柱：立春换年、节换月；next_day 23:00 换日，same_day 日柱不换、时干按次日起。"""
    d = dt.date()
    year = d.year if (d.month, d.day) >= (2, 4) else d.year - 1
    year_gz = _ganzhi(year - 4)

    month_branch = "子"  # 12 月 7 日之后、次年 1 月 6 日之前
    for m, day, branch in NOMINAL_JIE:
        if (d.month, d.day) >= (m, day):
            month_branch = branch
    offset = (BRANCHES.index(month_branch) - 2) % 12  # 寅月为正月
    month_stem = (STEMS.index(year_gz[0]) % 5 * 2 + 2 + offset) % 10
    month_gz = STEMS[month_stem] + month_branch

    next_day_gz = _ganzhi((d + timedelta(days=1) - JIAZI_DAY).days)
    day_gz = _ganzhi((d - JIAZI_DAY).days)
    if dt.hour == 23 and late_zi_rule == "next_day":
        day_gz = next_day_gz

    hour_branch = (dt.hour + 1) // 2 % 12
    hour_day_stem = next_day_gz[0] if dt.hour == 23 else day_gz[0]
    hour_stem = (STEMS.index(hour_day_stem) % 5 * 2 + hour_branch) % 10
    return [year_gz, month_gz, day_gz, STEMS[hour_stem] + BRANCHES[hour_branch]]


def _pillars(output):
    return [output["pillars"][k]["ganzhi"] for k in ("year", "month", "day", "time")]


class TestPillarsAgainstArithmetic:
    def test_random_dates(self):
        rng = random.Random(20261122)
        checked = 0
        while checked < 1500:
            dt = datetime(1901, 1, 1) + timedelta(minutes=rng.randrange(199 * 365 * 24 * 60))
            if _near_jie(dt.date()):
                continue
            assert _pillars(_chart(dt.strftime("%Y-%m-%d %H:%M"))) == _expected_pillars(dt), dt
            checked += 1

    def test_random_late_zi_same_day(self):
        rng = random.Random(23)
        for _ in range(200):
            dt = datetime(1901, 1, 1, 23, rng.randrange(60)) + timedelta(days=rng.randrange(199 * 365))
            if _near_jie(dt.date()):
                continue
            output = _chart(dt.strftime("%Y-%m-%d %H:%M"), late_zi_rule="same_day")
            assert _pillars(output) == _expected_pillars(dt, "same_day"), dt

    def test_known_chart(self):
        assert _pillars(_chart("1990-05-15 10:00")) == ["庚午", "辛巳", "庚辰", "辛巳"]


class TestJieBoundary:
    def test_lichun_switches_year_and_month_at_exact_time(self):
        # 2024 立春 02-04 16:27
        before, after = _chart("2024-02-04 16:00"), _chart("2024-02-04 17:00")
        assert _pillars(before)[:2] == ["癸卯", "乙丑"]
        assert _pillars(after)[:2] == ["甲辰", "丙寅"]
        assert any("节气" in w for w in before["warnings"])

    @pytest.mark.parametrize("birth", ["2024-03-05 08:00", "2024-03-05 12:00", "2024-02-04 16:26", "2024-02-04 16:28"])
    def test_prev_and_next_jie_bracket_birth_on_jie_day(self, birth):
        # 2024 惊蛰 03-05 10:22，立春 02-04 16:27：交节当天也要按时刻分前后
        calendar = _chart(birth)["calendar"]
        assert calendar["prev_jie"]["time"] <= birth + ":00" < calendar["next_jie"]["time"]

    def test_far_from_jie_has_no_jie_warning(self):
        assert not any("节气" in w for w in _chart("1990-05-15 10:00")["warnings"])


class TestLateZi:
    def test_next_day_is_default(self):
        output = _chart("1990-05-10 23:30")
        assert _pillars(output)[2:] == ["丙子", "戊子"]
        assert output["calendar"]["day_rollover_applied"] is True
        assert output["normalized_input"]["late_zi_rule"] == "next_day"

    def test_same_day(self):
        output = _chart("1990-05-10 23:30", late_zi_rule="same_day")
        # 夜子时：日柱仍取当日乙亥，时柱按次日日干起子时
        assert _pillars(output)[2:] == ["乙亥", "戊子"]
        assert output["calendar"]["day_rollover_applied"] is False

    def test_before_23_unaffected(self):
        assert _pillars(_chart("1990-05-10 22:59"))[2] == "乙亥"


class TestReferenceConsistency:
    def _hidden_table(self):
        rows = re.findall(r"^\| ([子丑寅卯辰巳午未申酉戌亥]) \|.*\| ([甲乙丙丁戊己庚辛壬癸]+) \|$", REFERENCE, re.M)
        assert len(rows) == 12
        return dict(rows)

    def test_hidden_stems_match_reference(self):
        table = self._hidden_table()
        for zhi in BRANCHES:
            # 找一个时支为 zhi 的时刻
            hour = (BRANCHES.index(zhi) * 2 - 1) % 24 + 1 if zhi != "子" else 0
            hide = [h["gan"] for h in _chart(f"1990-05-15 {hour:02d}:30")["pillars"]["time"]["hide_gan"]]
            assert set(hide) == set(table[zhi]), zhi
            assert hide[0] == table[zhi][0], f"{zhi} 本气"

    def test_reference_matches_yuanhai_ziping(self):
        # 《淵海子平》又地支藏遁歌（只给藏干集合，不分本气中气余气）
        yuanhai = {"子": "癸", "丑": "癸辛己", "寅": "甲丙戊", "卯": "乙", "辰": "乙戊癸", "巳": "庚丙戊",
                   "午": "丁己", "未": "乙己丁", "申": "庚壬戊", "酉": "辛", "戌": "辛丁戊", "亥": "壬甲"}
        table = self._hidden_table()
        assert {z: set(v) for z, v in table.items()} == {z: set(v) for z, v in yuanhai.items()}

    def test_shishen_matches_reference_rule(self):
        relation = {}
        for line in re.findall(r"^\| (生我|同我|我生|我克|克我) \| (\S+) \| (\S+) \|$", REFERENCE, re.M):
            relation[line[0]] = (re.sub(r"（.*）", "", line[1]), re.sub(r"（.*）", "", line[2]))
        assert len(relation) == 5
        element = "木木火火土土金金水水"
        gen = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
        ctl = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

        def expect(me, other):
            a, b = element[STEMS.index(me)], element[STEMS.index(other)]
            kind = ("同我" if a == b else "我生" if gen[a] == b else "生我" if gen[b] == a
                    else "我克" if ctl[a] == b else "克我")
            return relation[kind][0 if STEMS.index(me) % 2 == STEMS.index(other) % 2 else 1]

        rng = random.Random(7)
        for _ in range(200):
            dt = datetime(1950, 1, 1) + timedelta(hours=rng.randrange(70 * 365 * 24))
            p = _chart(dt.strftime("%Y-%m-%d %H:%M"))["pillars"]
            me = p["day"]["gan"]
            assert p["day"]["shishen_gan"] == "日主"
            for key in ("year", "month", "time"):
                assert p[key]["shishen_gan"] == expect(me, p[key]["gan"]), (dt, key)
            for key in ("year", "month", "day", "time"):
                for h in p[key]["hide_gan"]:
                    assert h["shishen"] == expect(me, h["gan"]), (dt, key)


class TestDayun:
    @pytest.mark.parametrize("birth,gender", [
        ("1990-05-15 10:00", "男"), ("1990-05-15 10:00", "女"),
        ("1985-11-20 03:15", "男"), ("1985-11-20 03:15", "女"),
    ])
    def test_structure(self, birth, gender):
        output = _chart(birth, gender)
        year_stem = output["pillars"]["year"]["gan"]
        forward = (STEMS.index(year_stem) % 2 == 0) == (gender == "男")
        dayun = output["dayun"]
        assert dayun["direction"] == ("顺排" if forward else "逆排")

        periods = dayun["periods"]
        # 交运前以月柱为大运
        assert periods[0]["ganzhi"] == output["pillars"]["month"]["ganzhi"]
        assert periods[0]["start_age"] == 1
        step = 1 if forward else -1
        month_idx = _sexagenary(output["pillars"]["month"]["ganzhi"])
        birth_year = int(birth[:4])
        for i, period in enumerate(periods[1:], start=1):
            assert period["ganzhi"] == _ganzhi(month_idx + step * i)
            assert period["end_age"] - period["start_age"] == 9
            assert period["start_year"] - birth_year + 1 == period["start_age"]
        for prev, cur in zip(periods, periods[1:]):
            assert cur["start_age"] == prev["end_age"] + 1

    @pytest.mark.parametrize("birth,gender", [
        ("1990-05-15 10:00", "男"), ("1990-05-15 10:00", "女"),
        ("1985-11-20 03:15", "男"), ("2001-08-01 17:40", "女"),
    ])
    def test_start_age_counts_shichen_to_jie(self, birth, gender):
        # 3 天 1 年：按时辰计数，36 个时辰 = 1 年，3 个时辰 = 1 个月，1 个时辰 = 10 天
        output = _chart(birth, gender)
        forward = output["dayun"]["direction"] == "顺排"
        jie = datetime.fromisoformat(output["calendar"]["next_jie" if forward else "prev_jie"]["time"])
        born = datetime.fromisoformat(birth)
        early, late = (born, jie) if forward else (jie, born)
        shichen = (late.date() - early.date()).days * 12 + (late.hour + 1) // 2 % 12 - (early.hour + 1) // 2 % 12
        start = output["dayun"]["start"]
        assert (start["years"], start["months"], start["days"]) == (shichen // 36, shichen % 36 // 3, shichen % 3 * 10)

    def test_liunian(self):
        output = _chart("1990-05-15 10:00", query_year=2026)
        liunian = output["liunian"]
        assert liunian["ganzhi"] == _ganzhi(2026 - 4)
        assert liunian["age"] == 37
        period = next(p for p in output["dayun"]["periods"] if p["start_year"] <= 2026 <= p["end_year"])
        assert liunian["dayun_ganzhi"] == period["ganzhi"]


class TestInput:
    def test_lunar_equals_solar(self):
        # 农历 1990 年四月廿一 = 公历 1990-05-15
        lunar = _chart({"year": 1990, "month": 4, "day": 21, "hour": 10}, calendar_type="lunar")
        assert _pillars(lunar) == _pillars(_chart("1990-05-15 10:00"))

    def test_leap_month(self):
        # 2020 年闰四月初一 = 公历 2020-05-23
        leap = _chart({"year": 2020, "month": 4, "day": 1, "hour": 12, "is_leap_month": True}, calendar_type="lunar")
        assert _pillars(leap) == _pillars(_chart("2020-05-23 12:00"))

    @pytest.mark.parametrize("payload,message", [
        ({"birth_time": "1990-05-15 10:00"}, "gender"),
        ({"birth_time": "1990-05-15", "gender": "男"}, "出生时间"),
        ({"birth_time": {"year": 2021, "month": 4, "day": 1, "hour": 1, "is_leap_month": True},
          "calendar_type": "lunar", "gender": "男"}, "闰4月"),
        ({"birth_time": "1990-05-15 10:00", "gender": "男", "late_zi_rule": "x"}, "late_zi_rule"),
        ({"birth_time": "1990-05-15 10:00", "gender": "男", "query_year": 1980}, "query_year"),
    ])
    def test_rejects_bad_input(self, payload, message):
        with pytest.raises(ValueError, match=message):
            build_output(payload)

    def test_born_before_lichun_warns_about_age(self):
        assert any("立春前" in w for w in _chart("2024-01-10 10:00")["warnings"])
        assert not any("立春前" in w for w in _chart("2024-03-10 10:00")["warnings"])

    def test_hour_boundary_warning(self):
        assert any("时辰交界" in w for w in _chart("1990-05-15 10:58")["warnings"])


class TestTrueSolarTime:
    def test_urumqi_moves_hour_pillar(self):
        # 乌鲁木齐东经 87.6°：北京时间 10:30 约为真太阳时 08:32，巳时变辰时
        output = _chart("1990-12-01 10:30", true_solar_time=True, location={"longitude": 87.6})
        assert output["pillars"]["time"]["zhi"] == "辰"
        assert output["normalized_input"]["true_solar_time"]["true_solar_datetime"].startswith("1990-12-01 08:3")
        assert "真太阳时" in output["ruleset"]["time_rule"]
        assert _chart("1990-12-01 10:30")["pillars"]["time"]["zhi"] == "巳"

    def test_requires_longitude(self):
        with pytest.raises(ValueError, match="longitude"):
            _chart("1990-12-01 10:30", true_solar_time=True)

    def test_china_dst_warning(self):
        assert any("夏令时" in w for w in _chart("1990-05-15 10:00")["warnings"])
        dst_free = _chart("1990-05-15 10:00", true_solar_time=True, location={"longitude": 120})
        assert not any("夏令时" in w for w in dst_free["warnings"])

    def test_dst_warning_follows_location_timezone(self):
        output = _chart("1986-07-01 12:00", location={"timezone": "America/New_York"})
        assert [w for w in output["warnings"] if "夏令时" in w and "Asia/Shanghai" in w] == []


class TestCalendarLocale:
    def test_vn_only_changes_lunar_display(self):
        cn, vn = _chart("1985-01-25 10:00"), _chart("1985-01-25 10:00", calendar_locale="vn")
        assert _pillars(cn) == _pillars(vn)
        assert cn["calendar"]["lunar_text"].startswith("甲子年腊月初五")
        assert vn["calendar"]["lunar_text"].startswith("乙丑年正月初五")

    def test_vn_lunar_input(self):
        vn = _chart({"year": 1985, "month": 1, "day": 1, "hour": 10}, calendar_type="lunar", calendar_locale="vn")
        assert _pillars(vn) == _pillars(_chart("1985-01-21 10:00"))

    def test_south_vietnam_warning(self):
        assert any("越南南方" in w for w in _chart("1970-06-01 10:00", calendar_locale="vn")["warnings"])


def test_vietnamese_glossary_covers_output_terms():
    glossary = (Path(__file__).resolve().parents[2] / "references" / "thuat-ngu-vi.md").read_text(encoding="utf-8")
    terms = set()
    rng = random.Random(5)
    for _ in range(200):
        dt = datetime(1950, 1, 1) + timedelta(hours=rng.randrange(70 * 365 * 24))
        for pillar in _chart(dt.strftime("%Y-%m-%d %H:%M"))["pillars"].values():
            terms |= {pillar["shishen_gan"], pillar["dishi"]} | {h["shishen"] for h in pillar["hide_gan"]}
    assert len(terms) >= 22  # 10 十神 + 日主 + 12 长生
    assert [t for t in terms if t not in glossary] == []
