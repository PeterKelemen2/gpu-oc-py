"""Status panel showing real-time GPU metrics."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel
from PyQt6.QtCore import Qt

from gpu_oc.ipc import IPCClient


class StatusPanel(QWidget):
    """Display real-time GPU status (temperature, clocks, power, etc.)."""

    def __init__(self, ipc_client: IPCClient):
        super().__init__()
        self.ipc_client = ipc_client
        
        self._setup_ui()
        self._initial_update()

    def _setup_ui(self) -> None:
        """Setup UI layout."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("GPU Status")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Grid for metrics
        grid = QGridLayout()
        
        # Temperature
        self.temp_label = QLabel("Temperature: --°C")
        grid.addWidget(QLabel("Temperature:"), 0, 0)
        grid.addWidget(self.temp_label, 0, 1)
        
        # Core Clock
        self.clock_label = QLabel("-- MHz")
        grid.addWidget(QLabel("Core Clock:"), 1, 0)
        grid.addWidget(self.clock_label, 1, 1)
        
        # Memory
        self.memory_label = QLabel("-- MB")
        grid.addWidget(QLabel("Memory:"), 2, 0)
        grid.addWidget(self.memory_label, 2, 1)
        
        # Power Draw
        self.power_label = QLabel("-- W")
        grid.addWidget(QLabel("Power Draw:"), 3, 0)
        grid.addWidget(self.power_label, 3, 1)
        
        # Fan Speed
        self.fan_label = QLabel("-- %")
        grid.addWidget(QLabel("Fan Speed:"), 4, 0)
        grid.addWidget(self.fan_label, 4, 1)
        
        # OC Status
        self.oc_status_label = QLabel("Enabled")
        grid.addWidget(QLabel("OC Status:"), 5, 0)
        grid.addWidget(self.oc_status_label, 5, 1)
        
        layout.addLayout(grid)
        layout.addStretch()

    def _initial_update(self) -> None:
        """Get initial status from service."""
        try:
            status = self.ipc_client.get_status()
            self.update_from_status(status)
        except RuntimeError:
            pass

    def update_from_status(self, status: dict) -> None:
        """Update displayed status from service response."""
        if status.get("status") == "error":
            self.temp_label.setText("Error")
            return
        
        temp = status.get("temperature", 0)
        self.temp_label.setText(f"{temp}°C")
        
        # Color code temperature
        if temp < 60:
            self.temp_label.setStyleSheet("color: green;")
        elif temp < 75:
            self.temp_label.setStyleSheet("color: orange;")
        else:
            self.temp_label.setStyleSheet("color: red;")
        
        # Update other metrics (placeholder - would need extended status from service)
        oc_enabled = status.get("oc_enabled", False)
        self.oc_status_label.setText("Enabled" if oc_enabled else "Disabled")
        self.oc_status_label.setStyleSheet("color: green;" if oc_enabled else "color: gray;")
