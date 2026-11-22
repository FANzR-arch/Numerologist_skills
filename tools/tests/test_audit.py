"""tools/audit.py：登记表与代码同步、审校结论的规则、指纹变化标记 stale。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import audit

SOURCES = [
    {"id": "t1-book", "tier": "T1"},
    {"id": "t3-book", "tier": "T3"},
    {"id": "soft-a", "tier": "T4", "lineage": "same"},
    {"id": "soft-b", "tier": "T4", "lineage": "same"},
]


def _rule(verdict, sources=(), **extra):
    return {"id": "x.table.Y", "engine": "x", "verdict": verdict, "claim": "c", "notes": "", "tests": [],
            "sources": [{"id": s, "locator": "p. 1"} for s in sources], **extra}


def test_registry_matches_code():
    _, changes = audit.merge(audit.load(audit.RULES), audit.extract())
    assert {k: v for k, v in changes.items() if v} == {}, "运行 python3 tools/audit.py sync"


def test_registry_is_valid():
    sources = audit.load(audit.SOURCES)
    assert audit.validate(audit.load(audit.RULES), sources) == []
    assert audit.validate_cases(sources) == []


def test_confirmed_needs_t1_t2_and_independent_source():
    assert audit.validate([_rule("confirmed", ["t1-book", "t3-book"])], SOURCES) == []
    assert any("T1/T2" in e for e in audit.validate([_rule("confirmed", ["t3-book", "soft-a"])], SOURCES))
    assert any("独立" in e for e in audit.validate([_rule("confirmed", ["t1-book"])], SOURCES))
    # 同源软件不算两个来源
    assert any("独立" in e for e in audit.validate([_rule("variant", ["soft-a", "soft-b"])], SOURCES))


def test_structural_errors():
    errors = audit.validate([_rule("confirmed", ["missing"]), _rule("not_applicable"), _rule("maybe")], SOURCES)
    assert any("未登记" in e for e in errors)
    assert any("notes" in e for e in errors)
    assert any("verdict" in e for e in errors)
    no_locator = _rule("conflict", ["t1-book"])
    no_locator["sources"][0]["locator"] = ""
    assert any("locator" in e for e in audit.validate([no_locator], SOURCES))


def test_extracts_binop_and_annotated_tables(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    script = tmp_path / "x_cli.py"
    script.write_text("A = [1] + [2]\nB: dict = {'k': 1}\nlower = 3\n", encoding="utf-8")
    assert {u["id"] for u in audit.code_units("x", script)} == {"x.table.A", "x.table.B"}


def test_real_binop_table_registered():
    assert "ziwei.table.MAJOR_STARS" in {u["id"] for u in audit.extract()}


def test_line_shift_alone_is_not_a_change():
    unit = {"id": "x.table.Y", "engine": "x", "kind": "table", "location": "f.py:9", "fingerprint": "same"}
    merged, changes = audit.merge([{**unit, "location": "f.py:1", "verdict": "unverified"}], [unit])
    assert changes["changed"] == [] and merged[0]["location"] == "f.py:9"


def test_malformed_source_is_reported_not_crash():
    errors = audit.validate([_rule("confirmed", ["t1-book", "t3-book"])], SOURCES + [{"title": "no id"}, {"id": "no-tier"}])
    assert any("tier" in e for e in errors)


def test_changed_code_marks_audited_rule_stale():
    unit = {"id": "x.table.Y", "engine": "x", "kind": "table", "location": "f.py:1", "fingerprint": "new"}
    old = [{**unit, "fingerprint": "old", "verdict": "confirmed", "claim": "c", "sources": [], "notes": "", "tests": []}]
    merged, changes = audit.merge(old, [unit])
    assert merged[0]["stale"] and merged[0]["verdict"] == "confirmed" and changes["stale"] == ["x.table.Y"]
    merged, changes = audit.merge([{**old[0], "verdict": "unverified"}], [unit])
    assert not merged[0]["stale"] and changes["changed"] == ["x.table.Y"]
