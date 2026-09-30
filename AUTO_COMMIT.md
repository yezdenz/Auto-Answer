# 📜 Auto-Commit Guidelines & Standards (`AUTO_COMMIT.md`)

This document defines the mandatory git commit standards and automated commit protocols for **Auto Answer**.

> [!IMPORTANT]
> **Codex & Development Agents**: All automated and manual commits in this repository must strictly adhere to these rules. No conventional commit prefixes (`feat:`, `fix:`, etc.) are permitted.

---

## 🚫 Prohibited Commit Formats (Image 1 Anti-Patterns)

The following styles are **strictly prohibited** across the entire repository:

1. **NO Conventional Commit Prefixes**:
   - ❌ `feat: initial commit - Auto Answer screen scanner...`
   - ❌ `fix(capture): attach to interactive Default desktop...`
   - ❌ `(docs) update README and troubleshooting`
   - ❌ `chore: update dependencies`
   - ❌ `refactor: clean up solver logic`

2. **NO Repetitive Blanket Commits**:
   - ❌ Staging all files together with a generic message so that every file in the GitHub file tree shows the exact same repeated text.
   - ❌ Commits containing "WIP", "Update files", "Fixes", "Changes", or "Misc".

---

## ✅ Approved Commit Formats (Image 2 Reference Standard)

All commit messages must be formatted as **clear, natural sentence explanations** of the exact capability, architecture change, or fix introduced.

### Principles:
- **Capitalized First Word**: Always start with a capital letter.
- **Descriptive Action Verb or Topic Prefix**: Use clear verbs (*Add, Implement, Configure, Fix, Optimize, Document, Scaffold, Integrate, Recalibrate, Record, Streamline*).
- **Concise & Meaningful**: State what the code actually does in plain, professional technical language.
- **No Trailing Periods** (standard git headline convention).

### Direct Examples (following reference standard):
- `Scaffold Next.js app and reshape into feature-based structure`
- `Record duplicate-identity retrospective entry; commit local changes`
- `Fix HTML entities leaking into fighter names at ingestion`
- `Add review-confidence floor to kill odds-match queue noise`
- `Attach capture thread to interactive Default desktop and add MSS fallback`
- `Calibrate Gemini multimodal solver for W3C SOAP and REST exam questions`
- `Add floating transparent HUD widget with live answer broadcast`
- `Configure global F8 hotkey listener and perceptual frame difference detector`

---

## 🎯 Per-File Distinct Descriptions Rule

In GitHub's repository view, each row displays the commit message from the **most recent commit that touched that specific file**.

To ensure that **every file row maintains a distinct, unique description**:

1. **Never commit all unrelated files in a single blanket commit.**
2. When multiple files are created or modified, stage and commit each file (or tightly coupled unit) individually with its own specific description.
3. Every file must have a description tailored to its unique role in the project.

### Example Workflow for Multi-File Changes:

```bash
# 1. Commit the capture engine
git add src/auto_answer/capture/screen.py
git commit -m "Attach capture thread to interactive Default desktop and add MSS fallback"

# 2. Commit the AI solver
git add src/auto_answer/ai/solver.py
git commit -m "Optimize Gemini solver with gemini-3.1-flash-lite and payload compression"

# 3. Commit the domain prompts
git add src/auto_answer/ai/prompts.py
git commit -m "Train solver prompts on W3C SOAP elements, REST constraints, and OAuth flows"

# 4. Commit configuration
git add config.json
git commit -m "Set default model to gemini-3.1-flash-lite and configure scan coordinates"

# 5. Push all distinct commits to remote
git push origin main
```

---

## 📂 Repository File Mapping & Approved Descriptions

When modifying or re-committing repository files, use these distinct descriptive templates:

| File / Folder | Role & Distinct Commit Description Template |
| :--- | :--- |
| `src/auto_answer/capture/screen.py` | `Attach capture thread to interactive Default desktop and add MSS fallback` |
| `src/auto_answer/capture/detector.py` | `Detect question scene transitions via grayscale perceptual frame difference` |
| `src/auto_answer/capture/hotkey.py` | `Implement low-level Win32 GetAsyncKeyState global F8 hotkey listener` |
| `src/auto_answer/capture/snipper.py` | `Build interactive translucent Tkinter canvas for drag-to-select scan area` |
| `src/auto_answer/capture/window_detector.py` | `Detect emulator HWND window bounds for BlueStacks, LDPlayer, and Nox` |
| `src/auto_answer/ai/solver.py` | `Send screen crops to Gemini Vision API with structured JSON output parsing` |
| `src/auto_answer/ai/prompts.py` | `Train reasoning prompts on W3C SOAP elements, REST constraints, and OAuth flows` |
| `src/auto_answer/ui/hud.py` | `Render transparent floating HUD overlay with live answer and confidence badges` |
| `src/auto_answer/ui/console.py` | `Format Rich terminal output with highlighted answers and radio button guides` |
| `src/auto_answer/automation/clicker.py` | `Simulate mouse clicks on calculated radio button coordinates with safety bounds` |
| `src/auto_answer/realtime.py` | `Orchestrate continuous screen capture loop with auto-diff and hotkey triggers` |
| `src/auto_answer/config.py` | `Manage Pydantic application settings, bounding boxes, and environment overrides` |
| `main.py` | `Provide unified CLI entry point supporting live, scan, snip, and hud commands` |
| `config.json` | `Configure active scan coordinates, Gemini model choice, and clicker preferences` |
| `requirements.txt` | `Define runtime dependencies for google-genai, pillow, mss, and rich` |
| `run.ps1` | `PowerShell launcher script with automatic Windows py launcher detection` |
| `run.bat` | `Windows Command Prompt batch shortcut for launching Auto Answer` |
| `.gitignore` | `Exclude Python cache, local environments, debug screenshots, and .env secrets` |
| `.gitattributes` | `Enforce consistent LF line endings and UTF-8 encoding across Windows` |
| `.env.example` | `Provide template for configuring GEMINI_API_KEY environment variable` |
| `README.md` | `Document project features, quickstart setup, architecture overview, and usage` |
| `AGENTS.md` | `Define multi-agent perception-reasoning-action architecture and state machine` |
| `ARCHITECTURE.md` | `Detail technical pipeline, sub-millisecond capture benchmarks, and data flow` |
| `TROUBLESHOOTING.md` | `Provide diagnostic solutions for black screen captures, DWM, and API keys` |
| `ROADMAP.md` | `Outline milestones for local OCR fallback, multi-screen setups, and mobile apps` |
| `SECURITY.md` | `Establish security policy, API credential handling, and vulnerability reporting` |
| `CHANGELOG.md` | `Record version history, latency optimizations, and critical bug fixes` |
| `CONTRIBUTING.md` | `Guidelines for code contributions, testing requirements, and PR workflows` |
| `LICENSE` | `Release project under standard open source MIT license permissions` |
| `tests/test_capture.py` | `Unit tests verifying screen geometry, region capture, and black-frame detection` |
| `tests/test_detector.py` | `Unit tests verifying perceptual diff calculations and baseline reset logic` |
| `tests/test_solver_schema.py` | `Unit tests verifying Pydantic JSON schema serialization for question answers` |
| `tests/test_config.py` | `Unit tests verifying bounding box calculations and config persistence` |
| `assets/samples/` | `Store high-fidelity sample quiz screenshots for offline verification` |
| `.github/` | `Configure GitHub Actions continuous integration workflows and issue templates` |

---

## 🤖 Automated Commit Helper Script (`scripts/auto_commit.py`)

An automated Python script is provided at [`scripts/auto_commit.py`](file:///c:/Users/hoody/OneDrive/Documents/Personal%20Projects/Auto%20Answer/scripts/auto_commit.py).

### How Codex or Developers Use It:
Run the script whenever changes need to be committed:

```powershell
py scripts/auto_commit.py
```

### What It Does Automatically:
1. Runs `git status --porcelain` to inspect all modified, added, or untracked files.
2. Matches each changed file against the repository knowledge mapping.
3. Stages each file individually (`git add <file>`).
4. Creates a distinct, unique sentence-style commit for that exact file.
5. Optionally pushes all commits to `origin main`.
