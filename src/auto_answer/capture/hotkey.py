"""
Global hotkey listener using Windows ctypes GetAsyncKeyState.
Runs in user space without requiring administrator privileges or external driver hooks.
"""

from __future__ import annotations
import sys
import time
import threading
import ctypes
from typing import Callable, Optional

# Virtual key codes
VK_F8 = 0x77
VK_F9 = 0x78
VK_F10 = 0x79


class GlobalHotkeyListener:
    """Monitors global hotkeys (e.g. F8) in a lightweight background thread."""

    def __init__(self, key_code: int = VK_F8, on_triggered: Optional[Callable[[], None]] = None):
        self.key_code = key_code
        self.on_triggered = on_triggered
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if sys.platform != "win32":
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def is_pressed(self) -> bool:
        """Checks if the key is currently pressed."""
        if sys.platform != "win32":
            return False
        user32 = ctypes.windll.user32
        # Highest bit set if key is currently down
        return bool(user32.GetAsyncKeyState(self.key_code) & 0x8000)

    def _loop(self):
        user32 = ctypes.windll.user32
        was_pressed = False

        while self._running:
            is_down = bool(user32.GetAsyncKeyState(self.key_code) & 0x8000)

            # Trigger only on key down transition (rising edge)
            if is_down and not was_pressed:
                if self.on_triggered:
                    try:
                        self.on_triggered()
                    except Exception as e:
                        print(f"[Hotkey Error]: {e}")
                time.sleep(0.2)  # Debounce

            was_pressed = is_down
            time.sleep(0.04)  # ~25Hz polling rate, negligible CPU usage

