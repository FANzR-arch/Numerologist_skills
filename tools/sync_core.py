#!/usr/bin/env python3
"""把 core/ 下的共用文件复制到每个 skill 目录。

每个 skill 目录要能单独安装运行，不能引用仓库根目录的 core/，所以各自带一份副本：
core/calendar_core.py -> <skill>/scripts/calendar_core.py
core/thuat-ngu-chung.md -> <skill>/references/thuat-ngu-chung.md
  python tools/sync_core.py          # 重新生成副本
  python tools/sync_core.py --check  # 副本与源头不一致时退出码 1（CI 用）
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHINESE_SKILLS = ["bazi", "liuyao", "qimen-dunjia", "ziwei-doushu"]
# (源文件, skill 内目标路径, 生成标记, 需要副本的 skill)
FILES = [
    ("calendar_core.py", "scripts/calendar_core.py", "# 由 tools/sync_core.py 从 core/calendar_core.py 生成，勿手改。\n", CHINESE_SKILLS + ["numerology"]),
    ("thuat-ngu-chung.md", "references/thuat-ngu-chung.md", "<!-- 由 tools/sync_core.py 从 core/thuat-ngu-chung.md 生成，勿手改。 -->\n", CHINESE_SKILLS),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    stale = []
    for source, relative, header, skills in FILES:
        expected = header + (ROOT / "core" / source).read_text(encoding="utf-8")
        for skill in skills:
            target = ROOT / skill / relative
            if target.exists() and target.read_text(encoding="utf-8") == expected:
                continue
            stale.append(target.relative_to(ROOT))
            if not args.check:
                target.write_text(expected, encoding="utf-8")

    if args.check and stale:
        print("副本与 core/ 源文件不一致，请运行 python tools/sync_core.py：", *stale, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
