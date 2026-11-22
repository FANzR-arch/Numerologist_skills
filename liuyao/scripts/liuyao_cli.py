#!/usr/bin/env python3
"""六爻纳甲筮法确定性排卦脚本。

本卦、变卦、京房八宫世应、纳甲、六亲、六神、伏神、月建日辰、旬空月破由脚本计算；
模型只负责访谈（问事、取用神）与解读，不手排。
"""
from __future__ import annotations

import secrets
from datetime import datetime
from typing import Any

from lunar_python import Solar

from calendar_core import get_zone, parse_datetime_string, payload_timezone, run_cli

DEFAULT_RULESET = "liuyao-najia-v1"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
BRANCH_ELEMENT = dict(zip(BRANCHES, "水土木木土火火土金金土水"))
# 卦线自下而上，1 为阳
TRIGRAMS = {
    "乾": {"bits": "111", "element": "金", "image": "天", "vi": "Thiên"},
    "兑": {"bits": "110", "element": "金", "image": "泽", "vi": "Trạch"},
    "离": {"bits": "101", "element": "火", "image": "火", "vi": "Hỏa"},
    "震": {"bits": "100", "element": "木", "image": "雷", "vi": "Lôi"},
    "巽": {"bits": "011", "element": "木", "image": "风", "vi": "Phong"},
    "坎": {"bits": "010", "element": "水", "image": "水", "vi": "Thủy"},
    "艮": {"bits": "001", "element": "土", "image": "山", "vi": "Sơn"},
    "坤": {"bits": "000", "element": "土", "image": "地", "vi": "Địa"},
}
TRIGRAM_BY_BITS = {t["bits"]: name for name, t in TRIGRAMS.items()}
# 京房纳甲：内卦三爻、外卦三爻（自下而上）
NAJIA = {
    "乾": ("甲子 甲寅 甲辰", "壬午 壬申 壬戌"),
    "坤": ("乙未 乙巳 乙卯", "癸丑 癸亥 癸酉"),
    "震": ("庚子 庚寅 庚辰", "庚午 庚申 庚戌"),
    "巽": ("辛丑 辛亥 辛酉", "辛未 辛巳 辛卯"),
    "坎": ("戊寅 戊辰 戊午", "戊申 戊戌 戊子"),
    "离": ("己卯 己丑 己亥", "己酉 己未 己巳"),
    "艮": ("丙辰 丙午 丙申", "丙戌 丙子 丙寅"),
    "兑": ("丁巳 丁卯 丁丑", "丁亥 丁酉 丁未"),
}
# 文王卦序：(上卦, 下卦, 卦名, 越南语卦名)
KING_WEN = [
    ("乾", "乾", "乾为天", "Thuần Càn"), ("坤", "坤", "坤为地", "Thuần Khôn"),
    ("坎", "震", "水雷屯", "Thủy Lôi Truân"), ("艮", "坎", "山水蒙", "Sơn Thủy Mông"),
    ("坎", "乾", "水天需", "Thủy Thiên Nhu"), ("乾", "坎", "天水讼", "Thiên Thủy Tụng"),
    ("坤", "坎", "地水师", "Địa Thủy Sư"), ("坎", "坤", "水地比", "Thủy Địa Tỷ"),
    ("巽", "乾", "风天小畜", "Phong Thiên Tiểu Súc"), ("乾", "兑", "天泽履", "Thiên Trạch Lý"),
    ("坤", "乾", "地天泰", "Địa Thiên Thái"), ("乾", "坤", "天地否", "Thiên Địa Bĩ"),
    ("乾", "离", "天火同人", "Thiên Hỏa Đồng Nhân"), ("离", "乾", "火天大有", "Hỏa Thiên Đại Hữu"),
    ("坤", "艮", "地山谦", "Địa Sơn Khiêm"), ("震", "坤", "雷地豫", "Lôi Địa Dự"),
    ("兑", "震", "泽雷随", "Trạch Lôi Tùy"), ("艮", "巽", "山风蛊", "Sơn Phong Cổ"),
    ("坤", "兑", "地泽临", "Địa Trạch Lâm"), ("巽", "坤", "风地观", "Phong Địa Quan"),
    ("离", "震", "火雷噬嗑", "Hỏa Lôi Phệ Hạp"), ("艮", "离", "山火贲", "Sơn Hỏa Bí"),
    ("艮", "坤", "山地剥", "Sơn Địa Bác"), ("坤", "震", "地雷复", "Địa Lôi Phục"),
    ("乾", "震", "天雷无妄", "Thiên Lôi Vô Vọng"), ("艮", "乾", "山天大畜", "Sơn Thiên Đại Súc"),
    ("艮", "震", "山雷颐", "Sơn Lôi Di"), ("兑", "巽", "泽风大过", "Trạch Phong Đại Quá"),
    ("坎", "坎", "坎为水", "Thuần Khảm"), ("离", "离", "离为火", "Thuần Ly"),
    ("兑", "艮", "泽山咸", "Trạch Sơn Hàm"), ("震", "巽", "雷风恒", "Lôi Phong Hằng"),
    ("乾", "艮", "天山遁", "Thiên Sơn Độn"), ("震", "乾", "雷天大壮", "Lôi Thiên Đại Tráng"),
    ("离", "坤", "火地晋", "Hỏa Địa Tấn"), ("坤", "离", "地火明夷", "Địa Hỏa Minh Di"),
    ("巽", "离", "风火家人", "Phong Hỏa Gia Nhân"), ("离", "兑", "火泽睽", "Hỏa Trạch Khuê"),
    ("坎", "艮", "水山蹇", "Thủy Sơn Kiển"), ("震", "坎", "雷水解", "Lôi Thủy Giải"),
    ("艮", "兑", "山泽损", "Sơn Trạch Tổn"), ("巽", "震", "风雷益", "Phong Lôi Ích"),
    ("兑", "乾", "泽天夬", "Trạch Thiên Quải"), ("乾", "巽", "天风姤", "Thiên Phong Cấu"),
    ("兑", "坤", "泽地萃", "Trạch Địa Tụy"), ("坤", "巽", "地风升", "Địa Phong Thăng"),
    ("兑", "坎", "泽水困", "Trạch Thủy Khốn"), ("坎", "巽", "水风井", "Thủy Phong Tỉnh"),
    ("兑", "离", "泽火革", "Trạch Hỏa Cách"), ("离", "巽", "火风鼎", "Hỏa Phong Đỉnh"),
    ("震", "震", "震为雷", "Thuần Chấn"), ("艮", "艮", "艮为山", "Thuần Cấn"),
    ("巽", "艮", "风山渐", "Phong Sơn Tiệm"), ("震", "兑", "雷泽归妹", "Lôi Trạch Quy Muội"),
    ("震", "离", "雷火丰", "Lôi Hỏa Phong"), ("离", "艮", "火山旅", "Hỏa Sơn Lữ"),
    ("巽", "巽", "巽为风", "Thuần Tốn"), ("兑", "兑", "兑为泽", "Thuần Đoài"),
    ("巽", "坎", "风水涣", "Phong Thủy Hoán"), ("坎", "兑", "水泽节", "Thủy Trạch Tiết"),
    ("巽", "兑", "风泽中孚", "Phong Trạch Trung Phu"), ("震", "艮", "雷山小过", "Lôi Sơn Tiểu Quá"),
    ("坎", "离", "水火既济", "Thủy Hỏa Ký Tế"), ("离", "坎", "火水未济", "Hỏa Thủy Vị Tế"),
]
# 京房八宫：相对本宫纯卦翻转的爻位 → (世代, 世爻)
GENERATIONS = [
    ((), "本宫", 6), ((1,), "一世", 1), ((1, 2), "二世", 2), ((1, 2, 3), "三世", 3),
    ((1, 2, 3, 4), "四世", 4), ((1, 2, 3, 4, 5), "五世", 5), ((1, 2, 3, 5), "游魂", 4), ((5,), "归魂", 3),
]
LIUSHEN = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
LIUSHEN_START = {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 3, "庚": 4, "辛": 4, "壬": 5, "癸": 5}
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
LIUQIN_ORDER = ["父母", "兄弟", "子孙", "妻财", "官鬼"]


def _build_hexagrams() -> dict[str, dict[str, Any]]:
    names = {upper + lower: (i + 1, name, vi) for i, (upper, lower, name, vi) in enumerate(KING_WEN)}
    table: dict[str, dict[str, Any]] = {}
    for palace, trigram in TRIGRAMS.items():
        pure = trigram["bits"] * 2
        for flips, generation, shi in GENERATIONS:
            bits = "".join(str(1 - int(b)) if i + 1 in flips else b for i, b in enumerate(pure))
            lower, upper = TRIGRAM_BY_BITS[bits[:3]], TRIGRAM_BY_BITS[bits[3:]]
            number, name, vi = names[upper + lower]
            table[bits] = {
                "name": name, "name_vi": vi, "number": number, "upper": upper, "lower": lower,
                "palace": palace, "palace_element": trigram["element"], "generation": generation,
                "shi": shi, "ying": (shi + 2) % 6 + 1,
            }
    return table


HEXAGRAMS = _build_hexagrams()


def liuqin(palace_element: str, element: str) -> str:
    if element == palace_element:
        return "兄弟"
    if GENERATES[palace_element] == element:
        return "子孙"
    if GENERATES[element] == palace_element:
        return "父母"
    if CONTROLS[palace_element] == element:
        return "妻财"
    return "官鬼"


def najia(bits: str) -> list[str]:
    lower, upper = TRIGRAM_BY_BITS[bits[:3]], TRIGRAM_BY_BITS[bits[3:]]
    return NAJIA[lower][0].split() + NAJIA[upper][1].split()


def toss() -> tuple[int, list[int]]:
    """三枚铜钱：字为 3、背为 2，合计 6 老阴、7 少阳、8 少阴、9 老阳。"""
    coins = [secrets.choice((2, 3)) for _ in range(3)]
    return sum(coins), coins


def resolve_time(payload: dict[str, Any]) -> datetime:
    raw = payload.get("time")
    if raw in (None, ""):
        raise ValueError("缺少 time：起卦时间（如 2026-11-22 10:00），或填 now 取当前时间")
    if str(raw).strip().lower() == "now":
        return datetime.now(get_zone(payload_timezone(payload))).replace(tzinfo=None, microsecond=0)
    parsed = parse_datetime_string(str(raw), "起卦时间需要具体时刻（时辰影响日辰换日）")
    return datetime(parsed["year"], parsed["month"], parsed["day"], parsed["hour"], parsed["minute"], parsed["second"])


def build_output(payload: dict[str, Any]) -> dict[str, Any]:
    coins = None
    cast = payload.get("cast", False)
    if not isinstance(cast, bool):
        raise ValueError("cast 只接受 true 或 false")
    if cast:
        if payload.get("lines"):
            raise ValueError("lines 与 cast 只能二选一：用户自己摇卦传 lines，请脚本代摇传 cast=true")
        tossed = [toss() for _ in range(6)]
        values, coins = [v for v, _ in tossed], [c for _, c in tossed]
    else:
        values = payload.get("lines")
        if not values:
            raise ValueError("缺少 lines：自下而上六个爻值（6 老阴、7 少阳、8 少阴、9 老阳），或传 cast=true 由脚本摇卦")
        if not isinstance(values, list) or len(values) != 6:
            raise ValueError("lines 需为 6 个爻值，自下而上")
        if any(type(v) is not int or v not in (6, 7, 8, 9) for v in values):
            raise ValueError("lines 的每个爻值只能是 6、7、8、9")

    moment = resolve_time(payload)
    late_zi_rule = payload.get("late_zi_rule") or "next_day"
    if late_zi_rule not in ("next_day", "same_day"):
        raise ValueError("late_zi_rule 只接受 next_day 或 same_day")
    lunar = Solar.fromYmdHms(moment.year, moment.month, moment.day, moment.hour, moment.minute, moment.second).getLunar()
    day_gz = lunar.getDayInGanZhiExact() if late_zi_rule == "next_day" else lunar.getDayInGanZhiExact2()
    month_gz = lunar.getMonthInGanZhiExact()
    xunkong = lunar.getDayXunKongExact() if late_zi_rule == "next_day" else lunar.getDayXunKongExact2()

    bits = "".join("1" if v in (7, 9) else "0" for v in values)
    changed_bits = "".join(str(1 - int(b)) if v in (6, 9) else b for b, v in zip(bits, values))
    moving = bits != changed_bits
    hexagram = HEXAGRAMS[bits]
    palace_element = hexagram["palace_element"]
    ganzhi = najia(bits)
    changed_ganzhi = najia(changed_bits)
    pure_ganzhi = najia(TRIGRAMS[hexagram["palace"]]["bits"] * 2)
    present = {liuqin(palace_element, BRANCH_ELEMENT[gz[1]]) for gz in ganzhi}
    missing = [q for q in LIUQIN_ORDER if q not in present]
    clash = {b: BRANCHES[(i + 6) % 12] for i, b in enumerate(BRANCHES)}
    shen_start = LIUSHEN_START[day_gz[0]]

    lines = []
    for i, (value, gz) in enumerate(zip(values, ganzhi)):
        position = i + 1
        element = BRANCH_ELEMENT[gz[1]]
        is_moving = value in (6, 9)
        pure = pure_ganzhi[i]
        pure_liuqin = liuqin(palace_element, BRANCH_ELEMENT[pure[1]])
        lines.append({
            "position": position,
            "value": value,
            "yin_yang": "阳" if value in (7, 9) else "阴",
            "moving": is_moving,
            "ganzhi": gz,
            "element": element,
            "liuqin": liuqin(palace_element, element),
            "liushen": LIUSHEN[(shen_start + i) % 6],
            "role": "世" if position == hexagram["shi"] else "应" if position == hexagram["ying"] else None,
            "xunkong": gz[1] in xunkong,
            "month_break": clash[gz[1]] == month_gz[1],
            "day_clash": clash[gz[1]] == day_gz[1],
            "changed": {
                "ganzhi": changed_ganzhi[i],
                "liuqin": liuqin(palace_element, BRANCH_ELEMENT[changed_ganzhi[i][1]]),
                "element": BRANCH_ELEMENT[changed_ganzhi[i][1]],
            } if is_moving else None,
            "fushen": {"ganzhi": pure, "liuqin": pure_liuqin, "element": BRANCH_ELEMENT[pure[1]]} if pure_liuqin in missing else None,
        })

    return {
        "normalized_input": {
            "question": payload.get("question"),
            "lines": values,
            "cast_by_script": coins is not None,
            "coins": coins,
            "time": moment.isoformat(sep=" "),
            "late_zi_rule": late_zi_rule,
        },
        "ruleset": {
            "id": str(payload.get("ruleset") or DEFAULT_RULESET),
            "system": "京房八宫纳甲筮法：世应按八宫世代，六亲按本卦宫五行，六神按日干起，伏神取本宫纯卦同位爻。",
            "lines_rule": "爻值自下而上：6 老阴（动）、7 少阳、8 少阴、9 老阳（动）；动爻变出变卦，变爻六亲仍按本卦宫。",
            "calendar_rule": "月建按节气换月，日辰按起卦时刻；23:00 起" + ("换日（与其他 skill 一致）。" if late_zi_rule == "next_day" else "不换日（夜子时）。"),
            "time_rule": "按输入的钟表时间，不做真太阳时校正。",
        },
        "calendar": {
            "datetime": moment.isoformat(sep=" "),
            "month_ganzhi": month_gz,
            "day_ganzhi": day_gz,
            "day_xunkong": xunkong,
        },
        "hexagram": hexagram,
        "changed": HEXAGRAMS[changed_bits] if moving else None,
        "lines": lines,
        "missing_liuqin": missing,
        "warnings": [] if moving else ["静卦：无动爻，以世应、用神旺衰与日月作用为主断。"],
    }


def main() -> int:
    return run_cli(build_output, "Compute a structured liuyao (najia) hexagram payload.")


if __name__ == "__main__":
    raise SystemExit(main())
