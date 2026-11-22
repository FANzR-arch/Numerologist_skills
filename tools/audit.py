#!/usr/bin/env python3
"""按文献审校的规则登记表（audit/rules.json）的同步与检查。

  python3 tools/audit.py sync    # 从代码与文档重新抽取审校单元，合并进 audit/rules.json
  python3 tools/audit.py check   # CI：登记表与代码一致、结构合法；打印各体系覆盖率

审校单元由代码自动抽取，不手工罗列：
  table    模块级大写常量（规则表）
  function 顶层函数（算法规则；纯解析类可标 not_applicable）
  ruleset  输出 ruleset 字典里的每一项口径说明
  doc      SKILL.md 与 references/*.md（解读内容）
每个单元带内容指纹；已审校的单元内容变化后标记 stale，需要重新审校。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = ROOT / "audit" / "rules.json"
CASES = ROOT / "audit" / "cases"
SOURCES = ROOT / "audit" / "sources.json"
ENGINES = {"bazi": "bazi", "liuyao": "liuyao", "numerology": "numerology", "qimen": "qimen-dunjia", "ziwei": "ziwei-doushu"}
VERDICTS = {"unverified", "confirmed", "variant", "conflict", "not_applicable"}
AUDITED = {"confirmed", "variant", "conflict"}
TIERS = {"T1", "T2", "T3", "T4"}
HUMAN_FIELDS = ("claim", "sources", "verdict", "notes", "tests")


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def code_units(engine: str, path: Path) -> list[dict]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    rel = path.relative_to(ROOT).as_posix()
    units = []
    for node in tree.body:
        target = node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else getattr(node, "target", None)
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(target, ast.Name) and target.id.isupper():
            units.append({"id": f"{engine}.table.{target.id}", "kind": "table", "node": node})
        elif isinstance(node, ast.FunctionDef) and node.name != "main":
            units.append({"id": f"{engine}.function.{node.name}", "kind": "function", "node": node})
        elif isinstance(node, ast.ClassDef):
            units.append({"id": f"{engine}.function.{node.name}", "kind": "function", "node": node})
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == "ruleset" and isinstance(value, ast.Dict):
                    for k, v in zip(value.keys, value.values):
                        if isinstance(k, ast.Constant) and k.value not in ("id", "name", "source"):
                            units.append({"id": f"{engine}.ruleset.{k.value}", "kind": "ruleset", "node": v})
    merged: dict[str, dict] = {}
    for u in units:
        segment = ast.get_source_segment(source, u["node"]) or ""
        if u["id"] in merged:  # 同名常量多次赋值（如先写原表再变换）：合成一个单元
            merged[u["id"]]["text"] += "\n" + segment
            continue
        merged[u["id"]] = {"id": u["id"], "engine": engine, "kind": u["kind"], "location": f"{rel}:{u['node'].lineno}", "text": segment}
    return [{**{k: v for k, v in m.items() if k != "text"}, "fingerprint": fingerprint(m["text"])} for m in merged.values()]


def doc_units(engine: str, skill_dir: Path) -> list[dict]:
    files = [skill_dir / "SKILL.md", *sorted((skill_dir / "references").glob("*.md"))]
    units = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        if f.name == "thuat-ngu-chung.md":
            continue  # 生成副本，源头在 core/
        units.append({"id": f"{engine}.doc.{f.name}", "engine": engine, "kind": "doc",
                      "location": f.relative_to(ROOT).as_posix(), "fingerprint": fingerprint(text)})
    return units


def extract() -> list[dict]:
    units = code_units("core", ROOT / "core" / "calendar_core.py")
    glossary = ROOT / "core" / "thuat-ngu-chung.md"
    units.append({"id": "core.doc.thuat-ngu-chung.md", "engine": "core", "kind": "doc",
                  "location": "core/thuat-ngu-chung.md", "fingerprint": fingerprint(glossary.read_text(encoding="utf-8"))})
    for engine, folder in ENGINES.items():
        units += code_units(engine, ROOT / folder / "scripts" / f"{engine}_cli.py")
        units += doc_units(engine, ROOT / folder)
    ids = [u["id"] for u in units]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise SystemExit(f"审校单元 id 重复：{sorted(duplicates)}")
    return units


def merge(existing: list[dict], current: list[dict]) -> tuple[list[dict], dict[str, list[str]]]:
    old = {r["id"]: r for r in existing}
    merged, changes = [], {"added": [], "removed": [], "changed": [], "stale": []}
    for unit in current:
        record = {**unit, "claim": "", "sources": [], "verdict": "unverified", "notes": "", "tests": [], "stale": False}
        prev = old.get(unit["id"])
        if prev is None:
            changes["added"].append(unit["id"])
        else:
            record.update({k: prev[k] for k in HUMAN_FIELDS if k in prev})
            record["stale"] = prev.get("stale", False)
            if prev.get("fingerprint") != unit["fingerprint"]:  # 只挪行号不算变化，sync 时顺带更新 location
                changes["changed"].append(unit["id"])
            if prev.get("fingerprint") != unit["fingerprint"] and record["verdict"] in AUDITED:
                record["stale"] = True
                changes["stale"].append(unit["id"])
        merged.append(record)
    changes["removed"] = sorted(set(old) - {u["id"] for u in current})
    return merged, changes


def validate(rules: list[dict], sources: list[dict]) -> list[str]:
    errors = []
    for s in sources:
        if not s.get("id"):
            errors.append(f"source {s.get('title')}: 缺 id")
        if s.get("tier") not in TIERS:
            errors.append(f"source {s.get('id')}: tier 必须是 {sorted(TIERS)}")
    by_id = {s["id"]: s for s in sources if s.get("id") and s.get("tier") in TIERS}
    for r in rules:
        rid = r["id"]
        if r.get("verdict") not in VERDICTS:
            errors.append(f"{rid}: verdict 必须是 {sorted(VERDICTS)}")
            continue
        cited = r.get("sources") or []
        for c in cited:
            if c.get("id") not in by_id:
                errors.append(f"{rid}: 未登记的来源 {c.get('id')}")
            if not c.get("locator"):
                errors.append(f"{rid}: 来源 {c.get('id')} 缺 locator（卷/页）")
        if r["verdict"] in AUDITED and not r.get("claim"):
            errors.append(f"{rid}: {r['verdict']} 需要写 claim")
        if r["verdict"] in ("confirmed", "variant"):
            known = [by_id[c["id"]] for c in cited if c.get("id") in by_id]
            if not any(s["tier"] in ("T1", "T2") for s in known):
                errors.append(f"{rid}: {r['verdict']} 至少需要一个 T1/T2 来源")
            lineages = {s.get("lineage") or s["id"] for s in known}
            if len(lineages) < 2:
                errors.append(f"{rid}: {r['verdict']} 需要两个相互独立的来源（lineage 不同）")
        if r["verdict"] == "not_applicable" and not r.get("notes"):
            errors.append(f"{rid}: not_applicable 需要在 notes 说明理由")
        for test in r.get("tests") or []:
            if not (ROOT / test.split("::")[0]).exists():
                errors.append(f"{rid}: 测试文件不存在 {test}")
    return errors


def validate_cases(sources: list[dict]) -> list[str]:
    errors = []
    by_id = {s["id"]: s for s in sources if s.get("id")}
    for path in sorted(CASES.glob("*/*.json")):
        name = path.relative_to(ROOT).as_posix()
        case = json.loads(path.read_text(encoding="utf-8"))
        if path.parent.name not in ENGINES:
            errors.append(f"{name}: 目录名必须是 {sorted(ENGINES)}")
        source = case.get("source") or {}
        if source.get("id") not in by_id or not source.get("locator"):
            errors.append(f"{name}: source 需要已登记的 id 和 locator（书中盘例的出处）")
        if not isinstance(case.get("input"), dict) or not case.get("expect"):
            errors.append(f"{name}: 需要 input（对象）与 expect（字段路径 → 期望值）")
    return errors


def coverage(rules: list[dict]) -> str:
    engines = sorted({r["engine"] for r in rules})
    header = ["engine", "units", *sorted(VERDICTS), "stale"]
    rows = []
    for engine in engines:
        rs = [r for r in rules if r["engine"] == engine]
        rows.append([engine, str(len(rs)), *[str(sum(r["verdict"] == v for r in rs)) for v in sorted(VERDICTS)],
                     str(sum(bool(r.get("stale")) for r in rs))])
    widths = [max(len(x) for x in col) for col in zip(header, *rows)]
    return "\n".join("  ".join(x.ljust(w) for x, w in zip(line, widths)) for line in [header, *rows])


def load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def dump(path: Path, data: list[dict]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["sync", "check"])
    args = parser.parse_args()

    merged, changes = merge(load(RULES), extract())
    if args.command == "sync":
        dump(RULES, merged)
        for kind, ids in changes.items():
            if ids:
                print(f"{kind}: {len(ids)}", *ids, sep="\n  ")
        return 0

    problems = []
    for kind in ("added", "removed", "changed"):
        if changes[kind]:
            problems.append(f"登记表未同步（{kind}）：{', '.join(changes[kind][:10])} … 请运行 python3 tools/audit.py sync")
    rules = load(RULES)
    problems += validate(rules, load(SOURCES)) + validate_cases(load(SOURCES))
    print(coverage(rules))
    # 已审校规则的代码变了只提示，不让 CI 失败：先同步，再安排重新审校
    for r in rules:
        if r.get("stale"):
            print("⚠ 需要重新审校：", r["id"])
    for p in problems:
        print("✗", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
