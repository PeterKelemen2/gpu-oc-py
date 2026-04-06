import os
import threading


class Watchdog:
    """
    Manages the Linux hardware watchdog at /dev/watchdog.

    The kernel reboots the system if the process stops petting the watchdog
    within the configured timeout (inspect with `wdctl`).

    Requires a loaded watchdog kernel module, e.g.:
      sudo modprobe softdog      # software watchdog (for testing)
      sudo modprobe iTCO_wdt     # Intel hardware watchdog
    Needs root to open the device.
    """

    def __init__(self, path: str, interval_sec: int) -> None:
        self._path = path
        self._interval = interval_sec
        self._fd: int | None = None
        self._stop_event = threading.Event()

    def arm(self) -> bool:
        """Open the watchdog device. Returns True on success."""
        if not os.path.exists(self._path):
            print("No watchdog device found — skipping hardware watchdog.")
            return False
        try:
            self._fd = os.open(self._path, os.O_WRONLY)
            print("Watchdog armed. System will reboot if this process freezes.")
            return True
        except PermissionError:
            print(f"Cannot open {self._path} — run as root to enable the watchdog.")
            return False

    def start_keepalive(self) -> None:
        """Start the background thread that pets the watchdog."""
        if self._fd is not None:
            threading.Thread(target=self._pet_loop, daemon=True).start()

    def disarm(self) -> None:
        """Write the magic 'V' byte to cleanly disarm the watchdog on exit."""
        self._stop_event.set()
        if self._fd is None:
            return
        try:
            os.write(self._fd, b"V")
            os.close(self._fd)
        except OSError:
            pass
        self._fd = None

    def _pet_loop(self) -> None:
        while not self._stop_event.is_set():
            if self._fd is not None:
                try:
                    os.write(self._fd, b"1")
                except OSError as exc:
                    print(f"Watchdog write failed: {exc}")
                    break
            self._stop_event.wait(self._interval)
