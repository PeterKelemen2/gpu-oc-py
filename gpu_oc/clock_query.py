import re
import subprocess

from gpu_oc.models import FreqPair, GPUFreqs


def _get_raw_clocks() -> dict[str, list[int]]:
    result = subprocess.run(
        ["nvidia-smi", "-q", "-d", "SUPPORTED_CLOCKS"],
        capture_output=True,
        text=True,
    )
    data: dict[str, list[int]] = {"Graphics": [], "Memory": []}
    current_section: str | None = None

    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("Graphics"):
            current_section = "Graphics"
        elif line.startswith("Memory"):
            current_section = "Memory"
        match = re.search(r"(\d+)\s*MHz", line)
        if match and current_section:
            data[current_section].append(int(match.group(1)))

    return data


def get_gpu_freqs() -> GPUFreqs:
    raw = _get_raw_clocks()
    return GPUFreqs(
        CoreFreq=(
            FreqPair(min_freq=min(raw["Graphics"]), max_freq=max(raw["Graphics"]))
            if raw["Graphics"]
            else None
        ),
        MemFreq=(
            FreqPair(min_freq=min(raw["Memory"]), max_freq=max(raw["Memory"]))
            if raw["Memory"]
            else None
        ),
    )
