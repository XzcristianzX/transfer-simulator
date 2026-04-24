"""
socket_tab.py — Pestaña de control del servidor TCP Socket
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QApplication,
)

from core.file_info import FileInfo
from core.network_utils import get_primary_ip
from servers.socket_server import ServidorSocket
from ui.progress_widget import ProgressWidget
from ui.styles import COLOR


class SocketTab(QWidget):
    """Pestaña completa del servidor TCP Socket."""

    log_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._servidor = ServidorSocket()
        self._file_info: Optional[FileInfo] = None
        self._ip = get_primary_ip()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # ── Cabecera ──
        h = QHBoxLayout()
        icono = QLabel("⚡")
        icono.setStyleSheet("font-size: 28px;")
        h.addWidget(icono)
        titulo = QLabel("Servidor TCP Socket")
        titulo.setProperty("title", True)
        h.addWidget(titulo)
        h.addStretch()
        self._badge = self._badge_widget("INACTIVO", COLOR['inactive'])
        h.addWidget(self._badge)
        root.addLayout(h)

        desc = QLabel(
            "Transferencia binaria directa vía socket TCP. La velocidad más alta posible en red local. "
            "Protocolo simple: cabecera de texto + bytes del archivo. Multi-cliente simultáneo."
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

        fila = QHBoxLayout()
        fila.addWidget(QLabel("Puerto:"))
        self._spin_puerto = QSpinBox()
        self._spin_puerto.setRange(1024, 65535)
        self._spin_puerto.setValue(9000)
        self._spin_puerto.setFixedWidth(100)
        self._spin_puerto.setToolTip("Puerto TCP Socket (recomendado: 9000)")
        fila.addWidget(self._spin_puerto)
        fila.addStretch()
        conf_l.addLayout(fila)
        root.addWidget(conf)

        # ── Dirección ──
        addr_frame = QFrame()
        addr_frame.setStyleSheet(f"background:{COLOR['bg_card']}; border-radius:10px; border:1px solid {COLOR['border']};")
        addr_l = QVBoxLayout(addr_frame)
        addr_l.setContentsMargins(16, 14, 16, 14)
        addr_l.setSpacing(8)

        lbl_addr_t = QLabel("DIRECCIÓN DE CONEXIÓN")
        lbl_addr_t.setProperty("subtitle", True)
        addr_l.addWidget(lbl_addr_t)

        addr_row = QHBoxLayout()
        self._lbl_addr = QLabel("—")
        self._lbl_addr.setStyleSheet(
            f"color: {COLOR['teal']}; font-size: 15px; font-weight: 700; "
            f"font-family: 'Cascadia Code', 'Consolas', monospace;"
        )
        self._lbl_addr.setTextInteractionFlags(Qt.TextSelectableByMouse)
        addr_row.addWidget(self._lbl_addr)
        addr_row.addStretch()

        self._btn_copiar = QPushButton("📋 Copiar")
        self._btn_copiar.setProperty("success", True)
        self._btn_copiar.setFixedHeight(34)
        self._btn_copiar.clicked.connect(self._copiar)
        addr_row.addWidget(self._btn_copiar)
        addr_l.addLayout(addr_row)

        # Protocolo de ejemplo
        proto = QLabel(
            "Protocolo de recepción en el POS:\n"
            "  1. Conectar socket TCP a IP:PUERTO\n"
            "  2. Leer cabecera hasta '\\n':  POSFILE:<nombre>:<tamaño_bytes>\\n\n"
            "  3. Leer exactamente <tamaño_bytes> bytes → guardar en disco"
        )
        proto.setStyleSheet(
            f"color: {COLOR['text_secondary']}; font-size: 11px; "
            f"font-family: 'Cascadia Code', 'Consolas', monospace; "
            f"background:{COLOR['bg_surface']}; border-radius:6px; padding:8px;"
        )
        addr_l.addWidget(proto)
        root.addWidget(addr_frame)

        # ── Progreso ──
        self._progress = ProgressWidget()
        self._progress.vincular_stats(self._servidor.stats)
        root.addWidget(self._progress)

        # ── Botones ──
        btn_row = QHBoxLayout()
        self._btn_iniciar = QPushButton("▶  Iniciar Servidor Socket")
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

    def _badge_widget(self, texto: str, color: str) -> QLabel:
        badge = QLabel(f"  {texto}  ")
        badge.setStyleSheet(
            f"background-color: {color}22; color: {color}; "
            f"border: 1px solid {color}; border-radius: 10px; "
            f"font-size: 11px; font-weight: 700; padding: 2px 6px;"
        )
        return badge

    def set_file_info(self, fi: FileInfo):
        self._file_info = fi
        self._actualizar_addr()

    def _actualizar_addr(self):
        puerto = self._spin_puerto.value()
        self._lbl_addr.setText(f"{self._ip}  :  {puerto}")

    def _copiar(self):
        puerto = self._spin_puerto.value()
        QApplication.clipboard().setText(f"{self._ip}:{puerto}")
        self._btn_copiar.setText("✅ ¡Copiado!")
        QTimer.singleShot(2000, lambda: self._btn_copiar.setText("📋 Copiar"))

    def _iniciar(self):
        if not self._file_info:
            self.log_signal.emit("⚠️ Selecciona un archivo antes de iniciar el servidor Socket.")
            return
        puerto = self._spin_puerto.value()
        ok = self._servidor.iniciar(
            puerto=puerto,
            archivo=Path(self._file_info.path),
        )
        if ok:
            self._actualizar_addr()
            self._set_activo(True)
            self._progress.iniciar_actualizaciones()
            self.log_signal.emit(f"✅ Servidor Socket TCP iniciado en puerto {puerto}")
        else:
            self.log_signal.emit(f"❌ No se pudo iniciar Socket en puerto {puerto}. Puerto en uso?")

    def _detener(self):
        self._servidor.detener()
        self._set_activo(False)
        self._progress.detener_actualizaciones()
        self.log_signal.emit("⏹ Servidor Socket TCP detenido.")

    def _reiniciar(self):
        self._detener()
        QTimer.singleShot(300, self._iniciar)

    def _set_activo(self, activo: bool):
        self._btn_iniciar.setEnabled(not activo)
        self._btn_detener.setEnabled(activo)
        self._btn_reiniciar.setEnabled(activo)
        self._spin_puerto.setEnabled(not activo)

        color = COLOR['success'] if activo else COLOR['inactive']
        texto = "  ACTIVO  " if activo else "  INACTIVO  "
        self._badge.setText(texto)
        self._badge.setStyleSheet(
            f"background-color: {color}22; color: {color}; "
            f"border: 1px solid {color}; border-radius: 10px; "
            f"font-size: 11px; font-weight: 700; padding: 2px 6px;"
        )
