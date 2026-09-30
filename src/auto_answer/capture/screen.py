"""
High-performance Windows screen capture module using GDI BitBlt and ctypes.
Zero extra binary dependencies, DPI-aware, supports multi-monitor setups.
"""

from __future__ import annotations
import sys
import ctypes
from ctypes import wintypes
from typing import Tuple
from PIL import Image
from ..config import BoundingBox

# Enable Per-Monitor DPI awareness on Windows to prevent resolution scaling blur / offset
if sys.platform == "win32":
    try:
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def get_virtual_screen_geometry() -> Tuple[int, int, int, int]:
    """
    Returns (left, top, width, height) of the entire virtual desktop (all monitors).
    """
    if sys.platform == "win32":
        user32 = ctypes.windll.user32
        SM_XVIRTUALSCREEN = 76
        SM_YVIRTUALSCREEN = 77
        SM_CXVIRTUALSCREEN = 78
        SM_CYVIRTUALSCREEN = 79

        left = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        top = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)

        # Fallback if virtual metrics return 0
        if width == 0 or height == 0:
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            left = 0
            top = 0
        return left, top, width, height
    else:
        return 0, 0, 1920, 1080


def capture_screen_region(region: BoundingBox | Tuple[int, int, int, int]) -> Image.Image:
    """
    Captures a specific region of the screen and returns a PIL RGB Image.
    Region can be a BoundingBox or (left, top, width, height).
    """
    if isinstance(region, BoundingBox):
        x, y, w, h = region.left, region.top, region.width, region.height
    else:
        x, y, w, h = region

    w = max(1, int(w))
    h = max(1, int(h))
    x = int(x)
    y = int(y)

    if sys.platform != "win32":
        # Fallback for non-Windows platforms
        from PIL import ImageGrab
        return ImageGrab.grab(bbox=(x, y, x + w, y + h)).convert("RGB")

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    # Get desktop window and device context
    hdesktop = user32.GetDesktopWindow()
    hdesktop_dc = user32.GetWindowDC(hdesktop)
    
    # Create compatible memory DC and bitmap
    hmem_dc = gdi32.CreateCompatibleDC(hdesktop_dc)
    hbitmap = gdi32.CreateCompatibleBitmap(hdesktop_dc, w, h)
    h_old_bmp = gdi32.SelectObject(hmem_dc, hbitmap)

    # Perform BitBlt transfer
    SRCCOPY = 0x00CC0020
    # CAPTUREBLT includes layered / semi-transparent windows
    CAPTUREBLT = 0x40000000
    rop = SRCCOPY | CAPTUREBLT

    gdi32.BitBlt(hmem_dc, 0, 0, w, h, hdesktop_dc, x, y, rop)

    # Define BITMAPINFO structure for extracting raw DIB bits
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
    bmi.biHeight = -h  # Negative indicates top-down bitmap
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buffer_size = w * h * 4
    buf = ctypes.create_string_buffer(buffer_size)
    gdi32.GetDIBits(hmem_dc, hbitmap, 0, h, buf, ctypes.byref(bmi), 0)

    # Cleanup GDI resources
    gdi32.SelectObject(hmem_dc, h_old_bmp)
    gdi32.DeleteObject(hbitmap)
    gdi32.DeleteDC(hmem_dc)
    user32.ReleaseDC(hdesktop, hdesktop_dc)

    # Convert raw BGRA buffer to PIL RGB Image
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1)
    return img.convert("RGB")
