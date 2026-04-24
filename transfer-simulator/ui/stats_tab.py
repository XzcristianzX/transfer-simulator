"""
stats_tab.py — Pestaña de estadísticas de red y resumen de transferencias
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QScrollArea,
)

from core.network_utils import get_network_interfaces
from ui.styles import COLOR


class StatsTab(QWidget):
    """
    Pestaña de estadísticas:
    - Interfaces de red detectadas
    - Resumen de todos los servidores activos
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._servidores: dict = {}
        self._build_ui()

        # Refrescar interfaces cada 5 segundos
        timer = QTimer(self)
        timer.setInterval(5000)
        timer.timeout.connect(self._actualizar_interfaces)
        timer.start()
        self._actualizar_interfaces()

    # ──────────────────────── UI ────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # ── Cabecera ──
        h = QHBoxLayout()
        icono = QLabel("📡")
        icono.setStyleSheet("font-size: 24px;")
        h.addWidget(icono)
        titulo = QLabel("Red y Estadísticas")
        titulo.setProperty("title", True)
        h.addWidget(titulo)
        h.addStretch()
        root.addLayout(h)

        sep = QFrame(); sep.setProperty("separator", True); root.addWidget(sep)

        # ── Interfaces de red ──
        lbl_red = QLabel("INTERFACES DE RED DETECTADAS")
        lbl_red.setProperty("subtitle", True)
        root.addWidget(lbl_red)

        self._area_ifaces = QWidget()
        self._ifaces_layout = QVBoxLayout(self._area_ifaces)
        self._ifaces_layout.setContentsMargins(0, 0, 0, 0)
        self._ifaces_layout.setSpacing(8)
        root.addWidget(self._area_ifaces)

        sep2 = QFrame(); sep2.setProperty("separator", True); root.addWidget(sep2)

        # ── Estado de servidores ──
        lbl_srv = QLabel("ESTADO DE SERVIDORES")
        lbl_srv.setProperty("subtitle", True)
        root.addWidget(lbl_srv)

        self._srv_grid = QGridLayout()
        self._srv_grid.setSpacing(10)

        self._srv_cards: dict[str, QFrame] = {}
        for col, (key, nombre, icono_s) in enumerate([
            ("http",   "HTTP",         "🌐"),
            ("socket", "Socket TCP",   "⚡"),
            ("ftp",    "FTP",          "📡"),
        ]):
            card = self._crear_srv_card(nombre, icono_s)
            self._srv_cards[key] = card
            self._srv_grid.addWidget(card, 0, col)

        root.addLayout(self._srv_grid)

        # ── Guía rápida ──
        sep3 = QFrame(); sep3.setProperty("separator", True); root.addWidget(sep3)

        lbl_guia = QLabel("GUÍA RÁPIDA DE CONEXIÓN DESDE EL POS")
        lbl_guia.setProperty("subtitle", True)
        root.addWidget(lbl_guia)

        guia_text = (
            "HTTP  →  Abrir URL en WebView o usar HttpURLConnection / OkHttp en Android\n"
            "         Ejemplo:  new URL(\"http://192.168.x.x:8080/archivo.apk\").openStream();\n\n"
            "Socket →  Conectar socket a IP:9000, leer cabecera hasta '\\n', luego leer bytes\n"
            "         Ejemplo:  Socket s = new Socket(\"192.168.x.x\", 9000); s.getInputStream();\n\n"
            "FTP    →  Usar FTPClient (Apache Commons Net) o cliente nativo del sistema\n"
            "         Ejemplo:  ftp.connect(ip, 2121); ftp.login(user, pass); ftp.retrieveFile(...);"
        )
        lbl_guia_text = QLabel(guia_text)
        lbl_guia_text.setStyleSheet(
            f"color: {COLOR['text_secondary']}; font-size: 11px; "
            f"font-family: 'Cascadia Code', 'Consolas', monospace; "
            f"background:{COLOR['bg_surface']}; border-radius:8px; padding:12px; "
            f"border: 1px solid {COLOR['border']};"
        )
        root.addWidget(lbl_guia_text)
        root.addStretch()

    # ──────────────────────── Tarjeta servidor ────────────────────────

    def _crear_srv_card(self, nombre: str, icono: str) -> QFrame:
        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR['bg_surface']};
                border: 1px solid {COLOR['border']};
                border-radius: 10px;
            }}
        """)
        v = QVBoxLayout(f)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(4)

        row = QHBoxLayout()
        lbl_i = QLabel(icono)
        lbl_i.setStyleSheet("font-size: 20px;")
        row.addWidget(lbl_i)
        lbl_n = QLabel(nombre)
        lbl_n.setStyleSheet(f"color: {COLOR['text_primary']}; font-weight: 700; font-size: 14px;")
        row.addWidget(lbl_n)
        row.addStretch()
        v.addLayout(row)

        lbl_estado = QLabel("⭕ Inactivo")
        lbl_estado.setStyleSheet(f"color: {COLOR['inactive']}; font-size: 13px;")
        f._lbl_estado = lbl_estado
        v.addWidget(lbl_estado)

        lbl_port = QLabel("Puerto: —")
        lbl_port.setStyleSheet(f"color: {COLOR['text_secondary']}; font-size: 12px;")
        f._lbl_port = lbl_port
        v.addWidget(lbl_port)

        return f

    # ──────────────────────── Interfaces ────────────────────────

    def _actualizar_interfaces(self):
        # Limpiar
        while self._ifaces_layout.count():
            item = self._ifaces_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        ifaces = get_network_interfaces()
        if not ifaces:
            lbl = QLabel("No se detectaron interfaces de red activas.")
            lbl.setStyleSheet(f"color: {COLOR['error']};")
            self._ifaces_layout.addWidget(lbl)
            return

        grid = QGridLayout()
        grid.setSpacing(8)

        for i, iface in enumerate(ifaces):
            col = i % 3
            row = i // 3

            card = QFrame()
            color = COLOR['success'] if iface.activa else COLOR['inactive']
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {color}15;
                    border: 1px solid {color}55;
                    border-radius: 8px;
                }}
            """)
            v = QVBoxLayout(card)
            v.setContentsMargins(12, 10, 12, 10)
            v.setSpacing(3)

            tipo_lbl = QLabel(iface.tipo)
            tipo_lbl.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 12px;")
            v.addWidget(tipo_lbl)

            ip_lbl = QLabel(iface.ip)
            ip_lbl.setStyleSheet(
                f"color: {COLOR['text_primary']}; font-size: 14px; font-weight: 700; "
                f"font-family: 'Cascadia Code', 'Consolas', monospace;"
            )
            ip_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            v.addWidget(ip_lbl)

            nombre_lbl = QLabel(iface.name)
            nombre_lbl.setStyleSheet(f"color: {COLOR['text_secondary']}; font-size: 11px;")
            v.addWidget(nombre_lbl)

            grid.addWidget(card, row, col)

        contenedor = QWidget()
        contenedor.setLayout(grid)
        self._ifaces_layout.addWidget(contenedor)

    # ──────────────────────── Actualizar estado servidores ────────────────────────

    def actualizar_servidor(self, tipo: str, activo: bool, puerto: int = 0):
        """Llamado desde MainWindow cuando cambia el estado de un servidor."""
        card = self._srv_cards.get(tipo)
        if not card:
            return

        if activo:
            card._lbl_estado.setText("🟢 Activo")
            card._lbl_estado.setStyleSheet(f"color: {COLOR['success']}; font-size: 13px;")
            card._lbl_port.setText(f"Puerto: {puerto}")
        else:
            card._lbl_estado.setText("⭕ Inactivo")
            card._lbl_estado.setStyleSheet(f"color: {COLOR['inactive']}; font-size: 13px;")
            card._lbl_port.setText("Puerto: —")
