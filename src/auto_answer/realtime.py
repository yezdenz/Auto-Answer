"""
Real-time question scanning and answering engine.
Monitors the screen dynamically, detects new questions via perceptual diffs,
listens for global hotkeys, and delivers instantaneous answers.
"""

from __future__ import annotations
import time
import threading
from pathlib import Path
from typing import Optional, Callable
from PIL import Image

from .config import AppConfig
from .capture.screen import capture_screen_region
from .capture.detector import ScreenChangeDetector
from .capture.hotkey import GlobalHotkeyListener, VK_F8
from .ai.solver import GeminiQuestionSolver, AnswerResult
from .automation.clicker import AutoClicker
from .ui.console import console, display_answer_terminal
from .ui.hud import FloatingHUD


class RealtimeScanner:
    """Continuous real-time screen watcher and question solver."""

    def __init__(
        self,
        config: AppConfig,
        solver: GeminiQuestionSolver,
        clicker: AutoClicker,
        hud: Optional[FloatingHUD] = None,
        on_solved_callback: Optional[Callable[[AnswerResult], None]] = None,
        poll_interval: Optional[float] = None,
        change_threshold: Optional[float] = None,
    ):
        self.config = config
        self.solver = solver
        self.clicker = clicker
        self.hud = hud
        self.on_solved = on_solved_callback
        self.poll_interval = poll_interval if poll_interval is not None else config.poll_interval_sec
        threshold = change_threshold if change_threshold is not None else config.change_threshold
        self.detector = ScreenChangeDetector(threshold=threshold)
        self.is_running = False
        self._solve_lock = threading.Lock()
        self._hotkey_listener: Optional[GlobalHotkeyListener] = None

    @property
    def is_solving(self) -> bool:
        return self._solve_lock.locked()

    def trigger_scan(
        self,
        reason: str = "Manual Trigger",
        captured_image: Optional[Image.Image] = None,
    ) -> Optional[AnswerResult]:
        """Performs an immediate capture, AI solve, and UI update."""
        if not self._solve_lock.acquire(blocking=False):
            return None

        try:
            start_t = time.time()
            if self.hud:
                self.hud.set_analyzing()

            region = self.config.scan_region
            img = captured_image if captured_image is not None else capture_screen_region(region)

            if self.config.save_debug_screenshots:
                dbg_dir = Path(self.config.debug_dir)
                dbg_dir.mkdir(parents=True, exist_ok=True)
                img.save(dbg_dir / "latest_capture.png")

            self.detector.update_reference(img)

            result = self.solver.solve_image(img)
            elapsed = time.time() - start_t

            # Render to terminal
            console.print(f"\n[dim]⚡ Triggered by: {reason}[/dim]")
            display_answer_terminal(result, elapsed_sec=elapsed)

            # Render to HUD if active
            if self.hud:
                self.hud.update_result(result)

            # Auto-clicker if enabled
            if self.config.clicker.enabled:
                self.clicker.click_option(region, result)

            if self.on_solved:
                self.on_solved(result)

            return result
        except Exception as e:
            from .security import redact_secrets
            safe_error = redact_secrets(e)
            console.print(f"[bold red]❌ Realtime Solver Error:[/bold red] {safe_error}")
            if self.hud:
                self.hud.show_error(safe_error)
            return None
        finally:
            self._solve_lock.release()

    def start(self, auto_detect_changes: bool = True):
        """Starts real-time monitoring loop."""
        self.is_running = True

        # Initialize global hotkey listener (F8)
        self._hotkey_listener = GlobalHotkeyListener(
            key_code=VK_F8,
            on_triggered=lambda: self.trigger_scan(reason="Global Hotkey [F8]")
        )
        self._hotkey_listener.start()

        console.print("[bold green]╔═════════════════════════════════════════════════════╗[/bold green]")
        console.print("[bold green]║            ⚡ REAL-TIME MONITOR ACTIVE              ║[/bold green]")
        console.print("[bold green]╚═════════════════════════════════════════════════════╝[/bold green]")
        console.print(
            f"[cyan]📍 Region:[/cyan] Left={self.config.scan_region.left}, "
            f"Top={self.config.scan_region.top}, "
            f"Width={self.config.scan_region.width}, Height={self.config.scan_region.height}"
        )
        console.print("[yellow]⌨️  Global Hotkey:[/yellow] Press [bold white][F8][/bold white] anywhere for instant scan")
        if auto_detect_changes:
            console.print("[green]🔄 Auto-Detection:[/green] Active (auto-scans as soon as question changes)")
        console.print("[dim]Press Ctrl+C to stop real-time monitoring.[/dim]\n")

        # Capture initial baseline frame
        initial_img = capture_screen_region(self.config.scan_region)
        self.detector.update_reference(initial_img)

        # Trigger immediate first scan
        self.trigger_scan(reason="Initial Screen Read", captured_image=initial_img)

        try:
            while self.is_running:
                time.sleep(self.poll_interval)

                if self.is_solving:
                    continue

                if auto_detect_changes:
                    current_img = capture_screen_region(self.config.scan_region)
                    diff = self.detector.calculate_difference(current_img)

                    # If significant change detected, wait brief moment for animation to settle
                    if diff >= self.detector.threshold:
                        time.sleep(self.config.settle_delay_sec)
                        # Re-verify after settling
                        settled_img = capture_screen_region(self.config.scan_region)
                        self.trigger_scan(
                            reason=f"Auto Scene Change (diff: {diff:.1f})",
                            captured_image=settled_img,
                        )

        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping real-time monitor...[/yellow]")
        finally:
            self.stop()

    def stop(self):
        """Stops the real-time scanner."""
        self.is_running = False
        if self._hotkey_listener:
            self._hotkey_listener.stop()
            self._hotkey_listener = None
