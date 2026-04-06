import threading
import time

from pynvml import NVMLError

from gpu_oc.gpu_control import GPUController
from gpu_oc.recovery import reload_nvidia_driver


class GPUMonitor:
    """
    Background thread that polls GPU health and triggers recovery on TDR events.

    Recovery sequence on a detected driver crash:
      1. Reload the NVIDIA kernel modules (stopping/starting the display
         manager around it if `display_manager` is configured).
      2. Reinitialise the NVML session.
      3. Reset GPU clocks/offsets to safe defaults.
    """

    def __init__(
        self,
        controller: GPUController,
        interval_sec: int = 5,
        display_manager: str | None = None,
    ) -> None:
        self._controller = controller
        self._interval = interval_sec
        self._display_manager = display_manager
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
                reload_nvidia_driver(self._display_manager)
                try:
                    time.sleep(2)
                    self._controller.reinit()
                except Exception as reinit_exc:
                    print(f"NVML reinit failed: {reinit_exc}")
                self._controller.reset_to_safe_defaults()
            self._stop_event.wait(self._interval)
