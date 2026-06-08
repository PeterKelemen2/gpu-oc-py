"""System tray icon for GPU OC controller."""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtCore import Qt


class TrayIcon(QSystemTrayIcon):
    """System tray icon with context menu for quick access."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # Set icon (create a simple icon with a gear symbol)
        # For now, use a basic colored square; in production, use a proper GPU icon
        self._create_icon()
        
        # Setup context menu
        self._setup_menu()
        
        # Connect signals
        self.activated.connect(self._on_tray_activated)

    def _create_icon(self) -> None:
        """Create a simple application icon."""
        # Create a simple pixmap with GPU-like appearance
        from PyQt6.QtGui import QPixmap, QPainter
        
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.fillRect(4, 4, 24, 24, QColor(0, 120, 215))  # Windows blue
        painter.drawRect(4, 4, 24, 24)
        painter.end()
        
        self.setIcon(QIcon(pixmap))

    def _setup_menu(self) -> None:
        """Setup context menu."""
        menu = QMenu()
        
        # Show/hide window action
        show_action = menu.addAction("Show")
        show_action.triggered.connect(self._show_window)
        
        # Status action (read-only)
        status_action = menu.addAction("Status: Connected")
        status_action.setEnabled(False)
        
        menu.addSeparator()
        
        # Quit action
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._quit_app)
        
        self.setContextMenu(menu)

    def _on_tray_activated(self, reason) -> None:
        """Handle tray icon click."""
        from PyQt6.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self) -> None:
        """Show/toggle main window."""
        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.main_window.showNormal()
            self.main_window.activateWindow()

    def _quit_app(self) -> None:
        """Quit the application."""
        self.main_window.close()
        import sys
        sys.exit(0)
