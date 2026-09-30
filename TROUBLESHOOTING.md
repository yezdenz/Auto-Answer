# 🩺 Troubleshooting & FAQ Guide (`TROUBLESHOOTING.md`)

This guide addresses common questions, emulator quirks, and display configurations when running **Endependenz** on Windows.

---

## 🖥️ 1. Display Scaling & DPI Issues

### Symptom:
The captured region looks shifted, zoomed in, or offset from where you snipped.

### Cause:
Windows Display Scaling (e.g. 125%, 150%, or 200% on laptops or 4K monitors) causes non-DPI-aware applications to receive scaled virtual coordinates instead of physical pixel positions.

### Solution:
Endependenz includes built-in Per-Monitor DPI Awareness v2 (`ctypes.windll.shcore.SetProcessDpiAwareness(2)`).
If you encounter any offset:
1. Ensure both your primary monitor and emulator display scaling match.
2. Re-run the visual snipping tool:
   ```powershell
   .\run.ps1 snip
   ```
   The snipper automatically queries the virtual desktop geometry across all connected screens.

---

## 🎮 2. Android Emulator Quirks (BlueStacks, LDPlayer, Nox, MuMu)

### Symptom:
The captured screenshot appears black, blank, or frozen.

### Cause:
Some Android emulators use hardware-accelerated overlay modes (Vulkan or exclusive fullscreen DirectX) that bypass standard Windows desktop GDI BitBlt capture.

### Solution:
1. Open your emulator's **Settings**:
   - In **LDPlayer**: Go to *Settings -> Advanced -> Graphics Driver* -> Choose **DirectX** or **OpenGL**.
   - In **BlueStacks**: Go to *Settings -> Graphics -> Graphics Renderer* -> Select **DirectX** or **OpenGL** (Interface renderer: Auto).
2. Ensure the emulator is running in a normal **Windowed** mode (not exclusive borderless fullscreen).
3. Confirm by taking a test snip:
   ```powershell
   .\run.ps1 snip
   ```
   Check the preview image saved to `debug_output/latest_snip.png` to verify the question is clearly visible.

---

## 🔑 3. Gemini API Key & Authentication

### Symptom:
`ValueError: GEMINI_API_KEY is not set!` or `403 Forbidden: API_KEY_INVALID`.

### Solution:
1. Ensure your `.env` file exists in the root folder with:
   ```env
   GEMINI_API_KEY=AIzaSyYourActualKeyHere
   ```
2. Verify you do not have quotes or trailing spaces around the key.
3. Alternatively, set it in your current PowerShell session:
   ```powershell
   $env:GEMINI_API_KEY = "AIzaSyYourActualKeyHere"
   ```
4. Test with demo mode if you want to verify the interface without an API key:
   ```powershell
   .\run.ps1 test-sample --demo
   ```

---

## ⚡ 4. Terminal Encoding (`charmap` error)

### Symptom:
`UnicodeEncodeError: 'charmap' codec can't encode characters`.

### Solution:
Endependenz configures Python's standard output to UTF-8 automatically.
If using an older PowerShell or Command Prompt console:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

---

## 🪟 5. Floating HUD Not Visible

### Symptom:
Running `.\run.ps1 hud` opens, but the window is behind the emulator.

### Solution:
1. Check `config.json` and ensure `"hud_always_on_top": true` is set.
2. The HUD spawns at coordinates `(50, 50)` by default. You can drag it by its top header bar anywhere on any of your monitors.

