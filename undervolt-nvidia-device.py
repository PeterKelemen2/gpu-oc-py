from pynvml import *
from clock_util import get_gpu_freqs
from models import GPUFreqs

data: GPUFreqs = get_gpu_freqs()

nvmlInit()
device = nvmlDeviceGetHandleByIndex(0)

core_offset = 160 # Mhz
power_limit = 260 # Watt
min_clock = data.CoreFreq.min_freq
max_clock = data.CoreFreq.max_freq

final_core_max = max_clock - core_offset

nvmlDeviceSetGpuLockedClocks(device,min_clock,2000)
nvmlDeviceSetGpcClkVfOffset(device,core_offset)
# nvmlDeviceSetPowerManagementLimit(device,power_limit * 100)