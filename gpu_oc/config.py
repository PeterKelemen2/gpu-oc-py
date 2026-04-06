from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

CONFIG_FILE = Path("config.toml")


class OCProfile(BaseModel):
    """OC settings schema. All fields are required — set them in config.toml."""

    gpu_index: int = Field(ge=0)
    core_offset_mhz: int = Field(ge=-500, le=500)
    power_limit_watt: int | None = Field(default=None, ge=1, le=600)
    max_core_clock_mhz: int = Field(ge=100, le=4000)

    def __str__(self) -> str:
        return (
            f"GPU {self.gpu_index}: Core offset {self.core_offset_mhz} MHz, "
            f"Power limit {self.power_limit_watt} W, "
            f"Max core clock {self.max_core_clock_mhz} MHz"
        )

def load_profile() -> OCProfile:
    """Load OCProfile from config.toml, with clear errors if it is missing or invalid."""
    if not CONFIG_FILE.exists():
        print(
            f"Error: '{CONFIG_FILE}' not found.\n"
            "Copy config.toml.example to config.toml and fill in your values."
        )
        sys.exit(1)

    with CONFIG_FILE.open("rb") as f:
        data = tomllib.load(f)

    try:
        oc_profile = OCProfile(**data.get("profile", {}))
        print(f"Loaded OC profile: {oc_profile}")
        return oc_profile
    except ValidationError as exc:
        print(f"Error: invalid config.toml:\n{exc}")
        sys.exit(1)


# Hardware watchdog constants
WATCHDOG_PATH: str = "/dev/watchdog"
WATCHDOG_INTERVAL_SEC: int = 10  # must be less than the kernel watchdog timeout

# GPU health-poll interval
MONITOR_INTERVAL_SEC: int = 5
