"""
Configuration manager for Auto Answer.
Handles loading and persisting settings from config.json and .env.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

# Try loading python-dotenv if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class BoundingBox(BaseModel):
    left: int = 0
    top: int = 0
    width: int = 800
    height: int = 600

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    def to_tuple(self) -> tuple[int, int, int, int]:
        """Returns (left, top, width, height)."""
        return (self.left, self.top, self.width, self.height)

    def to_ltrb(self) -> tuple[int, int, int, int]:
        """Returns (left, top, right, bottom)."""
        return (self.left, self.top, self.right, self.bottom)


class ClickerConfig(BaseModel):
    enabled: bool = False
    dry_run: bool = True
    delay_sec: float = 1.0


class AppConfig(BaseModel):
    scan_region: BoundingBox = Field(default_factory=BoundingBox)
    model: str = "gemini-2.5-flash"
    gemini_api_key: Optional[str] = None
    auto_mode_interval_sec: float = 2.0
    save_debug_screenshots: bool = True
    debug_dir: str = "debug_output"
    hud_opacity: float = 0.92
    hud_always_on_top: bool = True
    clicker: ClickerConfig = Field(default_factory=ClickerConfig)

    @classmethod
    def load(cls, config_path: str | Path = "config.json") -> AppConfig:
        config_path = Path(config_path)
        data = {}

        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"[Warning] Failed to read {config_path}: {e}")

        # Environment variable overrides
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            data["gemini_api_key"] = api_key

        model_env = os.environ.get("GEMINI_MODEL")
        if model_env:
            data["model"] = model_env

        return cls(**data)

    def save(self, config_path: str | Path = "config.json") -> None:
        config_path = Path(config_path)
        # Avoid saving API keys into config.json directly for security
        data = self.model_dump()
        if "gemini_api_key" in data:
            del data["gemini_api_key"]

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
