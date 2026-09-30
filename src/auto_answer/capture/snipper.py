"""
Interactive screen snipping tool.
Allows the user to drag a rectangle on the screen to define the scan region.
Automatically saves the region to config.json.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional
from PIL import ImageGrab, ImageTk
from .screen import get_virtual_screen_geometry
from ..config import BoundingBox, AppConfig


class SnippingOverlay:
    """A full-screen transparent or dimmed overlay for rectangle selection."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.start_x: Optional[int] = None
        self.start_y: Optional[int] = None
        self.rect_id: Optional[int] = None
        self.selected_region: Optional[BoundingBox] = None

        # Get virtual screen metrics
        vx, vy, vw, vh = get_virtual_screen_geometry()
        self.virtual_left = vx
        self.virtual_top = vy
        self.root.geometry(f"{vw}x{vh}+{vx}+{vy}")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.config(cursor="cross")

        # Show an unchanged snapshot of the desktop. It behaves like a transparent
        # selection layer without dimming the display or risking click-through on
        # Windows color-keyed transparent pixels.
        transparent_key = "#010203"
        self.root.configure(bg=transparent_key)
        self._desktop_photo = None
        try:
            desktop = ImageGrab.grab(
                bbox=(vx, vy, vx + vw, vy + vh), all_screens=True
            )
            self._desktop_photo = ImageTk.PhotoImage(desktop)
        except Exception:
            # A color-keyed fallback still avoids the old dark overlay.
            try:
                self.root.attributes("-transparentcolor", transparent_key)
            except tk.TclError:
                pass

        self.canvas = tk.Canvas(
            self.root, cursor="cross", bg=transparent_key, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        if self._desktop_photo is not None:
            self.canvas.create_image(0, 0, image=self._desktop_photo, anchor="nw")

        # A small readable banner remains visible; the rest of the overlay is clear.
        self.canvas.create_rectangle(
            max(10, vw // 2 - 300), 20, min(vw - 10, vw // 2 + 300), 76,
            fill="#111827", outline="#60a5fa", width=1,
        )
        self.canvas.create_text(
            vw // 2,
            48,
            text="Click and drag to choose the scan area  •  Esc cancels",
            fill="#f8fafc",
            font=("Segoe UI", 13, "bold"),
        )

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Escape>", self.on_cancel)

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#60a5fa", width=3, dash=(8, 4)
        )

    def on_mouse_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)

        left = int(min(self.start_x, end_x))
        top = int(min(self.start_y, end_y))
        width = int(abs(end_x - self.start_x))
        height = int(abs(end_y - self.start_y))

        # Ignore tiny accidental clicks
        if width > 20 and height > 20:
            self.selected_region = BoundingBox(
                left=left + self.virtual_left,
                top=top + self.virtual_top,
                width=width,
                height=height,
            )

        self.root.destroy()

    def on_cancel(self, event):
        self.selected_region = None
        self.root.destroy()


def launch_snipping_tool(config_path: str = "config.json") -> Optional[BoundingBox]:
    """
    Launches the visual snipping tool, lets the user select an area,
    and updates config.json if an area was selected.
    """
    root = tk.Tk()
    app = SnippingOverlay(root)
    root.mainloop()

    if app.selected_region:
        cfg = AppConfig.load(config_path)
        cfg.scan_region = app.selected_region
        cfg.save(config_path)
        print(f"\n[✓] Region saved to {config_path}:")
        print(f"    Left: {app.selected_region.left}, Top: {app.selected_region.top}, "
              f"Width: {app.selected_region.width}, Height: {app.selected_region.height}")
        return app.selected_region
    else:
        print("\n[!] Snipping cancelled or selection too small.")
        return None
