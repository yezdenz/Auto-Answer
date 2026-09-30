"""
Native Windows mouse automation module using ctypes.
Allows optional automated selection of answers with safety guards and dry-run mode.
"""

from __future__ import annotations
import sys
import time
import ctypes
from typing import Optional
from ..config import ClickerConfig, BoundingBox
from ..ai.solver import AnswerResult


class AutoClicker:
    """Simulates native Windows mouse clicks safely."""

    def __init__(self, config: ClickerConfig):
        self.config = config

    @staticmethod
    def click_at(x: int, y: int):
        """Simulates a left mouse click at the given absolute screen coordinates."""
        if sys.platform != "win32":
            return

        user32 = ctypes.windll.user32
        # Move cursor
        user32.SetCursorPos(int(x), int(y))
        time.sleep(0.05)

        # MOUSEEVENTF_LEFTDOWN = 0x0002, MOUSEEVENTF_LEFTUP = 0x0004
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def click_option(self, region: BoundingBox, result: AnswerResult) -> bool:
        """
        Calculates the estimated position of the correct option relative to the question box
        and clicks it if enabled.
        """
        if not self.config.enabled:
            return False

        if not result.options:
            return False

        if result.correct_option_indices:
            idx = result.correct_option_indices[0]
            target_label = result.options[idx].label if idx < len(result.options) else result.correct_option_labels
        else:
            labels = [opt.label.upper().strip() for opt in result.options]
            target_label = result.correct_option_labels.upper().strip()
            if target_label not in labels:
                return False
            idx = labels.index(target_label)

        total = len(result.options)

        # Estimate the Y coordinate based on options distribution in the lower ~60% of the box
        # Radio button is typically near the left edge (~10% into width)
        options_start_y = region.top + int(region.height * 0.40)
        options_height = int(region.height * 0.50)
        step = options_height / max(1, total)

        target_x = region.left + int(region.width * 0.08)
        target_y = int(options_start_y + (idx + 0.5) * step)

        if self.config.dry_run:
            print(f"[AutoClicker Dry-Run] Would click at ({target_x}, {target_y}) for option {target_label}")
            return True

        time.sleep(self.config.delay_sec)
        self.click_at(target_x, target_y)
        print(f"[AutoClicker] Clicked option {target_label} at ({target_x}, {target_y})")
        return True
