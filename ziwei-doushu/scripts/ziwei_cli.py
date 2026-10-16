#!/usr/bin/env python3
"""紫微斗数确定性排盘脚本。

所有安星规则逐条对应 references/calculation.md、references/sihua.md、
references/stars.md 中的表与口诀；口径说明见 references/calculation.md
「脚本排盘口径」一节。模型只读脚本输出做解读，不手排。
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from lunar_python import Lunar, LunarYear, Solar

DEFAULT_RULESET = "ziwei-sanhe-v1"

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
# 地支序号即命盘宫位序号：子=0 … 亥=11；序号递增为顺时针（顺行）
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
YIN = 2  # 寅宫

PALACE_NAMES = [
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "交友", "官禄", "田宅", "福德", "父母",
]

# calculation.md §5 定五行局诀取数
STEM_NUMBER = {"甲": 1, "乙": 1, "丙": 2, "丁": 2, "戊": 3, "己": 3, "庚": 4, "辛": 4, "壬": 5, "癸": 5}
BRANCH_NUMBER = {
    "子": 1, "午": 1, "丑": 1, "未": 1,
    "寅": 2, "申": 2, "卯": 2, "酉": 2,
    "辰": 3, "戌": 3, "巳": 3, "亥": 3,
}
JU_BY_REMAINDER = {1: ("木三局", 3), 2: ("金四局", 4), 3: ("水二局", 2), 4: ("火六局", 6), 5: ("土五局", 5)}

# calculation.md §4 起寅首：年干 → 寅宫天干
YIN_STEM_BY_YEAR_STEM = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚", "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}

# calculation.md §7.1 紫微星系：相对紫微逆行的步数
ZIWEI_GROUP_OFFSETS = [("紫微", 0), ("天机", -1), ("太阳", -3), ("武曲", -4), ("天同", -5), ("廉贞", -8)]
# calculation.md §7.3 天府星系：相对天府顺行的步数
TIANFU_GROUP_OFFSETS = [
    ("天府", 0), ("太阴", 1), ("贪狼", 2), ("巨门", 3),
    ("天相", 4), ("天梁", 5), ("七杀", 6), ("破军", 10),
]
MAJOR_STARS = [name for name, _ in ZIWEI_GROUP_OFFSETS] + [name for name, _ in TIANFU_GROUP_OFFSETS]

# calculation.md §8 天魁天钺（丙丁猪鸡位：丁年同丙年，魁亥钺酉）
KUI_YUE = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "辛": ("午", "寅"),
    "壬": ("卯", "巳"), "癸": ("卯", "巳"),
}
# calculation.md §8 禄存
LUCUN = {"甲": "寅", "乙": "卯", "丙": "巳", "戊": "巳", "丁": "午", "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}

# calculation.md §8 火铃起点、天马（按年支三合组）
SANHE_GROUP = {
    "寅": "寅午戌", "午": "寅午戌", "戌": "寅午戌",
    "申": "申子辰", "子": "申子辰", "辰": "申子辰",
    "巳": "巳酉丑", "酉": "巳酉丑", "丑": "巳酉丑",
    "亥": "亥卯未", "卯": "亥卯未", "未": "亥卯未",
}
HUO_START = {"寅午戌": "丑", "申子辰": "寅", "巳酉丑": "卯", "亥卯未": "酉"}
LING_START = {"寅午戌": "卯", "申子辰": "戌", "巳酉丑": "戌", "亥卯未": "戌"}
TIANMA = {"寅午戌": "申", "申子辰": "寅", "巳酉丑": "亥", "亥卯未": "巳"}

# sihua.md 生年四化表：年干 → (化禄, 化权, 化科, 化忌)
SIHUA_TYPES = ["化禄", "化权", "化科", "化忌"]
SIHUA = {
    "甲": ("廉贞", "破军", "武曲", "太阳"),
    "乙": ("天机", "天梁", "紫微", "太阴"),
    "丙": ("天同", "天机", "文昌", "廉贞"),
    "丁": ("太阴", "天同", "天机", "巨门"),
    "戊": ("贪狼", "太阴", "右弼", "天机"),
    "己": ("武曲", "贪狼", "天梁", "文曲"),
    "庚": ("太阳", "武曲", "太阴", "天同"),
    "辛": ("巨门", "太阳", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左辅", "武曲"),
    "癸": ("破军", "巨门", "太阴", "贪狼"),
}

# stars.md 十四主星庙旺利平陷表，列序 子→亥
BRIGHTNESS = {
    "紫微": "旺 落陷 庙 平 得地 得地 庙 落陷 庙 平 得地 得地",
    "天机": "庙 得地 庙 旺 平 落陷 庙 得地 庙 旺 平 落陷",
    "太阳": "落陷 不得地 旺 庙 旺 庙 庙 得地 得地 落陷 落陷 落陷",
    "武曲": "旺 庙 得地 利 庙 平 旺 庙 得地 利 庙 平",
    "天同": "旺 不得地 落陷 平 庙 落陷 落陷 不得地 落陷 平 庙 落陷",
    "廉贞": "庙 平 落陷 落陷 得地 旺 庙 平 落陷 落陷 得地 旺",
    "天府": "旺 得地 庙 得地 庙 旺 庙 得地 庙 得地 庙 旺",
    "太阴": "庙 庙 得地 落陷 落陷 落陷 落陷 不得地 得地 旺 庙 庙",
    "贪狼": "旺 庙 平 庙 落陷 旺 旺 庙 平 庙 落陷 旺",
    "巨门": "旺 不得地 庙 庙 落陷 庙 旺 不得地 庙 庙 落陷 庙",
    "天相": "庙 落陷 得地 庙 旺 利 庙 落陷 得地 庙 旺 利",
    "天梁": "庙 旺 落陷 庙 庙 旺 庙 旺 落陷 庙 庙 旺",
    "七杀": "旺 庙 庙 旺 平 庙 旺 庙 庙 旺 平 庙",
    "破军": "旺 庙 落陷 平 平 旺 旺 庙 落陷 平 平 旺",
}
BRIGHTNESS = {star: row.split() for star, row in BRIGHTNESS.items()}

# calculation.md §11 命主（按命宫地支）、身主（按年支）
MING_ZHU = ["贪狼", "巨门", "禄存", "文曲", "廉贞", "武曲", "破军", "武曲", "廉贞", "文曲", "禄存", "巨门"]
SHEN_ZHU = ["火星", "天相", "天梁", "天同", "文昌", "天机", "火星", "天相", "天梁", "天同", "文昌", "天机"]

# calculation.md §7.4 紫微同宫组合只可能出现的宫位（issue #5：紫杀只在巳亥）
ZIWEI_PAIR_BRANCHES = {
    "天府": {"寅", "申"},
    "贪狼": {"卯", "酉"},
    "天相": {"辰", "戌"},
    "七杀": {"巳", "亥"},
    "破军": {"丑", "未"},
}

LEAP_MONTH_RULES = {
    "current": "闰月整月按本月",
    "next": "闰月整月按下月",
    "split_15": "闰月十五日及以前按本月，十六日起按下月",
}
LATE_ZI_RULES = {
    "next_day": "23:00 起视为次日子时，农历日期按次日计算（calculation.md 默认口径）",
    "same_day": "23:00 起取子时，但农历日期仍按当天（沿用用户既定口径时使用）",
}

GENDER_ALIASES = {"男": "男", "male": "男", "m": "男", "女": "女", "female": "女", "f": "女"}


@dataclass
class BirthInfo:
    calendar_type: str
    solar_date: date  # 民用公历日期（未做子时换日）
    hour: int
    minute: int
    gender: str
    leap_month_rule: str | None
    late_zi_rule: str
    original_input: Any
    warnings: list[str]


def b(name: str) -> int:
    return BRANCHES.index(name)


def wrap(index: int) -> int:
    return index % 12


def parse_datetime_string(value: str) -> dict[str, int]:
    normalized = value.strip().replace("T", " ").replace("/", "-").replace("年", "-").replace("月", "-").replace("日", " ")
    normalized = normalized.replace("时", ":").replace("點", ":").replace("点", ":").replace("分", "").replace("秒", "")
    parts = normalized.split()
    if not parts:
        raise ValueError("birth_time 不能为空")
    date_bits = [int(bit) for bit in parts[0].split("-") if bit]
    if len(date_bits) != 3:
        raise ValueError("日期格式需为 YYYY-MM-DD")
    if len(parts) < 2:
        raise ValueError("缺少出生时间：紫微排盘需要出生时辰，请先向用户确认")
    time_bits = [int(bit) for bit in parts[1].split(":") if bit]
    if not time_bits:
        raise ValueError("出生时间格式需为 HH:MM")
    return {
        "year": date_bits[0],
        "month": date_bits[1],
        "day": date_bits[2],
        "hour": time_bits[0],
        "minute": time_bits[1] if len(time_bits) > 1 else 0,
    }


def lunar_to_solar_date(year: int, month: int, day: int, is_leap: bool) -> date:
    if is_leap and LunarYear.fromYear(year).getLeapMonth() != month:
        raise ValueError(f"农历 {year} 年没有闰{month}月")
    lunar = Lunar.fromYmd(year, -month if is_leap else month, day)
    solar = lunar.getSolar()
    return date(solar.getYear(), solar.getMonth(), solar.getDay())


def normalize_input(payload: dict[str, Any]) -> BirthInfo:
    warnings: list[str] = []
    calendar_type = str(payload.get("calendar_type") or "solar").strip().lower()
    raw_input = payload.get("birth_time")
    if raw_input in (None, ""):
        raise ValueError("缺少 birth_time")

    if isinstance(raw_input, dict):
        if "hour" not in raw_input:
            raise ValueError("缺少出生时间：紫微排盘需要出生时辰，请先向用户确认")
        raw = {
            "year": int(raw_input["year"]),
            "month": int(raw_input["month"]),
            "day": int(raw_input["day"]),
            "hour": int(raw_input["hour"]),
            "minute": int(raw_input.get("minute", 0)),
        }
        is_leap = bool(raw_input.get("is_leap_month", False))
    else:
        raw = parse_datetime_string(str(raw_input))
        is_leap = bool(payload.get("is_leap_month", False))

    if not (0 <= raw["hour"] <= 23 and 0 <= raw["minute"] <= 59):
        raise ValueError("出生时间超出范围，小时应为 0-23，分钟 0-59")

    if calendar_type == "solar":
        solar_date = date(raw["year"], raw["month"], raw["day"])
    elif calendar_type == "lunar":
        solar_date = lunar_to_solar_date(raw["year"], raw["month"], raw["day"], is_leap)
    else:
        raise ValueError(f"不支持的 calendar_type: {calendar_type}（只接受 solar 或 lunar）")

    gender_raw = str(payload.get("gender") or "").strip().lower()
    if gender_raw not in GENDER_ALIASES:
        raise ValueError("缺少或无法识别 gender（男/女）：性别决定大限顺逆，请先向用户确认")

    leap_rule = payload.get("leap_month_rule")
    if leap_rule is not None and leap_rule not in LEAP_MONTH_RULES:
        raise ValueError(f"leap_month_rule 只接受 {sorted(LEAP_MONTH_RULES)}")
    late_zi_rule = payload.get("late_zi_rule") or "next_day"
    if late_zi_rule not in LATE_ZI_RULES:
        raise ValueError(f"late_zi_rule 只接受 {sorted(LATE_ZI_RULES)}")

    minutes = raw["hour"] * 60 + raw["minute"]
    boundary_distance = min((minutes - 60) % 120, 120 - (minutes - 60) % 120)
    if boundary_distance <= 15:
        warnings.append("出生时间距时辰交界不足 15 分钟，时辰有误差时盘面会整体改变，建议按相邻两个时辰各排一盘对照。")

    return BirthInfo(
        calendar_type=calendar_type,
        solar_date=solar_date,
        hour=raw["hour"],
        minute=raw["minute"],
        gender=GENDER_ALIASES[gender_raw],
        leap_month_rule=leap_rule,
        late_zi_rule=late_zi_rule,
        original_input=raw_input,
        warnings=warnings,
    )


def hour_branch_index(hour: int) -> int:
    """calculation.md §1 时辰对照：23:00-00:59 子，01:00-02:59 丑 …"""
    return ((hour + 1) // 2) % 12


def resolve_calendar(info: BirthInfo) -> dict[str, Any]:
    """把民用日期换成排盘用的农历年、月、日与时辰。"""
    hour_idx = hour_branch_index(info.hour)
    chart_date = info.solar_date
    day_rollover = False
    if info.hour == 23 and info.late_zi_rule == "next_day":
        chart_date = info.solar_date + timedelta(days=1)
        day_rollover = True

    lunar = Solar.fromYmd(chart_date.year, chart_date.month, chart_date.day).getLunar()
    lunar_month = abs(lunar.getMonth())
    is_leap = lunar.getMonth() < 0
    lunar_day = lunar.getDay()

    chart_month = lunar_month
    if is_leap:
        rule = info.leap_month_rule
        if rule is None:
            raise ValueError(
                f"出生在农历闰{lunar_month}月{lunar_day}日，闰月归属口径未确认。"
                "请先向用户确认后在 leap_month_rule 中指定："
                + "；".join(f"{key}（{desc}）" for key, desc in LEAP_MONTH_RULES.items())
            )
        if rule == "next" or (rule == "split_15" and lunar_day > 15):
            chart_month = lunar_month % 12 + 1

    year_stem = STEMS[lunar.getYearGanIndex()]
    year_branch = BRANCHES[lunar.getYearZhiIndex()]
    return {
        "chart_solar_date": chart_date,
        "day_rollover": day_rollover,
        "lunar_year": lunar.getYear(),
        "lunar_month": lunar_month,
        "lunar_day": lunar_day,
        "is_leap_month": is_leap,
        "chart_month": chart_month,
        "year_stem": year_stem,
        "year_branch": year_branch,
        "hour_index": hour_idx,
        "lunar_text": f"{lunar.getYearInGanZhi()}年{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}",
    }


def palace_stem(year_stem: str, branch_idx: int) -> str:
    """calculation.md §4 起寅首：寅宫起首干，按寅卯…亥子丑顺排。"""
    start = STEMS.index(YIN_STEM_BY_YEAR_STEM[year_stem])
    return STEMS[(start + wrap(branch_idx - YIN)) % 10]


def wuxing_ju(stem: str, branch: str) -> tuple[str, int]:
    total = STEM_NUMBER[stem] + BRANCH_NUMBER[branch]
    while total > 5:
        total -= 5
    return JU_BY_REMAINDER[total]


def ziwei_position(ju_number: int, lunar_day: int) -> int:
    """安紫微星诀：商数从寅起数，不足数奇逆偶顺（与 calculation.md §6 表一致）。"""
    quotient = math.ceil(lunar_day / ju_number)
    shortfall = quotient * ju_number - lunar_day
    base = wrap(YIN + quotient - 1)
    if shortfall == 0:
        return base
    if shortfall % 2 == 1:
        return wrap(base - shortfall)
    return wrap(base + shortfall)


def tianfu_position(ziwei_idx: int) -> int:
    """calculation.md §7.2 紫微—天府对照表：两星以寅申为轴对称。"""
    return wrap(4 - ziwei_idx)


def place_major_stars(ziwei_idx: int) -> dict[str, int]:
    positions = {name: wrap(ziwei_idx + offset) for name, offset in ZIWEI_GROUP_OFFSETS}
    tianfu_idx = tianfu_position(ziwei_idx)
    positions.update({name: wrap(tianfu_idx + offset) for name, offset in TIANFU_GROUP_OFFSETS})
    return positions


def place_minor_stars(year_stem: str, year_branch: str, chart_month: int, hour_idx: int) -> dict[str, int]:
    """calculation.md §8 甲级辅星。"""
    group = SANHE_GROUP[year_branch]
    kui, yue = KUI_YUE[year_stem]
    lucun = b(LUCUN[year_stem])
    return {
        "文昌": wrap(b("戌") - hour_idx),
        "文曲": wrap(b("辰") + hour_idx),
        "左辅": wrap(b("辰") + chart_month - 1),
        "右弼": wrap(b("戌") - (chart_month - 1)),
        "天魁": b(kui),
        "天钺": b(yue),
        "禄存": lucun,
        "擎羊": wrap(lucun + 1),
        "陀罗": wrap(lucun - 1),
        "火星": wrap(b(HUO_START[group]) + hour_idx),
        "铃星": wrap(b(LING_START[group]) + hour_idx),
        "地空": wrap(b("亥") - hour_idx),
        "地劫": wrap(b("亥") + hour_idx),
        "天马": b(TIANMA[group]),
    }


def place_adjective_stars(year_branch: str, chart_month: int) -> dict[str, int]:
    """calculation.md §9 已给出完整规则的乙级星（孤辰、寡宿文档未给表，暂不安）。"""
    yb = b(year_branch)
    hongluan = wrap(b("卯") - yb)
    return {
        "天刑": wrap(b("酉") + chart_month - 1),
        "天姚": wrap(b("丑") + chart_month - 1),
        "红鸾": hongluan,
        "天喜": wrap(hongluan + 6),
        "天哭": wrap(b("午") - yb),
        "天虚": wrap(b("午") + yb),
    }


def sihua_for_stem(stem: str, star_index: dict[str, int], palace_name_by_branch: dict[int, str]) -> list[dict[str, Any]]:
    result = []
    for kind, star in zip(SIHUA_TYPES, SIHUA[stem]):
        idx = star_index[star]
        result.append({"type": kind, "star": star, "branch": BRANCHES[idx], "palace": palace_name_by_branch[idx]})
    return result


def decadal_direction(year_stem: str, gender: str) -> int:
    """calculation.md §10：阳男阴女顺行，阴男阳女逆行。"""
    is_yang_year = STEMS.index(year_stem) % 2 == 0
    return 1 if is_yang_year == (gender == "男") else -1


def build_chart(info: BirthInfo) -> dict[str, Any]:
    cal = resolve_calendar(info)
    year_stem, year_branch = cal["year_stem"], cal["year_branch"]
    hour_idx, chart_month = cal["hour_index"], cal["chart_month"]

    month_palace = wrap(YIN + chart_month - 1)
    ming_idx = wrap(month_palace - hour_idx)
    shen_idx = wrap(month_palace + hour_idx)

    palace_name_by_branch = {wrap(ming_idx - i): name for i, name in enumerate(PALACE_NAMES)}
    stems_by_branch = {idx: palace_stem(year_stem, idx) for idx in range(12)}
    ju_name, ju_number = wuxing_ju(stems_by_branch[ming_idx], BRANCHES[ming_idx])

    ziwei_idx = ziwei_position(ju_number, cal["lunar_day"])
    major = place_major_stars(ziwei_idx)
    minor = place_minor_stars(year_stem, year_branch, chart_month, hour_idx)
    adjective = place_adjective_stars(year_branch, chart_month)
    star_index = {**major, **minor, **adjective}

    year_sihua = sihua_for_stem(year_stem, star_index, palace_name_by_branch)
    sihua_by_star = {item["star"]: item["type"] for item in year_sihua}

    direction = decadal_direction(year_stem, info.gender)
    decadal_by_branch = {}
    for step in range(12):
        idx = wrap(ming_idx + direction * step)
        decadal_by_branch[idx] = {"start_age": ju_number + 10 * step, "end_age": ju_number + 10 * step + 9}

    palaces = []
    for i, name in enumerate(PALACE_NAMES):
        idx = wrap(ming_idx - i)
        palaces.append({
            "name": name,
            "branch": BRANCHES[idx],
            "stem": stems_by_branch[idx],
            "ganzhi": stems_by_branch[idx] + BRANCHES[idx],
            "is_shen_gong": idx == shen_idx,
            "major_stars": [
                {"name": s, "brightness": BRIGHTNESS[s][idx], "sihua": sihua_by_star.get(s)}
                for s in MAJOR_STARS if major[s] == idx
            ],
            "minor_stars": [
                {"name": s, "sihua": sihua_by_star.get(s)} for s in minor if minor[s] == idx
            ],
            "adjective_stars": [s for s in adjective if adjective[s] == idx],
            "decadal": decadal_by_branch[idx],
        })

    return {
        "calendar": cal,
        "ming_idx": ming_idx,
        "shen_idx": shen_idx,
        "ju_name": ju_name,
        "ju_number": ju_number,
        "star_index": star_index,
        "major": major,
        "year_sihua": year_sihua,
        "direction": direction,
        "palaces": palaces,
        "palace_name_by_branch": palace_name_by_branch,
        "stems_by_branch": stems_by_branch,
        "decadal_by_branch": decadal_by_branch,
    }


def self_check(chart: dict[str, Any]) -> dict[str, Any]:
    major = chart["major"]
    issues = []
    if sorted(major) != sorted(MAJOR_STARS):
        issues.append("十四主星不完整")
    ziwei_branch = BRANCHES[major["紫微"]]
    for partner, allowed in ZIWEI_PAIR_BRANCHES.items():
        if major[partner] == major["紫微"] and ziwei_branch not in allowed:
            issues.append(f"紫微{partner}同宫出现在{ziwei_branch}，违反 calculation.md §7.4")
    for item in chart["year_sihua"]:
        if item["star"] not in chart["star_index"]:
            issues.append(f"四化星 {item['star']} 不在盘上")
    if issues:
        raise AssertionError("；".join(issues))
    return {
        "major_star_count": len(major),
        "ziwei_branch": ziwei_branch,
        "ziwei_partner": next((p for p in ZIWEI_PAIR_BRANCHES if major[p] == major["紫微"]), None),
        "passed": True,
    }


def build_horoscope(chart: dict[str, Any], query_year: int) -> dict[str, Any]:
    """大限四化（大限宫干）与流年命宫、流年四化（流年天干），见 sihua.md「运限四化」。"""
    cal = chart["calendar"]
    nominal_age = query_year - cal["lunar_year"] + 1
    names = chart["palace_name_by_branch"]
    year_stem = STEMS[(query_year - 4) % 10]
    year_branch_idx = (query_year - 4) % 12
    result: dict[str, Any] = {
        "query_lunar_year": query_year,
        "nominal_age": nominal_age,
        "yearly": {
            "ganzhi": year_stem + BRANCHES[year_branch_idx],
            "ming_branch": BRANCHES[year_branch_idx],
            "ming_on_natal_palace": names[year_branch_idx],
            "palaces": [
                {"name": PALACE_NAMES[i], "branch": BRANCHES[wrap(year_branch_idx - i)],
                 "natal_palace": names[wrap(year_branch_idx - i)]}
                for i in range(12)
            ],
            "sihua": sihua_for_stem(year_stem, chart["star_index"], names),
        },
        "decadal": None,
    }
    for idx, span in chart["decadal_by_branch"].items():
        if span["start_age"] <= nominal_age <= span["end_age"]:
            stem = chart["stems_by_branch"][idx]
            result["decadal"] = {
                "branch": BRANCHES[idx],
                "ganzhi": stem + BRANCHES[idx],
                "natal_palace": names[idx],
                "start_age": span["start_age"],
                "end_age": span["end_age"],
                "sihua": sihua_for_stem(stem, chart["star_index"], names),
            }
    return result


def build_output(payload: dict[str, Any]) -> dict[str, Any]:
    info = normalize_input(payload)
    chart = build_chart(info)
    cal = chart["calendar"]
    check = self_check(chart)
    warnings = list(info.warnings)
    if cal["day_rollover"]:
        warnings.append("出生于 23 点后，已按次日子时排盘（农历日期取次日）；若用户既定口径不换日，请改用 late_zi_rule=same_day 重排。")
    if cal["is_leap_month"]:
        warnings.append(f"出生于闰月，按 {LEAP_MONTH_RULES[info.leap_month_rule]} 定月。")

    ming_idx, shen_idx = chart["ming_idx"], chart["shen_idx"]
    output: dict[str, Any] = {
        "normalized_input": {
            "calendar_type": info.calendar_type,
            "original_birth_time": info.original_input,
            "civil_solar_datetime": f"{info.solar_date.isoformat()} {info.hour:02d}:{info.minute:02d}",
            "gender": info.gender,
            "leap_month_rule": info.leap_month_rule,
            "late_zi_rule": info.late_zi_rule,
        },
        "calendar": {
            "chart_solar_date": cal["chart_solar_date"].isoformat(),
            "day_rollover_applied": cal["day_rollover"],
            "lunar_year": cal["lunar_year"],
            "lunar_month": cal["lunar_month"],
            "lunar_day": cal["lunar_day"],
            "is_leap_month": cal["is_leap_month"],
            "chart_month": cal["chart_month"],
            "lunar_text": cal["lunar_text"],
            "year_ganzhi": cal["year_stem"] + cal["year_branch"],
            "year_yinyang": "阳" if STEMS.index(cal["year_stem"]) % 2 == 0 else "阴",
            "hour_branch": BRANCHES[cal["hour_index"]] + "时",
        },
        "ruleset": {
            "id": str(payload.get("ruleset") or DEFAULT_RULESET),
            "source": "references/calculation.md、references/sihua.md、references/stars.md",
            "year_rule": "以农历正月初一换年，年干支取农历年。",
            "late_zi_rule": LATE_ZI_RULES[info.late_zi_rule],
            "leap_month_rule": LEAP_MONTH_RULES.get(info.leap_month_rule or "", "非闰月出生，不涉及"),
            "age_rule": "大限年龄为虚岁。",
        },
        "chart": {
            "ming_gong": {"branch": BRANCHES[ming_idx], "ganzhi": chart["stems_by_branch"][ming_idx] + BRANCHES[ming_idx]},
            "shen_gong": {"branch": BRANCHES[shen_idx], "palace": chart["palace_name_by_branch"][shen_idx]},
            "wuxing_ju": {"name": chart["ju_name"], "number": chart["ju_number"]},
            "ming_zhu": MING_ZHU[ming_idx],
            "shen_zhu": SHEN_ZHU[b(cal["year_branch"])],
            "decadal_direction": "顺行" if chart["direction"] == 1 else "逆行",
            "year_sihua": chart["year_sihua"],
            "star_index": {name: BRANCHES[idx] for name, idx in chart["star_index"].items()},
            "palaces": chart["palaces"],
            "self_check": check,
        },
        "warnings": warnings,
    }
    query_year = payload.get("query_year")
    if query_year not in (None, ""):
        output["horoscope"] = build_horoscope(chart, int(query_year))
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute a structured ziwei doushu chart payload.")
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
