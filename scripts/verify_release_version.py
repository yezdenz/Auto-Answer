"""Verify a release tag matches every public version declaration."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    tag = sys.argv[1] if len(sys.argv) > 1 else ""
    expected = tag.removeprefix("v")
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    package_init = Path("src/auto_answer/__init__.py").read_text(encoding="utf-8")
    project_match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    package_match = re.search(r'^__version__\s*=\s*"([^"]+)"', package_init, re.MULTILINE)
    versions = {
        "tag": expected,
        "pyproject.toml": project_match.group(1) if project_match else "<missing>",
        "auto_answer.__version__": package_match.group(1) if package_match else "<missing>",
    }
    if not expected or len(set(versions.values())) != 1:
        print("Release version mismatch:")
        for source, value in versions.items():
            print(f"- {source}: {value}")
        return 1
    print(f"Release version verified: {expected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
