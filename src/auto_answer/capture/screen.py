"""
Robust Windows screen capture module.
Supports MSS, 64-bit GDI BitBlt (with CAPTUREBLT), and Pillow ImageGrab with automatic fallback.
DPI-aware, supports multi-monitor setups and emulator capture.
"""

from __future__ import annotations
import sys
import os
from pathlib import Path
from typing import Tuple, Union
from PIL import Image, ImageStat
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


def ensure_default_desktop() -> bool:
    """
    Ensures the current thread is attached to the active user's interactive 'Default' desktop.
    Required on Windows when running under sandbox, background shells, or isolated desktop threads.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            # 0x01FF = MAXIMUM_ALLOWED for Desktop access rights
            hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
            if hdesk:
                return bool(user32.SetThreadDesktop(hdesk))
        except Exception:
            pass
    return True


def get_virtual_screen_geometry() -> Tuple[int, int, int, int]:
    """
    Returns (left, top, width, height) of the entire virtual desktop (all monitors).
    """
    ensure_default_desktop()
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


def _is_black_image(img: Image.Image) -> bool:
    """Detects if an image is completely black (failed DWM / GDI grab)."""
    try:
        stat = ImageStat.Stat(img)
        # If mean of all channels is near zero (< 0.5), it's an unrendered black buffer
        return all(m < 0.5 for m in stat.mean[:3])
    except Exception:
        return False


def _capture_mss(x: int, y: int, w: int, h: int) -> Image.Image:
    """Captures region using high-speed MSS (C-level Windows graphics capture)."""
    import mss
    with mss.MSS() as sct:
        monitor = {"left": x, "top": y, "width": w, "height": h}
        sct_img = sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        if _is_black_image(img):
            raise RuntimeError("MSS captured solid black pixels (unrendered surface)")
        return img


def _capture_gdi(x: int, y: int, w: int, h: int) -> Image.Image:
    """Captures region using 64-bit safe Windows GDI BitBlt with CAPTUREBLT."""
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

    # SRCCOPY (0x00CC0020) | CAPTUREBLT (0x40000000) = 0x40CC0020
    # CAPTUREBLT is mandatory for capturing layered / hardware-accelerated emulator windows
    ROP_CAPTURE = 0x40CC0020
    res = gdi32.BitBlt(hmem_dc, 0, 0, w, h, hdesktop_dc, x, y, ROP_CAPTURE)
    if not res:
        # Fallback to standard SRCCOPY
        res = gdi32.BitBlt(hmem_dc, 0, 0, w, h, hdesktop_dc, x, y, 0x00CC0020)

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

    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    if _is_black_image(img):
        raise RuntimeError("GDI BitBlt captured solid black pixels (unrendered surface)")
    return img


def _capture_imagegrab(x: int, y: int, w: int, h: int) -> Image.Image:
    """Captures region using Pillow ImageGrab."""
    from PIL import ImageGrab
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h)).convert("RGB")
    if _is_black_image(img):
        raise RuntimeError("ImageGrab captured solid black pixels")
    return img


def capture_screen_region(region: Union[BoundingBox, Tuple[int, int, int, int]]) -> Image.Image:
    """
    Captures a specific region of the screen and returns a PIL RGB Image.
    Uses multi-tiered capture with automatic fallback and black-frame detection:
    1. Fast C-level MSS with interactive desktop attachment.
    2. 64-bit Windows GDI BitBlt with CAPTUREBLT.
    3. Pillow ImageGrab.
    """
    if isinstance(region, BoundingBox):
        x, y, w, h = region.left, region.top, region.width, region.height
    else:
        x, y, w, h = region

    w = max(1, int(w))
    h = max(1, int(h))
    x = int(x)
    y = int(y)

    ensure_default_desktop()

    last_error = None

    # Tier 1: MSS (Fastest ~10ms, multi-monitor, DWM layered window support)
    try:
        return _capture_mss(x, y, w, h)
    except Exception as e:
        last_error = e

    # Tier 2: 64-bit Windows GDI BitBlt with CAPTUREBLT
    if sys.platform == "win32":
        try:
            return _capture_gdi(x, y, w, h)
        except Exception as e:
            last_error = e

    # Tier 3: Pillow ImageGrab
    try:
        return _capture_imagegrab(x, y, w, h)
    except Exception as e:
        last_error = e

    raise RuntimeError(
        f"All screen capture methods failed or returned black frames for region ({x}, {y}, {w}, {h}): {last_error}"
    )
