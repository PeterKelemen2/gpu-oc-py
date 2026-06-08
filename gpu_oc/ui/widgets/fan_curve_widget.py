"""Fan curve editor with draggable control points."""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QComboBox,
    QLabel,
    QSlider,
    QSpinBox,
)
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont

from gpu_oc.ipc import IPCClient


class FanCurveWidget(QWidget):
    """Draggable fan curve editor with temperature on x-axis, fan % on y-axis."""

    def __init__(self, ipc_client: IPCClient):
        super().__init__()
        self.ipc_client = ipc_client
        self.config = {}
        self.curve_points = [[30, 30], [45, 50], [60, 100]]
        self.dragging_index = -1
        self.current_temp = 0
        
        self._setup_ui()
        self._load_config()

    def _setup_ui(self) -> None:
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_layout = QHBoxLayout()
        
        title = QLabel("Fan Control")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_layout.addWidget(title)
        
        # Fan mode selector
        title_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Auto", "Curve", "Manual"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        title_layout.addWidget(self.mode_combo)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Container for mode-specific UI
        self.mode_container = QVBoxLayout()
        
        # Curve graph (shown in Curve mode)
        self.graph = FanCurveGraph(self.curve_points)
        self.graph.points_changed.connect(self._on_points_changed)
        
        # Manual fan slider (shown in Manual mode)
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Fan Speed:"))
        self.manual_slider = QSlider(Qt.Orientation.Horizontal)
        self.manual_slider.setRange(0, 100)
        self.manual_slider.setValue(50)
        manual_layout.addWidget(self.manual_slider)
        self.manual_value = QSpinBox()
        self.manual_value.setRange(0, 100)
        self.manual_value.setValue(50)
        self.manual_slider.valueChanged.connect(self.manual_value.setValue)
        self.manual_value.valueChanged.connect(self.manual_slider.setValue)
        manual_layout.addWidget(self.manual_value)
        manual_layout.addWidget(QLabel("%"))
        
        self.manual_widget = QWidget()
        self.manual_widget.setLayout(manual_layout)
        
        layout.addLayout(self.mode_container)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self._reset_curve)
        btn_layout.addWidget(reset_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply_settings)
        btn_layout.addWidget(apply_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()

    def _on_mode_changed(self, mode_text: str) -> None:
        """Update UI when mode changes."""
        # Clear previous widgets
        while self.mode_container.count():
            self.mode_container.removeWidget(self.mode_container.itemAt(0).widget())
        
        if mode_text == "Curve":
            self.mode_container.addWidget(self.graph)
        elif mode_text == "Manual":
            self.mode_container.addWidget(self.manual_widget)
        else:  # Auto
            self.mode_container.addWidget(QLabel("Auto mode: GPU controls fan based on its own thermal management."))


    def _load_config(self) -> None:
        """Load current config from service."""
        try:
            self.config = self.ipc_client.get_config()
            fan_mode = self.config.get("fan_mode", "auto")
            points = self.config.get("fan_curve_points", [[30, 30], [45, 50], [60, 100]])
            
            mode_index = {"auto": 0, "curve": 1, "manual": 2}.get(fan_mode, 0)
            self.mode_combo.setCurrentIndex(mode_index)
            
            self.curve_points = points
            self.graph.set_points(points)
        except RuntimeError as e:
            QMessageBox.warning(self, "Error", f"Failed to load config: {e}")

    def _on_points_changed(self, points: list) -> None:
        """Handle curve points change."""
        self.curve_points = points

    def _reset_curve(self) -> None:
        """Reset to default curve."""
        if self.mode_combo.currentText() == "Curve":
            self.curve_points = [[30, 30], [45, 50], [60, 100]]
            self.graph.set_points(self.curve_points)
        elif self.mode_combo.currentText() == "Manual":
            self.manual_value.setValue(50)

    def _apply_settings(self) -> None:
        """Apply fan settings based on current mode."""
        mode = self.mode_combo.currentText().lower()
        print(f"Applying fan settings: mode={mode}")
        
        try:
            if mode == "curve":
                result = self.ipc_client.set_fan_curve(self.curve_points)
                if result.get("status") == "ok":
                    QMessageBox.information(self, "Success", "Fan curve applied!")
                else:
                    QMessageBox.critical(self, "Error", result.get("error", "Unknown error"))
            elif mode == "manual":
                manual_percent = self.manual_value.value()
                print(f"Manual mode: {manual_percent}%")
                # TODO: Implement manual fan control via IPC
                QMessageBox.information(self, "Info", 
                    f"Manual fan control set to {manual_percent}%\n\n"
                    "Note: Direct fan control is not available on consumer GPUs.\n"
                    "This requires nvidia-settings with X11 display server.")
            else:  # auto
                QMessageBox.information(self, "Info", 
                    "Auto mode enabled.\nGPU will control fan based on its thermal management.")
        except RuntimeError as e:
            QMessageBox.critical(self, "Error", str(e))


class FanCurveGraph(QWidget):
    """Canvas for drawing and editing fan curve."""

    points_changed = pyqtSignal(list)

    def __init__(self, points: list):
        super().__init__()
        self.points = points
        self.dragging_index = -1
        self.setMinimumHeight(300)
        self.setStyleSheet("background-color: #f0f0f0;")

    def set_points(self, points: list) -> None:
        """Set new curve points."""
        self.points = points
        self.update()

    def paintEvent(self, event) -> None:
        """Draw the fan curve graph."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        margin = 50
        
        # Draw background grid
        painter.setPen(QPen(QColor(220, 220, 220)))
        for i in range(0, 101, 10):
            x = margin + (i / 100) * (w - 2 * margin)
            painter.drawLine(int(x), margin, int(x), h - margin)
            y = margin + (i / 100) * (h - 2 * margin)
            painter.drawLine(margin, int(y), w - margin, int(y))
        
        # Draw axes
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawLine(margin, h - margin, w - margin, h - margin)  # X-axis
        painter.drawLine(margin, h - margin, margin, margin)  # Y-axis
        
        # Draw axis labels
        painter.setFont(QFont("Arial", 10))
        painter.drawText(w - margin - 20, h - margin + 25, "Temperature (°C)")
        painter.save()
        painter.translate(20, h // 2)
        painter.rotate(-90)
        painter.drawText(0, 0, "Fan % (0-100)")
        painter.restore()
        
        # Draw curve
        if len(self.points) >= 2:
            painter.setPen(QPen(QColor(0, 120, 215), 2))
            for i in range(len(self.points) - 1):
                t1, f1 = self.points[i]
                t2, f2 = self.points[i + 1]
                
                x1 = margin + (t1 / 100) * (w - 2 * margin)
                y1 = h - margin - (f1 / 100) * (h - 2 * margin)
                x2 = margin + (t2 / 100) * (w - 2 * margin)
                y2 = h - margin - (f2 / 100) * (h - 2 * margin)
                
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Draw control points
        for i, (temp, fan) in enumerate(self.points):
            x = margin + (temp / 100) * (w - 2 * margin)
            y = h - margin - (fan / 100) * (h - 2 * margin)
            
            # Highlight if dragging
            if i == self.dragging_index:
                painter.setBrush(QBrush(QColor(255, 0, 0)))
            else:
                painter.setBrush(QBrush(QColor(0, 120, 215)))
            
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawEllipse(int(x) - 6, int(y) - 6, 12, 12)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press to start dragging."""
        w, h = self.width(), self.height()
        margin = 50
        
        # PyQt6: use event.position() instead of event.x()/y()
        pos = event.position()
        mouse_x, mouse_y = int(pos.x()), int(pos.y())
        
        for i, (temp, fan) in enumerate(self.points):
            x = margin + (temp / 100) * (w - 2 * margin)
            y = h - margin - (fan / 100) * (h - 2 * margin)
            
            if (mouse_x - x) ** 2 + (mouse_y - y) ** 2 < 100:  # 10px radius
                self.dragging_index = i
                break

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move to drag points."""
        if self.dragging_index >= 0:
            w, h = self.width(), self.height()
            margin = 50
            
            # PyQt6: use event.position() instead of event.x()/y()
            pos = event.position()
            mouse_x, mouse_y = int(pos.x()), int(pos.y())
            
            # Calculate new temp and fan from mouse position
            new_temp = max(0, min(100, int((mouse_x - margin) / (w - 2 * margin) * 100)))
            new_fan = max(0, min(100, int((h - margin - mouse_y) / (h - 2 * margin) * 100)))
            
            # Don't allow reordering by temperature
            if self.dragging_index > 0:
                new_temp = max(new_temp, self.points[self.dragging_index - 1][0] + 1)
            if self.dragging_index < len(self.points) - 1:
                new_temp = min(new_temp, self.points[self.dragging_index + 1][0] - 1)
            
            self.points[self.dragging_index] = [new_temp, new_fan]
            self.points_changed.emit(self.points)
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release to stop dragging."""
        self.dragging_index = -1
        self.update()
