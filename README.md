# 🎯 Auto Answer

> An automated screen scanner and AI question solver designed for Android emulators (LDPlayer, BlueStacks, Nox, MuMu) and desktop quizzes. Powered by Google Gemini multimodal vision.

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20PowerShell-0078D6.svg)](https://microsoft.com)

---

## 🌟 Key Features

- **✂ Clear Visual Snipping Tool**: Select a scan region without dimming or tinting the screen; only a blue outline is drawn.
- **🧠 Direct Multimodal Vision AI**: Uses Google Gemini (`gemini-2.5-flash` or `gemini-3.8-flash`) to analyze questions and options straight from pixels. No brittle OCR errors, handles complex wording, code snippets, and diagrams effortlessly.
- **🖥️ Beautiful PowerShell Console**: Renders colorized questions, checkmarked options `[✓]`, highlighted answers, confidence scores, and concise explanations directly in your terminal.
- **🪟 Floating HUD Overlay**: An always-on-top, semi-transparent HUD window you can place right next to your emulator for instant answers without switching windows.
- **🎮 Emulator Detection**: Detects common Android emulator windows (BlueStacks, LDPlayer, Nox, MuMu) to help coordinate setup.
- **⚡ Zero Extra Drivers or C++ Compilers**: High-speed Windows GDI BitBlt screen capture implemented natively with ctypes and Pillow.
- **🛡️ Guarded Auto-Clicker**: Disabled by default, dry-run by default, and blocked for low-confidence, invalid, out-of-range, or multi-select results unless explicitly allowed.
- **🔒 Privacy-Safe Defaults**: No scan sound, no screenshot retention, and no capture/upload until the user explicitly requests a scan.

---

## 📸 Preview

```
┌─────────────────────── 📝 Detected Question (0.81s) ────────────────────────┐
│ What is the meaning of the term flow as it relates to the OAuth 2.0         │
│ authorization framework?                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

   ✓     [A]      It is a process for an API user to obtain an access token
                  from the authorization server.
   ○     [B]      It is the sequence of data exchanged between a REST API
                  request and a response.
   ○     [C]      It is a process for an API request to send authentication
                  credentials to a web service.
   ○     [D]      It is the number of requests contained in the token bucket.

┌──────────────────────── ✅ SOLVED | 99% confidence ─────────────────────────┐
│ 🎯 Best Answer: (A) It is a process for an API user to obtain an access     │
│ token from the authorization server.                                        │
│                                                                             │
│ 💡 Explanation: In OAuth 2.0, an authorization 'flow' (or grant type)       │
│ specifies the exact process through which a client application secures an   │
│ access token from the authorization server.                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart in PowerShell

### 1. Clone the Repository
```powershell
git clone https://github.com/your-username/Auto-Answer.git
cd "Auto Answer"
```

### 2. Install Dependencies
```powershell
py -3 -m pip install -r requirements.txt
```

### 3. Configure Your Gemini API Key
For development, create a `.env` file in the project folder (or copy from `.env.example`):
```powershell
Copy-Item .env.example .env
```
Open `.env` and add your free Gemini API key:
```env
GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
```
> 💡 *Don't have an API key? Get one for free at [Google AI Studio](https://aistudio.google.com/app/apikey).*

If no key is configured, the app prompts with masked input and stores the key in the operating system credential vault. This is recommended for distributed builds; `.env` remains a plaintext development option.

---

## 🎯 How to Use

### Step 1: Select Your Emulator Region
Launch the interactive snipping tool and drag a rectangle over the question area in your emulator:
```powershell
.\run.ps1 snip
# Or: py main.py snip
```
*Your selected coordinates will be automatically saved to `config.json`.*

### Step 2: Run Auto Answer

You can run in whichever mode best suits your workflow:

#### Option A: Interactive Watch Mode (Recommended)
Keeps running in your PowerShell window. Whenever a new question appears on screen, press **Enter** to instantly solve it:
```powershell
.\run.ps1
# Or: py main.py watch
```
- Press **[Enter]**: Scan the region and solve the question
- Press **[s]**: Re-snip a new area on the fly
- Press **[q]**: Quit

#### Option B: Floating HUD Mode
Launches a sleek floating window that stays on top next to your emulator:
```powershell
.\run.ps1 hud
# Or: py main.py hud
```
Click **"⚡ Scan Now"** whenever a question appears.

#### Option C: Automatic Timer Mode
Continuously monitors the region and solves every few seconds:
```powershell
.\run.ps1 watch --auto
# Or: py main.py watch --auto
```

#### Option D: Test with Sample Question (Demo Mode)
Verify the display and layout right away without consuming any API quota:
```powershell
.\run.ps1 test-sample --demo
```

---

## ⚙️ Configuration (`config.json`)

The `config.json` file allows fine-tuning application behavior:

```json
{
  "scan_region": {
    "left": 100,
    "top": 100,
    "width": 800,
    "height": 600
  },
  "model": "gemini-2.5-flash",
  "auto_mode_interval_sec": 2.0,
  "poll_interval_sec": 0.25,
  "settle_delay_sec": 0.18,
  "change_threshold": 4.5,
  "save_debug_screenshots": false,
  "debug_dir": "debug_output",
  "hud_opacity": 0.96,
  "hud_always_on_top": true,
  "clicker": {
    "enabled": false,
    "dry_run": true,
    "delay_sec": 1.0,
    "min_confidence": 0.9,
    "allow_multi_select": false
  }
}
```

### Configuration Options
| Setting | Description |
|---|---|
| `scan_region` | Coordinates `(left, top, width, height)` of the screen area to capture. |
| `model` | Gemini model name (default: `gemini-2.5-flash` or `gemini-3.8-flash`). |
| `auto_mode_interval_sec` | Pause duration between scans in `--auto` mode. |
| `poll_interval_sec` | Real-time change-detection interval; lower values react faster but use more CPU. |
| `settle_delay_sec` | Brief pause for screen animations before a changed frame is analyzed. |
| `change_threshold` | Sensitivity of real-time visual change detection. |
| `save_debug_screenshots` | Opt-in local screenshot retention for troubleshooting. Keep off for privacy. |
| `hud_opacity` | Window opacity of the floating HUD (0.1 to 1.0). |
| `hud_always_on_top` | Keeps the HUD window floating above all other windows. |
| `clicker.enabled` | Whether to automatically click the estimated radio button. |
| `clicker.dry_run` | Prints simulated click coordinates without moving the mouse. |
| `clicker.min_confidence` | Minimum model confidence required before automation is permitted. |
| `clicker.allow_multi_select` | Allows multi-select automation when explicitly enabled. |

## 🔐 Privacy and Safe Use

- A normal launch waits for a command and does not capture the screen automatically.
- Screenshots are processed in memory unless `save_debug_screenshots` is explicitly enabled.
- A requested scan sends the selected image region to the configured Google Gemini API over HTTPS. Do not include passwords, personal messages, or unrelated private data in the region.
- Keep auto-click disabled unless you have tested the selected region and understand the result-confidence limits. The application is intended for authorized study, accessibility, and testing workflows; follow the rules of the system you use it with.
- Before distributing a build, rotate any development API key, run the test suite and dependency audit, and sign published installers/artifacts.

---

## 🛠️ Project Structure

```
Auto Answer/
├── assets/
│   └── samples/
│       └── sample_question.png      # Test sample question image
├── src/
│   └── auto_answer/
│       ├── __init__.py
│       ├── config.py                # Pydantic configuration & .env loader
│       ├── capture/
│       │   ├── screen.py            # Windows GDI BitBlt screen capture
│       │   ├── snipper.py           # Interactive Tkinter snipping overlay
│       │   └── window_detector.py   # Windows API emulator detector
│       ├── ai/
│       │   ├── solver.py            # Multimodal Gemini vision solver
│       │   └── prompts.py           # Specialized exam & quiz prompts
│       ├── ui/
│       │   ├── console.py           # PowerShell Rich console renderer
│       │   └── hud.py               # Tkinter floating HUD overlay
│       └── automation/
│           └── clicker.py           # Windows mouse automation (ctypes)
├── tests/
│   ├── test_capture.py              # Capture & screen geometry tests
│   ├── test_config.py               # Config & BoundingBox math tests
│   └── test_solver_schema.py        # Pydantic schema validation tests
├── main.py                          # CLI entry point
├── run.ps1                          # PowerShell launcher script
├── run.bat                          # Windows batch launcher
├── config.json                      # Application settings
├── .env.example                     # Environment variables template
├── ARCHITECTURE.md                  # Comprehensive architectural overview
└── requirements.txt                 # Project dependencies
```

---

## 🧪 Running Tests

Run the test suite at any time using standard `unittest`:
```powershell
py -3 -m unittest discover tests
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
