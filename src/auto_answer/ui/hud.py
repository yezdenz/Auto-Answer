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
from .formatting import format_selected_answers


BG = "#061009"
PANEL = "#0b1f11"
PANEL_ALT = "#102b18"
GREEN = "#39ff88"
GREEN_DARK = "#168a49"
WHITE = "#f4fff7"
MUTED = "#9bc7a8"
ERROR = "#ff6b6b"
PIXEL_FONT = "Consolas"


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
        self.root.geometry("540x430+50+50")
        self.root.minsize(420, 340)
        self.root.resizable(True, True)
        self.root.attributes("-alpha", config.hud_opacity)
        if config.hud_always_on_top:
            self.root.attributes("-topmost", True)

        self.root.configure(bg=BG)

        # Make window draggable by dragging the header
        self._drag_start_x = 0
        self._drag_start_y = 0

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(40, self._drain_ui_events)

    def _build_ui(self):
        # Header / Drag handle
        header = tk.Frame(self.root, bg=PANEL_ALT, height=46, bd=2, relief="solid")
        header.pack(fill="x", side="top")

        title_lbl = tk.Label(
            header, text="[ QUEST LOG // AUTO ANSWER ]",
            font=(PIXEL_FONT, 12, "bold"), fg=GREEN, bg=PANEL_ALT
        )
        title_lbl.pack(side="left", padx=10, pady=4)

        header.bind("<ButtonPress-1>", self._start_drag)
        header.bind("<B1-Motion>", self._on_drag)
        title_lbl.bind("<ButtonPress-1>", self._start_drag)
        title_lbl.bind("<B1-Motion>", self._on_drag)

        # Main content container
        content = tk.Frame(self.root, bg=BG, padx=12, pady=10)
        content.pack(fill="both", expand=True)

        # Status badge
        self.status_lbl = tk.Label(
            content, text="> STATUS: READY", font=(PIXEL_FONT, 10, "bold"),
            fg=GREEN, bg=BG, anchor="w"
        )
        self.status_lbl.pack(fill="x")

        self.privacy_lbl = tk.Label(
            content,
            text=(
                ("Debug captures ON" if self.config.save_debug_screenshots else "Memory-only captures")
                + "  •  "
                + ("Auto-click armed" if self.config.clicker.enabled else "Auto-click off")
            ),
            font=(PIXEL_FONT, 8), fg=MUTED, bg=BG, anchor="w",
        )
        self.privacy_lbl.pack(fill="x", pady=(2, 4))

        self.question_lbl = tk.Label(
            content, text="", font=(PIXEL_FONT, 9, "bold"), fg=WHITE, bg=BG,
            wraplength=450, justify="left", anchor="w",
        )
        self.question_lbl.pack(fill="x", pady=(0, 4))

        # Answer Box (large highlight)
        self.answer_frame = tk.Frame(
            content, bg=PANEL, bd=3, relief="solid", highlightthickness=1,
            highlightbackground=GREEN_DARK,
        )
        self.answer_frame.pack(fill="x", pady=8)

        self.choice_lbl = tk.Label(
            self.answer_frame, text=">>", font=(PIXEL_FONT, 13, "bold"),
            fg=GREEN, bg=PANEL, width=3
        )
        self.choice_lbl.pack(side="left", padx=8, pady=4)

        self.answer_text_lbl = tk.Label(
            self.answer_frame, text="NO ACTIVE QUEST\nPRESS [SCAN] TO BEGIN",
            font=(PIXEL_FONT, 11, "bold"), fg=WHITE, bg=PANEL,
            wraplength=410, justify="left", anchor="w"
        )
        self.answer_text_lbl.pack(side="left", fill="x", expand=True, padx=4, pady=4)

        # Explanation Label
        self.explanation_lbl = tk.Label(
            content, text="", font=(PIXEL_FONT, 9),
            fg=MUTED, bg=BG, wraplength=490, justify="left", anchor="nw"
        )
        self.explanation_lbl.pack(fill="both", expand=True, pady=4)

        # Action Buttons
        btn_bar = tk.Frame(self.root, bg=BG, padx=10, pady=8)
        btn_bar.pack(fill="x", side="bottom")

        if self.on_scan:
            self.scan_btn = tk.Button(
                btn_bar, text="[ SCAN ]", font=(PIXEL_FONT, 10, "bold"),
                bg=GREEN, fg=BG, activebackground=WHITE, activeforeground=BG,
                command=self._request_scan, padx=14, pady=5, relief="raised", bd=3, cursor="hand2"
            )
            self.scan_btn.pack(side="left", padx=4)
        else:
            self.scan_btn = None

        if self.on_snip:
            snip_btn = tk.Button(
                btn_bar, text="[ SET AREA ]", font=(PIXEL_FONT, 9, "bold"),
                bg=PANEL_ALT, fg=WHITE, activebackground=GREEN_DARK, activeforeground=WHITE,
                command=self.on_snip, padx=10, pady=4, relief="raised", bd=3, cursor="hand2"
            )
            snip_btn.pack(side="left", padx=4)

        quit_btn = tk.Button(
            btn_bar, text="[ X ]", font=(PIXEL_FONT, 9, "bold"),
            bg=PANEL_ALT, fg=WHITE, activebackground=GREEN_DARK, activeforeground=WHITE,
            command=self._close, padx=8, pady=4, relief="raised", bd=3, cursor="hand2"
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
            self.scan_btn.configure(state="disabled", text="[ SCANNING... ]")
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
                    self.scan_btn.configure(state="normal", text="[ SCAN ]")
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
            self.status_lbl.config(text="> STATUS: NO QUEST DETECTED", fg=WHITE)
            self.question_lbl.config(text="")
            self.choice_lbl.config(text="--", fg=MUTED)
            self.answer_text_lbl.config(text="ADJUST THE SCAN AREA\nOR WAIT FOR A QUESTION")
            self.explanation_lbl.config(text="")
            return

        pct = int(result.confidence * 100)
        status_text = f"> STATUS: QUEST COMPLETE // {pct}% CONFIDENCE"
        if result.is_negative_question:
            status_text += " // NOT-FALSE CHECK"
        self.status_lbl.config(text=status_text, fg=GREEN if pct >= 80 else WHITE)
        self.question_lbl.config(text=f"QUEST: {result.question_text}")
        self.choice_lbl.config(text=">>", fg=GREEN)
        formatted_answers = format_selected_answers(result)
        self.answer_text_lbl.config(text=formatted_answers or result.click_instruction or "NO ANSWER")
        self.explanation_lbl.config(
            text=f"[ LOG ] {result.explanation}" if result.explanation else ""
        )

    def set_analyzing(self):
        """Resets HUD into active scanning state so stale answers from previous questions are never shown."""
        self._ui_events.put(("analyzing", None))

    def _apply_analyzing(self):
        self.status_lbl.config(text="> STATUS: ANALYZING QUEST...", fg=GREEN)
        self.question_lbl.config(text="")
        self.choice_lbl.config(text=">>", fg=GREEN)
        self.answer_text_lbl.config(text="READING QUEST DATA...")
        self.explanation_lbl.config(text="")

    def show_error(self, message: str):
        """Display clear error notification in HUD."""
        self._ui_events.put(("error", message))

    def _apply_error(self, message: str):
        self.status_lbl.config(text="> STATUS: QUEST FAILED", fg=ERROR)
        self.choice_lbl.config(text="!!", fg=ERROR)
        self.answer_text_lbl.config(text=message[:160])
        self.explanation_lbl.config(text="[ LOG ] CHECK API KEY, CONNECTION, AND SCAN AREA.")

    def set_status(self, text: str, color: str = GREEN):
        """Update status label."""
        self._ui_events.put(("status", (text, color)))

    def run(self):
        """Starts the Tkinter HUD mainloop."""
        self.root.mainloop()
