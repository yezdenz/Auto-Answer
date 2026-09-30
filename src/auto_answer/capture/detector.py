"""
Real-time screen change and scene transition detector.
Prevents duplicate API calls by calculating perceptual differences between frames.
"""

from __future__ import annotations
from typing import Optional
from PIL import Image, ImageChops, ImageStat


class ScreenChangeDetector:
    """Detects whether screen content inside the scan region has significantly changed."""

    def __init__(self, threshold: float = 4.0, sample_size: tuple[int, int] = (64, 64)):
        self.threshold = threshold
        self.sample_size = sample_size
        self._last_thumbnail: Optional[Image.Image] = None

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
