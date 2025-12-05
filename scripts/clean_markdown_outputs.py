#!/usr/bin/env python3
"""
Remove stray triple-backtick code fences from generated Markdown deliverables.

Applies to OUTPUT/*/*.md (excluding archive/examples). Safe to run repeatedly.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
EXCLUDED_DIRS = {"archive", "examples"}

CODE_FENCE_PATTERN = re.compile(r"```[a-zA-Z0-9_+-]*\s*\n(.*?)\n```", re.DOTALL)


def strip_code_fences(content: str) -> str:
    cleaned = CODE_FENCE_PATTERN.sub(r"\1\n", content)
    cleaned = cleaned.replace("```", "")
    return cleaned.strip() + "\n"


def clean_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    cleaned = strip_code_fences(original)
    if cleaned != original:
        path.write_text(cleaned, encoding="utf-8")
        return True
    return False


def main():
    if not OUTPUT_DIR.exists():
        print("No output directory found.")
        return

    changed = 0
    for project_dir in OUTPUT_DIR.iterdir():
        if not project_dir.is_dir() or project_dir.name in EXCLUDED_DIRS:
            continue
        for md_file in project_dir.glob("*.md"):
            if clean_file(md_file):
                changed += 1
                print(f"Cleaned code fences: {md_file}")
    if changed == 0:
        print("No code fences found.")
    else:
        print(f"Completed. {changed} file(s) cleaned.")


if __name__ == "__main__":
    main()
