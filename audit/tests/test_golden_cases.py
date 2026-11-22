"""书中盘例金样：audit/cases/<engine>/*.json 逐个送进对应脚本，核对 expect 中的字段。"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ENGINES = {"bazi": "bazi", "liuyao": "liuyao", "numerology": "numerology", "qimen": "qimen-dunjia", "ziwei": "ziwei-doushu"}
CASES = sorted((ROOT / "audit" / "cases").glob("*/*.json"))


def _build_output(engine):
    scripts = ROOT / ENGINES[engine] / "scripts"
    sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location(f"{engine}_cli", scripts / f"{engine}_cli.py")
    module = importlib.util.module_from_spec(spec)
    # dataclass 在 3.11–3.13 需要从 sys.modules 找到所在模块
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(scripts))
    return module.build_output


def _get(output, path):
    for key in path.split("."):
        output = output[int(key)] if isinstance(output, list) else output[key]
    return output


@pytest.mark.parametrize("path", CASES, ids=lambda p: f"{p.parent.name}/{p.stem}")
def test_golden_case(path):
    case = json.loads(path.read_text(encoding="utf-8"))
    output = _build_output(path.parent.name)(case["input"])
    mismatches = {k: (v, _get(output, k)) for k, v in case["expect"].items() if _get(output, k) != v}
    assert not mismatches, f"{case['source']}: 期望 vs 实际 {mismatches}"


@pytest.mark.parametrize("engine", sorted(ENGINES))
def test_every_engine_loads(engine):
    # 有 dataclass + from __future__ import annotations 的脚本，需注册进 sys.modules 才能加载（3.11–3.13）
    assert callable(_build_output(engine))


def test_get_path():
    assert _get({"a": [{"b": 1}]}, "a.0.b") == 1
