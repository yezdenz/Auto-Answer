#!/usr/bin/env python3
"""
Automated Git Commit Helper for Auto Answer.
Enforces Image 2 sentence-style commit messages and per-file distinct descriptions.
Strips prohibited conventional commit tags (feat:, fix:, (docs), etc.).
"""

from __future__ import annotations
import subprocess
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional

# Ensure safe console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Canonical distinct descriptions for files across the repository
FILE_DESCRIPTIONS: Dict[str, str] = {
    # Documentation
    "AUTO_COMMIT.md": "Establish automated commit protocols and per-file sentence description rules for Codex",
    "AGENTS.md": "Define autonomous agent architecture and real-time perception loop",
    "ARCHITECTURE.md": "Detail technical pipeline, sub-millisecond capture benchmarks, and data flow",
    "CHANGELOG.md": "Record version history, latency optimizations, and critical bug fixes",
    "CONTRIBUTING.md": "Guidelines for code contributions, testing requirements, and PR workflows",
    "LICENSE": "Release project under standard open source MIT license permissions",
    "README.md": "Document project features, quickstart setup, architecture overview, and usage",
    "ROADMAP.md": "Outline milestones for local OCR fallback, multi-screen setups, and mobile apps",
    "SECURITY.md": "Establish security policy, API credential handling, and vulnerability reporting",
    "TROUBLESHOOTING.md": "Provide diagnostic solutions for black screen captures, DWM, and API keys",

    # Config & Core
    "config.json": "Configure active scan coordinates, Gemini model choice, and clicker preferences",
    "requirements.txt": "Define runtime dependencies for google-genai, pillow, mss, and rich",
    ".gitignore": "Exclude Python cache, local environments, debug screenshots, and .env secrets",
    ".gitattributes": "Enforce consistent LF line endings and UTF-8 encoding across Windows",
    ".env.example": "Provide template for configuring GEMINI_API_KEY environment variable",
    "main.py": "Provide unified CLI entry point supporting live, scan, snip, and hud commands",
    "run.ps1": "PowerShell launcher script with automatic Windows py launcher detection",
    "run.bat": "Windows Command Prompt batch shortcut for launching Auto Answer",

    # Automation & Config
    "scripts/auto_commit.py": "Automate individual per-file git commits with distinct descriptive messages",
    "pyproject.toml": "Configure project metadata, build backend, and package tool definitions",
    ".github/workflows/ci.yml": "Expand GitHub Actions matrix to test across Python versions",

    # Source: Security & Config
    "src/auto_answer/security.py": "Implement secret redaction in error messages and OS credential vault integration",
    "src/auto_answer/config.py": "Manage Pydantic application settings, bounding boxes, and environment overrides",
    "src/auto_answer/realtime.py": "Orchestrate continuous screen capture loop with auto-diff and hotkey triggers",

    # Source: Capture
    "src/auto_answer/capture/screen.py": "Attach capture thread to interactive Default desktop and add MSS fallback",
    "src/auto_answer/capture/detector.py": "Detect question scene transitions via grayscale perceptual frame difference",
    "src/auto_answer/capture/hotkey.py": "Implement low-level Win32 GetAsyncKeyState global F8 hotkey listener",
    "src/auto_answer/capture/snipper.py": "Build interactive translucent Tkinter canvas for drag-to-select scan area",
    "src/auto_answer/capture/window_detector.py": "Detect emulator HWND window bounds for BlueStacks, LDPlayer, and Nox",

    # Source: AI
    "src/auto_answer/ai/solver.py": "Send screen crops to Gemini Vision API with structured JSON output parsing",
    "src/auto_answer/ai/prompts.py": "Train reasoning prompts on W3C SOAP elements, REST constraints, and OAuth flows",

    # Source: UI & Automation
    "src/auto_answer/ui/hud.py": "Render transparent floating HUD overlay with live answer and confidence badges",
    "src/auto_answer/ui/console.py": "Format Rich terminal output with highlighted answers and radio button guides",
    "src/auto_answer/ui/formatting.py": "Extract shared presentation helpers for multi-option answer line formatting",
    "src/auto_answer/ui/hud.py": "Adopt shared answer formatter and improve multi-choice display in floating HUD",
    "src/auto_answer/ui/console.py": "Integrate shared answer formatting into Rich terminal presentation",
    "src/auto_answer/automation/clicker.py": "Simulate mouse clicks on calculated radio button coordinates with safety bounds",
    "src/auto_answer/references.py": "Safe bounded local PDF reference document extraction and text caching",

    # Tests
    "tests/test_capture.py": "Unit tests verifying screen geometry, region capture, and black-frame detection",
    "tests/test_detector.py": "Unit tests verifying perceptual diff calculations and baseline reset logic",
    "tests/test_solver_schema.py": "Unit tests verifying Pydantic JSON schema serialization for question answers",
    "tests/test_config.py": "Unit tests verifying bounding box calculations and config persistence",
    "tests/test_clicker.py": "Unit tests verifying clicker safety thresholds and dry-run coordinates",
    "tests/test_realtime.py": "Unit tests verifying real-time polling state transitions and hotkey hooks",
    "tests/test_security.py": "Unit tests verifying regex secret redaction and credential vault persistence",
    "tests/test_answer_formatting.py": "Unit tests verifying multi-option answer extraction and line formatting",
    "tests/test_references.py": "Unit tests verifying bounded PDF text parsing and reference context limits",
}


def sanitize_message(msg: str) -> str:
    """Removes prohibited prefixes like feat:, fix:, (docs) and capitalizes."""
    # Remove conventional commit tags like "feat:", "fix(capture):", "(docs)", etc.
    cleaned = re.sub(r"^(feat|fix|chore|docs|refactor|test|style|perf)(\([a-zA-Z0-9_\-]+\))?:\s*", "", msg, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\((docs|feat|fix|chore)\)\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    # Capitalize the first letter
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]

    # Remove trailing dot if present
    if cleaned.endswith("."):
        cleaned = cleaned[:-1]

    return cleaned


def get_git_status() -> List[tuple[str, str]]:
    """Returns list of (status_code, file_path) from git status --porcelain."""
    res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    items = []
    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        status = line[:2].strip()
        path = line[3:].strip()
        # Handle quoted filenames
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        # Normalize slashes
        path = path.replace("\\", "/")
        items.append((status, path))
    return items


def auto_generate_description(file_path: str, custom_reason: Optional[str] = None) -> str:
    """Finds or builds an approved sentence-style commit description."""
    if custom_reason:
        return sanitize_message(custom_reason)

    if file_path in FILE_DESCRIPTIONS:
        return FILE_DESCRIPTIONS[file_path]

    # Dynamic heuristics for new files
    p = Path(file_path)
    stem = p.stem.replace("_", " ")

    if "test" in file_path:
        return f"Add unit verification test for {stem}"
    elif file_path.endswith(".md"):
        return f"Add documentation and guidelines for {stem}"
    elif "capture" in file_path:
        return f"Implement visual capture routines in {stem}"
    elif "ai" in file_path:
        return f"Enhance multimodal reasoning and parsing in {stem}"
    elif "ui" in file_path:
        return f"Update user interface components in {stem}"
    else:
        return f"Implement functionality and updates in {file_path}"


def commit_file(file_path: str, message: str) -> bool:
    """Stages a single file and commits it with the given message."""
    clean_msg = sanitize_message(message)
    print(f"\n[+] Staging: {file_path}")
    add_res = subprocess.run(["git", "add", file_path], capture_output=True, text=True)
    if add_res.returncode != 0:
        print(f"[-] Failed to stage {file_path}: {add_res.stderr}")
        return False

    print(f"[✓] Committing: \"{clean_msg}\"")
    commit_res = subprocess.run(["git", "commit", "-m", clean_msg], capture_output=True, text=True)
    if commit_res.returncode != 0:
        print(f"[-] Commit failed: {commit_res.stderr.strip()}")
        return False

    return True


def run_auto_commit(push: bool = False, custom_messages: Optional[Dict[str, str]] = None) -> None:
    """Iterates through all modified files and commits each one distinctly."""
    changes = get_git_status()
    if not changes:
        print("[i] Working tree clean. Nothing to commit.")
        return

    print(f"[*] Found {len(changes)} changed file(s). Processing per-file commits...\n")

    committed_count = 0
    for _, path in changes:
        custom_msg = (custom_messages or {}).get(path)
        desc = auto_generate_description(path, custom_reason=custom_msg)
        success = commit_file(path, desc)
        if success:
            committed_count += 1

    print(f"\n[✓] Successfully created {committed_count} distinct commit(s).")

    if push:
        print("\n[*] Pushing to origin main...")
        push_res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
        if push_res.returncode == 0:
            print("[✓] Pushed successfully to remote repository.")
        else:
            print(f"[-] Push failed: {push_res.stderr.strip()}")


if __name__ == "__main__":
    should_push = "--push" in sys.argv
    run_auto_commit(push=should_push)
