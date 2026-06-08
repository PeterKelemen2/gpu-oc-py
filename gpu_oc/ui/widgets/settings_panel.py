"""Settings panel for OC configuration."""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer

from gpu_oc.ipc import IPCClient


class SettingsPanel(QWidget):
    """GPU OC settings with sliders and tooltips."""

    def __init__(self, ipc_client: IPCClient):
        super().__init__()
        self.ipc_client = ipc_client
        self.config = {}
        
        self._setup_ui()
        self._load_config()

    def _setup_ui(self) -> None:
        """Setup UI with settings controls."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("GPU OC Settings")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        grid = QGridLayout()
        
        # Core Offset
        grid.addWidget(QLabel("Core Offset (MHz):"), 0, 0)
        grid.addWidget(QLabel("-500"), 0, 1)
        self.core_offset_slider = QSlider(Qt.Orientation.Horizontal)
        self.core_offset_slider.setRange(-500, 500)
        self.core_offset_slider.setTickInterval(50)
        self.core_offset_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        grid.addWidget(self.core_offset_slider, 0, 2)
        grid.addWidget(QLabel("500"), 0, 3)
        
        self.core_offset_value = QSpinBox()
        self.core_offset_value.setRange(-500, 500)
        self.core_offset_slider.valueChanged.connect(self.core_offset_value.setValue)
        self.core_offset_value.valueChanged.connect(self.core_offset_slider.setValue)
        grid.addWidget(self.core_offset_value, 0, 4)
        
        core_tooltip = QLabel("Higher = better performance + more heat. Range: -500 to +500 MHz")
        core_tooltip.setStyleSheet("color: gray; font-size: 10px;")
        grid.addWidget(core_tooltip, 1, 1, 1, 4)
        
        # Power Limit
        grid.addWidget(QLabel("Power Limit (W):"), 2, 0)
        self.power_limit_spin = QSpinBox()
        self.power_limit_spin.setRange(1, 600)
        grid.addWidget(self.power_limit_spin, 2, 1, 1, 2)
        
        power_tooltip = QLabel("Lower = cooler but potentially throttled. Check your PSU rating.")
        power_tooltip.setStyleSheet("color: gray; font-size: 10px;")
        grid.addWidget(power_tooltip, 3, 1, 1, 4)
        
        # Max Core Clock
        grid.addWidget(QLabel("Max Core Clock (MHz):"), 4, 0)
        self.max_clock_spin = QSpinBox()
        self.max_clock_spin.setRange(100, 4000)
        grid.addWidget(self.max_clock_spin, 4, 1, 1, 2)
        
        max_clock_tooltip = QLabel("Hard cap on clock speed. Prevents thermal runaway.")
        max_clock_tooltip.setStyleSheet("color: gray; font-size: 10px;")
        grid.addWidget(max_clock_tooltip, 5, 1, 1, 4)
        
        layout.addLayout(grid)
        
        # Apply button
        apply_btn = QPushButton("Apply Settings")
        apply_btn.clicked.connect(self._apply_settings)
        layout.addWidget(apply_btn)
        
        layout.addStretch()

    def _load_config(self) -> None:
        """Load current config from service."""
        try:
            self.config = self.ipc_client.get_config()
            self.core_offset_slider.setValue(self.config.get("core_offset_mhz", 0))
            self.power_limit_spin.setValue(self.config.get("power_limit_watt", 250))
            self.max_clock_spin.setValue(self.config.get("max_core_clock_mhz", 2000))
        except RuntimeError as e:
            QMessageBox.warning(self, "Error", f"Failed to load config: {e}")

    def _apply_settings(self) -> None:
        """Apply new settings."""
        # Note: Settings are typically read-only from the service
        # This is a placeholder for future settings persistence
        QMessageBox.information(
            self,
            "Info",
            "Settings are controlled via config.toml.\n"
            "Edit /opt/gpu-oc/config/config.toml and restart the service.",
        )
