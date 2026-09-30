"""
Robust Windows screen capture module.
Supports 64-bit GDI BitBlt and Pillow ImageGrab with automatic fallback.
DPI-aware, supports multi-monitor setups and emulator capture.
"""

from __future__ import annotations
import sys
import os
from pathlib import Path
from typing import Tuple
from PIL import Image
from ..config import BoundingBox

# Enable Per-Monitor DPI awareness on Windows to prevent resolution scaling blur / offset
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def get_virtual_screen_geometry() -> Tuple[int, int, int, int]:
    """
    Returns (left, top, width, height) of the entire virtual desktop (all monitors).
    """
    if sys.platform == "win32":
        import ctypes
        user32 = ctypes.windll.user32
        SM_XVIRTUALSCREEN = 76
        SM_YVIRTUALSCREEN = 77
        SM_CXVIRTUALSCREEN = 78
        SM_CYVIRTUALSCREEN = 79

        left = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        top = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)

        if width == 0 or height == 0:
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            left = 0
            top = 0
        return left, top, width, height
    else:
        return 0, 0, 1920, 1080


def _capture_gdi(x: int, y: int, w: int, h: int) -> Image.Image:
    """Captures region using 64-bit safe Windows GDI BitBlt."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    # Set up 64-bit return and argument types to avoid pointer truncation
    user32.GetDesktopWindow.restype = wintypes.HWND
    user32.GetWindowDC.restype = wintypes.HDC
    user32.GetWindowDC.argtypes = [wintypes.HWND]

    user32.ReleaseDC.restype = wintypes.INT
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]

    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]

    gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, wintypes.INT, wintypes.INT]

    gdi32.SelectObject.restype = wintypes.HGDIOBJ
    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]

    gdi32.BitBlt.restype = wintypes.BOOL
    gdi32.BitBlt.argtypes = [
        wintypes.HDC, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.INT,
        wintypes.HDC, wintypes.INT, wintypes.INT, wintypes.DWORD
    ]

    gdi32.DeleteObject.restype = wintypes.BOOL
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]

    gdi32.DeleteDC.restype = wintypes.BOOL
    gdi32.DeleteDC.argtypes = [wintypes.HDC]

    gdi32.GetDIBits.restype = wintypes.INT
    gdi32.GetDIBits.argtypes = [
        wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
        ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT
    ]

    hdesktop = user32.GetDesktopWindow()
    hdesktop_dc = user32.GetWindowDC(hdesktop)
    hmem_dc = gdi32.CreateCompatibleDC(hdesktop_dc)
    hbitmap = gdi32.CreateCompatibleBitmap(hdesktop_dc, w, h)
    h_old_bmp = gdi32.SelectObject(hmem_dc, hbitmap)

    # SRCCOPY = 0x00CC0020
    SRCCOPY = 0x00CC0020
    gdi32.BitBlt(hmem_dc, 0, 0, w, h, hdesktop_dc, x, y, SRCCOPY)

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h  # Top-down bitmap
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hmem_dc, hbitmap, 0, h, buf, ctypes.byref(bmi), 0)

    gdi32.SelectObject(hmem_dc, h_old_bmp)
    gdi32.DeleteObject(hbitmap)
    gdi32.DeleteDC(hmem_dc)
    user32.ReleaseDC(hdesktop, hdesktop_dc)

    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1)
    return img.convert("RGB")


def _capture_imagegrab(x: int, y: int, w: int, h: int) -> Image.Image:
    """Captures region using Pillow ImageGrab."""
    from PIL import ImageGrab
    return ImageGrab.grab(bbox=(x, y, x + w, y + h)).convert("RGB")


def capture_screen_region(region: BoundingBox | Tuple[int, int, int, int]) -> Image.Image:
    """
    Captures a specific region of the screen and returns a PIL RGB Image.
    Uses robust 64-bit GDI BitBlt on Windows, with fallback to ImageGrab.
    """
    if isinstance(region, BoundingBox):
        x, y, w, h = region.left, region.top, region.width, region.height
    else:
        x, y, w, h = region

    w = max(1, int(w))
    h = max(1, int(h))
    x = int(x)
    y = int(y)

    last_error = None

    # Try method 1: 64-bit Windows GDI BitBlt (sub-millisecond, hardware-direct)
    if sys.platform == "win32":
        try:
            return _capture_gdi(x, y, w, h)
        except Exception as e:
            last_error = e

    # Try method 2: Pillow ImageGrab
    try:
        return _capture_imagegrab(x, y, w, h)
    except Exception as e:
        last_error = e

    raise RuntimeError(f"All screen capture methods failed for region ({x}, {y}, {w}, {h}): {last_error}")
