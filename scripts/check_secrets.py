"""Fail CI when tracked files or Git history contain likely credentials.

Only filenames/pattern names are reported; matched secret values are never printed.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


PATTERNS = {
    "google_api_key": re.compile(rb"AIza[0-9A-Za-z_-]{30,}"),
    "aq_token": re.compile(rb"AQ\.[0-9A-Za-z_\\-]{35,}"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(rb"gh[pousr]_[0-9A-Za-z]{30,}"),
}
ENV_ASSIGNMENT = re.compile(
    rb"(?im)^\s*(?:GEMINI_API_KEY|GOOGLE_API_KEY)\s*=\s*([^\s#]+)"
)
SAFE_MARKERS = (b"your_", b"example", b"placeholder", b"replace_me", b"<")


def suspicious_labels(data: bytes) -> set[str]:
    labels = {name for name, pattern in PATTERNS.items() if pattern.search(data)}
    for match in ENV_ASSIGNMENT.finditer(data):
        value = match.group(1).lower()
        if not any(marker in value for marker in SAFE_MARKERS):
            labels.add("api_key_assignment")
    return labels


def tracked_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files", "-z"])
    return [Path(item.decode("utf-8")) for item in output.split(b"\0") if item]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", action="store_true")
    args = parser.parse_args()
    findings: list[tuple[str, str]] = []

    for path in tracked_files():
        try:
            data = path.read_bytes()
        except OSError:
            continue
        for label in sorted(suspicious_labels(data)):
            findings.append((str(path), label))

    if args.history:
        history = subprocess.check_output(
            ["git", "log", "-p", "--all", "--", ".", ":!assets/**"],
            stderr=subprocess.DEVNULL,
        )
        for label in sorted(suspicious_labels(history)):
            findings.append(("<git-history>", label))

    if findings:
        print("Potential credentials detected (values suppressed):")
        for location, label in findings:
            print(f"- {location}: {label}")
        return 1
    print("Secret scan passed: no likely credentials found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
