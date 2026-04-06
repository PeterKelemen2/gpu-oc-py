from pydantic import BaseModel


class OCProfile(BaseModel):
    """User-facing OC settings. Edit these values to tune your card."""

    gpu_index: int = 0
    core_offset_mhz: int = 160
    power_limit_watt: int = 260
    max_core_clock_mhz: int = 2000


# Hardware watchdog constants
WATCHDOG_PATH: str = "/dev/watchdog"
WATCHDOG_INTERVAL_SEC: int = 10  # must be less than the kernel watchdog timeout

# GPU health-poll interval
MONITOR_INTERVAL_SEC: int = 5
