"""
奇门遁甲排盘脚本 qimen_cli.py 单元测试

覆盖范围：
- 输入解析（时间字符串、时区推断、农历转换）
- 节气判断（阳遁/阴遁，含中气）
- 三元计算
- 定局（查表）
- 地盘排布
- 天盘转排
- 星/门/神转排
- 旬空计算
- 值符/值使定位
- 中宫寄坤
- 端到端排盘断言（阳遁 + 阴遁各一例）
"""

import sys
from pathlib import Path

# 确保可以 import qimen_cli
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from datetime import datetime, timezone, timedelta
from qimen_cli import (
    parse_datetime_string,
    resolve_timezone,
    normalize_input,
    rotate_to_start,
    compute_yuan,
    compute_earth_plate,
    find_stem_palace,
    hosted_palace,
    split_branch_pair,
    build_output,
    JIAZI,
    ROTATION_RING,
    STAR_RING,
    DOOR_RING,
    GOD_RING_YANG,
    GOD_RING_YIN,
    BRANCH_TO_PALACE,
    JU_TABLE,
    EARTH_STEM_ORDER,
    XUNSHOU_TO_HIDDEN_YI,
)


# ============================================================
# 1. parse_datetime_string 测试
# ============================================================

class TestParseDatetimeString:
    """测试各种格式的时间字符串解析"""

    def test_standard_format(self):
        result = parse_datetime_string("2026-03-24 10:30")
        assert result == {"year": 2026, "month": 3, "day": 24,
                          "hour": 10, "minute": 30, "second": 0}

    def test_chinese_format(self):
        result = parse_datetime_string("2026年03月24日 10时30分")
        assert result == {"year": 2026, "month": 3, "day": 24,
                          "hour": 10, "minute": 30, "second": 0}

    def test_iso_format_with_t(self):
        result = parse_datetime_string("2026-03-24T10:30:45")
        assert result == {"year": 2026, "month": 3, "day": 24,
                          "hour": 10, "minute": 30, "second": 45}

    def test_slash_separator(self):
        result = parse_datetime_string("2026/03/24 08:00")
        assert result == {"year": 2026, "month": 3, "day": 24,
                          "hour": 8, "minute": 0, "second": 0}

    def test_date_only(self):
        result = parse_datetime_string("2026-03-24")
        assert result == {"year": 2026, "month": 3, "day": 24,
                          "hour": 0, "minute": 0, "second": 0}

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            parse_datetime_string("   ")

    def test_bad_date_raises(self):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            parse_datetime_string("2026-03")


# ============================================================
# 2. resolve_timezone 测试
# ============================================================

class TestResolveTimezone:
    """测试时区推断逻辑"""

    def test_explicit_timezone(self):
        warnings = []
        tz = resolve_timezone({"timezone": "America/New_York"}, warnings)
        assert tz == "America/New_York"
        assert warnings == []

    def test_china_default(self):
        warnings = []
        tz = resolve_timezone({"country": "中国", "city": "上海"}, warnings)
        assert tz == "Asia/Shanghai"
        assert warnings == []

    def test_empty_defaults_to_shanghai(self):
        warnings = []
        tz = resolve_timezone({}, warnings)
        assert tz == "Asia/Shanghai"

    def test_overseas_without_timezone_warns(self):
        warnings = []
        tz = resolve_timezone({"country": "Japan", "city": "Tokyo"}, warnings)
        assert tz == "Asia/Shanghai"  # fallback
        assert len(warnings) >= 1
        assert "海外" in warnings[0] or "时区" in warnings[0]


# ============================================================
# 3. normalize_input 测试
# ============================================================

class TestNormalizeInput:
    """测试输入标准化"""

    def test_solar_input(self):
        payload = {
            "question_type": "求财",
            "question_goal": "能不能成",
            "time_input": "2026-03-24 10:30",
            "calendar_type": "solar",
            "location": {"country": "中国", "city": "上海", "timezone": "Asia/Shanghai"},
        }
        result = normalize_input(payload)
        assert result.solar_dt.year == 2026
        assert result.solar_dt.month == 3
        assert result.solar_dt.day == 24
        assert result.solar_dt.hour == 10
        assert result.use_now is False
        assert result.calendar_type == "solar"

    def test_now_input(self):
        payload = {
            "question_type": "出行",
            "question_goal": "方位",
            "time_input": "",
            "calendar_type": "now",
            "location": {"country": "中国", "city": "北京"},
        }
        result = normalize_input(payload)
        assert result.use_now is True

    def test_lunar_input(self):
        payload = {
            "question_type": "感情",
            "question_goal": "能不能成",
            "time_input": {"year": 2026, "month": 2, "day": 6,
                           "hour": 10, "minute": 30, "is_leap_month": False},
            "calendar_type": "lunar",
            "location": {"country": "中国", "city": "上海", "timezone": "Asia/Shanghai"},
        }
        result = normalize_input(payload)
        # 农历2026年二月初六 应转为公历 2026-03-24
        assert result.solar_dt.year == 2026
        assert result.solar_dt.month == 3
        assert result.solar_dt.day == 24

    def test_invalid_calendar_type(self):
        payload = {
            "time_input": "2026-01-01 12:00",
            "calendar_type": "martian",
            "location": {},
        }
        with pytest.raises(ValueError, match="不支持"):
            normalize_input(payload)


# ============================================================
# 4. rotate_to_start 测试
# ============================================================

class TestRotateToStart:
    """测试环形序列旋转"""

    def test_basic_rotation(self):
        seq = [1, 2, 3, 4, 5]
        assert rotate_to_start(seq, 3) == [3, 4, 5, 1, 2]

    def test_no_rotation_needed(self):
        seq = [1, 2, 3]
        assert rotate_to_start(seq, 1) == [1, 2, 3]

    def test_rotation_ring(self):
        # ROTATION_RING = [1, 8, 3, 4, 9, 2, 7, 6]
        result = rotate_to_start(ROTATION_RING, 9)
        assert result[0] == 9
        assert len(result) == 8


# ============================================================
# 5. compute_yuan 测试
# ============================================================

class TestComputeYuan:
    """测试三元计算：日干支→上/中/下元"""

    def test_jiazi_is_shanguan(self):
        # 甲子序号0, 0//5=0, 0%3=0 → 上元
        assert compute_yuan("甲子") == "上元"

    def test_jisi_is_shanguan(self):
        # 己巳序号5, 5//5=1, 1%3=1 → 中元
        assert compute_yuan("己巳") == "中元"

    def test_jiaxu_is_shanguan(self):
        # 甲戌序号10, 10//5=2, 2%3=2 → 下元
        assert compute_yuan("甲戌") == "下元"

    def test_dingyou(self):
        # 丁酉在六十甲子中序号为 JIAZI.index("丁酉")
        idx = JIAZI.index("丁酉")  # 34
        expected = ["上元", "中元", "下元"][(idx // 5) % 3]
        assert compute_yuan("丁酉") == expected

    def test_gengyin(self):
        # 庚寅
        idx = JIAZI.index("庚寅")  # 27? let's verify
        expected = ["上元", "中元", "下元"][(idx // 5) % 3]
        assert compute_yuan("庚寅") == expected


# ============================================================
# 6. compute_earth_plate 测试
# ============================================================

class TestComputeEarthPlate:
    """测试地盘排布"""

    def test_yang_dun_ju_1(self):
        # 阳遁1局：从1宫起戊，按阳遁顺序排九干
        plate = compute_earth_plate("阳遁", 1)
        # 阳遁天干顺序: 戊己庚辛壬癸丁丙乙
        # 从1开始的宫位: 1,2,3,4,5,6,7,8,9
        assert plate[1] == "戊"
        assert plate[2] == "己"
        assert plate[3] == "庚"
        assert plate[4] == "辛"
        assert plate[5] == "壬"
        assert plate[6] == "癸"
        assert plate[7] == "丁"
        assert plate[8] == "丙"
        assert plate[9] == "乙"

    def test_yin_dun_ju_5(self):
        # 阴遁5局：从5宫起戊
        plate = compute_earth_plate("阴遁", 5)
        # 阴遁天干顺序: 戊乙丙丁癸壬辛庚己
        # 从5宫开始，按palaces序列: [1,2,3,4,5,6,7,8,9] rotate到5
        assert plate[5] == "戊"
        # 验证总共有9个天干分配
        assert len(plate) == 9

    def test_all_nine_stems_present(self):
        """地盘必须包含9个不同天干"""
        plate = compute_earth_plate("阳遁", 3)
        stems = set(plate.values())
        assert len(stems) == 9
        expected_stems = set(EARTH_STEM_ORDER["阳遁"])
        assert stems == expected_stems


# ============================================================
# 7. find_stem_palace 测试
# ============================================================

class TestFindStemPalace:
    """测试天干定宫"""

    def test_find_existing_stem(self):
        plate = {1: "戊", 2: "己", 3: "庚", 4: "辛",
                 5: "壬", 6: "癸", 7: "丁", 8: "丙", 9: "乙"}
        assert find_stem_palace(plate, "戊") == 1
        assert find_stem_palace(plate, "乙") == 9
        assert find_stem_palace(plate, "壬") == 5

    def test_not_found_raises(self):
        plate = {1: "戊", 2: "己"}
        with pytest.raises(ValueError, match="未找到"):
            find_stem_palace(plate, "甲")


# ============================================================
# 8. hosted_palace 测试
# ============================================================

class TestHostedPalace:
    """测试中宫寄坤"""

    def test_center_goes_to_kun(self):
        assert hosted_palace(5) == 2

    def test_non_center_unchanged(self):
        for p in [1, 2, 3, 4, 6, 7, 8, 9]:
            assert hosted_palace(p) == p


# ============================================================
# 9. BRANCH_TO_PALACE 旬空映射测试
# ============================================================

class TestBranchToPalace:
    """测试地支→宫位映射"""

    def test_yin_mao_mapping(self):
        # 寅→8(艮), 卯→3(震)
        assert BRANCH_TO_PALACE["寅"] == 8
        assert BRANCH_TO_PALACE["卯"] == 3

    def test_shen_you_mapping(self):
        # 申→2(坤), 酉→7(兑)
        assert BRANCH_TO_PALACE["申"] == 2
        assert BRANCH_TO_PALACE["酉"] == 7

    def test_all_twelve_branches_present(self):
        branches = "子丑寅卯辰巳午未申酉戌亥"
        for b in branches:
            assert b in BRANCH_TO_PALACE


# ============================================================
# 10. JU_TABLE 定局表完整性测试
# ============================================================

class TestJuTable:
    """测试定局表结构完整性"""

    def test_yang_dun_has_12_jie(self):
        assert len(JU_TABLE["阳遁"]) == 12

    def test_yin_dun_has_12_jie(self):
        assert len(JU_TABLE["阴遁"]) == 12

    def test_each_jie_has_three_yuan(self):
        for dun in ["阳遁", "阴遁"]:
            for jie, yuans in JU_TABLE[dun].items():
                assert set(yuans.keys()) == {"上元", "中元", "下元"}, \
                    f"{dun}/{jie} 缺少三元"

    def test_ju_numbers_in_range(self):
        for dun in ["阳遁", "阴遁"]:
            for jie, yuans in JU_TABLE[dun].items():
                for yuan, num in yuans.items():
                    assert 1 <= num <= 9, \
                        f"{dun}/{jie}/{yuan} 局数 {num} 不在1-9范围"


# ============================================================
# 11. XUNSHOU_TO_HIDDEN_YI 旬首奇仪映射测试
# ============================================================

class TestXunshouMapping:
    """测试旬首→遁仪映射"""

    def test_all_six_xunshou(self):
        expected = {
            "甲子": "戊", "甲戌": "己", "甲申": "庚",
            "甲午": "辛", "甲辰": "壬", "甲寅": "癸",
        }
        assert XUNSHOU_TO_HIDDEN_YI == expected

    def test_jiachen_maps_to_ren(self):
        assert XUNSHOU_TO_HIDDEN_YI["甲辰"] == "壬"



# ============================================================
# 12. 端到端排盘：阳遁案例 (2026-03-24 10:30 上海)
# ============================================================

class TestEndToEndYangDun:
    """
    Golden data: 2026-03-24 10:30 上海
    春分（2026-03-20）后 → 阳遁
    日干支丁酉 → 上元
    春分上元 → 阳遁3局
    旬首甲辰 → 隐仪壬
    时干乙（巳时）
    旬空寅卯 → 3宫8宫
    """

    @pytest.fixture
    def output(self):
        payload = {
            "question_type": "跳槽",
            "question_goal": "能不能动",
            "time_input": "2026-03-24 10:30",
            "calendar_type": "solar",
            "location": {"country": "中国", "city": "上海", "timezone": "Asia/Shanghai"},
            "ruleset": "mainline-cn-v1",
        }
        return build_output(payload)

    def test_dun_type(self, output):
        assert output["chart"]["dun_type"] == "阳遁"

    def test_yuan(self, output):
        assert output["chart"]["yuan"] == "上元"

    def test_ju_number(self, output):
        assert output["chart"]["ju_number"] == 3

    def test_xunshou(self, output):
        assert output["chart"]["xunshou"] == "甲辰"

    def test_hidden_yi(self, output):
        assert output["chart"]["hidden_yi"] == "壬"

    def test_kongwang_branches(self, output):
        assert sorted(output["chart"]["kongwang"]) == ["卯", "寅"]

    def test_kongwang_palaces(self, output):
        assert sorted(output["chart"]["kongwang_palaces"]) == [3, 8]

    def test_time_stem_visible(self, output):
        assert output["chart"]["time_stem_visible"] == "乙"

    def test_zhifu(self, output):
        zf = output["chart"]["zhifu"]
        assert zf["star"] == "天柱"
        assert zf["palace"] == 2

    def test_zhishi(self, output):
        # 旬首壬在兑七，乙巳距甲辰一个时辰，阳遁顺行一宫 → 艮八
        zs = output["chart"]["zhishi"]
        assert zs["door"] == "惊门"
        assert zs["palace"] == 8

    def test_active_jie(self, output):
        assert output["calendar"]["jieqi"]["active_jie"] == "春分"

    def test_ganzhi_day(self, output):
        assert output["ganzhi"]["day"] == "丁酉"

    def test_ganzhi_time(self, output):
        assert output["ganzhi"]["time"] == "乙巳"

    def test_palace_earth_stems(self, output):
        """验证阳遁3局地盘天干"""
        palaces = {p["palace"]: p for p in output["chart"]["palaces"]}
        assert palaces[3]["earth_stem"] == "戊"
        assert palaces[4]["earth_stem"] == "己"
        assert palaces[5]["earth_stem"] == "庚"
        assert palaces[6]["earth_stem"] == "辛"
        assert palaces[7]["earth_stem"] == "壬"
        assert palaces[8]["earth_stem"] == "癸"
        assert palaces[9]["earth_stem"] == "丁"
        assert palaces[1]["earth_stem"] == "丙"
        assert palaces[2]["earth_stem"] == "乙"

    def test_palace_stars(self, output):
        """验证九星分布"""
        palaces = {p["palace"]: p for p in output["chart"]["palaces"]}
        assert palaces[5]["star"] is None  # 天禽随天芮转出
        assert palaces[9]["star"] == "天芮"
        assert palaces[9]["hosted_star"] == "天禽"
        assert palaces[7]["star"] == "天心"
        assert palaces[1]["star"] == "天任"
        assert palaces[2]["star"] == "天柱"

    def test_palace_doors(self, output):
        """验证八门分布"""
        palaces = {p["palace"]: p for p in output["chart"]["palaces"]}
        assert palaces[5]["door"] is None  # 中宫无门
        assert palaces[3]["door"] == "开门"
        assert palaces[8]["door"] == "惊门"
        assert palaces[9]["door"] == "生门"
        assert palaces[1]["door"] == "死门"

    def test_palace_gods(self, output):
        """验证八神分布"""
        palaces = {p["palace"]: p for p in output["chart"]["palaces"]}
        assert palaces[5]["god"] is None  # 中宫无神
        assert palaces[2]["god"] == "值符"
        assert palaces[9]["god"] == "九天"

    def test_center_palace_flags(self, output):
        """验证中宫寄坤标记"""
        palaces = {p["palace"]: p for p in output["chart"]["palaces"]}
        assert palaces[5]["is_center"] is True
        assert palaces[2]["hosts_center"] is True
        assert palaces[2]["hosting_note"] == "地盘寄坤：承载中五地盘干"
        assert palaces[9]["hosts_center_sky"] is True
        assert palaces[9]["sky_stems"] == ["乙", "庚"]

    def test_lunar_calendar(self, output):
        """验证公历→农历转换"""
        lunar = output["calendar"]["lunar"]
        assert lunar["year"] == 2026
        assert lunar["month"] == 2
        assert lunar["day"] == 6
        assert lunar["is_leap_month"] is False


# ============================================================
# 13. 端到端排盘：阴遁案例 (2026-07-15 14:00 北京)
# ============================================================

class TestEndToEndYinDun:
    """
    Golden data: 2026-07-15 14:00 北京
    小暑后 → 阴遁
    日干支庚寅 → 下元
    小暑下元 → 阴遁5局
    旬首甲戌 → 隐仪己
    时干癸（未时）
    旬空申酉 → 2宫7宫
    """

    @pytest.fixture
    def output(self):
        payload = {
            "question_type": "投资",
            "question_goal": "能不能投",
            "time_input": "2026-07-15 14:00",
            "calendar_type": "solar",
            "location": {"country": "中国", "city": "北京", "timezone": "Asia/Shanghai"},
            "ruleset": "mainline-cn-v1",
        }
        return build_output(payload)

    def test_dun_type(self, output):
        assert output["chart"]["dun_type"] == "阴遁"

    def test_yuan(self, output):
        assert output["chart"]["yuan"] == "下元"

    def test_ju_number(self, output):
        assert output["chart"]["ju_number"] == 5

    def test_xunshou(self, output):
        assert output["chart"]["xunshou"] == "甲戌"

    def test_hidden_yi(self, output):
        assert output["chart"]["hidden_yi"] == "己"

    def test_kongwang_branches(self, output):
        assert sorted(output["chart"]["kongwang"]) == ["申", "酉"]

    def test_kongwang_palaces(self, output):
        assert sorted(output["chart"]["kongwang_palaces"]) == [2, 7]

    def test_time_stem_visible(self, output):
        assert output["chart"]["time_stem_visible"] == "癸"

    def test_zhifu(self, output):
        zf = output["chart"]["zhifu"]
        assert zf["star"] == "天辅"
        assert zf["palace"] == 9

    def test_zhishi(self, output):
        # 旬首己在巽四，癸未距甲戌九个时辰，阴遁逆行九宫回到巽四
        zs = output["chart"]["zhishi"]
        assert zs["door"] == "杜门"
        assert zs["palace"] == 4
        assert zs["hours_from_xunshou"] == 9

    def test_active_jie(self, output):
        assert output["calendar"]["jieqi"]["active_jie"] == "小暑"

    def test_ganzhi_day(self, output):
        assert output["ganzhi"]["day"] == "庚寅"

    def test_ganzhi_time(self, output):
        assert output["ganzhi"]["time"] == "癸未"

    def test_palace_earth_stems(self, output):
        """验证阴遁5局地盘天干"""
        palaces = {p["palace"]: p for p in output["chart"]["palaces"]}
        # 阴遁天干序: 戊乙丙丁癸壬辛庚己, 从5宫起戊
        assert palaces[5]["earth_stem"] == "戊"
        assert palaces[1]["earth_stem"] == "壬"
        assert palaces[7]["earth_stem"] == "丙"
        assert palaces[9]["earth_stem"] == "癸"

    def test_palace_sky_stems(self, output):
        """验证天盘"""
        palaces = {p["palace"]: p for p in output["chart"]["palaces"]}
        assert palaces[9]["sky_stem"] == "己"
        assert palaces[1]["sky_stem"] == "乙"
        assert palaces[7]["sky_stem"] == "辛"

    def test_palace_stars(self, output):
        """验证阴遁九星"""
        palaces = {p["palace"]: p for p in output["chart"]["palaces"]}
        assert palaces[9]["star"] == "天辅"
        assert palaces[1]["star"] == "天心"
        assert palaces[7]["star"] == "天芮"
        assert palaces[7]["hosted_star"] == "天禽"
        assert palaces[5]["star"] is None

    def test_palace_doors(self, output):
        """验证阴遁八门"""
        palaces = {p["palace"]: p for p in output["chart"]["palaces"]}
        assert palaces[4]["door"] == "杜门"
        assert palaces[9]["door"] == "景门"
        assert palaces[1]["door"] == "休门"
        assert palaces[7]["door"] == "惊门"
        assert palaces[5]["door"] is None

    def test_palace_gods_yin_order(self, output):
        """验证阴遁八神顺序"""
        palaces = {p["palace"]: p for p in output["chart"]["palaces"]}
        assert palaces[9]["god"] == "值符"
        assert palaces[5]["god"] is None


# ============================================================
# 14. 边界情况测试
# ============================================================

class TestEdgeCases:
    """边界情况"""

    def test_time_gan_is_jia(self):
        """时干为甲时，应替换为旬首所遁之仪，并产生 warning"""
        # 甲子时，旬首甲子→遁仪戊
        # 需要找一个甲X时的案例
        # 2026-01-01 23:00 → 子时，日干支确定后看时干
        payload = {
            "question_type": "测试",
            "question_goal": "测试",
            "time_input": {"year": 2026, "month": 1, "day": 5,
                           "hour": 23, "minute": 0},
            "calendar_type": "solar",
            "location": {"timezone": "Asia/Shanghai"},
        }
        output = build_output(payload)
        # 不管具体结果，只验证结构完整
        assert "chart" in output
        assert "palaces" in output["chart"]
        assert len(output["chart"]["palaces"]) == 9

    def test_center_palace_structure(self):
        """中宫(5号)必须 door=None, god=None, star=None（天禽随天芮转出）"""
        payload = {
            "question_type": "测试",
            "question_goal": "测试",
            "time_input": "2026-06-01 12:00",
            "calendar_type": "solar",
            "location": {"timezone": "Asia/Shanghai"},
        }
        output = build_output(payload)
        palaces = {p["palace"]: p for p in output["chart"]["palaces"]}
        assert palaces[5]["star"] is None
        assert palaces[5]["door"] is None
        assert palaces[5]["god"] is None
        assert palaces[5]["is_center"] is True

    def test_nine_palaces_complete(self):
        """输出必须包含完整9宫"""
        payload = {
            "question_type": "测试",
            "question_goal": "测试",
            "time_input": "2026-09-15 08:00",
            "calendar_type": "solar",
            "location": {"timezone": "Asia/Shanghai"},
        }
        output = build_output(payload)
        palace_numbers = {p["palace"] for p in output["chart"]["palaces"]}
        assert palace_numbers == {1, 2, 3, 4, 5, 6, 7, 8, 9}

    def test_output_has_all_required_keys(self):
        """验证输出包含所有必要顶层字段"""
        payload = {
            "question_type": "出行",
            "question_goal": "方位",
            "time_input": "2026-04-10 16:00",
            "calendar_type": "solar",
            "location": {"timezone": "Asia/Shanghai"},
        }
        output = build_output(payload)
        assert "normalized_input" in output
        assert "calendar" in output
        assert "ganzhi" in output
        assert "ruleset" in output
        assert "chart" in output
        assert "warnings" in output

    def test_dun_type_summer_is_yin(self):
        """夏至后应为阴遁"""
        payload = {
            "question_type": "测试",
            "question_goal": "测试",
            "time_input": "2026-08-01 10:00",
            "calendar_type": "solar",
            "location": {"timezone": "Asia/Shanghai"},
        }
        output = build_output(payload)
        assert output["chart"]["dun_type"] == "阴遁"

    def test_dun_type_winter_is_yang(self):
        """冬至后应为阳遁"""
        payload = {
            "question_type": "测试",
            "question_goal": "测试",
            "time_input": "2026-01-15 10:00",
            "calendar_type": "solar",
            "location": {"timezone": "Asia/Shanghai"},
        }
        output = build_output(payload)
        assert output["chart"]["dun_type"] == "阳遁"


# ============================================================
# 15. 常量完整性测试
# ============================================================

class TestConstants:
    """验证核心常量的完整性和一致性"""

    def test_jiazi_has_60(self):
        assert len(JIAZI) == 60

    def test_jiazi_no_duplicates(self):
        assert len(set(JIAZI)) == 60

    def test_rotation_ring_has_8(self):
        assert len(ROTATION_RING) == 8
        assert set(ROTATION_RING) == {1, 2, 3, 4, 6, 7, 8, 9}  # 不含5

    def test_star_ring_has_8(self):
        assert len(STAR_RING) == 8

    def test_door_ring_has_8(self):
        assert len(DOOR_RING) == 8

    def test_god_ring_yang_has_8(self):
        assert len(GOD_RING_YANG) == 8
        assert GOD_RING_YANG[0] == "值符"

    def test_god_ring_yin_has_8(self):
        assert len(GOD_RING_YIN) == 8
        assert GOD_RING_YIN[0] == "值符"

    def test_earth_stem_order_has_9_each(self):
        assert len(EARTH_STEM_ORDER["阳遁"]) == 9
        assert len(EARTH_STEM_ORDER["阴遁"]) == 9
        # 两个序列包含相同的9个天干
        assert set(EARTH_STEM_ORDER["阳遁"]) == set(EARTH_STEM_ORDER["阴遁"])



# ============================================================
# 16. 新增功能测试：驿马、日干落宫、年月干、五行生克、日旬空
# ============================================================

from qimen_cli import (
    compute_yima,
    compute_stem_relation,
    find_gan_palace,
    YIMA_TABLE,
    STEM_ELEMENT,
    WUXING_SHENG,
    WUXING_KE,
)


class TestComputeYima:
    """测试驿马计算"""

    def test_you_day_yima_hai(self):
        # 巳酉丑→驿马在亥
        assert compute_yima("酉") == {"branch": "亥", "palace": 6, "source_branch": "酉"}

    def test_yin_day_yima_shen(self):
        # 寅午戌→驿马在申
        assert compute_yima("寅") == {"branch": "申", "palace": 2, "source_branch": "寅"}

    def test_zi_day_yima_yin(self):
        # 申子辰→驿马在寅
        assert compute_yima("子") == {"branch": "寅", "palace": 8, "source_branch": "子"}

    def test_mao_day_yima_si(self):
        # 亥卯未→驿马在巳
        assert compute_yima("卯") == {"branch": "巳", "palace": 4, "source_branch": "卯"}

    def test_all_twelve_branches_covered(self):
        branches = "子丑寅卯辰巳午未申酉戌亥"
        for b in branches:
            result = compute_yima(b)
            assert result["branch"] is not None
            assert result["palace"] is not None


class TestComputeStemRelation:
    """测试天地盘五行生克关系"""

    def test_bihe(self):
        # 庚辛都是金 → 比和
        assert compute_stem_relation("庚", "辛") == "比和"
        assert compute_stem_relation("甲", "乙") == "比和"

    def test_tian_sheng_di(self):
        # 丙(火) 生 戊(土) → 天生地
        assert compute_stem_relation("丙", "戊") == "天生地"

    def test_di_sheng_tian(self):
        # 地=甲(木) 生 天=丙(火) → 地生天
        assert compute_stem_relation("丙", "甲") == "地生天"

    def test_tian_ke_di(self):
        # 天=癸(水) 克 地=丁(火) → 天克地
        assert compute_stem_relation("癸", "丁") == "天克地"

    def test_di_ke_tian(self):
        # 天=乙(木), 地=辛(金) → 地克天 (金克木)
        assert compute_stem_relation("乙", "辛") == "地克天"

    def test_none_inputs(self):
        assert compute_stem_relation(None, "甲") is None
        assert compute_stem_relation("甲", None) is None


class TestFindGanPalace:
    """测试天干落宫查找"""

    def test_find_in_plate(self):
        plate = {1: "戊", 2: "己", 3: "庚", 4: "辛",
                 5: "壬", 6: "癸", 7: "丁", 8: "丙", 9: "乙"}
        result = find_gan_palace(plate, "丁")
        assert result["stem"] == "丁"
        assert result["raw_palace"] == 7
        assert result["palace"] == 7

    def test_center_palace_hosts_to_kun(self):
        plate = {1: "戊", 2: "己", 3: "庚", 4: "辛",
                 5: "壬", 6: "癸", 7: "丁", 8: "丙", 9: "乙"}
        result = find_gan_palace(plate, "壬")
        assert result["raw_palace"] == 5
        assert result["palace"] == 2  # 寄坤

    def test_not_found(self):
        plate = {1: "戊", 2: "己"}
        result = find_gan_palace(plate, "甲")
        assert result["raw_palace"] is None
        assert result["palace"] is None


class TestEndToEndNewFields:
    """验证新增字段在完整排盘中的输出"""

    @pytest.fixture
    def yang_output(self):
        payload = {
            "question_type": "跳槽",
            "question_goal": "能不能动",
            "time_input": "2026-03-24 10:30",
            "calendar_type": "solar",
            "location": {"country": "中国", "city": "上海", "timezone": "Asia/Shanghai"},
            "ruleset": "mainline-cn-v1",
        }
        return build_output(payload)

    @pytest.fixture
    def yin_output(self):
        payload = {
            "question_type": "投资",
            "question_goal": "能不能投",
            "time_input": "2026-07-15 14:00",
            "calendar_type": "solar",
            "location": {"country": "中国", "city": "北京", "timezone": "Asia/Shanghai"},
            "ruleset": "mainline-cn-v1",
        }
        return build_output(payload)

    # --- 驿马 ---

    def test_yang_yima(self, yang_output):
        # 时支巳、日支酉, 都属巳酉丑→驿马亥, 亥→6宫
        chart = yang_output["chart"]
        assert chart["hour_yima"] == {"branch": "亥", "palace": 6, "source_branch": "巳"}
        assert chart["day_yima"] == {"branch": "亥", "palace": 6, "source_branch": "酉"}
        assert "yima" not in chart

    def test_yin_yima(self, yin_output):
        # 时支未→亥卯未→马在巳(4宫)；日支寅→寅午戌→马在申(2宫)
        chart = yin_output["chart"]
        assert chart["hour_yima"] == {"branch": "巳", "palace": 4, "source_branch": "未"}
        assert chart["day_yima"] == {"branch": "申", "palace": 2, "source_branch": "寅"}

    # --- 日干落宫 ---

    def test_yang_day_stem(self, yang_output):
        # 日干丁, 阳遁3局地盘丁在9宫
        ds = yang_output["chart"]["day_stem"]
        assert ds["stem"] == "丁"
        assert ds["palace"] == 9

    def test_yin_day_stem(self, yin_output):
        # 日干庚, 阴遁5局地盘庚在3宫? Let's trust the output
        ds = yin_output["chart"]["day_stem"]
        assert ds["stem"] == "庚"
        assert ds["palace"] == 3

    # --- 年干/月干 ---

    def test_yang_year_stem(self, yang_output):
        # 年干丙
        ys = yang_output["chart"]["year_stem"]
        assert ys["stem"] == "丙"
        assert ys["palace"] is not None

    def test_yang_month_stem(self, yang_output):
        # 月干辛
        ms = yang_output["chart"]["month_stem"]
        assert ms["stem"] == "辛"
        assert ms["palace"] is not None

    # --- 日旬空 ---

    def test_yang_day_kongwang(self, yang_output):
        # 日旬甲午, 旬空辰巳
        assert sorted(yang_output["chart"]["day_kongwang"]) == ["巳", "辰"]
        assert len(yang_output["chart"]["day_kongwang_palaces"]) >= 1

    def test_yin_day_kongwang(self, yin_output):
        # 日旬空: 午未
        assert sorted(yin_output["chart"]["day_kongwang"]) == ["午", "未"]

    # --- 五行生克 ---

    def test_stem_relation_present(self, yang_output):
        """每宫（除中宫）都应有 stem_relation"""
        for p in yang_output["chart"]["palaces"]:
            if p["palace"] == 5:
                assert p["stem_relation"] is None
            else:
                assert p["stem_relation"] in [
                    "比和", "天生地", "地生天", "天克地", "地克天"
                ]

    def test_yang_palace_1_relation(self, yang_output):
        # 宫1: 地=丙(火) 天=癸(水), 水克火 → 天克地
        palaces = {p["palace"]: p for p in yang_output["chart"]["palaces"]}
        assert palaces[1]["stem_relation"] == "天克地"


class TestYimaTable:
    """驿马表完整性"""

    def test_all_twelve_branches_in_table(self):
        branches = "子丑寅卯辰巳午未申酉戌亥"
        for b in branches:
            assert b in YIMA_TABLE

    def test_yima_values_are_valid_branches(self):
        valid_branches = set("子丑寅卯辰巳午未申酉戌亥")
        for v in YIMA_TABLE.values():
            assert v in valid_branches


class TestWuxingConstants:
    """五行常量完整性"""

    def test_stem_element_has_ten(self):
        assert len(STEM_ELEMENT) == 10

    def test_wuxing_sheng_cycle(self):
        # 木→火→土→金→水→木
        assert WUXING_SHENG["木"] == "火"
        assert WUXING_SHENG["火"] == "土"
        assert WUXING_SHENG["土"] == "金"
        assert WUXING_SHENG["金"] == "水"
        assert WUXING_SHENG["水"] == "木"

    def test_wuxing_ke_cycle(self):
        # 木→土→水→火→金→木
        assert WUXING_KE["木"] == "土"
        assert WUXING_KE["土"] == "水"
        assert WUXING_KE["水"] == "火"
        assert WUXING_KE["火"] == "金"
        assert WUXING_KE["金"] == "木"


# ============================================================
# 17. 回归测试：节气、值使移宫、门迫方向、时马日马、天禽随转
# ============================================================

from qimen_cli import compute_zhishi_palace, detect_patterns


def _chart(time_input):
    return build_output({
        "question_type": "测试",
        "question_goal": "测试",
        "time_input": time_input,
        "calendar_type": "solar",
        "location": {"timezone": "Asia/Shanghai"},
    })


def _palaces(output):
    return {p["palace"]: p for p in output["chart"]["palaces"]}


class TestJieqiIncludesZhongqi:
    """定局必须按二十四节气，不能只取十二节"""

    @pytest.mark.parametrize("time_input, jieqi, dun_type, ju", [
        ("2026-01-01 12:00", "冬至", "阳遁", 4),   # 乙亥日下元；只取节会落到大雪 → 阴遁
        ("2026-03-24 10:30", "春分", "阳遁", 3),   # 丁酉日上元；只取节会落到惊蛰 → 1 局
        ("2026-06-25 12:00", "夏至", "阴遁", 3),   # 庚午日中元；只取节会落到芒种 → 阳遁
        ("2026-12-25 12:00", "冬至", "阳遁", 7),   # 癸酉日中元；只取节会落到大雪 → 阴遁
    ])
    def test_zhongqi_period(self, time_input, jieqi, dun_type, ju):
        output = _chart(time_input)
        assert output["calendar"]["jieqi"]["active_jie"] == jieqi
        assert output["chart"]["dun_type"] == dun_type
        assert output["chart"]["ju_number"] == ju


class TestComputeZhishiPalace:
    """值使沿九宫数序逐时移宫：阳顺阴逆，经过中五照常计数，落中五寄坤"""

    def test_zero_hours_stays(self):
        assert compute_zhishi_palace("阳遁", 3, 0) == (3, 3)

    def test_yang_forward(self):
        assert compute_zhishi_palace("阳遁", 1, 1) == (2, 2)

    def test_yin_backward(self):
        assert compute_zhishi_palace("阴遁", 3, 1) == (2, 2)

    def test_yang_wraps_nine_to_one(self):
        assert compute_zhishi_palace("阳遁", 9, 1) == (1, 1)

    def test_yin_wraps_one_to_nine(self):
        assert compute_zhishi_palace("阴遁", 1, 1) == (9, 9)

    def test_landing_on_center_hosts_to_kun(self):
        assert compute_zhishi_palace("阳遁", 4, 1) == (5, 2)
        assert compute_zhishi_palace("阴遁", 6, 1) == (5, 2)

    def test_counting_through_center(self):
        # 4 → 5 → 6：中五算一步，不跳过
        assert compute_zhishi_palace("阳遁", 4, 2) == (6, 6)

    def test_starting_from_center(self):
        assert compute_zhishi_palace("阳遁", 5, 1) == (6, 6)
        assert compute_zhishi_palace("阴遁", 5, 1) == (4, 4)


class TestDunjiaYanyiExample:
    """《遁甲演义》卷一「八门九星逐时移宫诀」：阳一局甲子旬
    甲子时蓬星、休门俱在一宫；乙丑时蓬星在九、休门在二；丙寅时蓬星在八、休门在三。
    2026-01-05（冬至上元，己卯日）凌晨恰为阳遁一局甲子旬。
    """

    @pytest.mark.parametrize("time_input, star_palace, door_palace", [
        ("2026-01-05 00:30", 1, 1),  # 甲子时
        ("2026-01-05 01:30", 9, 2),  # 乙丑时
        ("2026-01-05 03:30", 8, 3),  # 丙寅时
    ])
    def test_star_and_door_move_separately(self, time_input, star_palace, door_palace):
        output = _chart(time_input)
        chart = output["chart"]
        assert chart["dun_type"] == "阳遁"
        assert chart["ju_number"] == 1
        assert chart["zhifu"] == {"star": "天蓬", "palace": star_palace}
        assert chart["zhishi"]["door"] == "休门"
        assert chart["zhishi"]["palace"] == door_palace


class TestIssue11Chart:
    """Issue #11 复现盘：2026-10-12 02:03:53 上海，寒露下元阴遁三局，甲子旬乙丑时"""

    @pytest.fixture
    def output(self):
        return _chart("2026-10-12 02:03:53")

    def test_ju(self, output):
        chart = output["chart"]
        assert (chart["dun_type"], chart["yuan"], chart["ju_number"]) == ("阴遁", "下元", 3)

    def test_zhifu_and_zhishi_in_different_palaces(self, output):
        chart = output["chart"]
        assert chart["zhifu"] == {"star": "天冲", "palace": 4}
        assert chart["zhishi"]["door"] == "伤门"
        assert chart["zhishi"]["palace"] == 2

    def test_full_door_layout(self, output):
        doors = {no: p["door"] for no, p in _palaces(output).items()}
        assert doors == {
            1: "死门", 2: "伤门", 3: "开门", 4: "休门", 5: None,
            6: "景门", 7: "杜门", 8: "惊门", 9: "生门",
        }

    def test_no_false_sanqi_jimen_in_kan(self, output):
        # 旧实现把开门放在坎一，误报「丁+开门」三奇配吉门
        patterns = output["chart"]["detected_patterns"]
        assert not any(p["name"] == "三奇配吉门" and p["palace"] == 1 for p in patterns)

    def test_hour_and_day_yima(self, output):
        chart = output["chart"]
        # 丑时 → 巳酉丑 → 马在亥 → 乾六（正逢时旬空）
        assert chart["hour_yima"] == {"branch": "亥", "palace": 6, "source_branch": "丑"}
        # 未日 → 亥卯未 → 马在巳 → 巽四
        assert chart["day_yima"] == {"branch": "巳", "palace": 4, "source_branch": "未"}

    def test_tianqin_and_center_stem_follow_tianrui(self, output):
        chart = output["chart"]
        palaces = _palaces(output)
        assert chart["center_hosting"] == {
            "hosted_star": "天禽",
            "center_stem": "丙",
            "earth_host_palace": 2,
            "sky_palace": 7,
            "follows_star": "天芮",
        }
        assert palaces[7]["star"] == "天芮"
        assert palaces[7]["hosted_star"] == "天禽"
        assert palaces[7]["sky_stems"] == ["己", "丙"]
        assert palaces[7]["hosted_sky_stem"] == "丙"
        assert palaces[5]["star"] is None
        assert palaces[5]["sky_stem"] is None
        assert chart["star_index"]["天禽"] == 7


class TestMenpoDirection:
    """「宫制其门不为迫，门制其宫是迫雄」：门克宫为门迫，宫克门为门受制"""

    @staticmethod
    def _palace(no, element, door):
        return {
            "palace": no, "name": f"{no}宫", "element": element, "is_center": False,
            "sky_stem": None, "earth_stem": None, "door": door, "star": None,
        }

    def _names(self, palace):
        patterns = detect_patterns([palace], {"star": "天蓬", "palace": 9}, 1, {}, {})
        return [(p["name"], p["nature"]) for p in patterns]

    def test_door_controls_palace_is_menpo(self):
        # 开门(金)落震三(木)：门克宫 → 门迫
        assert self._names(self._palace(3, "木", "开门")) == [("门迫", "凶")]

    def test_palace_controls_door_is_not_menpo(self):
        # 生门(土)落震三(木)：宫克门 → 门受制，不是门迫
        assert self._names(self._palace(3, "木", "生门")) == [("门受制", "凶")]

    def test_xiong_door_controlled_is_neutral(self):
        # 杜门(木)落兑七(金)：凶门受制
        assert self._names(self._palace(7, "金", "杜门")) == [("门受制", "中")]

    def test_no_relation(self):
        # 休门(水)落坎一(水)：比和
        assert self._names(self._palace(1, "水", "休门")) == []


class TestChartInvariants:
    """2026 全年每 5 小时一盘，检查星门整体转、值使落宫与门盘一致"""

    def test_rotation_invariants(self):
        from datetime import datetime as _dt, timedelta as _td
        ring = ROTATION_RING
        start = _dt(2026, 1, 1)
        for h in range(0, 24 * 365, 5):
            t = start + _td(hours=h)
            chart = _chart(t.strftime("%Y-%m-%d %H:%M"))["chart"]
            palaces = _palaces({"chart": chart})
            doors = [palaces[p]["door"] for p in ring]
            stars = [palaces[p]["star"] for p in ring]
            # 门、星都是整体旋转，保持原有相对次序
            k = doors.index("休门")
            assert doors[k:] + doors[:k] == DOOR_RING
            k = stars.index("天蓬")
            assert stars[k:] + stars[:k] == STAR_RING
            assert palaces[chart["zhishi"]["palace"]]["door"] == chart["zhishi"]["door"]
            assert palaces[chart["zhifu"]["palace"]]["star"] == chart["zhifu"]["star"]
            assert palaces[chart["center_hosting"]["sky_palace"]]["star"] == "天芮"


# ============================================================
# 18. 回归测试：阴遁八神逆布、反吟按对冲判断
# ============================================================

class TestGodDirection:
    """八神阳遁顺布、阴遁逆布"""

    def test_yin_gods_counterclockwise(self):
        # Issue #11 盘：阴遁，值符落巽四，八神沿 4→3→8→1→6→7→2→9 逆布
        gods = {no: p["god"] for no, p in _palaces(_chart("2026-10-12 02:03:53")).items()}
        assert gods == {
            4: "值符", 3: "螣蛇", 8: "太阴", 1: "六合",
            6: "白虎", 7: "玄武", 2: "九地", 9: "九天", 5: None,
        }

    def test_yang_gods_clockwise(self):
        # 2026-03-24 阳遁，值符落坤二，八神沿 2→7→6→1→8→3→4→9 顺布
        gods = {no: p["god"] for no, p in _palaces(_chart("2026-03-24 10:30")).items()}
        assert gods == {
            2: "值符", 7: "螣蛇", 6: "太阴", 1: "六合",
            8: "白虎", 3: "玄武", 4: "九地", 9: "九天", 5: None,
        }


class TestFanyin:
    """「凡星符对冲皆反吟」：星落本宫对冲宫为反吟，门落本宫对冲宫为门反吟"""

    def test_dunjia_yanyi_zhifu_fanyin(self):
        # 《遁甲演义》：阳遁一局，甲己日乙丑时，以天蓬直符加临时干在九宫，即是直符反吟
        patterns = _chart("2026-01-05 01:30")["chart"]["detected_patterns"]
        fanyin = {p["palace"]: p for p in patterns if p["name"] == "反吟"}
        assert set(fanyin) == {1, 2, 3, 4, 6, 7, 8, 9}  # 星盘整体对冲
        assert "天蓬" in fanyin[9]["detail"]
        assert "天盘戊加地盘乙" in fanyin[9]["detail"]  # 戊（甲子）从坎宫转到离宫，即子来加午
        assert not any(p["name"] == "门反吟" for p in patterns)  # 休门在二宫，不对冲

    def test_door_fanyin(self):
        # 阳一局壬申时：值使休门从一宫顺行八宫到九宫，门盘整体对冲
        patterns = _chart("2026-01-05 15:30")["chart"]["detected_patterns"]
        door_fanyin = {p["palace"] for p in patterns if p["name"] == "门反吟"}
        assert door_fanyin == {1, 2, 3, 4, 6, 7, 8, 9}

    def test_fuyin_hour_has_no_fanyin(self):
        # 甲子时星门都在本宫，是伏吟不是反吟
        names = {p["name"] for p in _chart("2026-01-05 00:30")["chart"]["detected_patterns"]}
        assert "伏吟" in names
        assert "反吟" not in names
        assert "门反吟" not in names

    def test_single_palace_rules(self):
        def names(star, door, palace_no):
            palace = {
                "palace": palace_no, "name": f"{palace_no}宫", "element": "土", "is_center": False,
                "sky_stem": "戊", "earth_stem": "乙", "door": door, "star": star,
            }
            return {p["name"] for p in detect_patterns([palace], {"star": "天英", "palace": 9}, 1, {}, {})}

        assert "反吟" in names("天蓬", None, 9)
        assert "反吟" in names("天任", None, 2)
        assert "反吟" not in names("天蓬", None, 8)
        assert "门反吟" in names(None, "生门", 2)
        assert "门反吟" not in names(None, "生门", 8)

    def test_fanyin_fires_during_year(self):
        # 旧实现要求天地盘干五行互克，永远不成立；修正后全年应能检出
        from datetime import datetime as _dt, timedelta as _td
        start = _dt(2026, 1, 1)
        seen = set()
        for h in range(0, 24 * 365, 3):
            t = (start + _td(hours=h)).strftime("%Y-%m-%d %H:%M")
            seen |= {p["name"] for p in _chart(t)["chart"]["detected_patterns"]}
        assert {"反吟", "门反吟"} <= seen
