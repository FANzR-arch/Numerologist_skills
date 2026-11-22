import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from calendar_core import (
    apply_true_solar_time,
    LunarDate,
    _lunar_from_jdn,
    _sui_months,
    calendar_locale_warnings,
    lunar_to_solar,
    parse_calendar_locale,
    solar_to_lunar,
    clock_warnings,
    equation_of_time_minutes,
    hour_boundary_warning,
    parse_datetime_string,
    parse_gender,
    true_solar_time,
    validate_leap_month,
)


class TestParseDatetimeString:
    @pytest.mark.parametrize("text,expected", [
        ("1990-05-15 14:30", (1990, 5, 15, 14, 30, 0)),
        ("1990年5月15日 14时30分", (1990, 5, 15, 14, 30, 0)),
        ("1990/05/15T14:30:45", (1990, 5, 15, 14, 30, 45)),
        ("1990-05-15 14", (1990, 5, 15, 14, 0, 0)),
        ("1990-05-15", (1990, 5, 15, 0, 0, 0)),
    ])
    def test_formats(self, text, expected):
        keys = ("year", "month", "day", "hour", "minute", "second")
        assert tuple(parse_datetime_string(text)[k] for k in keys) == expected

    def test_missing_time_error(self):
        with pytest.raises(ValueError, match="需要时辰"):
            parse_datetime_string("1990-05-15", missing_time_error="需要时辰")

    @pytest.mark.parametrize("text,message", [("  ", "不能为空"), ("1990-05", "YYYY-MM-DD")])
    def test_bad_input(self, text, message):
        with pytest.raises(ValueError, match=message):
            parse_datetime_string(text)


def test_parse_gender():
    assert parse_gender("Female", "x") == "女"
    with pytest.raises(ValueError, match="大运顺逆"):
        parse_gender("", "大运顺逆")


def test_validate_leap_month():
    validate_leap_month(2020, 4)
    with pytest.raises(ValueError, match="闰4月"):
        validate_leap_month(2021, 4)


def test_hour_boundary_warning():
    assert "盘面" in hour_boundary_warning(10, 58, "盘面会改变")
    assert hour_boundary_warning(10, 0, "盘面会改变") is None


class TestEquationOfTime:
    # 均时差极值与零点的常见参考值（分钟；未核对出处，只作合理性检查，出处见 TestAgainstSources）
    @pytest.mark.parametrize("day,expected", [
        ((2, 11), -14.2), ((5, 14), 3.7), ((7, 26), -6.5), ((11, 3), 16.4),
        ((4, 15), 0.0), ((6, 13), 0.0), ((9, 1), 0.0), ((12, 25), 0.0),
    ])
    def test_published_values(self, day, expected):
        assert equation_of_time_minutes(datetime(2026, *day, 12)) == pytest.approx(expected, abs=0.7)


class TestTrueSolarTime:
    def test_urumqi(self):
        # 乌鲁木齐东经 87.6°，比东八区中央经线 120° 晚 129.6 分钟；12 月 1 日均时差约 +11 分钟
        true_dt, detail = true_solar_time(datetime(1990, 12, 1, 12, 0), 87.6)
        assert detail["longitude_correction_minutes"] == -129.6
        assert abs((true_dt - datetime(1990, 12, 1, 10, 1, 24)).total_seconds()) < 60

    def test_china_dst_is_removed(self):
        # 1990 年夏令时 UTC+9：钟表 10:00 = 北京标准时间 09:00，再加 5 月中旬均时差约 +3.7 分钟
        true_dt, detail = true_solar_time(datetime(1990, 5, 15, 10, 0), 120.0)
        assert detail["utc_offset_hours"] == 9
        assert abs((true_dt - datetime(1990, 5, 15, 9, 3, 40)).total_seconds()) < 60

    def test_other_timezone(self):
        # 河内东经 105.85°，东七区中央经线 105°
        _, detail = true_solar_time(datetime(2000, 4, 15, 8, 0), 105.85, "Asia/Ho_Chi_Minh")
        assert detail["longitude_correction_minutes"] == pytest.approx(3.4)

    def test_rejects_bad_longitude(self):
        with pytest.raises(ValueError, match="经度"):
            true_solar_time(datetime(2000, 1, 1), 200)

    def test_opt_in(self):
        civil = datetime(1990, 12, 1, 12, 0)
        assert apply_true_solar_time({}, civil) == (civil, None)
        with pytest.raises(ValueError, match="longitude"):
            apply_true_solar_time({"true_solar_time": True}, civil)
        with pytest.raises(ValueError, match="location.longitude"):
            apply_true_solar_time({"true_solar_time": True, "location": {"longitude": "abc"}}, civil)
        with pytest.raises(ValueError, match="true 或 false"):
            apply_true_solar_time({"true_solar_time": "false"}, civil)
        true_dt, detail = apply_true_solar_time({"true_solar_time": True, "location": {"longitude": 87.6}}, civil)
        assert detail["timezone"] == "Asia/Shanghai" and true_dt < civil


class TestClockWarnings:
    def test_dst(self):
        assert any("夏令时" in w for w in clock_warnings({}, datetime(1990, 5, 15, 10, 0)))
        assert clock_warnings({}, datetime(1990, 12, 1, 10, 0)) == []

    def test_uses_payload_timezone(self):
        payload = {"location": {"timezone": "America/New_York"}}
        assert any("America/New_York" in w for w in clock_warnings(payload, datetime(1986, 7, 1, 12, 0)))
        assert clock_warnings(payload, datetime(1990, 12, 15, 10, 0)) == []

    def test_dst_not_repeated_when_true_solar_time_applied(self):
        assert clock_warnings({"true_solar_time": True}, datetime(1990, 5, 15, 10, 0)) == []

    @pytest.mark.parametrize("civil,word", [
        (datetime(1986, 5, 4, 2, 30), "不存在"),   # 拨快一小时的空档
        (datetime(1986, 9, 14, 1, 30), "出现两次"),  # 拨回一小时的重叠
    ])
    def test_gap_and_overlap(self, civil, word):
        for payload in ({}, {"true_solar_time": True}):
            assert any(word in w for w in clock_warnings(payload, civil))


class TestLunarCalendar:
    def test_cn_matches_lunar_python(self):
        from lunar_python import Solar
        d = date(1900, 2, 1)
        while d < date(2100, 12, 1):
            lunar = Solar.fromYmd(d.year, d.month, d.day).getLunar()
            assert solar_to_lunar(d) == (lunar.getYear(), abs(lunar.getMonth()), lunar.getDay(), lunar.getMonth() < 0)
            d += timedelta(days=29)

    def test_vn_engine_at_utc8_matches_chinese_calendar(self):
        # 同一套定朔定气与置闰规则放在东八区，必须复现 lunar_python 的中国农历（1967-2100）每个月的初一、月号与闰月；
        # 月内其余日期只是初一的偏移，所以逐月核对初一即覆盖全部日期
        from lunar_python import Solar
        for year in range(1967, 2100):
            for month, is_leap, first in _sui_months(year, 8):
                d = date.fromordinal(first - 1721425)
                lunar = Solar.fromYmd(d.year, d.month, d.day).getLunar()
                assert (abs(lunar.getMonth()), lunar.getDay(), lunar.getMonth() < 0) == (month, 1, is_leap), d
                assert _lunar_from_jdn(first, 8, d.year).year == lunar.getYear(), d

    @pytest.mark.parametrize("vn_tet,cn_tet", [
        (date(1968, 1, 29), date(1968, 1, 30)),  # 戊申年春节，越南北方新历
        (date(1985, 1, 21), date(1985, 2, 20)),  # 越南乙丑年正月比中国早一个月
        (date(2007, 2, 17), date(2007, 2, 18)),
    ])
    def test_documented_tet_differences(self, vn_tet, cn_tet):
        assert lunar_to_solar(vn_tet.year, 1, 1, False, "vn") == vn_tet
        assert lunar_to_solar(cn_tet.year, 1, 1, False, "cn") == cn_tet
        assert solar_to_lunar(vn_tet, "vn") == (vn_tet.year, 1, 1, False)

    def test_vn_before_1968_follows_chinese_calendar(self):
        assert solar_to_lunar(date(1960, 6, 1), "vn") == solar_to_lunar(date(1960, 6, 1), "cn")

    def test_vn_round_trip(self):
        d = date(1967, 12, 1)
        while d < date(2100, 1, 1):
            assert lunar_to_solar(*solar_to_lunar(d, "vn"), "vn") == d, d
            d += timedelta(days=5)

    def test_vn_rejects_missing_days(self):
        with pytest.raises(ValueError, match="没有闰"):
            lunar_to_solar(2021, 4, 1, True, "vn")
        with pytest.raises(ValueError, match="没有30日"):
            lunar_to_solar(2024, 1, 30, False, "vn")  # 越南 2024 年正月小
        with pytest.raises(ValueError, match="改历交界"):
            lunar_to_solar(1967, 10, 30, False, "vn")
        assert lunar_to_solar(1967, 10, 29, False, "vn") == date(1967, 11, 30)

    def test_text(self):
        assert LunarDate(2020, 4, 1, True).text == "庚子年闰四月初一"

    def test_locale(self):
        assert parse_calendar_locale({}) == "cn"
        with pytest.raises(ValueError, match="calendar_locale"):
            parse_calendar_locale({"calendar_locale": "jp"})
        assert calendar_locale_warnings("vn", date(1970, 1, 1))
        assert calendar_locale_warnings("cn", date(1970, 1, 1)) == []

    def test_vn_warns_when_differs_from_chinese_calendar(self):
        # 1985-01-25：越南乙丑年正月初五，中国甲子年腊月初五；提醒以免把正确结果当成错误
        warnings = calendar_locale_warnings("vn", date(1985, 1, 25))
        assert any("乙丑年正月初五" in w and "甲子年腊月初五" in w for w in warnings)
        assert calendar_locale_warnings("vn", date(1990, 5, 15)) == []


def test_common_glossary_covers_stems_and_branches():
    glossary = (Path(__file__).resolve().parents[1] / "thuat-ngu-chung.md").read_text(encoding="utf-8")
    for char in "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥金木水火土":
        assert f"| {char} |" in glossary or f"{char} " in glossary, char


class TestAgainstSources:
    def test_equation_of_time_follows_noaa(self):
        # NOAA GML "General Solar Position Calculations"：γ = 2π/365·(day_of_year − 1 + (hour − 12)/24)，闰年分母用 366；hour 为 UTC
        import math
        for utc, days in ((datetime(2024, 3, 1, 3, 0), 366), (datetime(2023, 3, 1, 3, 0), 365)):
            gamma = 2 * math.pi / days * (utc.timetuple().tm_yday - 1 + (utc.hour - 12) / 24)
            expected = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma)
                                 - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma))
            assert equation_of_time_minutes(utc) == pytest.approx(expected, abs=1e-9)

    def test_true_solar_time_uses_utc_for_eot(self):
        # NOAA：time_offset = eqtime + 4·longitude − 60·timezone；均时差按 UTC 时刻取
        civil = datetime(2024, 3, 1, 10, 0)
        true_dt, detail = true_solar_time(civil, 120.0)
        eot = equation_of_time_minutes(datetime(2024, 3, 1, 2, 0))
        assert detail["equation_of_time_minutes"] == round(eot, 1)
        assert abs((true_dt - (civil + timedelta(minutes=eot))).total_seconds()) < 1

    def test_south_vietnam_warning_window_follows_tzdb(self):
        # tzdb asia：南越 1959-12-31 至 1975-06-13 使用 +08；Aslaksen (2010) p.29：1968 年南越春节按东八区为 1 月 30 日
        assert any("越南南方" in w for w in calendar_locale_warnings("vn", date(1975, 6, 12)))
        assert not any("越南南方" in w for w in calendar_locale_warnings("vn", date(1975, 6, 13)))
