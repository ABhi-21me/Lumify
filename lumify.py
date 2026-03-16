import sys
import ctypes
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QPoint
from PyQt5.QtGui import QColor, QPainter, QPen, QPainterPath, QIcon, QPixmap, QFont, QFontDatabase

WS_EX_LAYERED     = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
GWL_EXSTYLE       = -20

def set_clickthrough(hwnd):
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

def resource_path(f):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, f)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), f)

class Bridge(QObject):
    redraw = pyqtSignal()
bridge = Bridge()

# ── Ring Overlay ─────────────────────────────────────────────────────
class RingOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.enabled    = True
        self.brightness = 85
        self.warmth     = 4200
        self.corner_r   = 12
        bridge.redraw.connect(self.update)

    def get_color(self):
        w_min, w_max = 2000, 6500
        t = (self.warmth - w_min) / (w_max - w_min)
        if t < 0.5:
            s = t / 0.5
            r = int(255 - s * 60)
            g = int(255 - s * 30)
            b = 255
        else:
            s = (t - 0.5) / 0.5
            r = 255
            g = int(255 - s * 60)
            b = int(255 - s * 120)
        return r, g, b

    def paintEvent(self, event):
        if not self.enabled:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        sw, sh     = self.width(), self.height()
        brightness = self.brightness / 100.0
        r, g, b    = self.get_color()
        layers     = 22
        max_thick  = min(sw, sh) * 0.28 * 0.7
        for i in range(layers):
            t     = i / layers
            alpha = (t ** 1.2) * brightness * 1.4
            alpha = max(0.0, min(alpha, 1.0))
            if alpha < 0.012:
                continue
            color = QColor(r, g, b, int(alpha * 255))
            pad   = max_thick * (1 - t)
            lw    = max(2, int(max_thick * 0.22))
            painter.setPen(QPen(color, lw))
            painter.setBrush(Qt.NoBrush)
            path = QPainterPath()
            path.addRoundedRect(pad, pad, sw - 2*pad, sh - 2*pad, self.corner_r, self.corner_r)
            painter.drawPath(path)
        painter.end()

# ── Power Button Widget ───────────────────────────────────────────────
class PowerButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(130, 130)
        self._on = True

    def set_on(self, val):
        self._on = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        r = min(w, h) // 2 - 2

        # Background circle
        if self._on:
            grad = QColor(30, 37, 53)
            painter.setBrush(QColor(17, 21, 32))
        else:
            painter.setBrush(QColor(14, 14, 24))

        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - r, cy - r, 2*r, 2*r)

        # Border
        if self._on:
            border_color = QColor(96, 165, 250, 90)
        else:
            border_color = QColor(255, 255, 255, 20)
        pen = QPen(border_color, 1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(cx - r, cy - r, 2*r, 2*r)

        # Power icon
        icon_color = QColor(96, 165, 250) if self._on else QColor(255, 255, 255, 50)
        pen2 = QPen(icon_color, 2.8, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen2)

        # Vertical line
        painter.drawLine(cx, cy - 20, cx, cy - 8)

        # Arc
        from PyQt5.QtCore import QRectF
        arc_rect = QRectF(cx - 14, cy - 14, 28, 28)
        painter.drawArc(arc_rect, 45 * 16, 270 * 16)

        # Label
        lbl_color = QColor(96, 165, 250) if self._on else QColor(255, 255, 255, 50)
        painter.setPen(lbl_color)
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(0, cy + 16, w, 20, Qt.AlignCenter, "ON" if self._on else "OFF")

        painter.end()

# ── Control Panel ─────────────────────────────────────────────────────
class ControlPanel(QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay    = overlay
        self._drag_pos  = None
        self._listening = False
        self._shortcut  = "Space"
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(340)

        ico = resource_path("icon.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

        self._build_ui()
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center().x() - self.width()//2,
                  screen.center().y() - self.height()//2)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame()
        self.card.setObjectName("card")
        outer.addWidget(self.card)

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(0, 0, 0, 24)
        layout.setSpacing(0)

        # ── Titlebar ──
        tb = QFrame()
        tb.setObjectName("titlebar")
        tb_lay = QHBoxLayout(tb)
        tb_lay.setContentsMargins(18, 16, 18, 14)
        tb_lay.setSpacing(10)

        ico_lbl = QLabel()
        ico_path = resource_path("icon.png")
        if os.path.exists(ico_path):
            pix = QPixmap(ico_path).scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            ico_lbl.setPixmap(pix)
        else:
            ico_lbl.setText("🔆")
            ico_lbl.setFont(QFont("Segoe UI", 14))

        info = QVBoxLayout()
        info.setSpacing(1)
        t1 = QLabel("Lumify")
        t1.setObjectName("appTitle")
        t2 = QLabel("SMART CONTROL")
        t2.setObjectName("appSub")
        info.addWidget(t1)
        info.addWidget(t2)

        tb_lay.addWidget(ico_lbl)
        tb_lay.addLayout(info)
        tb_lay.addStretch()

        min_btn = QPushButton("−")
        min_btn.setObjectName("tbBtn")
        min_btn.setFixedSize(24, 24)
        min_btn.clicked.connect(self.showMinimized)

        close_btn = QPushButton("×")
        close_btn.setObjectName("tbClose")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(QApplication.quit)

        tb_lay.addWidget(min_btn)
        tb_lay.addSpacing(4)
        tb_lay.addWidget(close_btn)

        layout.addWidget(tb)
        layout.addWidget(self._div())

        # ── Power ──
        power_frame = QFrame()
        power_frame.setObjectName("powerFrame")
        pf_lay = QVBoxLayout(power_frame)
        pf_lay.setAlignment(Qt.AlignCenter)
        pf_lay.setContentsMargins(20, 32, 20, 28)

        self.power_btn = PowerButton()
        self.power_btn.clicked.connect(self.toggle_power)
        pf_lay.addWidget(self.power_btn, alignment=Qt.AlignCenter)

        layout.addWidget(power_frame)
        layout.addWidget(self._div())

        # ── Sliders ──
        sl_frame = QFrame()
        sl_lay = QVBoxLayout(sl_frame)
        sl_lay.setContentsMargins(20, 22, 20, 10)
        sl_lay.setSpacing(0)

        self._make_slider(sl_lay, "☀️  Brightness", 0, 100, 85, "%", "blue",
                          lambda v: self._set_overlay("brightness", v))
        self._make_slider(sl_lay, "🌡️  Warmth", 2000, 6500, 4200, "K", "warm",
                          lambda v: self._set_overlay("warmth", v))
        self._make_slider(sl_lay, "⬛  Corner Radius", 0, 32, 12, "px", "purple",
                          lambda v: self._set_overlay("corner_r", v))

        layout.addWidget(sl_frame)
        layout.addWidget(self._div())

        # ── Shortcut ──
        sc_frame = QFrame()
        sc_lay = QHBoxLayout(sc_frame)
        sc_lay.setContentsMargins(20, 22, 20, 0)

        sc_texts = QVBoxLayout()
        sc_texts.setSpacing(5)
        sc_title = QLabel("Shortcut")
        sc_title.setObjectName("scTitle")
        sc_sub = QLabel("Double click to change shortcut")
        sc_sub.setObjectName("scSub")
        sc_texts.addWidget(sc_title)
        sc_texts.addWidget(sc_sub)

        self.sc_badge = QPushButton(self._shortcut)
        self.sc_badge.setObjectName("scBadge")
        self.sc_badge.setFixedHeight(32)
        self.sc_badge.mouseDoubleClickEvent = self._start_listening

        sc_lay.addLayout(sc_texts)
        sc_lay.addStretch()
        sc_lay.addWidget(self.sc_badge)

        layout.addWidget(sc_frame)
        self._apply_styles()

    def _make_slider(self, parent_lay, label, lo, hi, default, unit, color, cb):
        row = QFrame()
        row.setObjectName("sliderRow")
        rl = QVBoxLayout(row)
        rl.setContentsMargins(0, 14, 0, 14)
        rl.setSpacing(12)

        top = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setObjectName("sliderLbl")
        val_lbl = QLabel(f"{default}{unit}")
        val_lbl.setObjectName(f"sliderVal_{color}")
        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(val_lbl)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(lo)
        slider.setMaximum(hi)
        slider.setValue(default)
        slider.setObjectName(f"slider_{color}")

        def on_change(v):
            val_lbl.setText(f"{v}{unit}")
            cb(v)

        slider.valueChanged.connect(on_change)
        rl.addLayout(top)
        rl.addWidget(slider)
        parent_lay.addWidget(row)

    def _div(self):
        d = QFrame()
        d.setObjectName("divider")
        d.setFrameShape(QFrame.HLine)
        d.setFixedHeight(1)
        return d

    def _set_overlay(self, attr, val):
        setattr(self.overlay, attr, val)
        bridge.redraw.emit()

    def toggle_power(self):
        self.overlay.enabled = not self.overlay.enabled
        self.power_btn.set_on(self.overlay.enabled)
        bridge.redraw.emit()

    def _start_listening(self, event=None):
        self._listening = True
        self.sc_badge.setText("...")
        self.sc_badge.setObjectName("scBadgeListening")
        self._apply_styles()

    def keyPressEvent(self, event):
        if self._listening:
            key = event.text().upper() if event.text() else event.key()
            if event.key() == Qt.Key_Space:
                key_name = "Space"
            elif event.text():
                key_name = event.text().upper()
            else:
                key_name = str(event.key())
            self._shortcut  = key_name
            self._listening = False
            self.sc_badge.setText(key_name)
            self.sc_badge.setObjectName("scBadge")
            self._apply_styles()
        else:
            if event.key() == Qt.Key_Space and self._shortcut == "Space":
                self.toggle_power()
            elif event.text() and event.text().upper() == self._shortcut:
                self.toggle_power()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.LeftButton:
            self.move(e.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    def _apply_styles(self):
        self.setStyleSheet("""
        QFrame#card {
            background: #0d0d14;
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.08);
        }
        QFrame#titlebar { background: transparent; }
        QLabel#appTitle { font-size:15px; font-weight:700; color:#ffffff; font-family:'Segoe UI'; }
        QLabel#appSub   { font-size:9px; color:rgba(255,255,255,0.3); font-family:'Segoe UI'; letter-spacing:2px; }

        QPushButton#tbBtn {
            background: none; border: none;
            color: rgba(255,255,255,0.45);
            font-size: 18px; font-family: 'Segoe UI';
        }
        QPushButton#tbBtn:hover { color: rgba(255,255,255,0.95); }
        QPushButton#tbClose {
            background: none; border: none;
            color: rgba(255,255,255,0.45);
            font-size: 16px; font-family: 'Segoe UI';
        }
        QPushButton#tbClose:hover { color: #ff4466; }

        QFrame#powerFrame { background: transparent; }
        QFrame#divider { background: rgba(255,255,255,0.05); border: none; }

        QFrame#sliderRow { background: transparent; border-bottom: 1px solid rgba(255,255,255,0.04); }
        QLabel#sliderLbl { font-size:13px; font-weight:600; color:rgba(255,255,255,0.75); font-family:'Segoe UI'; }

        QLabel#sliderVal_blue   { font-size:11px; font-weight:600; color:rgba(255,255,255,0.35); font-family:'Segoe UI'; }
        QLabel#sliderVal_warm   { font-size:11px; font-weight:600; color:rgba(255,255,255,0.35); font-family:'Segoe UI'; }
        QLabel#sliderVal_purple { font-size:11px; font-weight:600; color:rgba(255,255,255,0.35); font-family:'Segoe UI'; }

        QSlider#slider_blue::groove:horizontal   { height:3px; background:rgba(255,255,255,0.08); border-radius:2px; }
        QSlider#slider_blue::handle:horizontal   { background:white; width:14px; height:14px; border-radius:7px; margin:-6px 0; }
        QSlider#slider_blue::sub-page:horizontal { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #3b82f6, stop:1 #a855f7); border-radius:2px; }

        QSlider#slider_warm::groove:horizontal   { height:3px; background:rgba(255,255,255,0.08); border-radius:2px; }
        QSlider#slider_warm::handle:horizontal   { background:white; width:14px; height:14px; border-radius:7px; margin:-6px 0; }
        QSlider#slider_warm::sub-page:horizontal { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #60a5fa, stop:0.5 #ffffff, stop:1 #fb923c); border-radius:2px; }

        QSlider#slider_purple::groove:horizontal   { height:3px; background:rgba(255,255,255,0.08); border-radius:2px; }
        QSlider#slider_purple::handle:horizontal   { background:white; width:14px; height:14px; border-radius:7px; margin:-6px 0; }
        QSlider#slider_purple::sub-page:horizontal { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #3b82f6, stop:1 #a855f7); border-radius:2px; }

        QLabel#scTitle { font-size:14px; font-weight:700; color:rgba(255,255,255,0.75); font-family:'Segoe UI'; }
        QLabel#scSub   { font-size:11px; color:rgba(255,255,255,0.25); font-family:'Segoe UI'; }

        QPushButton#scBadge {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 0 14px;
            font-size: 12px; font-weight: 700;
            color: rgba(255,255,255,0.45);
            font-family: 'Segoe UI';
        }
        QPushButton#scBadge:hover {
            background: rgba(255,255,255,0.08);
            color: white;
            border-color: rgba(255,255,255,0.2);
        }
        QPushButton#scBadgeListening {
            background: rgba(236,72,153,0.1);
            border: 1px solid #ec4899;
            border-radius: 8px;
            padding: 0 14px;
            font-size: 12px; font-weight: 700;
            color: #f9a8d4;
            font-family: 'Segoe UI';
        }
        """)

# ── Main ──────────────────────────────────────────────────────────────
def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("Lumify")

    ico = resource_path("icon.ico")
    if os.path.exists(ico):
        app.setWindowIcon(QIcon(ico))

    overlay = RingOverlay()
    overlay.show()

    panel = ControlPanel(overlay)
    panel.show()
    panel.setFocus()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
