# 由 tools/sync_core.py 从 core/calendar_core.py 生成，勿手改。
"""三个排盘脚本共用的输入解析与时间校正。

本文件是唯一源头。各 skill 的 scripts/calendar_core.py 由 tools/sync_core.py 生成，
每个 skill 单独安装时也能运行；改动只改这里，再运行 python tools/sync_core.py。
"""
from __future__ import annotations

import argparse
import calendar
import json
import math
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, NamedTuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "Asia/Shanghai"


@lru_cache(maxsize=None)
def _lp() -> SimpleNamespace:
    """按需导入 lunar_python：只用解析与 CLI 的脚本（如 numerology）不依赖它。"""
    try:
        from lunar_python import Lunar, LunarYear, Solar
        from lunar_python.util import LunarUtil
        from lunar_python.util.ShouXingUtil import ShouXingUtil
    except ImportError as exc:
        raise RuntimeError("缺少依赖 lunar_python，请先运行 pip install -r <skill_dir>/scripts/requirements.txt") from exc
    return SimpleNamespace(Lunar=Lunar, LunarYear=LunarYear, Solar=Solar, LunarUtil=LunarUtil, ShouXingUtil=ShouXingUtil)
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
CALENDAR_LOCALES = {
    "cn": "中国农历（东八区定朔定气，lunar_python）",
    "vn": "越南农历：1967 年十一月（1967-12）起按东七区定朔定气；此前按中国农历（东八区）计算，越南当时实际用北京子午线的传统历，个别日期可能差一天",
}
J2000_JDN = 2451545
ORDINAL_TO_JDN = 1721425  # date.toordinal() + ORDINAL_TO_JDN = 儒略日数
VN_UTC7_FROM_SUI = 1967  # 越南 1967 年改用东七区编历，1968 年春节起与中国农历分开
GENDER_ALIASES = {"男": "男", "male": "男", "m": "男", "女": "女", "female": "女", "f": "女"}


def parse_datetime_string(value: str, missing_time_error: str | None = None) -> dict[str, int]:
    """解析 "YYYY-MM-DD HH:MM[:SS]" 及中文写法。缺时间时，给了 missing_time_error 就报错，否则按 00:00。"""
    normalized = value.strip().replace("T", " ").replace("/", "-").replace("年", "-").replace("月", "-").replace("日", " ")
    normalized = normalized.replace("时", ":").replace("點", ":").replace("点", ":").replace("分", "").replace("秒", "")
    parts = normalized.split()
    if not parts:
        raise ValueError("时间不能为空")
    date_bits = [int(bit) for bit in parts[0].split("-") if bit]
    if len(date_bits) != 3:
        raise ValueError("日期格式需为 YYYY-MM-DD")
    time_bits = [int(bit) for bit in parts[1].split(":") if bit] if len(parts) > 1 else []
    if not time_bits and missing_time_error:
        raise ValueError(missing_time_error)
    time_bits += [0] * (3 - len(time_bits))
    return {
        "year": date_bits[0],
        "month": date_bits[1],
        "day": date_bits[2],
        "hour": time_bits[0],
        "minute": time_bits[1],
        "second": time_bits[2],
    }


def parse_gender(value: Any, reason: str) -> str:
    gender = str(value or "").strip().lower()
    if gender not in GENDER_ALIASES:
        raise ValueError(f"缺少或无法识别 gender（男/女）：{reason}，请先向用户确认")
    return GENDER_ALIASES[gender]


def validate_leap_month(year: int, month: int) -> None:
    if _lp().LunarYear.fromYear(year).getLeapMonth() != month:
        raise ValueError(f"农历 {year} 年没有闰{month}月")


def hour_boundary_warning(hour: int, minute: int, effect: str) -> str | None:
    minutes = hour * 60 + minute
    distance = min((minutes - 60) % 120, 120 - (minutes - 60) % 120)
    if distance <= 15:
        return f"出生时间距时辰交界不足 15 分钟，时辰有误差时{effect}，建议按相邻两个时辰各排一盘对照。"
    return None


def get_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"无法识别时区 {name}: {exc}") from exc


def payload_timezone(payload: dict[str, Any]) -> str:
    return (payload.get("location") or {}).get("timezone") or DEFAULT_TIMEZONE


def clock_warnings(payload: dict[str, Any], civil: datetime) -> list[str]:
    """钟表时间的时区提醒，不改变排盘结果：
    拨钟空档 / 重叠（总是提醒）；夏令时（如中国 1986-1991 年夏季，已开真太阳时则不提醒，因为已按实际时差换算）。"""
    name = payload_timezone(payload)
    zone = get_zone(name)
    first, second = civil.replace(tzinfo=zone, fold=0), civil.replace(tzinfo=zone, fold=1)
    warnings = []
    if first.utcoffset() != second.utcoffset():
        exists = first.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) == civil
        kind = "当天出现两次（夏令时结束拨回），按第一次（夏令时）计算" if exists else "不存在（夏令时开始拨快），按标准时间计算"
        warnings.append(f"{civil:%Y-%m-%d %H:%M} 在 {name} {kind}；请向用户确认出生时刻。")
    dst = first.dst()
    if dst and not payload.get("true_solar_time"):
        warnings.append(f"{civil:%Y-%m-%d %H:%M} 在 {name} 处于夏令时（快 {dst.total_seconds() / 3600:g} 小时），"
                        f"标准时间为 {civil - dst:%H:%M}；若用户报的是当时钟表时间，时辰可能需按标准时间或真太阳时（true_solar_time）重排。")
    return warnings


def equation_of_time_minutes(utc: datetime) -> float:
    """均时差（真太阳时 − 平太阳时，分钟），按 NOAA GML《General Solar Position Calculations》公式：
    γ 取 UTC 时刻的年内分数，闰年分母为 366。"""
    days_in_year = 366 if calendar.isleap(utc.year) else 365
    gamma = 2 * math.pi / days_in_year * (utc.timetuple().tm_yday - 1 + (utc.hour - 12) / 24)
    return 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma)
                     - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma))


def true_solar_time(civil: datetime, longitude: float, timezone_name: str = DEFAULT_TIMEZONE) -> tuple[datetime, dict[str, Any]]:
    """民用时间换算真太阳时：先按时区（含夏令时）换回 UTC，再加经度时差与均时差。"""
    if not -180 <= longitude <= 180:
        raise ValueError("经度 longitude 需在 -180 到 180 之间（东经为正）")
    offset = civil.replace(tzinfo=get_zone(timezone_name)).utcoffset()
    utc = civil - offset
    eot = equation_of_time_minutes(utc)
    # NOAA：time_offset = eqtime + 4·longitude − 60·timezone
    true_dt = (utc + timedelta(minutes=longitude * 4 + eot)).replace(microsecond=0)
    detail = {
        "civil_datetime": civil.isoformat(sep=" "),
        "timezone": timezone_name,
        "utc_offset_hours": offset.total_seconds() / 3600,
        "longitude": longitude,
        "longitude_correction_minutes": round(longitude * 4 - offset.total_seconds() / 60, 1),
        "equation_of_time_minutes": round(eot, 1),
        "true_solar_datetime": true_dt.isoformat(sep=" "),
    }
    return true_dt, detail


def apply_true_solar_time(payload: dict[str, Any], civil: datetime) -> tuple[datetime, dict[str, Any] | None]:
    """payload 带 "true_solar_time": true 时按 location.longitude / location.timezone 校正，否则原样返回。"""
    flag = payload.get("true_solar_time")
    if flag not in (None, True, False):
        raise ValueError("true_solar_time 只接受 true 或 false")
    if not flag:
        return civil, None
    location = payload.get("location") or {}
    if location.get("longitude") in (None, ""):
        raise ValueError("true_solar_time 需要出生地经度 location.longitude（东经为正），请先向用户确认出生地")
    try:
        longitude = float(location["longitude"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"location.longitude 需为数字（东经为正），收到 {location['longitude']!r}") from exc
    return true_solar_time(civil, longitude, payload_timezone(payload))


class LunarDate(NamedTuple):
    year: int
    month: int
    day: int
    is_leap: bool

    @property
    def text(self) -> str:
        ganzhi = STEMS[(self.year - 4) % 10] + BRANCHES[(self.year - 4) % 12]
        return f"{ganzhi}年{'闰' if self.is_leap else ''}{_lp().LunarUtil.MONTH[self.month]}月{_lp().LunarUtil.DAY[self.day]}"


def parse_calendar_locale(payload: dict[str, Any]) -> str:
    locale = str(payload.get("calendar_locale") or "cn").strip().lower()
    if locale not in CALENDAR_LOCALES:
        raise ValueError(f"calendar_locale 只接受 {sorted(CALENDAR_LOCALES)}")
    return locale


@lru_cache(maxsize=None)
def _new_moon_jdn(n: int, tz: int) -> int:
    """第 n 个朔（n=0 约在 2000-01-06）所在当地日的儒略日数；shuoHigh 返回东八区时刻（距 J2000 的日数）。"""
    return math.floor(_lp().ShouXingUtil.shuoHigh(n * 2 * math.pi) + 0.5 + (tz - 8) / 24) + J2000_JDN


@lru_cache(maxsize=None)
def _term_jdn(k: int, tz: int) -> int:
    """第 k 个节气（k=0 为 1999 年春分，每 15°，偶数为中气）所在当地日的儒略日数。"""
    return math.floor(_lp().ShouXingUtil.qiHigh(k * math.pi / 12) + 0.5 + (tz - 8) / 24) + J2000_JDN


def _lunation_containing(jdn: int, tz: int) -> int:
    n = math.floor((jdn - 2451551) / 29.5306)
    while _new_moon_jdn(n, tz) > jdn:
        n -= 1
    while _new_moon_jdn(n + 1, tz) <= jdn:
        n += 1
    return n


@lru_cache(maxsize=None)
def _sui_months(year: int, tz: int) -> tuple[tuple[int, bool, int], ...]:
    """year 年冬至所在月（十一月）起、到次年冬至所在月之前的各月 (月, 是否闰月, 初一儒略日数)。
    岁中有 13 个月时，十一月之后第一个不含中气的月为闰月。"""
    solstice_k = 24 * (year - 1999) + 18
    start = _lunation_containing(_term_jdn(solstice_k, tz), tz)
    end = _lunation_containing(_term_jdn(solstice_k + 24, tz), tz)
    zhongqi = [_term_jdn(k, tz) for k in range(solstice_k, solstice_k + 25, 2)]
    months: list[tuple[int, bool, int]] = []
    number, leap_pending = 11, end - start == 13
    for n in range(start, end):
        first, nxt = _new_moon_jdn(n, tz), _new_moon_jdn(n + 1, tz)
        if leap_pending and months and not any(first <= q < nxt for q in zhongqi):
            months.append((months[-1][0], True, first))
            leap_pending = False
            continue
        months.append((number, False, first))
        number = number % 12 + 1
    return tuple(months)


def _lunar_from_jdn(jdn: int, tz: int, year: int) -> LunarDate:
    sui_year = year if jdn >= _sui_months(year, tz)[0][2] else year - 1
    months = _sui_months(sui_year, tz)
    for i, (month, is_leap, first) in enumerate(months):
        if i + 1 == len(months) or months[i + 1][2] > jdn:
            lunar_year = sui_year if month >= 11 and i < 3 else sui_year + 1
            return LunarDate(lunar_year, month, jdn - first + 1, is_leap)
    raise AssertionError("unreachable")


def solar_to_lunar(day: date, locale: str = "cn") -> LunarDate:
    jdn = day.toordinal() + ORDINAL_TO_JDN
    if locale == "vn" and jdn >= _sui_months(VN_UTC7_FROM_SUI, 7)[0][2]:
        return _lunar_from_jdn(jdn, 7, day.year)
    lunar = _lp().Solar.fromYmd(day.year, day.month, day.day).getLunar()
    return LunarDate(lunar.getYear(), abs(lunar.getMonth()), lunar.getDay(), lunar.getMonth() < 0)


def lunar_to_solar(year: int, month: int, day: int, is_leap: bool, locale: str = "cn") -> date:
    sui_year = year if month >= 11 else year - 1
    if locale == "vn" and sui_year >= VN_UTC7_FROM_SUI:
        months = _sui_months(sui_year, 7)
        for m, leap, first in (months if month >= 11 else months[2:]):
            if m == month and leap == is_leap:
                result = date.fromordinal(first + day - 1 - ORDINAL_TO_JDN)
                if day < 1 or solar_to_lunar(result, "vn") != (year, month, day, is_leap):
                    raise ValueError(f"越南农历 {year} 年{'闰' if is_leap else ''}{month}月没有{day}日")
                return result
        raise ValueError(f"越南农历 {year} 年没有闰{month}月" if is_leap else f"越南农历 {year} 年没有 {month} 月")
    if is_leap:
        validate_leap_month(year, month)
    solar = _lp().Lunar.fromYmd(year, -month if is_leap else month, day).getSolar()
    result = date(solar.getYear(), solar.getMonth(), solar.getDay())
    # 改历交界：中国农历 1967 年十月三十已落在越南新历十一月初一，越南阴历没有这一天
    if locale == "vn" and solar_to_lunar(result, "vn") != (year, month, day, is_leap):
        raise ValueError(f"越南阴历 {year} 年{month}月没有{day}日（1967 年底改历交界）")
    return result


def calendar_locale_warnings(locale: str, day: date) -> list[str]:
    warnings = []
    if locale == "vn":
        vn, cn = solar_to_lunar(day, "vn"), solar_to_lunar(day, "cn")
        if vn != cn:
            warnings.append(f"{day.isoformat()} 越南阴历为 {vn.text}，中国农历为 {cn.text}：两国历法按不同时区（东七区 / 东八区）定朔，本盘按越南阴历排。"
                            "这不是计算错误，不要用中国农历的春节日期去“纠正”；用户要按中国农历看时改传 calendar_locale=cn。")
        # 南越 1959-12-31 至 1975-06-13 用 +08（tzdb asia）；1968 年南北春节不同（Aslaksen 2010 p.29）
        if date(1967, 12, 1) <= day < date(1975, 6, 13):
            warnings.append("1967 年 12 月至 1975-06-13 越南南方时钟用东八区，农历沿用传统历（1968 年南方春节为 1 月 30 日，北方为 1 月 29 日），与北方（东七区）个别月份日期不同；出生在南方时请向用户确认，必要时改用 calendar_locale=cn 对照。")
    return warnings


def run_cli(build_output: Callable[[dict[str, Any]], dict[str, Any]], description: str) -> int:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--input", required=True, help="Path to input JSON")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        payload = json.loads(input_path.read_text(encoding="utf-8-sig"))
        output = build_output(payload)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0
    except Exception as exc:
        error_payload = {"error": str(exc)}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(error_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1
