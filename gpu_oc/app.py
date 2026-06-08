import signal
import sys
import time

from pynvml import NVMLError

from gpu_oc.clock_query import get_gpu_freqs
from gpu_oc.config import (
    MONITOR_INTERVAL_SEC,
    WATCHDOG_INTERVAL_SEC,
    WATCHDOG_PATH,
    load_profile,
    load_fan_profile,
)
from gpu_oc.gpu_control import GPUController
from gpu_oc.gpu_monitor import GPUMonitor
from gpu_oc.ipc import IPCServer
from gpu_oc.watchdog import Watchdog


def main() -> None:
    profile = load_profile()
    fan_profile = load_fan_profile()
    freqs = get_gpu_freqs()

    controller = GPUController(profile, freqs)
    monitor = GPUMonitor(controller, MONITOR_INTERVAL_SEC, profile.display_manager)
    watchdog = Watchdog(WATCHDOG_PATH, WATCHDOG_INTERVAL_SEC)

    # Track OC state for GUI control
    oc_state = {"enabled": True, "fan_profile": fan_profile}

    # Setup IPC server for GUI communication
    ipc_server = IPCServer()

    def handle_get_status(params: dict) -> dict:
        """Return current GPU status."""
        try:
            temp = controller.get_temperature()
            return {
                "gpu_index": profile.gpu_index,
                "temperature": temp,
                "oc_enabled": oc_state["enabled"],
                "fan_mode": oc_state["fan_profile"].mode,
                "status": "running",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def handle_toggle_oc(params: dict) -> dict:
        """Toggle OC on/off without restarting service."""
        enabled = params.get("enabled", True)
        print(f"toggle_oc handler: enabled={enabled}, current_state={oc_state['enabled']}")
        
        if enabled and not oc_state["enabled"]:
            try:
                print("Applying OC...")
                controller.apply_oc()
                oc_state["enabled"] = True
                print("OC enabled")
                return {"status": "ok", "oc_enabled": True}
            except NVMLError as e:
                print(f"Error enabling OC: {e}")
                return {"status": "error", "error": str(e)}
        elif not enabled and oc_state["enabled"]:
            try:
                print("Disabling OC...")
                controller.reset_to_safe_defaults()
                oc_state["enabled"] = False
                print("OC disabled")
                return {"status": "ok", "oc_enabled": False}
            except NVMLError as e:
                print(f"Error disabling OC: {e}")
                return {"status": "error", "error": str(e)}
        
        print(f"No state change needed: enabling={enabled}, already_enabled={oc_state['enabled']}")
        return {"status": "ok", "oc_enabled": oc_state["enabled"]}

    def handle_set_fan_curve(params: dict) -> dict:
        """Set fan curve points."""
        points = params.get("points", [])
        print(f"set_fan_curve handler: points={points}")
        
        if not points:
            print("Error: no points provided")
            return {"status": "error", "error": "points required"}
        
        try:
            from gpu_oc.config import FanProfile
            print(f"Creating new fan profile with points: {points}")
            
            # Create a NEW FanProfile with the new points
            new_fan_profile = FanProfile(mode="curve", curve_points=points)
            oc_state["fan_profile"] = new_fan_profile
            
            print(f"Fan profile updated: mode={new_fan_profile.mode}, points={new_fan_profile.curve_points}")
            
            # Try to apply it
            print("Applying fan curve...")
            controller.apply_fan_curve(oc_state["fan_profile"])
            
            print("Fan curve applied successfully")
            return {"status": "ok", "fan_curve": points}
        except Exception as e:
            print(f"Error in set_fan_curve: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def handle_get_config(params: dict) -> dict:
        """Return current configuration."""
        return {
            "gpu_index": profile.gpu_index,
            "core_offset_mhz": profile.core_offset_mhz,
            "power_limit_watt": profile.power_limit_watt,
            "max_core_clock_mhz": profile.max_core_clock_mhz,
            "display_manager": profile.display_manager,
            "fan_mode": oc_state["fan_profile"].mode,
            "fan_curve_points": oc_state["fan_profile"].curve_points,
        }

    ipc_server.register_handler("get_status", handle_get_status)
    ipc_server.register_handler("toggle_oc", handle_toggle_oc)
    ipc_server.register_handler("set_fan_curve", handle_set_fan_curve)
    ipc_server.register_handler("get_config", handle_get_config)
    ipc_server.start_background()

    monitor.start()
    watchdog.arm()
    watchdog.start_keepalive()

    def shutdown(sig, frame) -> None:
        print("\nShutting down — disarming watchdog and resetting GPU...")
        ipc_server.stop()
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
            # Periodically apply fan curve if in curve mode
            if oc_state["enabled"] and oc_state["fan_profile"].mode == "curve":
                controller.apply_fan_curve(oc_state["fan_profile"])
            time.sleep(MONITOR_INTERVAL_SEC)
    except NVMLError as exc:
        print(f"Failed to apply OC settings: {exc}")
        ipc_server.stop()
        monitor.stop()
        watchdog.disarm()
        controller.reset_to_safe_defaults()
        controller.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()
