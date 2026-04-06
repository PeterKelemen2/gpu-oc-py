import subprocess
import time


def restart_display_manager(dm: str) -> bool:
    """
    Restart the display manager to reload the desktop session.

    Stopping the DM kills the compositor and all GPU-using processes,
    which is required before the NVIDIA modules can be unloaded.
    Returns True if systemctl reported success.
    """
    print(f"Stopping display manager '{dm}'...")
    stop = subprocess.run(["systemctl", "stop", dm], capture_output=True)
    if stop.returncode != 0:
        print(f"Failed to stop {dm}: {stop.stderr.decode().strip()}")
        return False

    print(f"Starting display manager '{dm}'...")
    start = subprocess.run(["systemctl", "start", dm], capture_output=True)
    if start.returncode != 0:
        print(f"Failed to start {dm}: {start.stderr.decode().strip()}")
        return False

    print(f"Display manager '{dm}' restarted.")
    return True


def reload_nvidia_driver(dm: str | None) -> bool:
    """
    Unload and reload the NVIDIA kernel modules, optionally bracketed by a
    display-manager stop/start so the modules are not held open.

    Module unload order matters: dependents must be removed before nvidia itself.
    Returns True if the full sequence succeeded.
    """
    if dm:
        print(f"Stopping display manager '{dm}' before driver reload...")
        subprocess.run(["systemctl", "stop", dm], capture_output=True)
        time.sleep(1)

    print("Unloading NVIDIA kernel modules...")
    unload = subprocess.run(
        ["modprobe", "-r", "nvidia_uvm", "nvidia_drm", "nvidia_modeset", "nvidia"],
        capture_output=True,
    )
    if unload.returncode != 0:
        print(f"Module unload failed: {unload.stderr.decode().strip()}")
        print("There may still be processes using the GPU. Skipping reload.")
        if dm:
            subprocess.run(["systemctl", "start", dm], capture_output=True)
        return False

    time.sleep(1)
    print("Loading NVIDIA kernel module...")
    load = subprocess.run(["modprobe", "nvidia"], capture_output=True)
    if load.returncode != 0:
        print(f"Module load failed: {load.stderr.decode().strip()}")
        return False

    print("NVIDIA driver reloaded.")

    if dm:
        print(f"Starting display manager '{dm}'...")
        subprocess.run(["systemctl", "start", dm], capture_output=True)

    return True
