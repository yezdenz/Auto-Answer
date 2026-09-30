"""
Interactive screen snipping tool.
Allows the user to drag a rectangle on the screen to define the scan region.
Automatically saves the region to config.json.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional
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
        self.root.attributes("-alpha", 0.28)
        self.root.config(cursor="cross")

        # A real translucent overlay is more reliable than displaying a captured
        # desktop snapshot: some Windows/DWM and emulator combinations return a
        # solid-black snapshot. Keep the selection itself outline-only.
        overlay_color = "#17211a"
        self.root.configure(bg=overlay_color)

        self.canvas = tk.Canvas(
            self.root, cursor="cross", bg=overlay_color, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

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
        self.root.bind("<Button-3>", self.on_cancel)
        self.root.after_idle(self._activate_overlay)

    def _activate_overlay(self):
        """Bring the selector forward and ensure it owns pointer/key input."""
        self.root.lift()
        self.root.focus_force()
        try:
            self.root.grab_set()
        except tk.TclError:
            pass

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
        try:
            self.root.grab_release()
        except tk.TclError:
            pass
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
