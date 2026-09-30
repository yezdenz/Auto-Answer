# 🗺️ Product Roadmap (`ROADMAP.md`)

This roadmap outlines planned enhancements and milestones for **Auto Answer**.

---

## 📌 Phase 1: Core Engine & Multimodal Vision (Current - v1.0)
- [x] High-performance Windows GDI BitBlt screen capture.
- [x] Per-Monitor DPI Awareness v2.
- [x] Interactive visual Snipping Tool overlay (Tkinter).
- [x] Direct Google Gemini Multimodal Vision integration (`gemini-2.5-flash`).
- [x] Structured JSON schema extraction for Question, Options, Answer, and Rationale.
- [x] Rich PowerShell Terminal UI with colorization and checkmarks.
- [x] Floating, draggable always-on-top HUD overlay.
- [x] Basic mouse click automation with dry-run protection.
- [x] GitHub repository architecture and GitHub Actions CI.

---

## 📌 Phase 2: Autonomous Real-Time Engine (v1.1)
- [ ] **Continuous Perceptual Diff Engine**:
  - Automatically detect when the emulator advances to the next question using image hashing (`dHash` / structural similarity) without wasting unnecessary API quota.
- [ ] **Global Background Hotkeys**:
  - Global hotkeys (`F8` or `Ctrl+Alt+A`) to trigger instant capture even when PowerShell is minimized.
- [ ] **Audio Feedback**:
  - Optional sound chime or speech synthesis announcing the correct letter (`"Answer is A"`).

---

## 📌 Phase 3: Advanced Intelligence & Hybrid Models (v1.2)
- [ ] **Dual-Agent Verification**:
  - Multi-turn critique agent that validates tricky trick questions (e.g. "Select all that apply").
- [ ] **Local Offline Fallback**:
  - Optional integration with local Vision-Language Models (e.g., Florence-2 or Ollama LLaVA/Qwen2-VL) when offline.
- [ ] **ADB (Android Debug Bridge) Direct Integration**:
  - Send direct touch tap commands (`adb shell input tap x y`) straight to Android emulators for headless, mouse-free clicks.

