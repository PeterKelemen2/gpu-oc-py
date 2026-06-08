"""Main window for GPU OC GUI application."""

from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from gpu_oc.ipc import IPCClient
from gpu_oc.ui.widgets.status_panel import StatusPanel
from gpu_oc.ui.widgets.settings_panel import SettingsPanel
from gpu_oc.ui.widgets.fan_curve_widget import FanCurveWidget
from gpu_oc.ui.tray_icon import TrayIcon


class MainWindow(QMainWindow):
    """Main application window with tabs for different GPU control features."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPU OC Controller")
        self.setGeometry(100, 100, 900, 700)
        
        self.ipc_client = IPCClient()
        self.connected = False
        
        # Setup UI
        self._setup_ui()
        
        # Setup tray icon
        self.tray_icon = TrayIcon(self)
        self.tray_icon.show()
        
        # Status update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(2000)  # Update every 2 seconds
        
        # Initial status check
        self._check_service_connection()

    def _setup_ui(self) -> None:
        """Setup the main UI with tabs."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Connection status indicator
        self.status_label = QLabel("Connecting to service...")
        layout.addWidget(self.status_label)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Status panel
        self.status_panel = StatusPanel(self.ipc_client)
        self.tabs.addTab(self.status_panel, "Status")
        
        # Settings panel
        self.settings_panel = SettingsPanel(self.ipc_client)
        self.tabs.addTab(self.settings_panel, "Settings")
        
        # Fan control panel
        self.fan_curve_widget = FanCurveWidget(self.ipc_client)
        self.tabs.addTab(self.fan_curve_widget, "Fan Control")
        
        # OC Toggle button
        self.toggle_btn = QPushButton("Disable OC")
        self.toggle_btn.clicked.connect(self._toggle_oc)
        layout.addWidget(self.toggle_btn)
        
        # About button
        about_btn = QPushButton("About")
        about_btn.clicked.connect(self._show_about)
        layout.addWidget(about_btn)

    def _check_service_connection(self) -> None:
        """Check connection to GPU OC service."""
        try:
            status = self.ipc_client.get_status()
            self.connected = True
            self.status_label.setText("✓ Connected to GPU OC service")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self._update_oc_button(status.get("oc_enabled", True))
        except RuntimeError as e:
            self.connected = False
            self.status_label.setText(f"✗ Disconnected: {e}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.toggle_btn.setEnabled(False)

    def _update_status(self) -> None:
        """Periodically update status from service."""
        if not self.connected:
            self._check_service_connection()
            return
        
        try:
            status = self.ipc_client.get_status()
            self.status_panel.update_from_status(status)
            self._update_oc_button(status.get("oc_enabled", True))
        except RuntimeError:
            self.connected = False
            self._check_service_connection()

    def _update_oc_button(self, enabled: bool) -> None:
        """Update the OC toggle button text based on current state."""
        self.toggle_btn.setText("Disable OC" if enabled else "Enable OC")

    def _toggle_oc(self) -> None:
        """Toggle OC on/off."""
        if not self.connected:
            QMessageBox.warning(self, "Error", "Not connected to service")
            return
        
        try:
            current_state = self.ipc_client.get_status()
            enabled = current_state.get("oc_enabled", True)
            print(f"GUI: Current OC state = {enabled}, toggling to {not enabled}")
            
            result = self.ipc_client.toggle_oc(not enabled)
            print(f"GUI: Toggle result = {result}")
            
            if result.get("status") == "ok":
                new_state = result.get("oc_enabled", True)
                self._update_oc_button(new_state)
                self.status_panel.update_from_status(self.ipc_client.get_status())
                QMessageBox.information(self, "Success", 
                    f"OC {'enabled' if new_state else 'disabled'} successfully")
            else:
                QMessageBox.critical(self, "Error", result.get("error", "Unknown error"))
        except RuntimeError as e:
            print(f"GUI: Error during toggle: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About GPU OC Controller",
            "GPU OC Python Controller v0.2.0\n\n"
            "A PyQt6 GUI for NVIDIA GPU overclocking with fan control.\n\n"
            "License: MIT",
        )

    def closeEvent(self, event) -> None:
        """Handle window close event - minimize to tray instead."""
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()
