"""
http_tab.py — Pestaña de control del servidor HTTP
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QApplication,
    QSizePolicy,
)

from core.file_info import FileInfo
from core.network_utils import get_primary_ip
from servers.http_server import ServidorHTTP
from ui.progress_widget import ProgressWidget
from ui.styles import COLOR


class HTTPTab(QWidget):
    """Pestaña completa del servidor HTTP."""

    log_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._servidor = ServidorHTTP()
        self._file_info: Optional[FileInfo] = None
        self._ip = get_primary_ip()
        self._build_ui()

    # ──────────────────────── UI ────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # ── Cabecera ──
        h = QHBoxLayout()
        icono = QLabel("🌐")
        icono.setStyleSheet("font-size: 28px;")
        h.addWidget(icono)
        titulo = QLabel("Servidor HTTP")
        titulo.setProperty("title", True)
        h.addWidget(titulo)
        h.addStretch()
        self._badge = self._crear_badge("INACTIVO", COLOR['inactive'])
        h.addWidget(self._badge)
        root.addLayout(h)

        # ── Descripción ──
        desc = QLabel(
            "Levanta un servidor web local. El POS descarga el archivo con un simple GET HTTP. "
            "Ideal para APKs y ZIPs. Soporte para reanudación y múltiples descargas simultáneas."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLOR['text_secondary']}; font-size: 12px;")
        root.addWidget(desc)

        sep = QFrame(); sep.setProperty("separator", True); root.addWidget(sep)

        # ── Configuración ──
        conf = QFrame()
        conf.setStyleSheet(f"background:{COLOR['bg_surface']}; border-radius:10px; border:1px solid {COLOR['border']};")
        conf_l = QVBoxLayout(conf)
        conf_l.setContentsMargins(16, 14, 16, 14)
        conf_l.setSpacing(12)

        lbl_conf = QLabel("CONFIGURACIÓN")
        lbl_conf.setProperty("subtitle", True)
        conf_l.addWidget(lbl_conf)

        fila_puerto = QHBoxLayout()
        fila_puerto.addWidget(QLabel("Puerto:"))
        self._spin_puerto = QSpinBox()
        self._spin_puerto.setRange(1024, 65535)
        self._spin_puerto.setValue(8080)
        self._spin_puerto.setFixedWidth(100)
        self._spin_puerto.setToolTip("Puerto HTTP (recomendado: 8080, 8000, 3000)")
        fila_puerto.addWidget(self._spin_puerto)
        fila_puerto.addStretch()
        conf_l.addLayout(fila_puerto)

        root.addWidget(conf)

        # ── URL de acceso ──
        url_frame = QFrame()
        url_frame.setStyleSheet(f"background:{COLOR['bg_card']}; border-radius:10px; border:1px solid {COLOR['border']};")
        url_l = QVBoxLayout(url_frame)
        url_l.setContentsMargins(16, 14, 16, 14)
        url_l.setSpacing(8)

        QLabel_url_titulo = QLabel("URL PARA EL POS")
        QLabel_url_titulo.setProperty("subtitle", True)
        url_l.addWidget(QLabel_url_titulo)

        url_row = QHBoxLayout()
        self._lbl_url = QLabel("—")
        self._lbl_url.setStyleSheet(
            f"color: {COLOR['accent']}; font-size: 15px; font-weight: 700; "
            f"font-family: 'Cascadia Code', 'Consolas', monospace;"
        )
        self._lbl_url.setTextInteractionFlags(Qt.TextSelectableByMouse)
        url_row.addWidget(self._lbl_url)
        url_row.addStretch()

        self._btn_copiar = QPushButton("📋 Copiar URL")
        self._btn_copiar.setProperty("success", True)
        self._btn_copiar.setFixedHeight(34)
        self._btn_copiar.clicked.connect(self._copiar_url)
        url_row.addWidget(self._btn_copiar)
        url_l.addLayout(url_row)

        # Código de ejemplo para POS
        codigo = QLabel(
            "POS (curl / wget):   GET /archivo.apk HTTP/1.1\n"
            "Android:              URL url = new URL(\"http://IP:PUERTO/archivo.apk\");"
        )
        codigo.setStyleSheet(
            f"color: {COLOR['text_secondary']}; font-size: 11px; "
            f"font-family: 'Cascadia Code', 'Consolas', monospace; "
            f"background:{COLOR['bg_surface']}; border-radius:6px; padding:8px;"
        )
        url_l.addWidget(codigo)
        root.addWidget(url_frame)

        # ── Progreso ──
        self._progress = ProgressWidget()
        self._progress.vincular_stats(self._servidor.stats)
        root.addWidget(self._progress)

        # ── Botones de control ──
        btn_row = QHBoxLayout()
        self._btn_iniciar = QPushButton("▶  Iniciar Servidor HTTP")
        self._btn_iniciar.setProperty("primary", True)
        self._btn_iniciar.setFixedHeight(42)
        self._btn_iniciar.clicked.connect(self._iniciar)

        self._btn_detener = QPushButton("⏹  Detener")
        self._btn_detener.setProperty("danger", True)
        self._btn_detener.setFixedHeight(42)
        self._btn_detener.setEnabled(False)
        self._btn_detener.clicked.connect(self._detener)

        self._btn_reiniciar = QPushButton("🔄 Reiniciar")
        self._btn_reiniciar.setFixedHeight(42)
        self._btn_reiniciar.setEnabled(False)
        self._btn_reiniciar.clicked.connect(self._reiniciar)

        btn_row.addWidget(self._btn_iniciar, stretch=2)
        btn_row.addWidget(self._btn_detener, stretch=1)
        btn_row.addWidget(self._btn_reiniciar, stretch=1)
        root.addLayout(btn_row)

        root.addStretch()

    def _crear_badge(self, texto: str, color: str) -> QLabel:
        badge = QLabel(f"  {texto}  ")
        badge.setStyleSheet(
            f"background-color: {color}22; color: {color}; "
            f"border: 1px solid {color}; border-radius: 10px; "
            f"font-size: 11px; font-weight: 700; padding: 2px 6px;"
        )
        return badge

    # ──────────────────────── Acciones ────────────────────────

    def set_file_info(self, fi: FileInfo):
        self._file_info = fi
        self._actualizar_url()

    def _actualizar_url(self):
        if self._file_info:
            puerto = self._spin_puerto.value()
            nombre = self._file_info.name
            self._lbl_url.setText(f"http://{self._ip}:{puerto}/{nombre}")
        else:
            self._lbl_url.setText("— (selecciona un archivo primero) —")

    def _copiar_url(self):
        url = self._lbl_url.text()
        QApplication.clipboard().setText(url)
        self._btn_copiar.setText("✅ ¡Copiado!")
        QTimer.singleShot(2000, lambda: self._btn_copiar.setText("📋 Copiar URL"))

    def _iniciar(self):
        if not self._file_info:
            self.log_signal.emit("⚠️ Selecciona un archivo antes de iniciar el servidor HTTP.")
            return
        puerto = self._spin_puerto.value()
        ok = self._servidor.iniciar(
            puerto=puerto,
            archivo=Path(self._file_info.path),
            progress_cb=None,
        )
        if ok:
            self._actualizar_url()
            self._set_activo(True)
            self._progress.iniciar_actualizaciones()
            self.log_signal.emit(f"✅ Servidor HTTP iniciado en puerto {puerto}")
        else:
            self.log_signal.emit(f"❌ No se pudo iniciar el servidor HTTP en puerto {puerto}. Puerto en uso?")

    def _detener(self):
        self._servidor.detener()
        self._set_activo(False)
        self._progress.detener_actualizaciones()
        self.log_signal.emit("⏹ Servidor HTTP detenido.")

    def _reiniciar(self):
        self._detener()
        QTimer.singleShot(300, self._iniciar)

    def _set_activo(self, activo: bool):
        self._btn_iniciar.setEnabled(not activo)
        self._btn_detener.setEnabled(activo)
        self._btn_reiniciar.setEnabled(activo)
        self._spin_puerto.setEnabled(not activo)

        if activo:
            self._badge.setText("  ACTIVO  ")
            self._badge.setStyleSheet(
                f"background-color: {COLOR['success']}22; color: {COLOR['success']}; "
                f"border: 1px solid {COLOR['success']}; border-radius: 10px; "
                f"font-size: 11px; font-weight: 700; padding: 2px 6px;"
            )
        else:
            self._badge.setText("  INACTIVO  ")
            self._badge.setStyleSheet(
                f"background-color: {COLOR['inactive']}22; color: {COLOR['inactive']}; "
                f"border: 1px solid {COLOR['inactive']}; border-radius: 10px; "
                f"font-size: 11px; font-weight: 700; padding: 2px 6px;"
            )
