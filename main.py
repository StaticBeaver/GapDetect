import sys
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QComboBox, QPushButton,
                             QMessageBox, QSizePolicy,
                             QFrame, QDesktopWidget, QSizeGrip,
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings, QSize
from PyQt5.QtGui import QFont, QColor
from printer_comms import PrinterInterface
import icons


def _detect_system_dark_mode():
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return value == 0
    except Exception:
        return False


LIGHT_PALETTE = {
    "bg_window": "#f4f6fb",
    "bg_panel": "#ffffff",
    "bg_input": "#eceff4",
    "bg_input_hover": "#e2e6ee",
    "fg_primary": "#1f2024",
    "fg_secondary": "#6b7076",
    "fg_title": "#1f2024",
    "accent": "#1a73e8",
    "accent_container": "#e3edfd",
    "on_accent_container": "#0b57be",
    "success": "#1e8e3e",
    "danger": "#d93025",
    "danger_container": "#fbe4e2",
}

DARK_PALETTE = {
    "bg_window": "#131417",
    "bg_panel": "#1e2024",
    "bg_input": "#2a2d32",
    "bg_input_hover": "#34373d",
    "fg_primary": "#e8eaed",
    "fg_secondary": "#9aa0a6",
    "fg_title": "#e8eaed",
    "accent": "#8ab4f8",
    "accent_container": "#2c3a50",
    "on_accent_container": "#adc7f7",
    "success": "#81c995",
    "danger": "#f28b82",
    "danger_container": "#4c2523",
}

IS_DARK = _detect_system_dark_mode()
PALETTE = DARK_PALETTE if IS_DARK else LIGHT_PALETTE


def _shade(hex_color, amount):
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r = max(0, min(255, r + amount))
    g = max(0, min(255, g + amount))
    b = max(0, min(255, b + amount))
    return f"#{r:02x}{g:02x}{b:02x}"


def build_stylesheet(c):
    chevron_down = icons.icon_file('fa5s.chevron-down', c['fg_secondary'], 9)
    accent_hover, accent_pressed = _shade(c['accent'], -12), _shade(c['accent'], -24)
    danger_hover, danger_pressed = _shade(c['danger'], 15), _shade(c['danger'], -20)
    return f"""
        QWidget {{
            color: {c['fg_primary']};
            font-family: 'Google Sans', 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
        }}
        QWidget#AppShell {{
            background-color: {c['bg_window']};
            border: none;
            border-radius: 20px;
        }}
        QLabel {{ color: {c['fg_primary']}; background: transparent; }}
        QLabel#SectionCaption {{
            color: {c['fg_secondary']};
            font-size: 13px;
            font-weight: 500;
        }}

        QFrame#Panel, QFrame#ResultTile {{
            background-color: {c['bg_panel']};
            border: none;
            border-radius: 16px;
        }}

        QComboBox {{
            background: transparent;
            border: none;
            padding: 8px 6px;
            min-height: 36px;
            color: {c['fg_primary']};
            font-size: 15px;
        }}
        QComboBox::drop-down {{ border: none; width: 26px; }}
        QComboBox::down-arrow {{ image: url({chevron_down}); width: 12px; height: 12px; }}
        QComboBox QAbstractItemView {{
            background-color: {c['bg_panel']};
            color: {c['fg_primary']};
            selection-background-color: {c['accent_container']};
            selection-color: {c['on_accent_container']};
            border: 1px solid {c['bg_input']};
            border-radius: 10px;
            padding: 4px;
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 10px 12px;
            min-height: 34px;
            border-radius: 8px;
            font-size: 15px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {c['bg_input']};
        }}

        QComboBox#DeviceCombo {{
            font-size: 17px;
            font-weight: 500;
            min-height: 40px;
        }}
        QComboBox#DeviceCombo QAbstractItemView::item {{
            font-size: 16px;
            min-height: 40px;
        }}

        QFrame#Divider {{
            background-color: {c['bg_input']};
            border: none;
        }}

        QPushButton {{
            background: transparent;
            border: none;
            color: {c['fg_primary']};
        }}

        QPushButton#IconBtn {{
            background-color: transparent;
            border-radius: 16px;
        }}
        QPushButton#IconBtn:hover {{ background-color: {c['bg_input']}; }}
        QPushButton#IconBtn:pressed {{ background-color: {c['bg_input_hover']}; }}

        /* Modern round title bar buttons */
        QPushButton#WinMinBtn {{
            background-color: transparent;
            border-radius: 14px;
        }}
        QPushButton#WinMinBtn:hover {{ background-color: {c['bg_input']}; }}
        QPushButton#WinMinBtn:pressed {{ background-color: {c['bg_input_hover']}; }}

        QPushButton#WinCloseBtn {{
            background-color: transparent;
            border-radius: 14px;
        }}
        QPushButton#WinCloseBtn:hover {{
            background-color: {c['danger_container']};
        }}
        QPushButton#WinCloseBtn:pressed {{
            background-color: {c['danger']};
        }}

        QPushButton#BtnPrimary {{
            background-color: {c['accent']};
            color: {c['bg_panel']};
            font-size: 16px;
            font-weight: 600;
            border-radius: 26px;
        }}
        QPushButton#BtnPrimary:hover {{ background-color: {accent_hover}; }}
        QPushButton#BtnPrimary:pressed {{ background-color: {accent_pressed}; }}
        QPushButton#BtnPrimary:disabled {{ background-color: {c['bg_input']}; color: {c['fg_secondary']}; }}

        QPushButton#BtnSecondary {{
            background-color: {c['accent_container']};
            color: {c['on_accent_container']};
            font-size: 16px;
            font-weight: 600;
            border-radius: 26px;
        }}
        QPushButton#BtnSecondary:hover {{ background-color: {c['bg_input_hover']}; }}
        QPushButton#BtnSecondary:pressed {{ background-color: {c['bg_input']}; }}
        QPushButton#BtnSecondary:disabled {{ background-color: {c['bg_input']}; color: {c['fg_secondary']}; }}

        /* Dialog styling */
        QMessageBox {{
            background-color: {c['bg_panel']};
            border-radius: 14px;
        }}
        QMessageBox QLabel {{
            color: {c['fg_primary']};
            font-size: 13px;
        }}
        QMessageBox QPushButton {{
            background-color: {c['accent']};
            color: {c['bg_panel']};
            border-radius: 8px;
            padding: 8px 20px;
            min-width: 70px;
            font-weight: 600;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {accent_hover};
        }}
        QMessageBox QPushButton:pressed {{
            background-color: {accent_pressed};
        }}
    """


STATUS_STYLES = {
    "waiting": ("Waiting", None),
    "connecting": ("Connecting…", "accent"),
    "connected": ("Connected", "success"),
    "error": ("Connection Error", "danger"),
    "not_found": ("No device found", "danger"),
}


class WorkerThread(QThread):
    result_signal = pyqtSignal(bool, str)
    response_signal = pyqtSignal(str)

    def __init__(self, interface, action, *args):
        super().__init__()
        self.interface = interface
        self.action = action
        self.args = args

    def run(self):
        try:
            if self.action == "connect":
                device = self.args[0]
                if device.upper().startswith("COM"):
                    success, msg = self.interface.connect_serial(device)
                else:
                    success, msg = self.interface.connect_spooler(device)
                self.result_signal.emit(success, msg)

            elif self.action == "send":
                cmd = self.args[0]
                success, msg = self.interface.send_command(cmd)
                self.result_signal.emit(success, msg)

            elif self.action == "send_and_read":
                cmd = self.args[0]
                success, msg = self.interface.send_command(cmd)
                if not success:
                    self.result_signal.emit(False, msg)
                    return
                resp = self.interface.read_response()
                self.response_signal.emit(resp)

        except Exception as e:
            self.result_signal.emit(False, str(e))


class DraggableArea(QFrame):
    def __init__(self, target_window):
        super().__init__()
        self._target = target_window
        self._drag_offset = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPos() - self._target.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and (event.buttons() & Qt.LeftButton):
            self._target.move(event.globalPos() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None


def _make_icon_button(name, color, size=32, icon_size=14, object_name="IconBtn"):
    btn = QPushButton()
    btn.setObjectName(object_name)
    btn.setIcon(icons.icon(name, color))
    btn.setIconSize(QSize(icon_size, icon_size))
    btn.setFixedSize(size, size)
    btn.setCursor(Qt.PointingHandCursor)
    return btn


def _add_elevation(widget, blur=24, alpha=30, y_offset=4):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(y_offset)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("StaticBeaver", "GapDetect")
        self.printer = PrinterInterface()
        self.worker = None
        self.is_connecting = False
        self.current_status_state = "waiting"

        self.last_length_str = None
        self.last_gap_str = None

        self.setWindowTitle("GapDetect")
        self.setWindowIcon(icons.app_icon())

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer_widget = QWidget()
        self.setCentralWidget(outer_widget)
        outer_layout = QVBoxLayout(outer_widget)
        outer_layout.setContentsMargins(16, 16, 16, 16)

        shell = DraggableArea(self)
        shell.setObjectName("AppShell")
        _add_elevation(shell, blur=36, alpha=45, y_offset=6)
        outer_layout.addWidget(shell)

        main_layout = QVBoxLayout(shell)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Modern Header with rounded window controls ---
        header = DraggableArea(self)
        header.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 16, 10)
        header_layout.setSpacing(10)

        header_icon = QLabel()
        header_icon.setPixmap(icons.logo_pixmap(24))
        header_layout.addWidget(header_icon)

        self.lbl_header_title = QLabel("GapDetect")
        self.lbl_header_title.setStyleSheet(
            f"font-size: 17px; font-weight: 700; color: {PALETTE['fg_title']}; letter-spacing: -0.3px;"
        )
        header_layout.addWidget(self.lbl_header_title)

        header_layout.addStretch(1)

        # Elegant rounded minimize & close buttons
        self.btn_minimize = QPushButton()
        self.btn_minimize.setObjectName("WinMinBtn")
        self.btn_minimize.setIcon(icons.icon('fa5s.minus', PALETTE['fg_secondary']))
        self.btn_minimize.setIconSize(QSize(11, 11))
        self.btn_minimize.setFixedSize(28, 28)
        self.btn_minimize.setCursor(Qt.PointingHandCursor)
        self.btn_minimize.setToolTip("Minimize")
        self.btn_minimize.clicked.connect(self.showMinimized)

        self.btn_close = QPushButton()
        self.btn_close.setObjectName("WinCloseBtn")
        self.btn_close.setIcon(icons.icon('fa5s.times', PALETTE['fg_secondary']))
        self.btn_close.setIconSize(QSize(12, 12))
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setToolTip("Close")
        self.btn_close.clicked.connect(self.close)

        win_btns = QWidget()
        win_btns_layout = QHBoxLayout(win_btns)
        win_btns_layout.setContentsMargins(0, 0, 0, 0)
        win_btns_layout.setSpacing(6)
        win_btns_layout.addWidget(self.btn_minimize)
        win_btns_layout.addWidget(self.btn_close)
        header_layout.addWidget(win_btns, 0, Qt.AlignVCenter)

        main_layout.addWidget(header)

        # --- Content Area ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(18, 4, 18, 16)
        main_layout.addWidget(content_widget)

        # --- Device & Settings Panel ---
        control_panel = QFrame()
        control_panel.setObjectName("Panel")
        _add_elevation(control_panel, blur=18, alpha=20, y_offset=2)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(16, 2, 12, 2)
        control_layout.setSpacing(0)

        device_row_layout = QHBoxLayout()
        device_row_layout.setContentsMargins(0, 8, 0, 8)
        device_row_layout.setSpacing(8)

        self.combo_devices = QComboBox()
        self.combo_devices.setObjectName("DeviceCombo")
        self.combo_devices.currentIndexChanged.connect(self.on_device_selected)

        self.btn_refresh = _make_icon_button('fa5s.sync-alt', PALETTE['fg_secondary'], size=32, icon_size=13)
        self.btn_refresh.setToolTip("Refresh Devices")
        self.btn_refresh.clicked.connect(self.update_device_list)

        device_row_layout.addWidget(self.combo_devices, stretch=1)
        device_row_layout.addWidget(self.btn_refresh)
        control_layout.addLayout(device_row_layout)

        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFixedHeight(1)
        control_layout.addWidget(divider)

        meta_row_layout = QHBoxLayout()
        meta_row_layout.setContentsMargins(0, 8, 0, 8)
        meta_row_layout.setSpacing(8)

        self.lbl_dpi = QLabel("Resolution")
        self.lbl_dpi.setStyleSheet(f"color: {PALETTE['fg_secondary']}; font-size: 13px; font-weight: 500;")
        self.combo_dpi = QComboBox()
        self.combo_dpi.addItem("203 DPI", 203)
        self.combo_dpi.addItem("300 DPI", 300)
        self.combo_dpi.addItem("600 DPI", 600)
        saved_dpi = int(self.settings.value("dpi", 203))
        idx = self.combo_dpi.findData(saved_dpi)
        self.combo_dpi.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_dpi.currentIndexChanged.connect(self.on_dpi_changed)

        self.btn_dpi_help = _make_icon_button('fa5s.question-circle', PALETTE['fg_secondary'], size=30, icon_size=13)
        self.btn_dpi_help.setToolTip("How to find your printer's DPI?")
        self.btn_dpi_help.clicked.connect(self.show_dpi_help)

        self.status_dot = QLabel()
        self.lbl_status = QLabel("Waiting")
        self.lbl_status.setFont(QFont("Segoe UI", 10))

        meta_row_layout.addWidget(self.lbl_dpi)
        meta_row_layout.addWidget(self.combo_dpi)
        meta_row_layout.addWidget(self.btn_dpi_help)
        meta_row_layout.addStretch(1)
        meta_row_layout.addWidget(self.status_dot)
        meta_row_layout.addWidget(self.lbl_status)
        control_layout.addLayout(meta_row_layout)

        content_layout.addWidget(control_panel)

        # --- Action Buttons ---
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        self.btn_calibrate = QPushButton("Calibrate")
        self.btn_calibrate.setObjectName("BtnPrimary")
        self.btn_calibrate.setIcon(icons.icon('fa5s.ruler-combined', PALETTE['bg_panel']))
        self.btn_calibrate.setMinimumHeight(52)
        self.btn_calibrate.clicked.connect(self.do_calibrate)
        self.btn_calibrate.setEnabled(False)
        self.btn_calibrate.setCursor(Qt.PointingHandCursor)

        self.btn_send_cmd = QPushButton("Get Info")
        self.btn_send_cmd.setObjectName("BtnSecondary")
        self.btn_send_cmd.setIcon(icons.icon('fa5s.download', PALETTE['on_accent_container']))
        self.btn_send_cmd.setMinimumHeight(52)
        self.btn_send_cmd.clicked.connect(self.send_and_read)
        self.btn_send_cmd.setEnabled(False)
        self.btn_send_cmd.setCursor(Qt.PointingHandCursor)

        actions_row.addWidget(self.btn_calibrate, stretch=1)
        actions_row.addWidget(self.btn_send_cmd, stretch=1)
        content_layout.addLayout(actions_row)

        # --- Result Tiles ---
        result_layout = QHBoxLayout()
        result_layout.setSpacing(10)

        length_tile = QFrame()
        length_tile.setObjectName("ResultTile")
        _add_elevation(length_tile, blur=18, alpha=20, y_offset=2)
        length_tile_layout = QVBoxLayout(length_tile)
        length_tile_layout.setContentsMargins(18, 14, 18, 14)
        length_tile_layout.setSpacing(4)
        self.lbl_length_title = QLabel("Label Length")
        self.lbl_length_title.setStyleSheet(f"color: {PALETTE['fg_secondary']}; font-size: 13px; font-weight: 500; border: none;")
        self.lbl_length = QLabel("—")
        self.lbl_length.setWordWrap(True)
        self.lbl_length.setStyleSheet(f"font-weight: 700; font-size: 26px; color: {PALETTE['fg_primary']}; border: none;")
        length_tile_layout.addWidget(self.lbl_length_title)
        length_tile_layout.addWidget(self.lbl_length)

        gap_tile = QFrame()
        gap_tile.setObjectName("ResultTile")
        _add_elevation(gap_tile, blur=18, alpha=20, y_offset=2)
        gap_tile_layout = QVBoxLayout(gap_tile)
        gap_tile_layout.setContentsMargins(18, 14, 18, 14)
        gap_tile_layout.setSpacing(4)
        self.lbl_gap_title = QLabel("Gap")
        self.lbl_gap_title.setStyleSheet(f"color: {PALETTE['fg_secondary']}; font-size: 13px; font-weight: 500; border: none;")
        self.lbl_gap = QLabel("—")
        self.lbl_gap.setWordWrap(True)
        self.lbl_gap.setStyleSheet(f"font-weight: 700; font-size: 26px; color: {PALETTE['fg_primary']}; border: none;")
        gap_tile_layout.addWidget(self.lbl_gap_title)
        gap_tile_layout.addWidget(self.lbl_gap)

        result_layout.addWidget(length_tile)
        result_layout.addWidget(gap_tile)
        content_layout.addLayout(result_layout)

        # --- Footer ---
        footer_layout = QHBoxLayout()
        self.lbl_footer = QLabel("Developed by Static Beaver © 2026")
        self.lbl_footer.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_footer.setFont(QFont("Segoe UI", 9))
        self.lbl_footer.setStyleSheet(f"color: {PALETTE['fg_secondary']}; padding-top: 4px;")
        footer_layout.addWidget(self.lbl_footer, stretch=1)
        content_layout.addLayout(footer_layout)

        # Size grip
        self._shell = shell
        self.size_grip = QSizeGrip(shell)
        self.size_grip.setFixedSize(14, 14)
        self.size_grip.raise_()

        self._set_status("waiting")
        self.update_device_list()

        min_size = outer_widget.minimumSizeHint()
        self.setMinimumSize(min_size)
        self.resize(max(400, min_size.width()), min_size.height())
        self._center_on_screen()
        self._position_size_grip()

    def _position_size_grip(self):
        g = self.size_grip
        g.move(self._shell.width() - g.width() - 6, self._shell.height() - g.height() - 6)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_size_grip()

    def _center_on_screen(self):
        frame = self.frameGeometry()
        center = QDesktopWidget().availableGeometry().center()
        frame.moveCenter(center)
        self.move(frame.topLeft())

    def on_dpi_changed(self):
        self.settings.setValue("dpi", self.combo_dpi.currentData())

    def show_dpi_help(self):
        title = "How do I find my printer's DPI?"
        text = (
            "You can find your printer's DPI value through:\n\n"
            "• Printer label on the bottom/back of the device.\n"
            "• User manual specifications section.\n"
            "• Searching online for \"<model> dpi\" (e.g. \"Xprinter XP-DT325B dpi\").\n\n"
            "Tip: Most standard label printers are 203 DPI. If unsure, start with 203 DPI."
        )
        QMessageBox.information(self, title, text)

    def _set_status(self, state):
        self.current_status_state = state
        text, color_key = STATUS_STYLES.get(state, ("Waiting", None))
        color = PALETTE[color_key] if color_key else PALETTE['fg_secondary']
        bold = color_key is not None
        self.status_dot.setPixmap(icons.pixmap('fa5s.circle', color, 8))
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"color: {color}; font-weight: {'600' if bold else '400'};")

    def update_device_list(self):
        self.combo_devices.blockSignals(True)
        self.combo_devices.clear()

        com_ports = self.printer.get_com_ports()
        windows_printers = self.printer.get_windows_printers()

        last_device = self.settings.value("last_device")
        target_index = -1

        if not com_ports and not windows_printers:
            self.combo_devices.addItem("No device found", None)
            self.combo_devices.setEnabled(False)
            self.btn_calibrate.setEnabled(False)
            self.btn_send_cmd.setEnabled(False)
            self._set_status("not_found")
        else:
            for p in com_ports:
                self.combo_devices.addItem(f"COM Port: {p}", p)
                self.combo_devices.setItemData(self.combo_devices.count() - 1, p, Qt.ToolTipRole)
                if p == last_device:
                    target_index = self.combo_devices.count() - 1

            for dev_path, name in windows_printers:
                self.combo_devices.addItem(f"USB: {name}", dev_path)
                self.combo_devices.setItemData(self.combo_devices.count() - 1, dev_path, Qt.ToolTipRole)
                if dev_path == last_device:
                    target_index = self.combo_devices.count() - 1

            self.combo_devices.setEnabled(True)

            if target_index >= 0:
                self.combo_devices.setCurrentIndex(target_index)
            else:
                self.combo_devices.setCurrentIndex(0)

        self.combo_devices.blockSignals(False)

        if self.combo_devices.count() > 0 and self.combo_devices.currentData():
            self.on_device_selected(self.combo_devices.currentIndex())

    def set_ui_enabled(self, enabled):
        if not self.is_connecting:
            self.combo_devices.setEnabled(enabled)
            self.btn_refresh.setEnabled(enabled)
            self.combo_dpi.setEnabled(enabled)

        if self.printer.connection:
            self.btn_calibrate.setEnabled(enabled)
            self.btn_send_cmd.setEnabled(enabled)
        else:
            self.btn_calibrate.setEnabled(False)
            self.btn_send_cmd.setEnabled(False)

    def on_device_selected(self, index):
        device = self.combo_devices.itemData(index)
        if not device:
            return

        self.settings.setValue("last_device", device)

        if self.printer.connection:
            self.printer.close()

        self.is_connecting = True
        self.combo_devices.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.btn_calibrate.setEnabled(False)
        self.btn_send_cmd.setEnabled(False)
        self._set_status("connecting")

        self.worker = WorkerThread(self.printer, "connect", device)
        self.worker.result_signal.connect(self.on_connect_result)
        self.worker.start()

    def on_connect_result(self, success, msg):
        self.is_connecting = False
        self.combo_devices.setEnabled(True)
        self.btn_refresh.setEnabled(True)

        if success:
            self.btn_calibrate.setEnabled(True)
            self.btn_send_cmd.setEnabled(True)
            self._set_status("connected")
        else:
            self.btn_calibrate.setEnabled(False)
            self.btn_send_cmd.setEnabled(False)
            self._set_status("error")
            QMessageBox.critical(self, "Connection Error", f"Could not connect to device:\n{msg}")

    def do_calibrate(self):
        self.set_ui_enabled(False)
        self.worker = WorkerThread(self.printer, "send", "GAPDETECT\r\n")
        self.worker.result_signal.connect(self.on_send_result)
        self.worker.start()

    def on_send_result(self, success, msg):
        self.set_ui_enabled(True)
        if not success:
            QMessageBox.warning(self, "Communication Error", f"Operation failed:\n{msg}")

    def send_and_read(self):
        self.set_ui_enabled(False)
        self.worker = WorkerThread(self.printer, "send_and_read", "ALLCONFIG\r\n")
        self.worker.result_signal.connect(self.on_send_result)
        self.worker.response_signal.connect(self.on_read_result)
        self.worker.start()

    def on_read_result(self, response):
        self.set_ui_enabled(True)
        if response:
            self.parse_response(response)
        else:
            QMessageBox.warning(self, "Warning", "Could not read data from printer.")

    def parse_response(self, text):
        dpi = self.combo_dpi.currentData() or 203
        dots_per_mm = dpi / 25.4

        size_match = re.search(r"Paper Size:\s*([0-9.]+)", text, re.IGNORECASE)
        gap_match = re.search(r"Gap Size:\s*([0-9.]+)", text, re.IGNORECASE)

        size_match_alt = re.search(r"SIZE\s+([0-9.]+)\s*(mm|inch|dot)?\s*,\s*([0-9.]+)\s*(mm|inch|dot)?", text, re.IGNORECASE)
        gap_match_alt = re.search(r"GAP\s+([0-9.]+)\s*(mm|inch|dot)?\s*,\s*([0-9.]+)", text, re.IGNORECASE)

        found_size = False
        found_gap = False

        if size_match:
            try:
                dots = float(size_match.group(1))
                mm = dots / dots_per_mm
                self.last_length_str = f"{mm:.1f} mm"
                self.lbl_length.setText(self.last_length_str)
                found_size = True
            except Exception:
                pass
        elif size_match_alt:
            length = size_match_alt.group(3)
            unit = size_match_alt.group(4) or "mm"
            if unit.lower() == "dot":
                try:
                    length = f"{float(length) / dots_per_mm:.1f}"
                    unit = "mm"
                except Exception:
                    pass
            self.last_length_str = f"{length} {unit}"
            self.lbl_length.setText(self.last_length_str)
            found_size = True

        if gap_match:
            try:
                dots = float(gap_match.group(1))
                mm = dots / dots_per_mm
                self.last_gap_str = f"{mm:.1f} mm"
                self.lbl_gap.setText(self.last_gap_str)
                found_gap = True
            except Exception:
                pass
        elif gap_match_alt:
            gap_dist = gap_match_alt.group(1)
            unit = gap_match_alt.group(2) or "mm"
            if unit.lower() == "dot":
                try:
                    gap_dist = f"{float(gap_dist) / dots_per_mm:.1f}"
                    unit = "mm"
                except Exception:
                    pass
            self.last_gap_str = f"{gap_dist} {unit}"
            self.lbl_gap.setText(self.last_gap_str)
            found_gap = True

        if not found_size and not found_gap:
            snippet = repr(text.strip()[:200])
            QMessageBox.information(
                self,
                "Info",
                f"Data received from printer but dimensions could not be parsed.\n\nReceived Data (Summary):\n{snippet}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(build_stylesheet(PALETTE))

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
