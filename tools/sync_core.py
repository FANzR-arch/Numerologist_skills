#!/usr/bin/env python3
"""把 core/calendar_core.py 复制到每个 skill 的 scripts/ 下。

每个 skill 目录要能单独安装运行，不能 import 仓库根目录的 core/，所以各自带一份副本。
  python tools/sync_core.py          # 重新生成副本
  python tools/sync_core.py --check  # 副本与源头不一致时退出码 1（CI 用）
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "core" / "calendar_core.py"
SKILLS = ["bazi", "qimen-dunjia", "ziwei-doushu"]
HEADER = "# 由 tools/sync_core.py 从 core/calendar_core.py 生成，勿手改。\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    expected = HEADER + SOURCE.read_text(encoding="utf-8")
    stale = []
    for skill in SKILLS:
        target = ROOT / skill / "scripts" / "calendar_core.py"
        if target.exists() and target.read_text(encoding="utf-8") == expected:
            continue
        stale.append(target.relative_to(ROOT))
        if not args.check:
            target.write_text(expected, encoding="utf-8")

    if args.check and stale:
        print("副本与 core/calendar_core.py 不一致，请运行 python tools/sync_core.py：", *stale, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
