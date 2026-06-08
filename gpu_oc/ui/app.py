#!/usr/bin/env python3
"""GPU OC Desktop Application - PyQt6 GUI for GPU overclocking control."""

import sys
from pathlib import Path

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
except ImportError:
    print("Error: PyQt6 not installed. Install with: pip install PyQt6")
    sys.exit(1)

from gpu_oc.ui.main_window import MainWindow
from gpu_oc.ipc import IPCClient


def main():
    """Launch GPU OC GUI application."""
    # Check if service is running
    try:
        client = IPCClient()
        status = client.get_status()
        print(f"Connected to GPU OC service: {status}")
    except RuntimeError as e:
        print(f"Warning: {e}")
        print("The service may not be running. You can still use the GUI, but OC won't be controlled.")

    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("GPU OC Controller")
    app.setApplicationVersion("0.2.0")
    app.setApplicationDisplayName("GPU OC Controller")

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
