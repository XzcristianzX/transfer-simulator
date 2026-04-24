"""
main_window.py — Ventana principal del Simulador POS
Coordina todas las pestañas y el panel de archivo.
"""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QIcon, QAction, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QLabel, QFrame,
    QScrollArea, QApplication, QStatusBar,
)

from core.file_info import FileInfo
from core.logger import get_emitter, configurar_logging
from core.network_utils import get_primary_ip
from ui.file_panel import FilePanel
from ui.http_tab import HTTPTab
from ui.socket_tab import SocketTab
from ui.ftp_tab import FTPTab
from ui.stats_tab import StatsTab
from ui.log_tab import LogTab
from ui.comparator_widget import ComparatorWidget
from ui.styles import COLOR


class MainWindow(QMainWindow):
    """Ventana principal del Simulador de Transferencia para POS."""

    APP_NAME = "POS Transfer Simulator"
    APP_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        configurar_logging()
        self._ip = get_primary_ip()
        self._setWindowSetup()
        self._build_ui()
        self._connect_signals()
        self._status_timer = QTimer(self)
        self._status_timer.setInterval(2000)
        self._status_timer.timeout.connect(self._actualizar_status)
        self._status_timer.start()

    # ──────────────────────── Window Setup ────────────────────────

    def _setWindowSetup(self):
        self.setWindowTitle(f"  {self.APP_NAME}  v{self.APP_VERSION}")
        self.setMinimumSize(1100, 750)
        self.resize(1280, 820)

        # Centrar en pantalla
        geo = QApplication.primaryScreen().availableGeometry()
        self.move(
            (geo.width() - 1280) // 2,
            (geo.height() - 820) // 2,
        )

    # ──────────────────────── UI ────────────────────────

    def _build_ui(self):
        

        # ── Widget central ──
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Banner superior ──
        banner = self._build_banner()
        root_layout.addWidget(banner)

        # ── Splitter: panel archivo (arriba) + tabs (abajo) ──
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLOR['border']};
            }}
            QSplitter::handle:hover {{
                background-color: {COLOR['accent']};
            }}
        """)

        # Panel de archivo
        self._file_panel = FilePanel()
        scroll_file = QScrollArea()
        scroll_file.setWidget(self._file_panel)
        scroll_file.setWidgetResizable(True)
        scroll_file.setMaximumHeight(240)
        scroll_file.setMinimumHeight(200)
        scroll_file.setFrameShape(QFrame.NoFrame)
        scroll_file.setStyleSheet("background: transparent;")

        file_wrapper = QWidget()
        fw_layout = QVBoxLayout(file_wrapper)
        fw_layout.setContentsMargins(12, 12, 12, 6)
        fw_layout.addWidget(self._file_panel)
        splitter.addWidget(file_wrapper)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(False)
        self._tabs.setTabPosition(QTabWidget.North)

        self._http_tab    = HTTPTab()
        self._socket_tab  = SocketTab()
        self._ftp_tab     = FTPTab()
        self._stats_tab   = StatsTab()
        self._log_tab     = LogTab()
        self._comp_widget = ComparatorWidget()

        # Envolver cada tab en scroll area para pantallas pequeñas
        def _scroll_wrap(widget: QWidget) -> QScrollArea:
            sa = QScrollArea()
            sa.setWidget(widget)
            sa.setWidgetResizable(True)
            sa.setFrameShape(QFrame.NoFrame)
            return sa

        self._tabs.addTab(_scroll_wrap(self._http_tab),    "🌐  HTTP")
        self._tabs.addTab(_scroll_wrap(self._socket_tab),  "⚡  Socket TCP")
        self._tabs.addTab(_scroll_wrap(self._ftp_tab),     "📡  FTP")
        self._tabs.addTab(_scroll_wrap(self._stats_tab),   "📡  Red")
        self._tabs.addTab(_scroll_wrap(self._log_tab),     "📋  Logs")
        self._tabs.addTab(_scroll_wrap(self._comp_widget), "📊  Comparador")

        tabs_wrapper = QWidget()
        tw_layout = QVBoxLayout(tabs_wrapper)
        tw_layout.setContentsMargins(12, 0, 12, 12)
        tw_layout.addWidget(self._tabs)
        splitter.addWidget(tabs_wrapper)

        splitter.setSizes([220, 600])
        root_layout.addWidget(splitter, stretch=1)
            
        # ── Menú ──
        self._build_menu()
        
        # ── Status bar ──
        self._build_status_bar()

    def _build_banner(self) -> QFrame:
        banner = QFrame()
        banner.setFixedHeight(60)
        banner.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLOR['bg_surface']},
                    stop:1 {COLOR['bg_deep']}
                );
                border-bottom: 1px solid {COLOR['border']};
            }}
        """)

        layout = QHBoxLayout(banner)
        layout.setContentsMargins(20, 0, 20, 0)

        # Logo / nombre
        logo = QLabel("🚀")
        logo.setStyleSheet("font-size: 28px;")
        layout.addWidget(logo)

        nombre = QLabel(f"<b>{self.APP_NAME}</b>")
        nombre.setStyleSheet(
            f"color: {COLOR['accent']}; font-size: 18px; font-weight: 700;"
        )
        layout.addWidget(nombre)

        version = QLabel(f"v{self.APP_VERSION}")
        version.setStyleSheet(f"color: {COLOR['text_secondary']}; font-size: 12px; margin-left: 8px;")
        layout.addWidget(version)

        layout.addStretch()

        # IP principal
        lbl_ip_key = QLabel("IP Local:")
        lbl_ip_key.setStyleSheet(f"color: {COLOR['text_secondary']}; font-size: 12px;")
        layout.addWidget(lbl_ip_key)

        self._lbl_ip = QLabel(self._ip)
        self._lbl_ip.setStyleSheet(
            f"color: {COLOR['teal']}; font-size: 14px; font-weight: 700; "
            f"font-family: 'Cascadia Code', 'Consolas', monospace; margin-left: 6px;"
        )
        self._lbl_ip.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self._lbl_ip)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color: {COLOR['border']};")
        sep.setFixedWidth(1)
        layout.addWidget(sep)

        # Servidores activos
        self._lbl_activos = QLabel("Sin servidores activos")
        self._lbl_activos.setStyleSheet(f"color: {COLOR['inactive']}; font-size: 12px; margin-left: 12px;")
        layout.addWidget(self._lbl_activos)

        return banner

    def _build_status_bar(self):
        sb = QStatusBar()
        sb.setFixedHeight(28)
        self.setStatusBar(sb)
        self._sb_msg = QLabel("Listo")
        self._sb_msg.setStyleSheet(f"color: {COLOR['text_secondary']};")
        sb.addWidget(self._sb_msg)

        self._sb_file = QLabel("Sin archivo seleccionado")
        self._sb_file.setStyleSheet(f"color: {COLOR['text_secondary']};")
        sb.addPermanentWidget(self._sb_file)

    def _build_menu(self):
        menubar = self.menuBar()

        # Menú Archivo
        menu_arch = menubar.addMenu("Archivo")

        act_abrir = QAction("📁  Seleccionar Archivo...", self)
        act_abrir.setShortcut("Ctrl+O")
        act_abrir.triggered.connect(lambda: self._file_panel._abrir_dialogo())
        menu_arch.addAction(act_abrir)

        menu_arch.addSeparator()

        act_salir = QAction("❌  Salir", self)
        act_salir.setShortcut("Ctrl+Q")
        act_salir.triggered.connect(self.close)
        menu_arch.addAction(act_salir)

        # Menú Herramientas
        menu_tools = menubar.addMenu("Herramientas")

        act_logs = QAction("💾  Exportar Logs", self)
        act_logs.triggered.connect(self._log_tab._exportar)
        menu_tools.addAction(act_logs)

        act_limpiar = QAction("🗑  Limpiar Logs", self)
        act_limpiar.triggered.connect(self._log_tab._limpiar)
        menu_tools.addAction(act_limpiar)

        # Menú Ayuda
        menu_help = menubar.addMenu("Ayuda")

        act_sobre = QAction("ℹ️  Acerca de", self)
        act_sobre.triggered.connect(self._mostrar_acerca)
        menu_help.addAction(act_sobre)

    # ──────────────────────── Señales ────────────────────────

    def _connect_signals(self):
        # Archivo cambiado → propagar a todos los tabs
        self._file_panel.archivo_cambiado.connect(self._on_archivo_cambiado)

        # Logs de cada tab → log_tab
        self._http_tab.log_signal.connect(self._log_tab.agregar_mensaje)
        self._socket_tab.log_signal.connect(self._log_tab.agregar_mensaje)
        self._ftp_tab.log_signal.connect(self._log_tab.agregar_mensaje)

        # Logs de servidores (desde hilos) → log_tab
        emitter = get_emitter()
        emitter.log_signal.connect(self._log_tab.agregar_log)

        # Cuando cambia tab → enfocar correctamente
        self._tabs.currentChanged.connect(self._on_tab_changed)

    @Slot(object)
    def _on_archivo_cambiado(self, fi: FileInfo):
        self._http_tab.set_file_info(fi)
        self._socket_tab.set_file_info(fi)
        self._ftp_tab.set_file_info(fi)
        self._sb_file.setText(f"  {fi.icon} {fi.name}  ({fi.size_human})")
        self._log_tab.agregar_mensaje(
            f"ℹ️ Archivo cargado: {fi.name} | {fi.size_human} | {fi.mime_type}"
        )

    @Slot(int)
    def _on_tab_changed(self, idx: int):
        pass   # placeholder para animaciones futuras

    # ──────────────────────── Status bar update ────────────────────────

    def _actualizar_status(self):
        http_ok    = self._http_tab._servidor.activo
        socket_ok  = self._socket_tab._servidor.activo
        ftp_ok     = self._ftp_tab._servidor.activo

        activos = []
        if http_ok:    activos.append("HTTP")
        if socket_ok:  activos.append("Socket")
        if ftp_ok:     activos.append("FTP")

        if activos:
            self._lbl_activos.setText(f"✅ Activos: {', '.join(activos)}")
            self._lbl_activos.setStyleSheet(f"color: {COLOR['success']}; font-size: 12px; margin-left: 12px;")
        else:
            self._lbl_activos.setText("Sin servidores activos")
            self._lbl_activos.setStyleSheet(f"color: {COLOR['inactive']}; font-size: 12px; margin-left: 12px;")

        # Actualizar cards del tab de stats
        self._stats_tab.actualizar_servidor("http",   http_ok,   self._http_tab._spin_puerto.value())
        self._stats_tab.actualizar_servidor("socket", socket_ok, self._socket_tab._spin_puerto.value())
        self._stats_tab.actualizar_servidor("ftp",    ftp_ok,    self._ftp_tab._spin_puerto.value())

    # ──────────────────────── Misc ────────────────────────

    def _mostrar_acerca(self):
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("Acerca de")
        msg.setText(
            f"<b>{self.APP_NAME}</b><br>"
            f"Versión {self.APP_VERSION}<br><br>"
            "Simulador/Servidor de transferencia de archivos<br>"
            "para pruebas con dispositivos POS.<br><br>"
            "<b>Protocolos:</b> HTTP · Socket TCP · FTP<br>"
            "<b>Tecnología:</b> Python 3.11 + PySide6"
        )
        msg.setStyleSheet(f"background-color: {COLOR['bg_surface']}; color: {COLOR['text_primary']};")
        msg.exec()

    def closeEvent(self, event):
        """Detener todos los servidores al cerrar."""
        self._http_tab._servidor.detener()
        self._socket_tab._servidor.detener()
        self._ftp_tab._servidor.detener()
        event.accept()
