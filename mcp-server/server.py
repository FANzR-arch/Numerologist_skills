#!/usr/bin/env python3
"""MCP server：把八字、紫微斗数、奇门遁甲、六爻、Thần số học 五个计算脚本暴露为 MCP tool。

每个 tool 的参数与对应 skill 的输入 JSON 一一对应（见各 skill 的 SKILL.md），返回值即脚本输出。
排盘逻辑全部在各 skill 的 scripts/ 里，这里只做参数到 payload 的转换。

  python mcp-server/server.py        # stdio 传输
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

ROOT = Path(__file__).resolve().parent.parent
for skill in ("bazi", "ziwei-doushu", "qimen-dunjia", "numerology", "liuyao"):
    sys.path.insert(0, str(ROOT / skill / "scripts"))

import bazi_cli  # noqa: E402
import liuyao_cli  # noqa: E402
import numerology_cli  # noqa: E402
import qimen_cli  # noqa: E402
import ziwei_cli  # noqa: E402

server = MCPServer(
    name="numerologist",
    instructions=(
        "八字、紫微斗数、奇门遁甲确定性排盘。先向用户确认出生（或起局）时间、性别、口径，再调用；"
        "盘面以返回结果为准，不要手算或改盘。越南用户的阴历日期传 calendar_locale=vn。"
    ),
)

Gender = Literal["男", "女"]
CalendarType = Literal["solar", "lunar"]
Locale = Literal["cn", "vn"]
LateZi = Literal["next_day", "same_day"]


def _payload(**fields: Any) -> dict[str, Any]:
    """去掉未提供的可选参数，经度/时区合成 location。"""
    longitude, timezone = fields.pop("longitude", None), fields.pop("timezone", None)
    payload = {key: value for key, value in fields.items() if value is not None}
    location = {key: value for key, value in (("longitude", longitude), ("timezone", timezone)) if value is not None}
    if location:
        payload["location"] = location
    return payload


def _chart(build_output: Any, payload: dict[str, Any]) -> dict[str, Any]:
    # 脚本的错误消息说明了要向用户补问什么；转成 ToolError 消息才会交给模型（SDK 对其他异常只回通用错误），与 CLI 的 error 字段一致
    try:
        return build_output(payload)
    except Exception as exc:
        raise ToolError(str(exc)) from exc


@server.tool()
def bazi_chart(
    birth_time: str,
    gender: Gender,
    calendar_type: CalendarType = "solar",
    is_leap_month: bool = False,
    late_zi_rule: LateZi = "next_day",
    query_year: int | None = None,
    true_solar_time: bool = False,
    longitude: float | None = None,
    timezone: str | None = None,
    calendar_locale: Locale = "cn",
) -> dict[str, Any]:
    """四柱八字排盘：四柱、藏干、十神、纳音、十二长生、大运，传 query_year（公历年）时附流年。

    birth_time 形如 "1990-05-15 10:00"（calendar_type=lunar 时写农历年月日）。
    true_solar_time=true 时必须给 longitude（东经为正），timezone 默认 Asia/Shanghai。
    """
    return _chart(bazi_cli.build_output, _payload(
        birth_time=birth_time, gender=gender, calendar_type=calendar_type, is_leap_month=is_leap_month,
        late_zi_rule=late_zi_rule, query_year=query_year, true_solar_time=true_solar_time,
        longitude=longitude, timezone=timezone, calendar_locale=calendar_locale,
    ))


@server.tool()
def ziwei_chart(
    birth_time: str,
    gender: Gender,
    calendar_type: CalendarType = "solar",
    is_leap_month: bool = False,
    late_zi_rule: LateZi = "next_day",
    leap_month_rule: Literal["split_15", "current", "next"] | None = None,
    sihua_rule: Literal["zuofu", "quanshu"] = "zuofu",
    query_year: int | None = None,
    true_solar_time: bool = False,
    longitude: float | None = None,
    timezone: str | None = None,
    calendar_locale: Locale = "cn",
) -> dict[str, Any]:
    """紫微斗数排盘：命宫、身宫、五行局、十二宫、主星辅星、四化、大限，传 query_year（农历年）时附流年。

    birth_time 形如 "1990-05-15 14:30"（calendar_type=lunar 时写农历年月日）。
    leap_month_rule 只对闰月出生有效，不传按 split_15。
    sihua_rule：壬干化科取左辅（zuofu，默认）或按《紫微斗數全書》取天府（quanshu）。
    """
    return _chart(ziwei_cli.build_output, _payload(
        birth_time=birth_time, gender=gender, calendar_type=calendar_type, is_leap_month=is_leap_month,
        late_zi_rule=late_zi_rule, leap_month_rule=leap_month_rule, sihua_rule=sihua_rule, query_year=query_year,
        true_solar_time=true_solar_time, longitude=longitude, timezone=timezone, calendar_locale=calendar_locale,
    ))


@server.tool()
def qimen_chart(
    question_type: str,
    question_goal: str,
    time_input: str | None = None,
    calendar_type: Literal["solar", "lunar", "now"] = "solar",
    is_leap_month: bool = False,
    timezone: str | None = None,
    true_solar_time: bool = False,
    longitude: float | None = None,
    calendar_locale: Locale = "cn",
) -> dict[str, Any]:
    """时家转盘奇门排盘（mainline-cn-v1）：阴阳遁、局数、值符值使、九宫天地盘、八门九星八神、格局。

    question_type / question_goal 是访谈确认的事项类型与想判断的事。
    time_input 形如 "2026-03-24 10:30"；calendar_type=now 时取当前时刻，可不传。
    """
    return _chart(qimen_cli.build_output, _payload(
        question_type=question_type, question_goal=question_goal, time_input=time_input,
        calendar_type=calendar_type, is_leap_month=is_leap_month, true_solar_time=true_solar_time,
        longitude=longitude, timezone=timezone, calendar_locale=calendar_locale,
    ))


@server.tool()
def numerology_chart(
    birth_date: str,
    full_name: str | None = None,
    query_year: int | None = None,
    life_path_rule: Literal["vn", "classic", "phillips"] = "vn",
    life_path_method: Literal["digits", "components"] = "digits",
    y_as_vowel: bool = True,
) -> dict[str, Any]:
    """Thần số học Pythagoras：số chủ đạo、số ngày sinh、biểu đồ ngày sinh và mũi tên、4 đỉnh cao/thử thách；
    给 full_name 时加算 số sứ mệnh / linh hồn / nhân cách / trưởng thành，给 query_year 时加算 năm cá nhân。

    birth_date 为公历 "YYYY-MM-DD"。life_path_rule：vn（2–11、22/4、33/6，越南常用）、classic（1–9 与 11/22/33）或 phillips（2–11、22/4；33 归为 6）。
    """
    return _chart(numerology_cli.build_output, _payload(
        birth_date=birth_date, full_name=full_name, query_year=query_year, life_path_rule=life_path_rule,
        life_path_method=life_path_method, y_as_vowel=y_as_vowel,
    ))


@server.tool()
def liuyao_chart(
    time: str,
    question: str | None = None,
    lines: list[int] | None = None,
    cast: bool = False,
    late_zi_rule: LateZi = "next_day",
    timezone: str | None = None,
) -> dict[str, Any]:
    """六爻纳甲排卦：本卦、变卦、八宫世应、纳甲、六亲、六神、伏神、月建日辰、旬空月破。

    lines 为自下而上六个爻值（6 老阴、7 少阳、8 少阴、9 老阳）；用户请你代摇时不传 lines，改传 cast=true。
    time 为起卦时刻（如 "2026-11-22 10:00"）或 "now"。
    """
    return _chart(liuyao_cli.build_output, _payload(
        time=time, question=question, lines=lines, cast=cast or None, late_zi_rule=late_zi_rule, timezone=timezone,
    ))


if __name__ == "__main__":
    server.run()
