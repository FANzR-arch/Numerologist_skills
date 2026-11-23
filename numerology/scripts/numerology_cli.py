#!/usr/bin/env python3
"""Thần số học (Pythagoras) 确定性计算脚本。

所有口径争议点都是参数，并写进输出的 ruleset；模型只读输出做解读，不手算。
"""
from __future__ import annotations

import unicodedata
from datetime import date
from typing import Any

from calendar_core import parse_datetime_string, run_cli

DEFAULT_RULESET = "pythagoras-v1"
MASTERS = (11, 22, 33)
LETTER_VALUES = {c: (i % 9) + 1 for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
VOWELS = set("AEIOU")
# 生日盘 3×3，自上而下：3 6 9 / 2 5 8 / 1 4 7
GRID = [[3, 6, 9], [2, 5, 8], [1, 4, 7]]
ARROWS = [(1, 2, 3), (4, 5, 6), (7, 8, 9), (1, 4, 7), (2, 5, 8), (3, 6, 9), (1, 5, 9), (3, 5, 7)]
LIFE_PATH_RULES = {
    "vn": "Rút gọn đến 2–11, giữ 22 và 33 (cách phổ biến ở Việt Nam: không có số chủ đạo 1, thay bằng 10).",
    "classic": "Rút gọn đến 1–9, giữ số master 11, 22, 33 (cách phương Tây).",
    "phillips": "Theo D. A. Phillips: rút gọn đến 2–11 hoặc 22/4; không có 1, thay bằng 10; 33 không phải số master, thành 6.",
}
LIFE_PATH_METHODS = {
    "digits": "Cộng tất cả chữ số của ngày, tháng, năm sinh rồi rút gọn.",
    "components": "Rút gọn riêng ngày, tháng, năm (giữ 11/22/33) rồi cộng lại và rút gọn.",
}


def digit_sum(n: int) -> int:
    return sum(int(c) for c in str(n))


def reduce_number(n: int, keep_masters: bool = True) -> int:
    while n > 9 and not (keep_masters and n in MASTERS):
        n = digit_sum(n)
    return n


def reduce_life_path(n: int, rule: str) -> int:
    if rule == "classic":
        return reduce_number(n)
    while n > 11 and n not in ((22,) if rule == "phillips" else (22, 33)):
        n = digit_sum(n)
    return n


def number(value: int) -> dict[str, Any]:
    """value 与展示形式：11/2、22/4、33/6、10/1。"""
    reduced = reduce_number(value, keep_masters=False)
    return {"value": value, "display": str(value) if value == reduced else f"{value}/{reduced}"}


def normalize_name(name: str) -> str:
    """去越南语声调与变音符号（Đ→D），只留拉丁字母与空格。"""
    text = unicodedata.normalize("NFD", name.replace("Đ", "D").replace("đ", "d"))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").upper()
    if any((c.isalpha() and c not in LETTER_VALUES) or c.isdigit() for c in text):
        raise ValueError("full_name chỉ nhận chữ cái Latin (kể cả chữ tiếng Việt có dấu), không nhận chữ số; tên chữ Hán hãy đổi sang cách viết tiếng Việt hoặc Latin")
    return " ".join("".join(c for c in word if c in LETTER_VALUES) for word in text.split()).strip()


def name_numbers(name: str, y_as_vowel: bool) -> dict[str, Any]:
    vowels = VOWELS | ({"Y"} if y_as_vowel else set())
    letters = [c for c in name if c in LETTER_VALUES]
    soul = sum(LETTER_VALUES[c] for c in letters if c in vowels)
    personality = sum(LETTER_VALUES[c] for c in letters if c not in vowels)
    return {
        "expression": {**number(reduce_number(soul + personality)), "raw_sum": soul + personality},
        "soul_urge": {**number(reduce_number(soul)), "raw_sum": soul},
        "personality": {**number(reduce_number(personality)), "raw_sum": personality},
        "letters": [{"letter": c, "value": LETTER_VALUES[c], "vowel": c in vowels} for c in letters],
    }


def birth_chart(birth: date) -> dict[str, Any]:
    digits = [int(c) for c in birth.strftime("%d%m%Y") if c != "0"]
    counts = {str(d): digits.count(d) for d in range(1, 10)}
    arrows = []
    for arrow in ARROWS:
        present = sum(1 for d in arrow if counts[str(d)])
        arrows.append({"digits": list(arrow), "status": "full" if present == 3 else "empty" if present == 0 else "partial"})
    return {
        "grid": GRID,
        "counts": counts,
        "missing": [d for d in range(1, 10) if not counts[str(d)]],
        "arrows": arrows,
    }


def pinnacles_and_challenges(birth: date, life_path: int, rule: str) -> tuple[list[dict[str, Any]], list[int]]:
    month, day, year = (reduce_number(digit_sum(v), keep_masters=False) for v in (birth.month, birth.day, birth.year))
    first = reduce_number(month + day)
    second = reduce_number(day + year)
    values = [first, second, reduce_number(first + second), reduce_number(month + year)]
    # Phillips 用 36 − 主导数本身（10→26、11→25），22/4 取 4；其余口径先把主导数化成个位数
    first_end = 36 - (life_path if rule == "phillips" and life_path in (10, 11) else reduce_number(life_path, keep_masters=False))
    spans = [(0, first_end), (first_end + 1, first_end + 9), (first_end + 10, first_end + 18), (first_end + 19, None)]
    pinnacles = [{"index": i + 1, **number(v), "start_age": a, "end_age": b} for i, (v, (a, b)) in enumerate(zip(values, spans))]
    c1, c2 = abs(month - day), abs(day - year)
    return pinnacles, [c1, c2, abs(c1 - c2), abs(month - year)]


def build_output(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("birth_date")
    if raw in (None, ""):
        raise ValueError("Thiếu birth_date (ngày sinh dương lịch, YYYY-MM-DD)")
    parsed = parse_datetime_string(str(raw))
    try:
        birth = date(parsed["year"], parsed["month"], parsed["day"])
    except ValueError as exc:
        raise ValueError(f"Ngày sinh không hợp lệ: {raw} ({exc})") from exc

    rule = payload.get("life_path_rule") or "vn"
    if not isinstance(rule, str) or rule not in LIFE_PATH_RULES:
        raise ValueError(f"life_path_rule chỉ nhận {sorted(LIFE_PATH_RULES)}")
    method = payload.get("life_path_method") or "digits"
    if not isinstance(method, str) or method not in LIFE_PATH_METHODS:
        raise ValueError(f"life_path_method chỉ nhận {sorted(LIFE_PATH_METHODS)}")
    y_as_vowel = payload.get("y_as_vowel", True)
    if not isinstance(y_as_vowel, bool):
        raise ValueError("y_as_vowel chỉ nhận true hoặc false")

    digits_total = digit_sum(int(birth.strftime("%Y%m%d")))
    components_total = sum(reduce_number(v) for v in (birth.day, birth.month, birth.year))
    life_path = reduce_life_path(components_total if method == "components" else digits_total, rule)
    pinnacles, challenges = pinnacles_and_challenges(birth, life_path, rule)

    output: dict[str, Any] = {
        "normalized_input": {
            "birth_date": birth.isoformat(),
            "full_name": payload.get("full_name"),
            "normalized_name": None,
            "life_path_rule": rule,
            "life_path_method": method,
            "y_as_vowel": y_as_vowel,
        },
        "ruleset": {
            "id": str(payload.get("ruleset") or DEFAULT_RULESET),
            "life_path_rule": LIFE_PATH_RULES[rule],
            "life_path_method": LIFE_PATH_METHODS[method],
            "letter_values": "Bảng Pythagoras: A J S=1, B K T=2, C L U=3, D M V=4, E N W=5, F O X=6, G P Y=7, H Q Z=8, I R=9; bỏ dấu tiếng Việt, Đ=D.",
            "name_rule": "Cộng toàn bộ chữ cái của họ tên rồi rút gọn (giữ 11/22/33). Nguyên âm: A E I O U" + (" và Y." if y_as_vowel else "; Y tính là phụ âm."),
            "birthday_rule": "Số ngày sinh: rút gọn ngày sinh, giữ 11 và 22.",
            "personal_year_rule": "Năm cá nhân: cộng chữ số của ngày, tháng sinh và năm cần xem, rút gọn về 1–9.",
            "pinnacle_rule": "Ngày, tháng, năm rút về 1–9; đỉnh 1 = tháng + ngày, đỉnh 2 = ngày + năm, đỉnh 3 = đỉnh 1 + đỉnh 2, đỉnh 4 = tháng + năm (giữ 11/22/33). Đỉnh 1 kết thúc ở tuổi 36 − số chủ đạo rút về 1–9 (luật phillips: 36 − 10 = 26, 36 − 11 = 25, 22/4 tính 4); đỉnh 2, 3 mỗi đỉnh 9 năm. Thử thách: |tháng − ngày|, |ngày − năm|, |thử thách 1 − thử thách 2|, |tháng − năm|.",
            "maturity_rule": "Số trưởng thành = số chủ đạo rút về 1–9 + số sứ mệnh, rút gọn (giữ 11/22/33).",
            "birth_chart_rule": "Biểu đồ ngày sinh: đếm chữ số 1–9 trong DDMMYYYY (bỏ số 0) trên lưới 3-6-9 / 2-5-8 / 1-4-7; mũi tên full khi đủ cả 3 số, empty khi thiếu cả 3.",
        },
        "life_path": {**number(life_path), "digit_sum": digits_total, **({"components_sum": components_total} if method == "components" else {})},
        "birthday": {**number(reduce_number(birth.day)), "day": birth.day},
        "birth_chart": birth_chart(birth),
        "pinnacles": pinnacles,
        "challenges": challenges,
        "warnings": [],
    }

    full_name = str(payload.get("full_name") or "").strip()
    if full_name:
        normalized = normalize_name(full_name)
        if not normalized:
            raise ValueError("full_name không có chữ cái nào để tính")
        output["normalized_input"]["normalized_name"] = normalized
        output["name"] = name_numbers(normalized, y_as_vowel)
        for key, label in (("soul_urge", "linh hồn (không có nguyên âm)"), ("personality", "nhân cách (không có phụ âm)")):
            if output["name"][key]["raw_sum"] == 0:
                output["warnings"].append(f"Tên không có chữ cái để tính số {label}; số này bằng 0, đừng diễn giải như một con số bình thường.")
        output["maturity"] = number(reduce_number(reduce_number(life_path, keep_masters=False) + output["name"]["expression"]["value"]))
    else:
        output["warnings"].append("Chưa có họ tên: không tính số sứ mệnh, linh hồn, nhân cách, trưởng thành.")

    query_year = payload.get("query_year")
    if query_year not in (None, ""):
        if isinstance(query_year, bool) or not str(query_year).isdigit() or int(query_year) < 1:
            raise ValueError(f"query_year phải là năm dương lịch (số nguyên dương), nhận được {query_year!r}")
        year = int(query_year)
        output["personal_year"] = {"year": year, "value": reduce_number(digit_sum(birth.day) + digit_sum(birth.month) + digit_sum(year), keep_masters=False)}
    return output


def main() -> int:
    return run_cli(build_output, "Compute a structured Pythagorean numerology payload.")


if __name__ == "__main__":
    raise SystemExit(main())
