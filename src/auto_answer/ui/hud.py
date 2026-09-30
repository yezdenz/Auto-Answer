"""
Floating Heads-Up Display (HUD) overlay.
Provides a modern, lightweight, always-on-top window for showing live answers beside an emulator.
"""

from __future__ import annotations
import tkinter as tk
import threading
import queue
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
        self._ui_events: queue.SimpleQueue[tuple[str, object]] = queue.SimpleQueue()
        self._closed = False
        self._scan_busy = False

        self.root = tk.Tk()
        self.root.title("Auto Answer HUD")
        self.root.geometry("500x380+50+50")
        self.root.minsize(390, 300)
        self.root.resizable(True, True)
        self.root.attributes("-alpha", config.hud_opacity)
        if config.hud_always_on_top:
            self.root.attributes("-topmost", True)

        self.root.configure(bg="#14141e")

        # Make window draggable by dragging the header
        self._drag_start_x = 0
        self._drag_start_y = 0

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(40, self._drain_ui_events)

    def _build_ui(self):
        # Header / Drag handle
        header = tk.Frame(self.root, bg="#1e293b", height=40)
        header.pack(fill="x", side="top")

        title_lbl = tk.Label(
            header, text="🎯 Auto Answer HUD",
            font=("Segoe UI", 11, "bold"), fg="#93c5fd", bg="#1e293b"
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

        self.privacy_lbl = tk.Label(
            content,
            text=(
                ("Debug captures ON" if self.config.save_debug_screenshots else "Memory-only captures")
                + "  •  "
                + ("Auto-click armed" if self.config.clicker.enabled else "Auto-click off")
            ),
            font=("Segoe UI", 8), fg="#94a3b8", bg="#14141e", anchor="w",
        )
        self.privacy_lbl.pack(fill="x", pady=(2, 4))

        self.question_lbl = tk.Label(
            content, text="", font=("Segoe UI", 9), fg="#cbd5e1", bg="#14141e",
            wraplength=450, justify="left", anchor="w",
        )
        self.question_lbl.pack(fill="x", pady=(0, 4))

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
            wraplength=380, justify="left", anchor="w"
        )
        self.answer_text_lbl.pack(side="left", fill="x", expand=True, padx=4, pady=4)

        # Explanation Label
        self.explanation_lbl = tk.Label(
            content, text="", font=("Segoe UI", 9),
            fg="#bac2de", bg="#14141e", wraplength=450, justify="left", anchor="nw"
        )
        self.explanation_lbl.pack(fill="both", expand=True, pady=4)

        # Action Buttons
        btn_bar = tk.Frame(self.root, bg="#14141e", padx=10, pady=6)
        btn_bar.pack(fill="x", side="bottom")

        if self.on_scan:
            self.scan_btn = tk.Button(
                btn_bar, text="⚡ Scan Now", font=("Segoe UI", 9, "bold"),
                bg="#22c55e", fg="black", activebackground="#16a34a",
                command=self._request_scan, padx=12, pady=4, relief="flat", cursor="hand2"
            )
            self.scan_btn.pack(side="left", padx=4)
        else:
            self.scan_btn = None

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
            command=self._close, padx=8, pady=2, relief="flat", cursor="hand2"
        )
        quit_btn.pack(side="right", padx=4)

        self.root.bind("<Configure>", self._resize_text)

    def _resize_text(self, event):
        if event.widget is not self.root:
            return
        wrap = max(260, event.width - 50)
        self.question_lbl.configure(wraplength=wrap)
        self.answer_text_lbl.configure(wraplength=max(200, wrap - 75))
        self.explanation_lbl.configure(wraplength=wrap)

    def _request_scan(self):
        if self._scan_busy or not self.on_scan:
            return
        self._scan_busy = True
        if self.scan_btn:
            self.scan_btn.configure(state="disabled", text="Scanning…")
        self.set_analyzing()

        def worker():
            try:
                self.on_scan()
            except Exception as exc:
                from ..security import redact_secrets
                self.show_error(redact_secrets(exc))
            finally:
                self._ui_events.put(("scan_finished", None))

        threading.Thread(target=worker, name="auto-answer-scan", daemon=True).start()

    def _drain_ui_events(self):
        if self._closed:
            return
        while True:
            try:
                event, payload = self._ui_events.get_nowait()
            except queue.Empty:
                break
            if event == "result":
                self._apply_result(payload)
            elif event == "analyzing":
                self._apply_analyzing()
            elif event == "error":
                self._apply_error(str(payload))
            elif event == "status":
                text, color = payload
                self.status_lbl.config(text=text, fg=color)
            elif event == "scan_finished":
                self._scan_busy = False
                if self.scan_btn:
                    self.scan_btn.configure(state="normal", text="⚡ Scan Now")
        self.root.after(40, self._drain_ui_events)

    def _close(self):
        self._closed = True
        self.root.destroy()

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
        self._ui_events.put(("result", result))

    def _apply_result(self, result: AnswerResult):
        if not result.is_valid_question:
            self.status_lbl.config(text="⚠️ No question detected in region", fg="#f9e2af")
            self.question_lbl.config(text="")
            self.choice_lbl.config(text="--", fg="#6c7086")
            self.answer_text_lbl.config(text="Adjust the scan area or wait until the question is visible.")
            self.explanation_lbl.config(text="")
            return

        pct = int(result.confidence * 100)
        status_text = f"✓ Solved  •  {pct}% confidence"
        if result.is_negative_question:
            status_text += "  •  NOT / FALSE"
        self.status_lbl.config(text=status_text, fg="#a6e3a1" if pct >= 80 else "#f9e2af")
        self.question_lbl.config(text=result.question_text)
        self.choice_lbl.config(text=result.correct_option_labels or "✓", fg="#a6e3a1")
        self.answer_text_lbl.config(text=result.correct_answer_text or result.click_instruction)
        self.explanation_lbl.config(text=f"💡 {result.explanation}" if result.explanation else "")

    def set_analyzing(self):
        """Resets HUD into active scanning state so stale answers from previous questions are never shown."""
        self._ui_events.put(("analyzing", None))

    def _apply_analyzing(self):
        self.status_lbl.config(text="⏳ Capturing and analyzing…", fg="#f9e2af")
        self.question_lbl.config(text="")
        self.choice_lbl.config(text="…", fg="#f9e2af")
        self.answer_text_lbl.config(text="Working on the current question")
        self.explanation_lbl.config(text="")

    def show_error(self, message: str):
        """Display clear error notification in HUD."""
        self._ui_events.put(("error", message))

    def _apply_error(self, message: str):
        self.status_lbl.config(text="❌ Solver error", fg="#f38ba8")
        self.choice_lbl.config(text="!", fg="#f38ba8")
        self.answer_text_lbl.config(text=message[:160])
        self.explanation_lbl.config(text="Check your API key, connection, and selected scan area.")

    def set_status(self, text: str, color: str = "#89b4fa"):
        """Update status label."""
        self._ui_events.put(("status", (text, color)))

    def run(self):
        """Starts the Tkinter HUD mainloop."""
        self.root.mainloop()
