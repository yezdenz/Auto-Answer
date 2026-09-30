"""
Floating Heads-Up Display (HUD) overlay.
Provides a modern, lightweight, always-on-top window for showing live answers beside an emulator.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional, Callable
from ..ai.solver import AnswerResult
from ..config import AppConfig


class FloatingHUD:
    """Floating HUD window that stays on top and updates with live answers."""

    def __init__(self, config: AppConfig, on_scan_requested: Optional[Callable[[], None]] = None,
                 on_snip_requested: Optional[Callable[[], None]] = None):
        self.config = config
        self.on_scan = on_scan_requested
        self.on_snip = on_snip_requested

        self.root = tk.Tk()
        self.root.title("Auto Answer HUD")
        self.root.geometry("420x260+50+50")
        self.root.attributes("-alpha", config.hud_opacity)
        if config.hud_always_on_top:
            self.root.attributes("-topmost", True)

        self.root.configure(bg="#14141e")

        # Make window draggable by dragging the header
        self._drag_start_x = 0
        self._drag_start_y = 0

        self._build_ui()

    def _build_ui(self):
        # Header / Drag handle
        header = tk.Frame(self.root, bg="#1e1e2e", height=32)
        header.pack(fill="x", side="top")

        title_lbl = tk.Label(
            header, text="🎯 Auto Answer HUD",
            font=("Segoe UI", 10, "bold"), fg="#89b4fa", bg="#1e1e2e"
        )
        title_lbl.pack(side="left", padx=10, pady=4)

        header.bind("<ButtonPress-1>", self._start_drag)
        header.bind("<B1-Motion>", self._on_drag)
        title_lbl.bind("<ButtonPress-1>", self._start_drag)
        title_lbl.bind("<B1-Motion>", self._on_drag)

        # Main content container
        content = tk.Frame(self.root, bg="#14141e", padx=12, pady=8)
        content.pack(fill="both", expand=True)

        # Status badge
        self.status_lbl = tk.Label(
            content, text="Ready to scan", font=("Segoe UI", 9, "italic"),
            fg="#a6adc8", bg="#14141e", anchor="w"
        )
        self.status_lbl.pack(fill="x")

        # Answer Box (large highlight)
        self.answer_frame = tk.Frame(content, bg="#1e2538", bd=1, relief="solid")
        self.answer_frame.pack(fill="x", pady=6)

        self.choice_lbl = tk.Label(
            self.answer_frame, text="--", font=("Segoe UI", 18, "bold"),
            fg="#a6e3a1", bg="#1e2538", width=3
        )
        self.choice_lbl.pack(side="left", padx=8, pady=4)

        self.answer_text_lbl = tk.Label(
            self.answer_frame, text="Press 'Scan Now' to answer",
            font=("Segoe UI", 10, "bold"), fg="#cdd6f4", bg="#1e2538",
            wraplength=310, justify="left", anchor="w"
        )
        self.answer_text_lbl.pack(side="left", fill="x", expand=True, padx=4, pady=4)

        # Explanation Label
        self.explanation_lbl = tk.Label(
            content, text="", font=("Segoe UI", 9),
            fg="#bac2de", bg="#14141e", wraplength=390, justify="left", anchor="w"
        )
        self.explanation_lbl.pack(fill="both", expand=True, pady=4)

        # Action Buttons
        btn_bar = tk.Frame(self.root, bg="#14141e", padx=10, pady=6)
        btn_bar.pack(fill="x", side="bottom")

        if self.on_scan:
            scan_btn = tk.Button(
                btn_bar, text="⚡ Scan Now", font=("Segoe UI", 9, "bold"),
                bg="#22c55e", fg="black", activebackground="#16a34a",
                command=self.on_scan, padx=12, pady=2, relief="flat", cursor="hand2"
            )
            scan_btn.pack(side="left", padx=4)

        if self.on_snip:
            snip_btn = tk.Button(
                btn_bar, text="✂ Snip Area", font=("Segoe UI", 9),
                bg="#313244", fg="#cdd6f4", activebackground="#45475a",
                command=self.on_snip, padx=10, pady=2, relief="flat", cursor="hand2"
            )
            snip_btn.pack(side="left", padx=4)

        quit_btn = tk.Button(
            btn_bar, text="✕ Close", font=("Segoe UI", 9),
            bg="#313244", fg="#f38ba8", activebackground="#45475a",
            command=self.root.destroy, padx=8, pady=2, relief="flat", cursor="hand2"
        )
        quit_btn.pack(side="right", padx=4)

    def _start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag(self, event):
        deltax = event.x - self._drag_start_x
        deltay = event.y - self._drag_start_y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def update_result(self, result: AnswerResult):
        """Thread-safe update of the HUD UI."""
        def _update():
            if not result.is_valid_question:
                self.status_lbl.config(text="⚠️ No question detected in region", fg="#f9e2af")
                self.choice_lbl.config(text="--", fg="#6c7086")
                self.answer_text_lbl.config(text="Adjust region or ensure question is visible.")
                self.explanation_lbl.config(text="")
                return

            pct = int(result.confidence * 100)
            self.status_lbl.config(
                text=f"✓ Question Solved ({pct}% confidence)",
                fg="#a6e3a1" if pct >= 80 else "#f9e2af"
            )
            self.choice_lbl.config(text=result.correct_option_label or "✓", fg="#a6e3a1")
            self.answer_text_lbl.config(text=result.correct_answer_text or "Answer found")
            self.explanation_lbl.config(text=f"💡 {result.explanation}" if result.explanation else "")

        self.root.after(0, _update)

    def set_status(self, text: str, color: str = "#89b4fa"):
        """Update status label."""
        self.root.after(0, lambda: self.status_lbl.config(text=text, fg=color))

    def run(self):
        """Starts the Tkinter HUD mainloop."""
        self.root.mainloop()
