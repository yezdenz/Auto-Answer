"""
Real-time screen change and scene transition detector.
Prevents duplicate API calls by calculating perceptual differences between frames.
"""

from __future__ import annotations
from typing import Optional
from PIL import Image, ImageChops, ImageStat


class ScreenChangeDetector:
    """Detects whether screen content inside the scan region has significantly changed."""

    def __init__(
        self,
        threshold: float = 4.0,
        sample_size: tuple[int, int] = (64, 64),
        scroll_match_threshold: float = 3.5,
        max_scroll_fraction: float = 0.40,
    ):
        self.threshold = threshold
        self.sample_size = sample_size
        self.scroll_match_threshold = scroll_match_threshold
        self.max_scroll_fraction = max_scroll_fraction
        self._last_thumbnail: Optional[Image.Image] = None

    @property
    def has_reference(self) -> bool:
        return self._last_thumbnail is not None

    def _to_thumbnail(self, image: Image.Image) -> Image.Image:
        """Converts an image to a normalized grayscale thumbnail for fast comparison."""
        return image.convert("L").resize(self.sample_size, Image.Resampling.BILINEAR)

    def calculate_difference(self, image: Image.Image) -> float:
        """
        Calculates the mean pixel difference (0.0 to 255.0) between the current frame
        and the previously registered frame.
        """
        current_thumb = self._to_thumbnail(image)
        if self._last_thumbnail is None:
            return 255.0

        diff = ImageChops.difference(self._last_thumbnail, current_thumb)
        mean_diff = ImageStat.Stat(diff).mean[0]
        return mean_diff

    @staticmethod
    def _overlap_difference(
        previous: Image.Image, current: Image.Image, vertical_shift: int
    ) -> float:
        """Compare the overlapping area after applying a vertical translation."""
        width, height = previous.size
        if vertical_shift > 0:
            previous_part = previous.crop((0, vertical_shift, width, height))
            current_part = current.crop((0, 0, width, height - vertical_shift))
        else:
            amount = abs(vertical_shift)
            previous_part = previous.crop((0, 0, width, height - amount))
            current_part = current.crop((0, amount, width, height))
        diff = ImageChops.difference(previous_part, current_part)
        return ImageStat.Stat(diff).mean[0]

    def classify_change(self, image: Image.Image) -> tuple[str, float]:
        """Classify a frame as ``same``, vertical ``scroll``, or ``changed``.

        A browser scroll moves most question pixels vertically while preserving
        their appearance. Matching the overlapping content at several offsets
        suppresses redundant AI calls without needing OCR or another API turn.
        """
        current = self._to_thumbnail(image)
        if self._last_thumbnail is None:
            return "changed", 255.0

        raw_difference = ImageStat.Stat(
            ImageChops.difference(self._last_thumbnail, current)
        ).mean[0]
        if raw_difference < self.threshold:
            return "same", raw_difference

        height = current.height
        max_shift = max(2, int(height * self.max_scroll_fraction))
        best_aligned = 255.0
        best_shift = 0
        for shift in range(-max_shift, max_shift + 1):
            if abs(shift) < 2:
                continue
            score = self._overlap_difference(self._last_thumbnail, current, shift)
            if score < best_aligned:
                best_aligned = score
                best_shift = shift
                if score == 0.0:
                    break  # No remaining offset can improve a perfect match.

        if best_shift and best_aligned <= self.scroll_match_threshold:
            return "scroll", best_aligned
        return "changed", raw_difference

    def update_reference(self, image: Image.Image) -> None:
        """Updates the baseline reference frame."""
        self._last_thumbnail = self._to_thumbnail(image)

    def has_changed(self, image: Image.Image, update_on_change: bool = True) -> bool:
        """
        Returns True if the image difference exceeds the change threshold.
        If update_on_change is True, automatically updates the reference frame when changed.
        """
        if self._last_thumbnail is None:
            if update_on_change:
                self.update_reference(image)
            return True

        diff = self.calculate_difference(image)
        if diff >= self.threshold:
            if update_on_change:
                self.update_reference(image)
            return True
        return False

    def reset(self) -> None:
        """Resets stored reference image."""
        self._last_thumbnail = None

