"""端到端：以子进程启动 server.py，经 stdio 走真实 MCP 协议调用 tool。"""
import asyncio
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")
from mcp import Client, StdioServerParameters  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "mcp-server" / "server.py"
sys.path.insert(0, str(ROOT / "bazi" / "scripts"))
sys.path.insert(0, str(ROOT / "ziwei-doushu" / "scripts"))
sys.path.insert(0, str(ROOT / "qimen-dunjia" / "scripts"))
sys.path.insert(0, str(ROOT / "numerology" / "scripts"))
sys.path.insert(0, str(ROOT / "liuyao" / "scripts"))

import bazi_cli  # noqa: E402
import liuyao_cli  # noqa: E402
import numerology_cli  # noqa: E402
import qimen_cli  # noqa: E402
import ziwei_cli  # noqa: E402


def _run(calls):
    async def main():
        params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], cwd=str(ROOT))
        async with Client(params) as client:
            tools = await client.list_tools()
            results = [await client.call_tool(name, args) for name, args in calls]
            return tools, results
    return asyncio.run(main())


def test_tools_over_stdio():
    tools, (bazi, ziwei, qimen, no_longitude, bad_locale, bad_lunar, numerology, liuyao) = _run([
        ("bazi_chart", {"birth_time": "1990-05-15 10:00", "gender": "男", "query_year": 2026}),
        ("ziwei_chart", {"birth_time": "1985-01-25 10:00", "gender": "男", "calendar_locale": "vn"}),
        ("qimen_chart", {"question_type": "事业", "question_goal": "能否入职", "time_input": "2026-01-05 15:30",
                         "true_solar_time": True, "longitude": 87.6}),
        ("bazi_chart", {"birth_time": "1990-05-15 10:00", "gender": "男", "true_solar_time": True}),
        ("bazi_chart", {"birth_time": "1990-05-15 10:00", "gender": "男", "calendar_locale": "jp"}),
        ("bazi_chart", {"birth_time": "1990-13-01 10:00", "gender": "男", "calendar_type": "lunar"}),
        ("numerology_chart", {"birth_date": "1990-05-15", "full_name": "Nguyễn Văn An", "query_year": 2026}),
        ("liuyao_chart", {"time": "2026-11-22 10:00", "lines": [7, 8, 9, 7, 6, 8]}),
    ])
    assert sorted(t.name for t in tools.tools) == ["bazi_chart", "liuyao_chart", "numerology_chart", "qimen_chart", "ziwei_chart"]
    assert liuyao.structured_content == liuyao_cli.build_output({"time": "2026-11-22 10:00", "lines": [7, 8, 9, 7, 6, 8]})
    assert numerology.structured_content == numerology_cli.build_output(
        {"birth_date": "1990-05-15", "full_name": "Nguyễn Văn An", "query_year": 2026})

    # 结果与直接调用脚本一致
    assert not bazi.is_error
    assert bazi.structured_content == bazi_cli.build_output({"birth_time": "1990-05-15 10:00", "gender": "男", "query_year": 2026})
    assert ziwei.structured_content == ziwei_cli.build_output(
        {"birth_time": "1985-01-25 10:00", "gender": "男", "calendar_locale": "vn"})
    assert ziwei.structured_content["calendar"]["year_ganzhi"] == "乙丑"
    expected_qimen = qimen_cli.build_output({
        "question_type": "事业", "question_goal": "能否入职", "time_input": "2026-01-05 15:30",
        "calendar_type": "solar", "true_solar_time": True, "location": {"longitude": 87.6}})
    assert qimen.structured_content["chart"] == expected_qimen["chart"]

    # 脚本报错与参数校验失败都作为 tool error 返回
    assert no_longitude.is_error and "longitude" in no_longitude.content[0].text
    assert bad_locale.is_error
    # lunar_python 抛的是普通 Exception，消息也要交给模型（与 CLI 的 error 字段一致）
    assert bad_lunar.is_error and "13" in bad_lunar.content[0].text
