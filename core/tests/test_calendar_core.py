import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from calendar_core import (
    apply_true_solar_time,
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
    # 均时差极值与零点（天文年历公布值，分钟）
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
