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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from lunar_python import LunarYear

DEFAULT_TIMEZONE = "Asia/Shanghai"
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
    if LunarYear.fromYear(year).getLeapMonth() != month:
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
