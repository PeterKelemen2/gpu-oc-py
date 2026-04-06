import signal
import sys
import time

from pynvml import NVMLError

from gpu_oc.clock_query import get_gpu_freqs
from gpu_oc.config import MONITOR_INTERVAL_SEC, WATCHDOG_INTERVAL_SEC, WATCHDOG_PATH, load_profile
from gpu_oc.gpu_control import GPUController
from gpu_oc.gpu_monitor import GPUMonitor
from gpu_oc.watchdog import Watchdog


def main() -> None:
    profile = load_profile()
    freqs = get_gpu_freqs()

    controller = GPUController(profile, freqs)
    monitor = GPUMonitor(controller, MONITOR_INTERVAL_SEC)
    watchdog = Watchdog(WATCHDOG_PATH, WATCHDOG_INTERVAL_SEC)

    monitor.start()
    watchdog.arm()
    watchdog.start_keepalive()

    def shutdown(sig, frame) -> None:
        print("\nShutting down — disarming watchdog and resetting GPU...")
        monitor.stop()
        watchdog.disarm()
        controller.reset_to_safe_defaults()
        controller.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        controller.apply_oc()
        print("OC settings applied. Monitoring GPU health. Press Ctrl+C to exit and reset.")
        while True:
            time.sleep(1)
    except NVMLError as exc:
        print(f"Failed to apply OC settings: {exc}")
        monitor.stop()
        watchdog.disarm()
        controller.reset_to_safe_defaults()
        controller.shutdown()
        sys.exit(1)
