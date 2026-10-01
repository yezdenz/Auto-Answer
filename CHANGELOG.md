# 📜 Changelog (`CHANGELOG.md`)

All notable changes to **Endependenz** will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-10-01

### Changed
- Renamed the application to Endependenz and added a paused-by-default control console with Start/Stop, Scroll/Next Page modes, and bounded local PDF references.
- Added scroll-aware visual matching so moving within the same question updates the local baseline without triggering another Gemini scan.
- Removed the unsupported `additionalProperties` keyword from the Gemini response schema, fixing HTTP 400 `INVALID_ARGUMENT` failures.
- Replaced the desktop-snapshot snipper, which could become a blocking black screen on some Windows/DWM setups, with a reliable translucent and cancellable overlay.
- Restyled the HUD as a green-and-white pixel quest log and formatted single or multi-select answers as separate labeled lines.
- Removed audible scan feedback and replaced the dim/green snipper with an outline-only, visually unchanged desktop overlay.
- Reworked the HUD with responsive sizing, clearer scan/privacy state, and non-blocking scan workers.
- Reduced live-scan latency with faster polling, shorter settling, persistent MSS capture sessions, sampled black-frame checks, and settled-frame reuse.
- Made screenshots opt-in, changed bare startup to wait for an explicit scan, and moved prompted API keys to the operating system credential vault.
- Added strict model-output, configuration, and auto-click safety validation plus secret redaction.
- Hardened the PowerShell launcher against argument injection and added package/dependency-audit metadata.

## [1.1.0] - 2026-09-30
### Added
- Real-time perceptual diff change detector for non-stop screen watching.
- Global background hotkey handler (`F8` / `Ctrl+Shift+A`).
- Comprehensive documentation suite: `AGENTS.md`, `TROUBLESHOOTING.md`, `ROADMAP.md`, `SECURITY.md`.

## [1.0.0] - 2026-09-30
### Added
- Native Windows GDI `BitBlt` capture via `ctypes` with Per-Monitor DPI Awareness v2.
- Interactive Tkinter snipping tool for 1-click region selection.
- Multimodal Gemini Vision Solver (`gemini-2.5-flash` / `gemini-3.8-flash`) with structured Pydantic schema output.
- PowerShell formatted console renderer using Rich.
- Floating always-on-top draggable HUD widget.
- Configurable mouse clicker with dry-run protection.
- Unit test suite and GitHub Actions CI workflow.
