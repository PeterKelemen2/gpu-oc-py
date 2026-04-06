from pynvml import (
    NVML_TEMPERATURE_GPU,
    NVMLError,
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetTemperature,
    nvmlDeviceResetGpuLockedClocks,
    nvmlDeviceSetGpcClkVfOffset,
    nvmlDeviceSetGpuLockedClocks,
    nvmlInit,
    nvmlShutdown,
)

from gpu_oc.config import OCProfile
from gpu_oc.models import GPUFreqs


class GPUController:
    """Owns the NVML session and applies / reverts OC settings for a single GPU."""

    def __init__(self, profile: OCProfile, freqs: GPUFreqs) -> None:
        self._profile = profile
        self._freqs = freqs
        nvmlInit()
        self._device = nvmlDeviceGetHandleByIndex(profile.gpu_index)

    def apply_oc(self) -> None:
        min_clock = self._freqs.CoreFreq.min_freq if self._freqs.CoreFreq else 0
        nvmlDeviceSetGpuLockedClocks(
            self._device, min_clock, self._profile.max_core_clock_mhz
        )
        nvmlDeviceSetGpcClkVfOffset(self._device, self._profile.core_offset_mhz)
        # nvmlDeviceSetPowerManagementLimit(self._device, self._profile.power_limit_watt * 1000)

    def reset_to_safe_defaults(self) -> None:
        """Remove locked clocks and VF offset, returning the GPU to driver defaults."""
        try:
            nvmlDeviceResetGpuLockedClocks(self._device)
            nvmlDeviceSetGpcClkVfOffset(self._device, 0)
            # nvmlDeviceSetPowerManagementLimit(self._device, <default_mW>)
            print("GPU reset to safe defaults.")
        except NVMLError as exc:
            print(f"Failed to reset GPU defaults: {exc}")

    def get_temperature(self) -> int:
        return nvmlDeviceGetTemperature(self._device, NVML_TEMPERATURE_GPU)

    def reinit(self) -> None:
        """Reinitialise the NVML session after a driver reset / TDR event."""
        nvmlShutdown()
        nvmlInit()
        self._device = nvmlDeviceGetHandleByIndex(self._profile.gpu_index)

    def shutdown(self) -> None:
        nvmlShutdown()
