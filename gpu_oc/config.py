from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

CONFIG_FILE = Path(os.environ.get("GPU_OC_CONFIG", "config.toml"))


class FanCurvePoint(BaseModel):
    """A single point on the fan curve: (temperature, fan_percent)."""
    temperature: int = Field(ge=0, le=100)
    fan_percent: int = Field(ge=0, le=100)


class FanProfile(BaseModel):
    """Fan control settings. Default: auto mode (driver-controlled)."""
    mode: str = Field(default="auto", pattern="^(auto|curve|manual)$")
    # Curve points: list of [temperature, fan_percent] pairs
    # Only used when mode="curve". Must have at least 2 points.
    curve_points: list[list[int]] = Field(
        default=[[30, 30], [45, 50], [60, 100]],
        description="Temperature (0-100°C) to fan % (0-100%) points"
    )

    @staticmethod
    def _validate_curve_points(points: list[list[int]]) -> None:
        """Validate curve points format and ranges."""
        if len(points) < 2:
            raise ValueError("Fan curve must have at least 2 points")
        for i, point in enumerate(points):
            if not isinstance(point, list) or len(point) != 2:
                raise ValueError(f"Point {i} must be [temperature, fan_percent]")
            temp, fan = point
            if not (0 <= temp <= 100):
                raise ValueError(f"Point {i}: temperature {temp} out of range [0-100]")
            if not (0 <= fan <= 100):
                raise ValueError(f"Point {i}: fan percent {fan} out of range [0-100]")
        # Check temperatures are ascending
        for i in range(len(points) - 1):
            if points[i][0] >= points[i + 1][0]:
                raise ValueError("Curve temperatures must be in ascending order")

    def __init__(self, **data):
        super().__init__(**data)
        if self.mode == "curve":
            self._validate_curve_points(self.curve_points)


class OCProfile(BaseModel):
    """OC settings schema. All fields are required — set them in config.toml."""

    gpu_index: int = Field(ge=0)
    core_offset_mhz: int = Field(ge=-500, le=500)
    power_limit_watt: int | None = Field(default=None, ge=1, le=600)
    max_core_clock_mhz: int = Field(ge=100, le=4000)
    # Display manager service name (e.g. "gdm", "sddm", "lightdm").
    # When set, a driver crash triggers a driver reload + DM restart instead of
    # relying solely on the hardware watchdog reboot.
    display_manager: str | None = None

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


def load_fan_profile() -> FanProfile:
    """Load FanProfile from config.toml, with sensible defaults."""
    if not CONFIG_FILE.exists():
        return FanProfile()  # Return default auto mode

    with CONFIG_FILE.open("rb") as f:
        data = tomllib.load(f)

    try:
        fan_data = data.get("fan_profile", {})
        fan_profile = FanProfile(**fan_data)
        print(f"Loaded fan profile: mode={fan_profile.mode}")
        return fan_profile
    except ValidationError as exc:
        print(f"Warning: invalid fan_profile in config.toml, using defaults:\n{exc}")
        return FanProfile()  # Fall back to defaults


# Hardware watchdog constants
WATCHDOG_PATH: str = "/dev/watchdog"
WATCHDOG_INTERVAL_SEC: int = 10  # must be less than the kernel watchdog timeout

# GPU health-poll interval
MONITOR_INTERVAL_SEC: int = 5
