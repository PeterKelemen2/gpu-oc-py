import threading
import time

from pynvml import NVMLError

from gpu_oc.gpu_control import GPUController


class GPUMonitor:
    """Background thread that polls GPU health and triggers recovery on TDR events."""

    def __init__(self, controller: GPUController, interval_sec: int = 5) -> None:
        self._controller = controller
        self._interval = interval_sec
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._controller.get_temperature()
            except NVMLError as exc:
                print(f"GPU health check failed ({exc}) — attempting recovery.")
                try:
                    time.sleep(2)
                    self._controller.reinit()
                except Exception as reinit_exc:
                    print(f"NVML reinit failed: {reinit_exc}")
                self._controller.reset_to_safe_defaults()
            self._stop_event.wait(self._interval)
