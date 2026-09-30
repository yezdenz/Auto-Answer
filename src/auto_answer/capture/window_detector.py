"""
Window detection and tracking utility using ctypes.
Helps find emulator windows (LDPlayer, BlueStacks, Nox, MuMu, etc.) and get their screen bounds.
"""

from __future__ import annotations
import sys
import ctypes
from ctypes import wintypes
from typing import List, Dict, Optional
from ..config import BoundingBox


def find_windows_by_title(keyword: str) -> List[Dict[str, any]]:
    """
    Finds all visible top-level windows whose titles match the given keyword (case-insensitive).
    Returns list of dicts with hwnd, title, and BoundingBox.
    """
    if sys.platform != "win32":
        return []

    user32 = ctypes.windll.user32
    results = []

    def enum_windows_callback(hwnd, extra):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
                if keyword.lower() in title.lower():
                    rect = wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    w = rect.right - rect.left
                    h = rect.bottom - rect.top
                    if w > 50 and h > 50:
                        results.append({
                            "hwnd": hwnd,
                            "title": title,
                            "bounds": BoundingBox(left=rect.left, top=rect.top, width=w, height=h)
                        })
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
    return results


def find_emulator_window() -> Optional[Dict[str, any]]:
    """
    Tries to find common Android emulator windows.
    """
    common_names = ["BlueStacks", "LDPlayer", "Nox", "MuMu", "MEmu", "Genymotion", "Android Emulator"]
    for name in common_names:
        matches = find_windows_by_title(name)
        if matches:
            return matches[0]
    return None
