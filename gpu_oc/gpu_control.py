from pynvml import (
    NVML_TEMPERATURE_GPU,
    NVMLError,
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetTemperature,
    nvmlDeviceResetGpuLockedClocks,
    nvmlDeviceSetGpcClkVfOffset,
    nvmlDeviceSetGpuLockedClocks,
    nvmlDeviceSetPowerManagementLimit,
    nvmlInit,
    nvmlShutdown,
)

from gpu_oc.config import OCProfile, FanProfile
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
        if self._profile.power_limit_watt is not None:
            nvmlDeviceSetPowerManagementLimit(self._device, self._profile.power_limit_watt * 1000)

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

    def apply_fan_curve(self, fan_profile: FanProfile) -> None:
        """Apply fan curve based on current GPU temperature.
        
        Interpolates between curve points to calculate target fan speed.
        Note: Direct fan control via NVML is limited and not available on most consumer GPUs.
        """
        if fan_profile.mode != "curve":
            print(f"Fan profile mode is '{fan_profile.mode}', not 'curve' - skipping fan curve application")
            return

        try:
            current_temp = self.get_temperature()
            target_fan = self._interpolate_fan_curve(
                current_temp, fan_profile.curve_points
            )
            print(f"Fan curve: {current_temp}°C → {target_fan}% target")
            
            # Note: NVML does not provide direct fan control for most consumer GPUs
            # Fan control is only available on certain professional GPUs (RTX, Quadro, etc.)
            # For consumer GPUs, you would need to:
            # - Edit NVIDIA settings files
            # - Use nvidia-settings with display server
            # - Use proprietary OEM tools
            
            print(f"  Note: Direct fan control via NVML not available on consumer GPUs.")
            print(f"  Target fan % is calculated but cannot be applied without nvidia-settings + X11 display server.")
            
        except NVMLError as exc:
            print(f"Failed to apply fan curve: {exc}")

    def _interpolate_fan_curve(self, temp: int, curve_points: list[list[int]]) -> int:
        """Linear interpolation of fan % based on temperature curve."""
        if temp <= curve_points[0][0]:
            return curve_points[0][1]
        if temp >= curve_points[-1][0]:
            return curve_points[-1][1]

        for i in range(len(curve_points) - 1):
            t1, f1 = curve_points[i]
            t2, f2 = curve_points[i + 1]
            if t1 <= temp <= t2:
                # Linear interpolation: fan % = f1 + (temp - t1) * (f2 - f1) / (t2 - t1)
                fan = f1 + (temp - t1) * (f2 - f1) // (t2 - t1)
                return fan

        return curve_points[-1][1]

    def reinit(self) -> None:
        """Reinitialise the NVML session after a driver reset / TDR event."""
        nvmlShutdown()
        nvmlInit()
        self._device = nvmlDeviceGetHandleByIndex(self._profile.gpu_index)

    def shutdown(self) -> None:
        nvmlShutdown()
