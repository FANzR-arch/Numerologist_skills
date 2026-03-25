#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from lunar_python import Lunar, Solar

DEFAULT_RULESET = "mainline-cn-v1"
DEFAULT_TIMEZONE = "Asia/Shanghai"
CHINA_NAMES = {"cn", "china", "中国", "中华人民共和国", ""}

JIAZI = [
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥",
]

YANG_TERMS = {
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
}

JU_TABLE = {
    "阳遁": {
        "冬至": {"上元": 1, "中元": 7, "下元": 4},
        "小寒": {"上元": 2, "中元": 8, "下元": 5},
        "大寒": {"上元": 3, "中元": 9, "下元": 6},
        "立春": {"上元": 8, "中元": 5, "下元": 2},
        "雨水": {"上元": 9, "中元": 6, "下元": 3},
        "惊蛰": {"上元": 1, "中元": 7, "下元": 4},
        "春分": {"上元": 3, "中元": 9, "下元": 6},
        "清明": {"上元": 4, "中元": 1, "下元": 7},
        "谷雨": {"上元": 5, "中元": 2, "下元": 8},
        "立夏": {"上元": 4, "中元": 1, "下元": 7},
        "小满": {"上元": 5, "中元": 2, "下元": 8},
        "芒种": {"上元": 6, "中元": 3, "下元": 9},
    },
    "阴遁": {
        "夏至": {"上元": 9, "中元": 3, "下元": 6},
        "小暑": {"上元": 8, "中元": 2, "下元": 5},
        "大暑": {"上元": 7, "中元": 1, "下元": 4},
        "立秋": {"上元": 2, "中元": 5, "下元": 8},
        "处暑": {"上元": 1, "中元": 4, "下元": 7},
        "白露": {"上元": 9, "中元": 3, "下元": 6},
        "秋分": {"上元": 7, "中元": 1, "下元": 4},
        "寒露": {"上元": 6, "中元": 9, "下元": 3},
        "霜降": {"上元": 5, "中元": 8, "下元": 2},
        "立冬": {"上元": 6, "中元": 9, "下元": 3},
        "小雪": {"上元": 5, "中元": 8, "下元": 2},
        "大雪": {"上元": 4, "中元": 7, "下元": 1},
    },
}

EARTH_STEM_ORDER = {
    "阳遁": ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"],
    "阴遁": ["戊", "乙", "丙", "丁", "癸", "壬", "辛", "庚", "己"],
}

ROTATION_RING = [1, 8, 3, 4, 9, 2, 7, 6]
STAR_RING = ["天蓬", "天任", "天冲", "天辅", "天英", "天芮", "天柱", "天心"]
DOOR_RING = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]
GOD_RING_YANG = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
GOD_RING_YIN = ["值符", "九天", "九地", "玄武", "白虎", "六合", "太阴", "螣蛇"]

XUNSHOU_TO_HIDDEN_YI = {
    "甲子": "戊",
    "甲戌": "己",
    "甲申": "庚",
    "甲午": "辛",
    "甲辰": "壬",
    "甲寅": "癸",
}

BRANCH_TO_PALACE = {
    "子": 1,
    "丑": 8,
    "寅": 8,
    "卯": 3,
    "辰": 4,
    "巳": 4,
    "午": 9,
    "未": 2,
    "申": 2,
    "酉": 7,
    "戌": 6,
    "亥": 6,
}

PALACE_INFO = {
    1: {"name": "坎宫", "direction": "北", "trigram": "坎", "element": "水"},
    2: {"name": "坤宫", "direction": "西南", "trigram": "坤", "element": "土"},
    3: {"name": "震宫", "direction": "东", "trigram": "震", "element": "木"},
    4: {"name": "巽宫", "direction": "东南", "trigram": "巽", "element": "木"},
    5: {"name": "中宫", "direction": "中", "trigram": "中", "element": "土"},
    6: {"name": "乾宫", "direction": "西北", "trigram": "乾", "element": "金"},
    7: {"name": "兑宫", "direction": "西", "trigram": "兑", "element": "金"},
    8: {"name": "艮宫", "direction": "东北", "trigram": "艮", "element": "土"},
    9: {"name": "离宫", "direction": "南", "trigram": "离", "element": "火"},
}

GRID_ORDER = [4, 9, 2, 3, 5, 7, 8, 1, 6]


def get_timezone(name: str):
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name == DEFAULT_TIMEZONE:
            return timezone(timedelta(hours=8), name=DEFAULT_TIMEZONE)
        if name.upper() == "UTC":
            return timezone.utc
        raise


@dataclass
class NormalizedInput:
    question_type: str
    question_goal: str
    calendar_type: str
    timezone: str
    country: str
    city: str
    use_now: bool
    leap_month: bool
    solar_dt: datetime
    lunar_input: dict[str, Any] | None
    original_time_input: Any
    warnings: list[str]


def rotate_to_start(seq: list[Any], start: Any) -> list[Any]:
    idx = seq.index(start)
    return seq[idx:] + seq[:idx]


def parse_datetime_string(value: str) -> dict[str, int]:
    normalized = value.strip().replace("T", " ").replace("/", "-").replace("年", "-").replace("月", "-").replace("日", " ")
    normalized = normalized.replace("时", ":").replace("點", ":").replace("点", ":").replace("分", "").replace("秒", "")
    parts = normalized.split()
    if not parts:
        raise ValueError("time_input 不能为空")
    date_part = parts[0]
    date_bits = [int(bit) for bit in date_part.split("-") if bit]
    if len(date_bits) != 3:
        raise ValueError("日期格式需为 YYYY-MM-DD")
    time_bits = [0, 0, 0]
    if len(parts) > 1:
        raw_time = parts[1]
        tmp = [int(bit) for bit in raw_time.split(":") if bit]
        if len(tmp) >= 2:
            time_bits[0] = tmp[0]
            time_bits[1] = tmp[1]
        if len(tmp) >= 3:
            time_bits[2] = tmp[2]
    return {
        "year": date_bits[0],
        "month": date_bits[1],
        "day": date_bits[2],
        "hour": time_bits[0],
        "minute": time_bits[1],
        "second": time_bits[2],
    }


def resolve_timezone(location: dict[str, Any], warnings: list[str]) -> str:
    timezone = (location.get("timezone") or "").strip()
    if timezone:
        return timezone
    country = (location.get("country") or "").strip().lower()
    city = (location.get("city") or "").strip()
    if country in CHINA_NAMES or not country:
        return DEFAULT_TIMEZONE
    warnings.append(f"未提供海外时区，脚本暂按 {DEFAULT_TIMEZONE} 计算，请在访谈中先补齐时区。")
    if city:
        warnings.append(f"已收到海外城市 {city}，但仍缺少明确时区。")
    return DEFAULT_TIMEZONE


def normalize_input(payload: dict[str, Any]) -> NormalizedInput:
    warnings: list[str] = []
    location = payload.get("location") or {}
    timezone = resolve_timezone(location, warnings)
    try:
        tz = get_timezone(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"无法识别时区 {timezone}: {exc}") from exc

    calendar_type = str(payload.get("calendar_type") or "solar").strip().lower()
    original_time_input = payload.get("time_input")
    leap_month = False
    lunar_input: dict[str, Any] | None = None

    if calendar_type == "now":
        solar_dt = datetime.now(tz).replace(microsecond=0)
        use_now = True
    elif calendar_type == "solar":
        use_now = False
        if isinstance(original_time_input, dict):
            raw = {
                "year": int(original_time_input["year"]),
                "month": int(original_time_input["month"]),
                "day": int(original_time_input["day"]),
                "hour": int(original_time_input.get("hour", 0)),
                "minute": int(original_time_input.get("minute", 0)),
                "second": int(original_time_input.get("second", 0)),
            }
        else:
            raw = parse_datetime_string(str(original_time_input))
        solar_dt = datetime(raw["year"], raw["month"], raw["day"], raw["hour"], raw["minute"], raw["second"], tzinfo=tz)
    elif calendar_type == "lunar":
        use_now = False
        if isinstance(original_time_input, dict):
            raw = {
                "year": int(original_time_input["year"]),
                "month": int(original_time_input["month"]),
                "day": int(original_time_input["day"]),
                "hour": int(original_time_input.get("hour", 0)),
                "minute": int(original_time_input.get("minute", 0)),
                "second": int(original_time_input.get("second", 0)),
                "is_leap_month": bool(original_time_input.get("is_leap_month", False)),
            }
        else:
            raw = parse_datetime_string(str(original_time_input))
            raw["is_leap_month"] = bool(payload.get("is_leap_month", False))
        leap_month = bool(raw.get("is_leap_month", False))
        lunar_month = -raw["month"] if leap_month else raw["month"]
        lunar_obj = Lunar.fromYmdHms(raw["year"], lunar_month, raw["day"], raw["hour"], raw["minute"], raw["second"])
        solar_obj = lunar_obj.getSolar()
        solar_dt = datetime(
            solar_obj.getYear(),
            solar_obj.getMonth(),
            solar_obj.getDay(),
            solar_obj.getHour(),
            solar_obj.getMinute(),
            solar_obj.getSecond(),
            tzinfo=tz,
        )
        lunar_input = raw
    else:
        raise ValueError(f"不支持的 calendar_type: {calendar_type}")

    return NormalizedInput(
        question_type=str(payload.get("question_type") or "").strip(),
        question_goal=str(payload.get("question_goal") or "").strip(),
        calendar_type=calendar_type,
        timezone=timezone,
        country=str(location.get("country") or "").strip(),
        city=str(location.get("city") or "").strip(),
        use_now=use_now,
        leap_month=leap_month,
        solar_dt=solar_dt,
        lunar_input=lunar_input,
        original_time_input=original_time_input,
        warnings=warnings,
    )


def build_solar_and_lunar(normalized: NormalizedInput) -> tuple[Solar, Any]:
    solar = Solar.fromYmdHms(
        normalized.solar_dt.year,
        normalized.solar_dt.month,
        normalized.solar_dt.day,
        normalized.solar_dt.hour,
        normalized.solar_dt.minute,
        normalized.solar_dt.second,
    )
    lunar = solar.getLunar()
    return solar, lunar


def active_jie(lunar: Any) -> tuple[str, Any, Any]:
    prev_jie = lunar.getPrevJie(False)
    next_jie = lunar.getNextJie(False)
    if prev_jie is None:
        raise ValueError("无法确定当前节令")
    return prev_jie.getName(), prev_jie, next_jie


def compute_yuan(day_ganzhi: str) -> str:
    idx = JIAZI.index(day_ganzhi)
    return ["上元", "中元", "下元"][(idx // 5) % 3]


def compute_earth_plate(dun_type: str, ju_number: int) -> dict[int, str]:
    palaces = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rotated = rotate_to_start(palaces, ju_number)
    stems = EARTH_STEM_ORDER[dun_type]
    return dict(zip(rotated, stems))


def find_stem_palace(earth_plate: dict[int, str], stem: str) -> int:
    for palace, palace_stem in earth_plate.items():
        if palace_stem == stem:
            return palace
    raise ValueError(f"地盘中未找到天干 {stem}")


def hosted_palace(palace: int) -> int:
    return 2 if palace == 5 else palace


def split_branch_pair(text: str) -> list[str]:
    return [text[i : i + 1] for i in range(0, len(text), 1) if text[i : i + 1]]


def build_chart(normalized: NormalizedInput, solar: Solar, lunar: Any) -> dict[str, Any]:
    warnings = list(normalized.warnings)

    current_jie_name, prev_jie, next_jie = active_jie(lunar)
    dun_type = "阳遁" if current_jie_name in YANG_TERMS else "阴遁"
    day_ganzhi = lunar.getDayInGanZhiExact()
    yuan = compute_yuan(day_ganzhi)
    ju_number = JU_TABLE[dun_type][current_jie_name][yuan]
    earth_plate = compute_earth_plate(dun_type, ju_number)

    time_ganzhi = lunar.getTimeInGanZhi()
    time_gan = lunar.getTimeGan()
    time_xun = lunar.getTimeXun()
    time_xunkong = lunar.getTimeXunKong()
    hidden_yi = XUNSHOU_TO_HIDDEN_YI[time_xun]
    visible_time_gan = hidden_yi if time_gan == "甲" else time_gan
    if time_gan == "甲":
        warnings.append(f"时干为甲，按旬首所遁之仪 {hidden_yi} 入盘。")

    xunshou_raw_palace = find_stem_palace(earth_plate, hidden_yi)
    time_raw_palace = find_stem_palace(earth_plate, visible_time_gan)
    xunshou_palace = hosted_palace(xunshou_raw_palace)
    time_palace = hosted_palace(time_raw_palace)

    if xunshou_raw_palace == 5 or time_raw_palace == 5:
        warnings.append("本规则集中宫相关判断一律寄坤处理。")

    if dun_type == "阳遁":
        palace_order = rotate_to_start(ROTATION_RING, time_palace)
        star_order = rotate_to_start(STAR_RING, STAR_RING[ROTATION_RING.index(xunshou_palace)])
        door_order = rotate_to_start(DOOR_RING, DOOR_RING[ROTATION_RING.index(xunshou_palace)])
        god_order = GOD_RING_YANG
        outer_earth = [earth_plate[palace] for palace in ROTATION_RING]
    else:
        reverse_ring = list(reversed(ROTATION_RING))
        reverse_star_ring = list(reversed(STAR_RING))
        reverse_door_ring = list(reversed(DOOR_RING))
        palace_order = rotate_to_start(reverse_ring, time_palace)
        star_order = rotate_to_start(reverse_star_ring, STAR_RING[ROTATION_RING.index(xunshou_palace)])
        door_order = rotate_to_start(reverse_door_ring, DOOR_RING[ROTATION_RING.index(xunshou_palace)])
        god_order = GOD_RING_YIN
        outer_earth = [earth_plate[palace] for palace in reverse_ring]

    sky_start_stem = hidden_yi if xunshou_raw_palace != 5 else earth_plate[xunshou_palace]
    sky_order = rotate_to_start(outer_earth, sky_start_stem)
    star_map = dict(zip(palace_order, star_order))
    door_map = dict(zip(palace_order, door_order))
    god_map = dict(zip(palace_order, god_order))
    sky_map = dict(zip(palace_order, sky_order))

    zhifu = {"star": star_map[time_palace], "palace": time_palace}
    zhishi = {"door": door_map[time_palace], "palace": time_palace}

    active_jie_dt = datetime.fromisoformat(prev_jie.getSolar().toYmdHms().replace(" ", "T")).replace(tzinfo=normalized.solar_dt.tzinfo)
    next_jie_dt = None
    if next_jie is not None:
        next_jie_dt = datetime.fromisoformat(next_jie.getSolar().toYmdHms().replace(" ", "T")).replace(tzinfo=normalized.solar_dt.tzinfo)
    if abs(normalized.solar_dt - active_jie_dt) <= timedelta(hours=24):
        warnings.append("当前时间距离节令起点较近，属于节气边界附近。")
    if next_jie_dt and abs(next_jie_dt - normalized.solar_dt) <= timedelta(hours=24):
        warnings.append("当前时间距离下一个节令较近，属于节气边界附近。")

    kongwang_branches = split_branch_pair(time_xunkong)
    kongwang_palaces = sorted({BRANCH_TO_PALACE[branch] for branch in kongwang_branches if branch in BRANCH_TO_PALACE})

    palaces: list[dict[str, Any]] = []
    for palace_no in sorted(PALACE_INFO):
        info = PALACE_INFO[palace_no]
        palace_entry = {
            "palace": palace_no,
            "name": info["name"],
            "direction": info["direction"],
            "trigram": info["trigram"],
            "element": info["element"],
            "earth_stem": earth_plate.get(palace_no),
            "sky_stem": sky_map.get(palace_no),
            "star": "天禽" if palace_no == 5 else star_map.get(palace_no),
            "door": None if palace_no == 5 else door_map.get(palace_no),
            "god": None if palace_no == 5 else god_map.get(palace_no),
            "is_center": palace_no == 5,
            "hosts_center": palace_no == 2,
            "hosting_note": "中宫寄坤" if palace_no in {2, 5} else None,
        }
        palaces.append(palace_entry)

    return {
        "dun_type": dun_type,
        "yuan": yuan,
        "ju_number": ju_number,
        "xunshou": time_xun,
        "hidden_yi": hidden_yi,
        "kongwang": kongwang_branches,
        "kongwang_palaces": kongwang_palaces,
        "time_stem_visible": visible_time_gan,
        "zhifu": zhifu,
        "zhishi": zhishi,
        "active_jie": current_jie_name,
        "active_jie_started_at": prev_jie.getSolar().toYmdHms(),
        "next_jie": next_jie.getName() if next_jie else None,
        "next_jie_at": next_jie.getSolar().toYmdHms() if next_jie else None,
        "grid_order": GRID_ORDER,
        "palaces": palaces,
        "warnings": warnings,
    }


def build_output(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_input(payload)
    solar, lunar = build_solar_and_lunar(normalized)
    chart = build_chart(normalized, solar, lunar)

    return {
        "normalized_input": {
            "question_type": normalized.question_type,
            "question_goal": normalized.question_goal,
            "calendar_type": normalized.calendar_type,
            "ruleset": str(payload.get("ruleset") or DEFAULT_RULESET),
            "timezone": normalized.timezone,
            "country": normalized.country,
            "city": normalized.city,
            "used_now": normalized.use_now,
            "original_time_input": normalized.original_time_input,
        },
        "calendar": {
            "solar": {
                "ymd_hms": solar.toYmdHms(),
                "timezone": normalized.timezone,
            },
            "lunar": {
                "year": lunar.getYear(),
                "month": abs(lunar.getMonth()),
                "day": lunar.getDay(),
                "month_text": lunar.getMonthInChinese(),
                "day_text": lunar.getDayInChinese(),
                "is_leap_month": lunar.getMonth() < 0,
            },
            "jieqi": {
                "active_jie": chart["active_jie"],
                "active_jie_started_at": chart["active_jie_started_at"],
                "next_jie": chart["next_jie"],
                "next_jie_at": chart["next_jie_at"],
            },
        },
        "ganzhi": {
            "year": lunar.getYearInGanZhiExact(),
            "month": lunar.getMonthInGanZhiExact(),
            "day": lunar.getDayInGanZhiExact(),
            "time": lunar.getTimeInGanZhi(),
            "day_xun_exact": lunar.getDayXunExact(),
            "day_xunkong_exact": lunar.getDayXunKongExact(),
            "time_xun": lunar.getTimeXun(),
            "time_xunkong": lunar.getTimeXunKong(),
        },
        "ruleset": {
            "id": str(payload.get("ruleset") or DEFAULT_RULESET),
            "name": "时家转盘奇门（大陆默认）",
            "timezone_default": DEFAULT_TIMEZONE,
            "dun_type_rule": "冬至到芒种用阳遁，夏至到大雪用阴遁，按当前节令判定。",
            "yuan_rule": "按日干支所在六十甲子序列，每 5 日一元，循环上元/中元/下元。",
            "ju_rule": "按当前节令和三元，从固定定局表取局数。",
            "center_hosting_rule": "中宫相关判断一律寄坤处理。",
        },
        "chart": {
            "dun_type": chart["dun_type"],
            "yuan": chart["yuan"],
            "ju_number": chart["ju_number"],
            "xunshou": chart["xunshou"],
            "hidden_yi": chart["hidden_yi"],
            "kongwang": chart["kongwang"],
            "kongwang_palaces": chart["kongwang_palaces"],
            "time_stem_visible": chart["time_stem_visible"],
            "zhifu": chart["zhifu"],
            "zhishi": chart["zhishi"],
            "grid_order": chart["grid_order"],
            "palaces": chart["palaces"],
        },
        "warnings": chart["warnings"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute a structured qimen dunjia chart payload.")
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


if __name__ == "__main__":
    raise SystemExit(main())
