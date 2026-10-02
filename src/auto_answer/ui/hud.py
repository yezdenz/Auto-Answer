"""Pixel-style floating control panel for Endependenz."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import filedialog
from typing import Callable, Optional

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
    """Always-on-top HUD with explicit run, mode, region, and reference controls."""

    def __init__(
        self,
        config: AppConfig,
        on_scan_requested: Optional[Callable[[], None]] = None,
        on_snip_requested: Optional[Callable[[], None]] = None,
        on_start_requested: Optional[Callable[[], None]] = None,
        on_stop_requested: Optional[Callable[[], None]] = None,
        on_mode_changed: Optional[Callable[[str], None]] = None,
        on_pdf_requested: Optional[Callable[[tuple[str, ...]], object]] = None,
    ):
        self.config = config
        self.on_scan = on_scan_requested
        self.on_snip = on_snip_requested
        self.on_start = on_start_requested
        self.on_stop = on_stop_requested
        self.on_mode_changed = on_mode_changed
        self.on_pdf = on_pdf_requested
        self._ui_events: queue.SimpleQueue[tuple[str, object]] = queue.SimpleQueue()
        self._closed = False
        self._scan_busy = False
        self._running = False
        self._last_result: Optional[AnswerResult] = None
        self._mode = config.scan_mode

        self.root = tk.Tk()
        self.root.title("Endependenz")
        self.root.geometry("610x540+50+50")
        self.root.minsize(500, 430)
        self.root.resizable(True, True)
        self.root.attributes("-alpha", config.hud_opacity)
        if config.hud_always_on_top:
            self.root.attributes("-topmost", True)
        self.root.configure(bg=BG)

        self._drag_start_x = 0
        self._drag_start_y = 0
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.bind("<Escape>", lambda event: self._request_stop())
        self.root.after(40, self._drain_ui_events)

    def _pixel_button(self, parent, text, command, primary: bool = False):
        return tk.Button(
            parent, text=text, font=(PIXEL_FONT, 9, "bold"),
            bg=GREEN if primary else PANEL_ALT,
            fg=BG if primary else WHITE,
            activebackground=WHITE if primary else GREEN_DARK,
            activeforeground=BG if primary else WHITE,
            command=command, padx=10, pady=4, relief="raised", bd=3,
            cursor="hand2", disabledforeground=MUTED,
        )

    def _build_ui(self):
        header = tk.Frame(self.root, bg=PANEL_ALT, height=46, bd=2, relief="solid")
        header.pack(fill="x", side="top")
        title = tk.Label(
            header, text="[ ENDEPENDENZ // QUEST CONSOLE ]",
            font=(PIXEL_FONT, 12, "bold"), fg=GREEN, bg=PANEL_ALT,
        )
        title.pack(side="left", padx=10, pady=6)
        for widget in (header, title):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)

        content = tk.Frame(self.root, bg=BG, padx=12, pady=10)
        content.pack(fill="both", expand=True)
        self.status_lbl = tk.Label(
            content, text="> STATUS: PAUSED", font=(PIXEL_FONT, 10, "bold"),
            fg=MUTED, bg=BG, anchor="w",
        )
        self.status_lbl.pack(fill="x")
        privacy_text = (
            ("Debug captures ON" if self.config.save_debug_screenshots else "Memory-only captures")
            + "  //  "
            + ("Auto-click armed" if self.config.clicker.enabled else "Auto-click off")
        )
        self.privacy_lbl = tk.Label(
            content, text=privacy_text, font=(PIXEL_FONT, 8),
            fg=MUTED, bg=BG, anchor="w",
        )
        self.privacy_lbl.pack(fill="x", pady=(2, 5))

        mode_bar = tk.Frame(content, bg=BG)
        mode_bar.pack(fill="x", pady=(4, 5))
        tk.Label(
            mode_bar, text="MODE:", font=(PIXEL_FONT, 9, "bold"), fg=WHITE, bg=BG,
        ).pack(side="left", padx=(0, 6))
        self.scroll_mode_btn = self._pixel_button(
            mode_bar, "[ SCROLL ]", lambda: self._select_mode("scroll")
        )
        self.scroll_mode_btn.pack(side="left", padx=3)
        self.next_mode_btn = self._pixel_button(
            mode_bar, "[ NEXT PAGE ]", lambda: self._select_mode("next_page")
        )
        self.next_mode_btn.pack(side="left", padx=3)

        self.mode_hint_lbl = tk.Label(
            content, text="", font=(PIXEL_FONT, 8), fg=MUTED, bg=BG, anchor="w",
        )
        self.mode_hint_lbl.pack(fill="x", pady=(0, 4))

        self.reference_lbl = tk.Label(
            content, text="REFERENCE: NONE", font=(PIXEL_FONT, 8),
            fg=MUTED, bg=BG, anchor="w",
        )
        self.reference_lbl.pack(fill="x", pady=(0, 6))
        self.question_lbl = tk.Label(
            content, text="", font=(PIXEL_FONT, 9, "bold"), fg=WHITE, bg=BG,
            wraplength=550, justify="left", anchor="w",
        )
        self.question_lbl.pack(fill="x", pady=(0, 4))

        self.answer_frame = tk.Frame(
            content, bg=PANEL, bd=3, relief="solid", highlightthickness=1,
            highlightbackground=GREEN_DARK,
        )
        self.answer_frame.pack(fill="x", pady=8)
        self.choice_lbl = tk.Label(
            self.answer_frame, text=">>", font=(PIXEL_FONT, 13, "bold"),
            fg=GREEN, bg=PANEL, width=3,
        )
        self.choice_lbl.pack(side="left", padx=8, pady=6)
        self.answer_text_lbl = tk.Label(
            self.answer_frame, text="SYSTEM PAUSED\nPRESS [ START ] TO MONITOR",
            font=(PIXEL_FONT, 11, "bold"), fg=WHITE, bg=PANEL,
            wraplength=460, justify="left", anchor="w",
        )
        self.answer_text_lbl.pack(side="left", fill="x", expand=True, padx=4, pady=6)
        self.explanation_lbl = tk.Label(
            content, text="", font=(PIXEL_FONT, 9), fg=MUTED, bg=BG,
            wraplength=550, justify="left", anchor="nw",
        )
        self.explanation_lbl.pack(fill="both", expand=True, pady=4)

        tool_bar = tk.Frame(self.root, bg=BG, padx=10, pady=7)
        tool_bar.pack(fill="x", side="bottom")
        self.scan_btn = self._pixel_button(tool_bar, "[ SCAN ]", self._request_scan, primary=True)
        self.scan_btn.pack(side="left", padx=4)
        self.scan_btn.configure(state="disabled")
        if self.on_snip:
            self._pixel_button(tool_bar, "[ SET AREA ]", self.on_snip).pack(side="left", padx=4)
        self.pdf_btn = self._pixel_button(tool_bar, "[ PDF REFERENCE ]", self._choose_pdfs)
        self.pdf_btn.pack(side="left", padx=4)
        self.clear_pdf_btn = self._pixel_button(tool_bar, "[ CLEAR PDF ]", self._clear_pdfs)
        self.clear_pdf_btn.pack(side="left", padx=4)
        self._pixel_button(tool_bar, "[ X ]", self._close).pack(side="right", padx=4)

        run_bar = tk.Frame(self.root, bg=PANEL_ALT, padx=10, pady=7, bd=2, relief="solid")
        run_bar.pack(fill="x", side="bottom")
        self.start_btn = self._pixel_button(run_bar, "[ START ]", self._request_start, primary=True)
        self.start_btn.pack(side="left", padx=4)
        self.stop_btn = self._pixel_button(run_bar, "[ STOP / ESC ]", self._request_stop)
        self.stop_btn.pack(side="left", padx=4)
        self.stop_btn.configure(state="disabled")
        self.run_state_lbl = tk.Label(
            run_bar, text="MONITOR: OFFLINE", font=(PIXEL_FONT, 9, "bold"),
            fg=MUTED, bg=PANEL_ALT,
        )
        self.run_state_lbl.pack(side="right", padx=6)

        self.root.bind("<Configure>", self._resize_text)
        self._apply_mode_style()

    def _resize_text(self, event):
        if event.widget is not self.root:
            return
        wrap = max(330, event.width - 60)
        self.question_lbl.configure(wraplength=wrap)
        self.answer_text_lbl.configure(wraplength=max(250, wrap - 80))
        self.explanation_lbl.configure(wraplength=wrap)

    def _request_start(self):
        if self._running or not self.on_start:
            return
        self.on_start()
        self._apply_running(True)

    def _request_stop(self):
        if not self._running:
            return
        if self.on_stop:
            self.on_stop()
        self._apply_running(False)

    def set_running(self, running: bool):
        self._ui_events.put(("running", running))

    def update_reference(self, result) -> None:
        self._ui_events.put(("reference", result))

    def _apply_running(self, running: bool):
        self._running = running
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")
        self.scan_btn.configure(state="normal" if running else "disabled")
        self.run_state_lbl.configure(
            text="MONITOR: ONLINE" if running else "MONITOR: OFFLINE",
            fg=GREEN if running else MUTED,
        )
        if not self._scan_busy:
            self.status_lbl.configure(
                text="> STATUS: MONITORING" if running else "> STATUS: PAUSED",
                fg=GREEN if running else MUTED,
            )
        if not running:
            if self._last_result is not None:
                self._apply_result(self._last_result)
            else:
                self.status_lbl.configure(text="> STATUS: PAUSED", fg=MUTED)
                self.answer_text_lbl.configure(text="SYSTEM PAUSED\nPRESS [ START ] TO MONITOR")

    def _select_mode(self, mode: str):
        if mode == self._mode:
            return
        self._mode = mode
        self.config.scan_mode = mode
        self._apply_mode_style()
        if self.on_mode_changed:
            self.on_mode_changed(mode)

    def _apply_mode_style(self):
        for mode, button in (
            ("scroll", self.scroll_mode_btn), ("next_page", self.next_mode_btn)
        ):
            active = mode == self._mode
            button.configure(bg=GREEN if active else PANEL_ALT, fg=BG if active else WHITE)
        self.mode_hint_lbl.configure(
            text=(
                "SCROLL: REFRESH ON VIEWPORT MOVEMENT"
                if self._mode == "scroll"
                else "NEXT PAGE: IGNORE SCROLLS WITHIN THE SAME QUESTION"
            )
        )

    def _choose_pdfs(self):
        if not self.on_pdf:
            return
        paths = filedialog.askopenfilenames(
            parent=self.root, title="Choose PDF reference material",
            filetypes=(("PDF documents", "*.pdf"),),
        )
        if not paths:
            return
        self.pdf_btn.configure(state="disabled", text="[ LOADING PDF... ]")
        self.reference_lbl.configure(text="REFERENCE: LOADING...", fg=GREEN)

        def worker():
            try:
                result = self.on_pdf(tuple(paths))
                self._ui_events.put(("reference", result))
            except Exception as exc:
                from ..security import redact_secrets
                self._ui_events.put(("reference_error", redact_secrets(exc)))

        threading.Thread(target=worker, name="endependenz-pdf", daemon=True).start()

    def _clear_pdfs(self):
        if not self.on_pdf:
            return

        def worker():
            try:
                result = self.on_pdf(())
                self._ui_events.put(("reference", result))
            except Exception as exc:
                from ..security import redact_secrets
                self._ui_events.put(("reference_error", redact_secrets(exc)))

        threading.Thread(target=worker, name="endependenz-pdf-clear", daemon=True).start()

    def _request_scan(self):
        if self._scan_busy or not self.on_scan or not self._running:
            return
        self._scan_busy = True
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

        threading.Thread(target=worker, name="endependenz-scan", daemon=True).start()

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
                self.status_lbl.configure(text=text, fg=color)
            elif event == "scan_finished":
                self._scan_busy = False
                self.scan_btn.configure(
                    state="normal" if self._running else "disabled", text="[ SCAN ]"
                )
            elif event == "running":
                self._apply_running(bool(payload))
            elif event == "reference":
                self.pdf_btn.configure(state="normal", text="[ PDF REFERENCE ]")
                warning_text = f" // {len(payload.warnings)} WARN" if payload.warnings else ""
                reference_text = "REFERENCE: NONE"
                if payload.document_count:
                    reference_text = (
                        f"REFERENCE: {payload.document_count} PDF // "
                        f"{payload.page_count} PAGES // {payload.character_count:,} CHARS"
                        f"{warning_text}"
                    )
                self.reference_lbl.configure(
                    text=reference_text,
                    fg=GREEN,
                )
            elif event == "reference_error":
                self.pdf_btn.configure(state="normal", text="[ PDF REFERENCE ]")
                self.reference_lbl.configure(text=f"REFERENCE ERROR: {payload}", fg=ERROR)
        self.root.after(40, self._drain_ui_events)

    def _close(self):
        if self.on_stop:
            self.on_stop()
        self._closed = True
        self.root.destroy()

    def _start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag(self, event):
        self.root.geometry(
            f"+{self.root.winfo_x() + event.x - self._drag_start_x}"
            f"+{self.root.winfo_y() + event.y - self._drag_start_y}"
        )

    def update_result(self, result: AnswerResult):
        self._ui_events.put(("result", result))

    def _apply_result(self, result: AnswerResult):
        if not result.is_valid_question:
            self.status_lbl.configure(text="> STATUS: NO QUEST DETECTED", fg=WHITE)
            self.question_lbl.configure(text="")
            self.choice_lbl.configure(text="--", fg=MUTED)
            self.answer_text_lbl.configure(text="ADJUST THE SCAN AREA\nOR WAIT FOR A QUESTION")
            self.explanation_lbl.configure(text="")
            return
        pct = int(result.confidence * 100)
        self._last_result = result
        state_label = "QUEST COMPLETE" if self._running else "PAUSED // LAST RESULT"
        status = f"> STATUS: {state_label} // {pct}% CONFIDENCE"
        if result.is_negative_question:
            status += " // NOT-FALSE CHECK"
        self.status_lbl.configure(text=status, fg=GREEN if pct >= 80 else WHITE)
        self.question_lbl.configure(text=f"QUEST: {result.question_text}")
        self.choice_lbl.configure(text=">>", fg=GREEN)
        answer = format_selected_answers(result)
        self.answer_text_lbl.configure(text=answer or result.click_instruction or "NO ANSWER")
        self.explanation_lbl.configure(
            text=f"[ LOG ] {result.explanation}" if result.explanation else ""
        )

    def set_analyzing(self):
        self._ui_events.put(("analyzing", None))

    def _apply_analyzing(self):
        self.status_lbl.configure(text="> STATUS: ANALYZING QUEST...", fg=GREEN)
        self.question_lbl.configure(text="")
        self.choice_lbl.configure(text=">>", fg=GREEN)
        self.answer_text_lbl.configure(text="READING QUEST DATA...")
        self.explanation_lbl.configure(text="")

    def show_error(self, message: str):
        self._ui_events.put(("error", message))

    def _apply_error(self, message: str):
        self.status_lbl.configure(text="> STATUS: QUEST FAILED", fg=ERROR)
        self.choice_lbl.configure(text="!!", fg=ERROR)
        self.answer_text_lbl.configure(text=message[:160])
        self.explanation_lbl.configure(text="[ LOG ] CHECK API KEY, CONNECTION, AND SCAN AREA.")

    def set_status(self, text: str, color: str = GREEN):
        self._ui_events.put(("status", (text, color)))

    def run(self):
        self.root.mainloop()
