"""numerology_cli.py 测试：手算例子 + 结构性质。"""
import random
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from numerology_cli import build_output

REFERENCE = (Path(__file__).resolve().parents[2] / "references" / "y-nghia-so.md").read_text(encoding="utf-8")


def _chart(birth_date, **extra):
    return build_output({"birth_date": birth_date, **extra})


class TestLifePath:
    # 逐位相加（digits，默认）：期望值均为手算，第二列是逐位和
    @pytest.mark.parametrize("birth,digit_sum,vn,classic", [
        ("1990-05-15", 30, 3, 3),
        ("1991-01-08", 29, 11, 11),
        ("1999-01-09", 38, 11, 11),
        ("2000-08-08", 18, 9, 9),
        ("1990-09-18", 37, 10, 1),
        ("1981-01-08", 28, 10, 1),
        ("1979-09-29", 46, 10, 1),
        ("1989-07-06", 40, 4, 4),
        ("1999-12-29", 42, 6, 6),
        ("1999-09-15", 43, 7, 7),
        ("2013-09-07", 22, 22, 22),
        ("2049-09-09", 33, 33, 33),
    ])
    def test_digits_method(self, birth, digit_sum, vn, classic):
        assert sum(int(c) for c in birth if c.isdigit()) == digit_sum
        out = _chart(birth)
        assert (out["life_path"]["digit_sum"], out["life_path"]["value"]) == (digit_sum, vn)
        assert _chart(birth, life_path_rule="classic")["life_path"]["value"] == classic

    @pytest.mark.parametrize("birth,display", [
        ("1990-05-15", "3"), ("1991-01-08", "11/2"), ("1990-09-18", "10/1"),
        ("2013-09-07", "22/4"), ("2049-09-09", "33/6"),
    ])
    def test_display(self, birth, display):
        assert _chart(birth)["life_path"]["display"] == display

    def test_components_sum_reported_separately(self):
        out = _chart("2049-09-09", life_path_method="components")["life_path"]
        assert out["digit_sum"] == 33 and out["components_sum"] == 24  # 9 + 9 + (2049→15→6)

    def test_components_method(self):
        # 来源例：6/7/1989 → 日 6，月 7，年 1+9+8+9=27→9；6+7+9 = 22 → 22/4（逐位相加则为 40 → 4）
        out = _chart("1989-07-06", life_path_method="components")
        assert (out["life_path"]["value"], out["life_path"]["display"]) == (22, "22/4")
        assert _chart("1989-07-06")["life_path"]["value"] == 4

    @pytest.mark.parametrize("birth,value", [
        ("1980-09-29", 11),  # 日 29→11（保留），月 9，年 1980→18→9：11+9+9 = 29 → 11
        ("1980-11-29", 4),   # 日 11，月 11（保留，不先拆成 1+1），年 9：31 → 4
        ("1980-02-29", 22),  # 11 + 2 + 9 = 22
    ])
    def test_components_keep_master_parts(self, birth, value):
        assert _chart(birth, life_path_method="components")["life_path"]["value"] == value

    def test_vn_rule_never_gives_one(self):
        # 越南常用口径：化简到 2–11，保留 22、33；没有 1，对应的是 10
        d, seen = date(1900, 1, 1), set()
        while d < date(2100, 1, 1):
            seen.add(_chart(d.isoformat())["life_path"]["value"])
            d += timedelta(days=17)
        assert 1 not in seen and 10 in seen
        assert seen <= set(range(2, 12)) | {22, 33}


class TestBirthday:
    @pytest.mark.parametrize("day,value", [(15, 6), (29, 11), (22, 22), (10, 1), (9, 9)])
    def test_birthday(self, day, value):
        assert _chart(f"1990-05-{day:02d}")["birthday"]["value"] == value


class TestPersonalYear:
    def test_known(self):
        # 15 + 5 + 2026：1+5+5+2+0+2+6 = 21 → 3
        assert _chart("1990-05-15", query_year=2026)["personal_year"] == {"year": 2026, "value": 3}

    def test_range(self):
        for year in range(2000, 2030):
            assert 1 <= _chart("1990-05-15", query_year=year)["personal_year"]["value"] <= 9


class TestName:
    def test_vietnamese_name(self):
        # NGUYENVANAN：N5 G7 U3 Y7 E5 N5 V4 A1 N5 A1 N5 = 48 → 12 → 3
        out = _chart("1990-05-15", full_name="Nguyễn Văn An")
        name = out["name"]
        assert out["normalized_input"]["normalized_name"] == "NGUYEN VAN AN"
        assert (name["expression"]["value"], name["soul_urge"]["value"], name["personality"]["value"]) == (3, 8, 4)

    def test_y_as_consonant_keeps_master(self):
        # Y 作辅音：元音 U3 E5 A1 A1 = 10 → 1；辅音 N5 G7 Y7 N5 V4 N5 N5 = 38 → 11（保留主数）
        name = _chart("1990-05-15", full_name="Nguyễn Văn An", y_as_vowel=False)["name"]
        assert (name["soul_urge"]["value"], name["personality"]["value"]) == (1, 11)
        assert name["personality"]["display"] == "11/2"

    def test_d_stroke(self):
        assert _chart("1990-05-15", full_name="Đỗ Đức")["normalized_input"]["normalized_name"] == "DO DUC"

    def test_maturity(self):
        out = _chart("1990-05-15", full_name="Nguyễn Văn An")
        assert out["maturity"]["value"] == 6  # 3 + 3

    def test_name_without_vowels_warns(self):
        out = _chart("1990-05-15", full_name="Ng")
        assert out["name"]["soul_urge"]["value"] == 0
        assert any("nguyên âm" in w for w in out["warnings"])

    def test_query_year_string(self):
        assert _chart("1990-05-15", query_year="2026")["personal_year"]["value"] == 3

    def test_rejects_non_latin(self):
        with pytest.raises(ValueError, match="full_name"):
            _chart("1990-05-15", full_name="张三")


class TestBirthChart:
    def test_counts_and_arrows(self):
        # 15/05/1990 → 1,5,0,5,1,9,9,0：1×2, 5×2, 9×2
        chart = _chart("1990-05-15")["birth_chart"]
        assert chart["counts"] == {"1": 2, "2": 0, "3": 0, "4": 0, "5": 2, "6": 0, "7": 0, "8": 0, "9": 2}
        assert chart["missing"] == [2, 3, 4, 6, 7, 8]
        status = {"-".join(map(str, a["digits"])): a["status"] for a in chart["arrows"]}
        assert status["1-5-9"] == "full"
        assert status["4-5-6"] == "partial"
        assert status["2-5-8"] == "partial"
        assert status["7-8-9"] == "partial"
        assert status["3-6-9"] == "partial"
        assert status["1-2-3"] == "partial"
        assert status["1-4-7"] == "partial"
        assert status["3-5-7"] == "partial"
        assert chart["grid"] == [[3, 6, 9], [2, 5, 8], [1, 4, 7]]

    def test_empty_arrow(self):
        # 22/12/2002 → 2,2,1,2,2,0,0,2：只有 1、2
        status = {"-".join(map(str, a["digits"])): a["status"] for a in _chart("2002-12-22")["birth_chart"]["arrows"]}
        assert status["4-5-6"] == "empty" and status["7-8-9"] == "empty" and status["3-5-7"] == "empty"

    def test_counts_sum_to_nonzero_digits(self):
        rng = random.Random(3)
        for _ in range(300):
            d = date(1900, 1, 1) + timedelta(days=rng.randrange(200 * 365))
            digits = [int(c) for c in d.strftime("%d%m%Y") if c != "0"]
            assert sum(_chart(d.isoformat())["birth_chart"]["counts"].values()) == len(digits)


class TestPinnacles:
    def test_known(self):
        # 15/05/1990：月 5、日 15→6、年 1990→19→10→1；生命灵数 3
        out = _chart("1990-05-15")
        assert [p["value"] for p in out["pinnacles"]] == [11, 7, 9, 6]  # 5+6=11（保留主数），6+1=7，11+7=18→9，5+1=6
        assert [(p["start_age"], p["end_age"]) for p in out["pinnacles"]] == [(0, 33), (34, 42), (43, 51), (52, None)]
        assert out["challenges"] == [1, 5, 4, 4]  # |5-6|, |6-1|, |1-5|, |5-1|

    def test_first_pinnacle_ends_at_36_minus_reduced_life_path(self):
        out = _chart("1981-01-08")  # 越南口径生命灵数 10，按 1 计：36-1 = 35
        assert out["pinnacles"][0]["end_age"] == 35


class TestInput:
    @pytest.mark.parametrize("payload,message", [
        ({}, "birth_date"),
        ({"birth_date": "1990-05-15", "life_path_method": "x"}, "life_path_method"),
        ({"birth_date": "1990-02-30"}, "không hợp lệ"),
        ({"birth_date": "1990-05-15", "life_path_rule": "x"}, "life_path_rule"),
        ({"birth_date": "1990-05-15", "life_path_rule": ["vn"]}, "life_path_rule"),
        ({"birth_date": "1990-05-15", "life_path_method": {"a": 1}}, "life_path_method"),
        ({"birth_date": "1990-05-15", "query_year": 2026.7}, "query_year"),
        ({"birth_date": "1990-05-15", "query_year": True}, "query_year"),
        ({"birth_date": "1990-05-15", "query_year": "-5"}, "query_year"),
        ({"birth_date": "1990-05-15", "full_name": "Trần 3 Văn"}, "full_name"),
    ])
    def test_rejects(self, payload, message):
        with pytest.raises(ValueError, match=message):
            build_output(payload)


def test_reference_covers_core_numbers():
    for number in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "22/4", "33/6"]:
        assert re.search(rf"^### Số {re.escape(number)}$", REFERENCE, re.M), number
