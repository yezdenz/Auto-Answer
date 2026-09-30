"""
Configuration manager for Auto Answer.
Handles loading and persisting settings from config.json and .env.
"""

from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from .security import load_stored_api_key

# Try loading python-dotenv if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class BoundingBox(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    left: int = 0
    top: int = 0
    width: int = Field(default=800, ge=1, le=32768)
    height: int = Field(default=600, ge=1, le=32768)

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
    model_config = ConfigDict(validate_assignment=True)

    enabled: bool = False
    dry_run: bool = True
    delay_sec: float = Field(default=1.0, ge=0.0, le=10.0)
    min_confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    allow_multi_select: bool = False


class AppConfig(BaseModel):
    model_config = ConfigDict(validate_assignment=True, extra="ignore")

    scan_region: BoundingBox = Field(default_factory=BoundingBox)
    model: str = "gemini-3.1-flash-lite"
    gemini_api_key: Optional[str] = None
    auto_mode_interval_sec: float = Field(default=2.0, ge=0.25, le=3600.0)
    poll_interval_sec: float = Field(default=0.25, ge=0.10, le=10.0)
    settle_delay_sec: float = Field(default=0.18, ge=0.0, le=5.0)
    change_threshold: float = Field(default=4.5, ge=0.1, le=255.0)
    save_debug_screenshots: bool = False
    debug_dir: str = "debug_output"
    hud_opacity: float = Field(default=0.96, ge=0.35, le=1.0)
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
        api_key = (
            os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or load_stored_api_key()
        )
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

        config_path.parent.mkdir(parents=True, exist_ok=True)
        # Write atomically so an interrupted save cannot corrupt the config.
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{config_path.name}.", suffix=".tmp", dir=config_path.parent
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_name, config_path)
        finally:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass
