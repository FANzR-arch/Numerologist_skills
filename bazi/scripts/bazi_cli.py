#!/usr/bin/env python3
"""四柱八字确定性排盘脚本。

历法、四柱、藏干、十神、大运由 lunar_python 计算；口径见输出的 ruleset 字段，
藏干与十神规则对应 references/tiangan-dizhi.md。模型只读脚本输出做解读，不手排。
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from lunar_python import Lunar, LunarYear, Solar

DEFAULT_RULESET = "bazi-ziping-v1"
STEMS = "甲乙丙丁戊己庚辛壬癸"
STEM_WUXING = "木木火火土土金金水水"

# lunar_python EightChar 的 sect：1 = 23:00 起日柱取次日；2 = 夜子时，日柱仍取当日
LATE_ZI_RULES = {
    "next_day": (1, "23:00 起换日，日柱取次日（早晚子不分），与紫微斗数、奇门遁甲脚本一致"),
    "same_day": (2, "夜子时：23:00-00:00 日柱仍取当日，时柱按次日日干起子时（沿用用户既定口径时使用）"),
}
GENDER_ALIASES = {"男": "男", "male": "男", "m": "男", "女": "女", "female": "女", "f": "女"}
JIE_WARNING_HOURS = 24
PILLAR_KEYS = ("year", "month", "day", "time")


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
        raise ValueError("缺少出生时间：八字时柱需要出生时辰，请先向用户确认")
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


def normalize_input(payload: dict[str, Any]) -> dict[str, Any]:
    calendar_type = str(payload.get("calendar_type") or "solar").strip().lower()
    raw_input = payload.get("birth_time")
    if raw_input in (None, ""):
        raise ValueError("缺少 birth_time")

    if isinstance(raw_input, dict):
        if "hour" not in raw_input:
            raise ValueError("缺少出生时间：八字时柱需要出生时辰，请先向用户确认")
        raw = {key: int(raw_input.get(key, 0)) for key in ("year", "month", "day", "hour", "minute")}
        is_leap = bool(raw_input.get("is_leap_month", False))
    else:
        raw = parse_datetime_string(str(raw_input))
        is_leap = bool(payload.get("is_leap_month", False))

    if not (0 <= raw["hour"] <= 23 and 0 <= raw["minute"] <= 59):
        raise ValueError("出生时间超出范围，小时应为 0-23，分钟 0-59")

    if calendar_type == "solar":
        solar = Solar.fromYmdHms(raw["year"], raw["month"], raw["day"], raw["hour"], raw["minute"], 0)
    elif calendar_type == "lunar":
        if is_leap and LunarYear.fromYear(raw["year"]).getLeapMonth() != raw["month"]:
            raise ValueError(f"农历 {raw['year']} 年没有闰{raw['month']}月")
        month = -raw["month"] if is_leap else raw["month"]
        solar = Lunar.fromYmdHms(raw["year"], month, raw["day"], raw["hour"], raw["minute"], 0).getSolar()
    else:
        raise ValueError(f"不支持的 calendar_type: {calendar_type}（只接受 solar 或 lunar）")

    gender_raw = str(payload.get("gender") or "").strip().lower()
    if gender_raw not in GENDER_ALIASES:
        raise ValueError("缺少或无法识别 gender（男/女）：性别决定大运顺逆，请先向用户确认")

    late_zi_rule = payload.get("late_zi_rule") or "next_day"
    if late_zi_rule not in LATE_ZI_RULES:
        raise ValueError(f"late_zi_rule 只接受 {sorted(LATE_ZI_RULES)}")

    return {
        "calendar_type": calendar_type,
        "original_birth_time": raw_input,
        "solar": solar,
        "gender": GENDER_ALIASES[gender_raw],
        "late_zi_rule": late_zi_rule,
    }


def to_datetime(solar: Solar) -> datetime:
    return datetime(solar.getYear(), solar.getMonth(), solar.getDay(), solar.getHour(), solar.getMinute(), solar.getSecond())


def build_pillar(eight_char: Any, key: str) -> dict[str, Any]:
    prefix = key.capitalize()

    def get(name: str) -> Any:
        return getattr(eight_char, f"get{prefix}{name}")()

    gan = get("Gan")
    wuxing = get("WuXing")
    hide_gan = get("HideGan")
    return {
        "ganzhi": getattr(eight_char, f"get{prefix}")(),
        "gan": gan,
        "zhi": get("Zhi"),
        "gan_wuxing": wuxing[0],
        "zhi_wuxing": wuxing[1],
        "gan_yinyang": "阳" if STEMS.index(gan) % 2 == 0 else "阴",
        "shishen_gan": get("ShiShenGan"),
        "hide_gan": [{"gan": g, "shishen": s} for g, s in zip(hide_gan, get("ShiShenZhi"))],
        "nayin": get("NaYin"),
        "dishi": get("DiShi"),
        "xun": get("Xun"),
        "xunkong": get("XunKong"),
    }


def build_output(payload: dict[str, Any]) -> dict[str, Any]:
    info = normalize_input(payload)
    solar = info["solar"]
    birth = to_datetime(solar)
    lunar = solar.getLunar()
    sect, late_zi_text = LATE_ZI_RULES[info["late_zi_rule"]]
    eight_char = lunar.getEightChar()
    eight_char.setSect(sect)
    pillars = {key: build_pillar(eight_char, key) for key in PILLAR_KEYS}

    warnings: list[str] = []
    minutes = birth.hour * 60 + birth.minute
    boundary_distance = min((minutes - 60) % 120, 120 - (minutes - 60) % 120)
    if boundary_distance <= 15:
        warnings.append("出生时间距时辰交界不足 15 分钟，时辰有误差时时柱会改变，建议按相邻两个时辰各排一盘对照。")
    day_rollover = birth.hour == 23 and info["late_zi_rule"] == "next_day"
    if day_rollover:
        warnings.append("出生于 23 点后，已按次日排日柱；若用户既定口径为夜子时，请改用 late_zi_rule=same_day 重排。")
    if lunar.getYearGanIndexExact() != (birth.year - 4) % 10:
        warnings.append(f"出生于 {birth.year} 年立春前，年柱属上一年；大运与流年的虚岁按公历年计，比按立春/农历年算的虚岁少 1 岁，向用户报年龄时请说明。")

    prev_jie, next_jie = lunar.getPrevJie(), lunar.getNextJie()
    jie_info = {}
    for label, jie in (("prev_jie", prev_jie), ("next_jie", next_jie)):
        jie_time = to_datetime(jie.getSolar())
        jie_info[label] = {"name": jie.getName(), "time": jie_time.isoformat(sep=" ")}
        hours = abs((jie_time - birth).total_seconds()) / 3600
        if hours < JIE_WARNING_HOURS:
            pillar = "年柱与月柱" if jie.getName() == "立春" else "月柱"
            warnings.append(f"出生时间距节气 {jie.getName()}（{jie_time:%Y-%m-%d %H:%M}）仅 {hours:.1f} 小时，出生时间有误差时{pillar}可能改变，请向用户确认准确时间。")

    yun = eight_char.getYun(1 if info["gender"] == "男" else 0, 1)
    periods = []
    for da_yun in yun.getDaYun():
        periods.append({
            "index": da_yun.getIndex(),
            # 交运前以月柱干支为大运（references/prompt-template.md 排运规则）
            "ganzhi": da_yun.getGanZhi() or pillars["month"]["ganzhi"],
            "start_age": da_yun.getStartAge(),
            "end_age": da_yun.getEndAge(),
            "start_year": da_yun.getStartYear(),
            "end_year": da_yun.getEndYear(),
        })

    output: dict[str, Any] = {
        "normalized_input": {
            "calendar_type": info["calendar_type"],
            "original_birth_time": info["original_birth_time"],
            "civil_solar_datetime": birth.isoformat(sep=" ", timespec="minutes"),
            "gender": info["gender"],
            "late_zi_rule": info["late_zi_rule"],
        },
        "ruleset": {
            "id": str(payload.get("ruleset") or DEFAULT_RULESET),
            "source": "references/tiangan-dizhi.md；历法与四柱由 lunar_python 计算",
            "year_rule": "以立春交节时刻换年。",
            "month_rule": "以十二节交节时刻换月，月干按年上起月法。",
            "late_zi_rule": late_zi_text,
            "yun_rule": "阳年男、阴年女顺排，阴年男、阳年女逆排；起运岁数 = 出生至下一个（顺）或上一个（逆）节的天数 ÷ 3（3 天 1 年、1 天 4 个月、1 个时辰 10 天）。",
            "age_rule": "虚岁 = 公历年 − 出生公历年 + 1（lunar_python 口径，立春前出生者比农历虚岁少 1）；交运前以月柱为大运；流年 query_year 为公历年，流年干支取该年立春后的干支。",
            "time_rule": "按输入的民用时间排盘，未做真太阳时校正。",
        },
        "calendar": {
            "lunar_text": f"{lunar.getYearInGanZhi()}年{lunar.getMonthInChinese()}月{lunar.getDayInChinese()} {lunar.getTimeZhi()}时",
            "day_rollover_applied": day_rollover,
            **jie_info,
        },
        "day_master": {
            "gan": pillars["day"]["gan"],
            "wuxing": STEM_WUXING[STEMS.index(pillars["day"]["gan"])],
            "yinyang": pillars["day"]["gan_yinyang"],
        },
        "pillars": pillars,
        "dayun": {
            "direction": "顺排" if yun.isForward() else "逆排",
            "start": {
                "years": yun.getStartYear(),
                "months": yun.getStartMonth(),
                "days": yun.getStartDay(),
                "hours": yun.getStartHour(),
                "solar_date": yun.getStartSolar().toYmd(),
            },
            "periods": periods,
        },
        "warnings": warnings,
    }

    query_year = payload.get("query_year")
    if query_year not in (None, ""):
        query_year = int(query_year)
        da_yun = next((d for d in yun.getDaYun() if d.getStartYear() <= query_year <= d.getEndYear()), None)
        if da_yun is None:
            raise ValueError(f"query_year {query_year} 不在大运范围 {periods[0]['start_year']}-{periods[-1]['end_year']} 内")
        liu_nian = next(n for n in da_yun.getLiuNian() if n.getYear() == query_year)
        output["liunian"] = {
            "year": query_year,
            "ganzhi": liu_nian.getGanZhi(),
            "age": liu_nian.getAge(),
            "dayun_ganzhi": da_yun.getGanZhi() or pillars["month"]["ganzhi"],
        }
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute a structured bazi chart payload.")
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
