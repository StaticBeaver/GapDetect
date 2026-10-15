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

# ═══════════════════════════════════════════════════════════════
# THEME PALETTE
# Flat design in the spirit of Material 3 / modern Google apps (Keep, Pay),
# without glassy effects: soft neutral surfaces, a single accent color,
# and cards separated by subtle shadows (elevation) instead of thick borders.
# Light/dark mode is read automatically from the Windows system theme.
# ═══════════════════════════════════════════════════════════════

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
    danger_pressed = _shade(c['danger'], -20)
    return f"""
        QWidget {{
            color: {c['fg_primary']};
            font-family: 'Google Sans', 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
        }}
        QWidget#AppShell {{
            background-color: {c['bg_window']};
            border: none;
            border-radius: 22px;
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
            border: none;
            border-radius: 0px;
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
            font-size: 18px;
            font-weight: 500;
            min-height: 40px;
        }}
        QComboBox#DeviceCombo QAbstractItemView::item {{
            font-size: 17px;
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
            border-radius: 17px;
        }}
        QPushButton#IconBtn:hover {{ background-color: {c['bg_input']}; }}
        QPushButton#IconBtn:pressed {{ background-color: {c['bg_input_hover']}; }}

        QPushButton#WinMinBtn, QPushButton#WinLangBtn {{
            background-color: transparent;
            border-radius: 0px;
            font-weight: 500;
            font-size: 13px;
            color: {c['fg_secondary']};
        }}
        QPushButton#WinMinBtn:hover, QPushButton#WinLangBtn:hover {{ background-color: {c['bg_input']}; }}
        QPushButton#WinMinBtn:pressed, QPushButton#WinLangBtn:pressed {{ background-color: {c['bg_input_hover']}; }}

        QPushButton#WinCloseBtn {{
            background-color: transparent;
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
            border-top-right-radius: 18px;
        }}
        QPushButton#WinCloseBtn:hover {{ background-color: {c['danger']}; }}
        QPushButton#WinCloseBtn:pressed {{ background-color: {danger_pressed}; }}

        QPushButton#BtnPrimary {{
            background-color: {c['accent']};
            color: {c['bg_panel']};
            font-size: 16px;
            font-weight: 500;
            border-radius: 28px;
        }}
        QPushButton#BtnPrimary:hover {{ background-color: {accent_hover}; }}
        QPushButton#BtnPrimary:pressed {{ background-color: {accent_pressed}; }}
        QPushButton#BtnPrimary:disabled {{ background-color: {c['bg_input']}; color: {c['fg_secondary']}; }}

        QPushButton#BtnSecondary {{
            background-color: {c['accent_container']};
            color: {c['on_accent_container']};
            font-size: 16px;
            font-weight: 500;
            border-radius: 28px;
        }}
        QPushButton#BtnSecondary:hover {{ background-color: {c['bg_input_hover']}; }}
        QPushButton#BtnSecondary:pressed {{ background-color: {c['bg_input']}; }}
        QPushButton#BtnSecondary:disabled {{ background-color: {c['bg_input']}; color: {c['fg_secondary']}; }}

        QProgressBar {{
            border: none;
            background-color: {c['bg_input']};
            border-radius: 2px;
        }}
        QProgressBar::chunk {{
            background-color: {c['accent']};
            border-radius: 2px;
        }}

        QMessageBox {{
            background-color: {c['bg_panel']};
        }}
        QMessageBox QLabel {{
            color: {c['fg_primary']};
            font-size: 13px;
        }}
        QMessageBox QPushButton {{
            background-color: {c['accent']};
            color: {c['bg_panel']};
            border-radius: 8px;
            padding: 6px 18px;
            min-width: 60px;
            font-weight: 500;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {accent_hover};
        }}
        QMessageBox QPushButton:pressed {{
            background-color: {accent_pressed};
        }}
    """


TRANSLATIONS = {
    "tr": {
        "window_title": "GapDetect Pro",
        "header_title": "GapDetect",
        "btn_minimize_tip": "Simge durumuna küçült",
        "btn_close_tip": "Kapat",
        "conn_group": "Cihaz",
        "btn_refresh": "Yenile",
        "lbl_dpi": "Çözünürlük",
        "dpi_help_title": "DPI değerini nasıl bulurum?",
        "dpi_help_text": (
            "Yazıcınızın DPI değerini şu yollarla öğrenebilirsiniz:\n\n"
            "• Yazıcının alt/arka kısmındaki etiket veya kutusunda genelde yazar.\n"
            "• Kullanım kılavuzunun teknik özellikler bölümünde belirtilir.\n"
            "• İnternette \"<yazıcı modeliniz> dpi\" şeklinde arama yaparak "
            "üretici sitesinden bulabilirsiniz (örn. \"Xprinter XP-DT325B dpi\").\n\n"
            "Genel kural: çoğu ucuz/orta segment etiket yazıcısı 203 DPI'dır, "
            "yüksek çözünürlüklü modeller 300 veya 600 DPI olabilir. Emin "
            "değilseniz 203 DPI ile başlayın."
        ),
        "control_group": "İşlemler",
        "status_waiting": "Bekleniyor",
        "btn_calibrate": "Ölçüm Yap",
        "btn_get_info": "Bilgileri Getir",
        "result_group": "Sonuçlar",
        "lbl_length_title": "Etiket Boyu",
        "lbl_gap_title": "Gap",
        "lbl_length": "{0}",
        "lbl_length_empty": "—",
        "lbl_gap": "{0}",
        "lbl_gap_empty": "—",
        "device_not_found": "Cihaz bulunamadı",
        "status_not_found": "Cihaz bulunamadı",
        "status_connecting": "Bağlanıyor…",
        "status_connected": "Bağlandı",
        "status_error": "Bağlantı Hatası",
        "msg_error_title": "Hata",
        "msg_conn_error_title": "Bağlantı Hatası",
        "msg_conn_error": "Cihaza bağlanılamadı:\n{0}",
        "msg_comm_error_title": "İletişim Hatası",
        "msg_comm_error": "İşlem başarısız:\n{0}",
        "msg_read_warn_title": "Uyarı",
        "msg_read_warn": "Yazıcıdan veri okunamadı.",
        "msg_info_title": "Bilgi",
        "msg_parse_fail": "Yazıcıdan veriler alındı ancak boyut bilgisi ayrıştırılamadı.\n\nGelen Veri (Özet):\n{0}",
        "footer_text": "Static Beaver tarafından geliştirilmiştir © 2026",
    },
    "en": {
        "window_title": "GapDetect Pro",
        "header_title": "GapDetect",
        "btn_minimize_tip": "Minimize",
        "btn_close_tip": "Close",
        "conn_group": "Device",
        "btn_refresh": "Refresh",
        "lbl_dpi": "Resolution",
        "dpi_help_title": "How do I find my printer's DPI?",
        "dpi_help_text": (
            "You can find your printer's DPI value here:\n\n"
            "• It's usually printed on a label on the bottom/back of the printer.\n"
            "• Listed in the technical specifications of the user manual.\n"
            "• Search online for \"<your printer model> dpi\" and check the "
            "manufacturer's site (e.g. \"Xprinter XP-DT325B dpi\").\n\n"
            "Rule of thumb: most budget/mid-range label printers are 203 DPI, "
            "higher-resolution models may be 300 or 600 DPI. If unsure, start "
            "with 203 DPI."
        ),
        "control_group": "Actions",
        "status_waiting": "Waiting",
        "btn_calibrate": "Calibrate",
        "btn_get_info": "Get Info",
        "result_group": "Results",
        "lbl_length_title": "Label Length",
        "lbl_gap_title": "Gap",
        "lbl_length": "{0}",
        "lbl_length_empty": "—",
        "lbl_gap": "{0}",
        "lbl_gap_empty": "—",
        "device_not_found": "No device found",
        "status_not_found": "No device found",
        "status_connecting": "Connecting…",
        "status_connected": "Connected",
        "status_error": "Connection Error",
        "msg_error_title": "Error",
        "msg_conn_error_title": "Connection Error",
        "msg_conn_error": "Could not connect to device:\n{0}",
        "msg_comm_error_title": "Communication Error",
        "msg_comm_error": "Operation failed:\n{0}",
        "msg_read_warn_title": "Warning",
        "msg_read_warn": "Could not read data from printer.",
        "msg_info_title": "Info",
        "msg_parse_fail": "Data received from printer but size could not be parsed.\n\nReceived Data (Summary):\n{0}",
        "footer_text": "Developed by Static Beaver © 2026",
    }
}

# state -> (translation key, palette color key or None=fg_secondary)
STATUS_STYLES = {
    "waiting": ("status_waiting", None),
    "connecting": ("status_connecting", "accent"),
    "connected": ("status_connected", "success"),
    "error": ("status_error", "danger"),
    "not_found": ("status_not_found", "danger"),
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
    """Since the native Windows title bar is removed (frameless window),
    this widget takes care of dragging the window with the mouse. Both the
    header and the whole body (shell) use it. Clickable controls such as
    buttons and combo boxes consume their own events, so only clicks on
    empty areas reach this widget (Qt forwards unhandled mouse events to
    the parent widget by default), which lets the window be dragged from
    there as well."""

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


def _make_icon_button(name, color, size=36, icon_size=15, object_name="IconBtn"):
    btn = QPushButton()
    btn.setObjectName(object_name)
    btn.setIcon(icons.icon(name, color))
    btn.setIconSize(QSize(icon_size, icon_size))
    btn.setFixedSize(size, size)
    btn.setCursor(Qt.PointingHandCursor)
    return btn


def _add_elevation(widget, blur=20, alpha=25, y_offset=2):
    """Gives the Material 'elevation' feel with a soft, subtle shadow
    instead of a thick border - no outline around the cards."""
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
        self.current_lang = self.settings.value("language", "en")
        if self.current_lang not in TRANSLATIONS:
            self.current_lang = "en"

        self.printer = PrinterInterface()
        self.worker = None
        self.is_connecting = False
        self.current_status_state = "waiting"

        self.last_length_str = None
        self.last_gap_str = None

        self.setWindowTitle(self.t("window_title"))
        self.setWindowIcon(icons.app_icon())

        # Remove the native Windows title bar and replace it with our own
        # header that matches the theme colors. The window itself is made
        # transparent and the actual visible surface (a rounded "shell") is
        # placed inside it with some padding - this way a soft, subtle
        # shadow falls outside the window, and the corners look rounded and
        # properly anti-aliased instead of hard/square.
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer_widget = QWidget()
        self.setCentralWidget(outer_widget)
        outer_layout = QVBoxLayout(outer_widget)
        outer_layout.setContentsMargins(14, 14, 14, 14)

        shell = DraggableArea(self)
        shell.setObjectName("AppShell")
        _add_elevation(shell, blur=32, alpha=45, y_offset=6)
        outer_layout.addWidget(shell)

        main_layout = QVBoxLayout(shell)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Header: icon/title on the left; on the right, rectangular
        # minimize/close buttons that fill all the way to the corner, like
        # the native Windows title bar. This row itself has no margins so the
        # buttons really stick to the edge/corner; the content on the left
        # carries its own inner padding.
        header = DraggableArea(self)
        # QVBoxLayout distributes extra vertical space arbitrarily between
        # two "Preferred" widgets (header + content) with no stretch/spacer
        # between them - this was needlessly inflating the header, leaving
        # the title vertically centered with empty space above and below.
        # Making the header vertically Fixed locks it to the size of its own
        # content; the remaining space goes to the content below.
        header.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        header_left = QWidget()
        header_left_layout = QHBoxLayout(header_left)
        header_left_layout.setContentsMargins(24, 6, 8, 6)
        header_left_layout.setSpacing(10)

        header_icon = QLabel()
        header_icon.setPixmap(icons.logo_pixmap(22))
        header_left_layout.addWidget(header_icon)

        self.lbl_header_title = QLabel(self.t("header_title"))
        self.lbl_header_title.setStyleSheet(
            f"font-size: 18px; font-weight: 600; color: {PALETTE['fg_title']}; background: transparent;"
        )
        header_left_layout.addWidget(self.lbl_header_title)

        header_layout.addWidget(header_left, 0, Qt.AlignVCenter)
        header_layout.addStretch(1)

        # Since the native title bar is gone, we have to provide our own
        # minimize / close buttons. The language toggle button (EN/TR) sits
        # in the same row with the same rectangular, cornerless style, like a
        # third "window control" - clicking it switches to the other
        # language, and the button always shows the language it will SWITCH
        # TO (it reads "TR" while English is active). All of them are
        # gapless and fill up to the corner like native Windows title bar
        # buttons - deliberately different from round/floating icon buttons.
        # Only the outer top corner of the close button matches the corner
        # radius of the body (AppShell) so it doesn't overflow.
        self.btn_lang_toggle = QPushButton()
        self.btn_lang_toggle.setObjectName("WinLangBtn")
        self.btn_lang_toggle.setFixedSize(44, 44)
        self.btn_lang_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_lang_toggle.clicked.connect(self.toggle_language)

        self.btn_minimize = QPushButton()
        self.btn_minimize.setObjectName("WinMinBtn")
        self.btn_minimize.setIcon(icons.icon('fa5s.window-minimize', PALETTE['fg_secondary']))
        self.btn_minimize.setIconSize(QSize(13, 13))
        self.btn_minimize.setFixedSize(44, 44)
        self.btn_minimize.setCursor(Qt.PointingHandCursor)
        self.btn_minimize.setToolTip(self.t("btn_minimize_tip"))
        self.btn_minimize.clicked.connect(self.showMinimized)

        self.btn_close = QPushButton()
        self.btn_close.setObjectName("WinCloseBtn")
        self.btn_close.setIcon(icons.icon('fa5s.times', PALETTE['fg_secondary']))
        self.btn_close.setIconSize(QSize(14, 14))
        self.btn_close.setFixedSize(44, 44)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setToolTip(self.t("btn_close_tip"))
        self.btn_close.clicked.connect(self.close)

        win_btns = QWidget()
        win_btns_layout = QHBoxLayout(win_btns)
        win_btns_layout.setContentsMargins(0, 0, 0, 0)
        win_btns_layout.setSpacing(0)
        win_btns_layout.addWidget(self.btn_lang_toggle)
        win_btns_layout.addWidget(self.btn_minimize)
        win_btns_layout.addWidget(self.btn_close)
        header_layout.addWidget(win_btns, 0, Qt.AlignVCenter)

        main_layout.addWidget(header)

        # --- Content area ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(24, 6, 24, 8)
        main_layout.addWidget(content_widget)

        # --- Device, resolution and status: two rows on a single surface,
        # split by a thin divider (instead of separate shadowed cards) - one
        # card + one shadow instead of three cards + three shadows, cleaner
        # and more minimal. The second row holds DPI and connection status
        # side by side, separated by a stretch - the status no longer fills
        # an empty card on its own.

        control_panel = QFrame()
        control_panel.setObjectName("Panel")
        _add_elevation(control_panel)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(18, 0, 12, 0)
        control_layout.setSpacing(0)

        device_row_layout = QHBoxLayout()
        device_row_layout.setContentsMargins(0, 10, 0, 10)
        device_row_layout.setSpacing(8)

        self.combo_devices = QComboBox()
        self.combo_devices.setObjectName("DeviceCombo")
        self.combo_devices.currentIndexChanged.connect(self.on_device_selected)

        self.btn_refresh = _make_icon_button('fa5s.sync-alt', PALETTE['fg_secondary'], size=34, icon_size=15)
        self.btn_refresh.setToolTip(self.t("btn_refresh"))
        self.btn_refresh.clicked.connect(self.update_device_list)

        device_row_layout.addWidget(self.combo_devices, stretch=1)
        device_row_layout.addWidget(self.btn_refresh)
        control_layout.addLayout(device_row_layout)

        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFixedHeight(1)
        control_layout.addWidget(divider)

        # Label length calculation depends on the printer's dots-per-mm
        # resolution (203 DPI = 8 dot/mm, 300 DPI = ~11.8 dot/mm, ...).
        # Instead of hard-coding it, we let the user pick it for their
        # printer; otherwise other models would silently get wrong mm values.
        meta_row_layout = QHBoxLayout()
        meta_row_layout.setContentsMargins(0, 10, 0, 10)
        meta_row_layout.setSpacing(8)

        self.lbl_dpi = QLabel(self.t("lbl_dpi"))
        self.combo_dpi = QComboBox()
        self.combo_dpi.addItem("203 DPI", 203)
        self.combo_dpi.addItem("300 DPI", 300)
        self.combo_dpi.addItem("600 DPI", 600)
        saved_dpi = int(self.settings.value("dpi", 203))
        idx = self.combo_dpi.findData(saved_dpi)
        self.combo_dpi.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_dpi.currentIndexChanged.connect(self.on_dpi_changed)

        self.btn_dpi_help = _make_icon_button('fa5s.question-circle', PALETTE['fg_secondary'], size=34, icon_size=15)
        self.btn_dpi_help.setToolTip(self.t("dpi_help_title"))
        self.btn_dpi_help.clicked.connect(self.show_dpi_help)

        self.status_dot = QLabel()
        self.lbl_status = QLabel(self.t("status_waiting"))
        self.lbl_status.setFont(QFont("Segoe UI", 11))

        meta_row_layout.addWidget(self.lbl_dpi)
        meta_row_layout.addWidget(self.combo_dpi)
        meta_row_layout.addWidget(self.btn_dpi_help)
        meta_row_layout.addStretch(1)
        meta_row_layout.addWidget(self.status_dot)
        meta_row_layout.addWidget(self.lbl_status)
        control_layout.addLayout(meta_row_layout)

        content_layout.addWidget(control_panel)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        self.btn_calibrate = QPushButton(self.t("btn_calibrate"))
        self.btn_calibrate.setObjectName("BtnPrimary")
        self.btn_calibrate.setIcon(icons.icon('fa5s.ruler-combined', PALETTE['bg_panel']))
        self.btn_calibrate.setMinimumHeight(56)
        self.btn_calibrate.clicked.connect(self.do_calibrate)
        self.btn_calibrate.setEnabled(False)
        self.btn_calibrate.setCursor(Qt.PointingHandCursor)

        self.btn_send_cmd = QPushButton(self.t("btn_get_info"))
        self.btn_send_cmd.setObjectName("BtnSecondary")
        self.btn_send_cmd.setIcon(icons.icon('fa5s.download', PALETTE['on_accent_container']))
        self.btn_send_cmd.setMinimumHeight(56)
        self.btn_send_cmd.clicked.connect(self.send_and_read)
        self.btn_send_cmd.setEnabled(False)
        self.btn_send_cmd.setCursor(Qt.PointingHandCursor)

        actions_row.addWidget(self.btn_calibrate, stretch=1)
        actions_row.addWidget(self.btn_send_cmd, stretch=1)
        content_layout.addLayout(actions_row)

        # --- Results: two simple cards, large value + small secondary title ---
        result_layout = QHBoxLayout()
        result_layout.setSpacing(10)

        length_tile = QFrame()
        length_tile.setObjectName("ResultTile")
        _add_elevation(length_tile)
        length_tile_layout = QVBoxLayout(length_tile)
        length_tile_layout.setContentsMargins(18, 16, 18, 16)
        length_tile_layout.setSpacing(6)
        self.lbl_length_title = QLabel(self.t("lbl_length_title"))
        self.lbl_length_title.setStyleSheet(f"color: {PALETTE['fg_secondary']}; font-size: 13px; font-weight: 500; border: none;")
        self.lbl_length = QLabel(self.t("lbl_length_empty"))
        self.lbl_length.setWordWrap(True)
        self.lbl_length.setStyleSheet(f"font-weight: 600; font-size: 27px; color: {PALETTE['fg_primary']}; border: none;")
        length_tile_layout.addWidget(self.lbl_length_title)
        length_tile_layout.addWidget(self.lbl_length)

        gap_tile = QFrame()
        gap_tile.setObjectName("ResultTile")
        _add_elevation(gap_tile)
        gap_tile_layout = QVBoxLayout(gap_tile)
        gap_tile_layout.setContentsMargins(18, 16, 18, 16)
        gap_tile_layout.setSpacing(6)
        self.lbl_gap_title = QLabel(self.t("lbl_gap_title"))
        self.lbl_gap_title.setStyleSheet(f"color: {PALETTE['fg_secondary']}; font-size: 13px; font-weight: 500; border: none;")
        self.lbl_gap = QLabel(self.t("lbl_gap_empty"))
        self.lbl_gap.setWordWrap(True)
        self.lbl_gap.setStyleSheet(f"font-weight: 600; font-size: 27px; color: {PALETTE['fg_primary']}; border: none;")
        gap_tile_layout.addWidget(self.lbl_gap_title)
        gap_tile_layout.addWidget(self.lbl_gap)

        result_layout.addWidget(length_tile)
        result_layout.addWidget(gap_tile)
        content_layout.addLayout(result_layout)

        footer_layout = QHBoxLayout()
        self.lbl_footer = QLabel(self.t("footer_text"))
        self.lbl_footer.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_footer.setFont(QFont("Segoe UI", 9))
        self.lbl_footer.setStyleSheet(f"color: {PALETTE['fg_secondary']};")
        footer_layout.addWidget(self.lbl_footer, stretch=1)
        content_layout.addLayout(footer_layout)

        # A frameless window loses edge-drag resizing, so a size grip is
        # needed. To keep it from being buried inside the content padding
        # and make it really stick to the bottom-right corner, it is added
        # directly to the shell as a free child widget (not to the layout)
        # and positioned manually.
        self._shell = shell
        self.size_grip = QSizeGrip(shell)
        self.size_grip.setFixedSize(16, 16)
        self.size_grip.raise_()

        self._update_lang_toggle_text()
        self._set_status("waiting")
        self.update_device_list()

        # The smallest size the window can actually fit into is computed
        # from the built layout instead of guessing a fixed number -
        # otherwise a small hand-picked value caused widgets to overlap
        # when the content didn't fit. The outer_widget's own minimum size
        # is used so the 14px margins left for the shadow are included.
        min_size = outer_widget.minimumSizeHint()
        self.setMinimumSize(min_size)
        # Snap to the actual computed minimum instead of a fixed 580px base
        # for a compact, minimal window - forcing extra height used to get
        # distributed to widgets like the header, causing needless gaps.
        self.resize(max(420, min_size.width()), min_size.height())
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

    def t(self, key):
        return TRANSLATIONS[self.current_lang].get(key, key)

    def toggle_language(self):
        self.current_lang = "tr" if self.current_lang == "en" else "en"
        self.settings.setValue("language", self.current_lang)
        self._update_lang_toggle_text()
        self.update_ui_texts()

    def _update_lang_toggle_text(self):
        # The button always shows the language it will SWITCH TO.
        self.btn_lang_toggle.setText("TR" if self.current_lang == "en" else "EN")

    def on_dpi_changed(self):
        self.settings.setValue("dpi", self.combo_dpi.currentData())

    def show_dpi_help(self):
        QMessageBox.information(self, self.t("dpi_help_title"), self.t("dpi_help_text"))

    def _set_status(self, state):
        """Sets the status icon (colored dot) and text consistently, from a single place."""
        self.current_status_state = state
        key, color_key = STATUS_STYLES[state]
        color = PALETTE[color_key] if color_key else PALETTE['fg_secondary']
        bold = color_key is not None
        self.status_dot.setPixmap(icons.pixmap('fa5s.circle', color, 8))
        self.lbl_status.setText(self.t(key))
        self.lbl_status.setStyleSheet(f"color: {color}; font-weight: {'600' if bold else '400'};")

    def update_ui_texts(self):
        self.setWindowTitle(self.t("window_title"))
        self.lbl_header_title.setText(self.t("header_title"))
        self.btn_minimize.setToolTip(self.t("btn_minimize_tip"))
        self.btn_close.setToolTip(self.t("btn_close_tip"))
        self.btn_refresh.setToolTip(self.t("btn_refresh"))
        self.lbl_dpi.setText(self.t("lbl_dpi"))
        self.btn_dpi_help.setToolTip(self.t("dpi_help_title"))
        self.btn_calibrate.setText(self.t("btn_calibrate"))
        self.btn_send_cmd.setText(self.t("btn_get_info"))
        self.lbl_length_title.setText(self.t("lbl_length_title"))
        self.lbl_gap_title.setText(self.t("lbl_gap_title"))
        self.lbl_footer.setText(self.t("footer_text"))

        if self.last_length_str:
            self.lbl_length.setText(self.t("lbl_length").format(self.last_length_str))
        else:
            self.lbl_length.setText(self.t("lbl_length_empty"))

        if self.last_gap_str:
            self.lbl_gap.setText(self.t("lbl_gap").format(self.last_gap_str))
        else:
            self.lbl_gap.setText(self.t("lbl_gap_empty"))

        if self.combo_devices.count() == 1 and self.combo_devices.itemData(0) is None:
            self.combo_devices.setItemText(0, self.t("device_not_found"))

        self._set_status(self.current_status_state)

    def update_device_list(self):
        self.combo_devices.blockSignals(True)
        self.combo_devices.clear()

        com_ports = self.printer.get_com_ports()
        windows_printers = self.printer.get_windows_printers()

        last_device = self.settings.value("last_device")
        target_index = -1

        if not com_ports and not windows_printers:
            self.combo_devices.addItem(self.t("device_not_found"), None)
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
            self.btn_lang_toggle.setEnabled(enabled)
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
        self.btn_lang_toggle.setEnabled(True)

        if success:
            self.btn_calibrate.setEnabled(True)
            self.btn_send_cmd.setEnabled(True)
            self._set_status("connected")
        else:
            self.btn_calibrate.setEnabled(False)
            self.btn_send_cmd.setEnabled(False)
            self._set_status("error")
            QMessageBox.critical(self, self.t("msg_conn_error_title"), self.t("msg_conn_error").format(msg))

    def do_calibrate(self):
        self.set_ui_enabled(False)
        self.worker = WorkerThread(self.printer, "send", "GAPDETECT\r\n")
        self.worker.result_signal.connect(self.on_send_result)
        self.worker.start()

    def on_send_result(self, success, msg):
        self.set_ui_enabled(True)
        if not success:
            QMessageBox.warning(self, self.t("msg_comm_error_title"), self.t("msg_comm_error").format(msg))

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
            QMessageBox.warning(self, self.t("msg_read_warn_title"), self.t("msg_read_warn"))

    def parse_response(self, text):
        # dot->mm conversion depends on the printer's resolution (203 DPI = 8
        # dot/mm, 300 DPI = ~11.8 dot/mm, ...); a fixed "8.0" would silently
        # give wrong results on other models, so it's computed from the DPI.
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
                self.lbl_length.setText(self.t("lbl_length").format(self.last_length_str))
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
            self.lbl_length.setText(self.t("lbl_length").format(self.last_length_str))
            found_size = True

        if gap_match:
            try:
                dots = float(gap_match.group(1))
                mm = dots / dots_per_mm
                self.last_gap_str = f"{mm:.1f} mm"
                self.lbl_gap.setText(self.t("lbl_gap").format(self.last_gap_str))
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
            self.lbl_gap.setText(self.t("lbl_gap").format(self.last_gap_str))
            found_gap = True

        if not found_size and not found_gap:
            snippet = repr(text.strip()[:200])
            QMessageBox.information(self, self.t("msg_info_title"), self.t("msg_parse_fail").format(snippet))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(build_stylesheet(PALETTE))

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
