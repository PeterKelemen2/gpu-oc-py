import subprocess
import re
from models import FreqPair, GPUFreqs

def get_clocks():
    result = subprocess.run(
        ["nvidia-smi", "-q", "-d", "SUPPORTED_CLOCKS"],
        capture_output=True,
        text=True
    )

    raw_output = result.stdout

    data = {
        "Graphics": [],
        "Memory": []
    }

    current_section = None

    for line in raw_output.splitlines():
        line = line.strip()

        if line.startswith("Graphics"):
            current_section = "Graphics"
        elif line.startswith("Memory"):
            current_section = "Memory"

        match = re.search(r"(\d+)\s*MHz", line)
        if match and current_section:
            value = int(match.group(1))
            data[current_section].append(value)

    return data


def get_clocks_min_max():
    data = get_clocks()

    return {
        key: (FreqPair(min_freq=min(vals), max_freq=max(vals)) if vals else None)
        for key, vals in data.items()
    }


def get_gpu_freqs():
    clocks = get_clocks_min_max()

    return GPUFreqs(
        CoreFreq=clocks.get("Graphics"),
        MemFreq=clocks.get("Memory")
    )