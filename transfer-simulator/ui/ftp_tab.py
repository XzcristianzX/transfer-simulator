"""
ftp_tab.py — Pestaña de control del servidor FTP
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSpinBox, QLineEdit, QApplication,
)

from core.file_info import FileInfo
from core.network_utils import get_primary_ip
from servers.ftp_server import ServidorFTP
from ui.progress_widget import ProgressWidget
from ui.styles import COLOR


class FTPTab(QWidget):
    """Pestaña completa del servidor FTP."""

    log_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._servidor = ServidorFTP()
        self._file_info: Optional[FileInfo] = None
        self._ip = get_primary_ip()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # ── Cabecera ──
        h = QHBoxLayout()
        icono = QLabel("📡")
        icono.setStyleSheet("font-size: 28px;")
        h.addWidget(icono)
        titulo = QLabel("Servidor FTP")
        titulo.setProperty("title", True)
        h.addWidget(titulo)
        h.addStretch()
        self._badge = self._make_badge("INACTIVO", COLOR['inactive'])
        h.addWidget(self._badge)
        root.addLayout(h)

        desc = QLabel(
            "Servidor FTP local con autenticación configurable. Compatible con cualquier cliente FTP "
            "(FileZilla, WinSCP, código Android). Modo pasivo habilitado. Soporta archivos grandes."
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
        conf_l.setSpacing(10)

        lbl_conf = QLabel("CONFIGURACIÓN")
        lbl_conf.setProperty("subtitle", True)
        conf_l.addWidget(lbl_conf)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Puerto:"), 0, 0)
        self._spin_puerto = QSpinBox()
        self._spin_puerto.setRange(1024, 65535)
        self._spin_puerto.setValue(2121)
        self._spin_puerto.setFixedWidth(100)
        self._spin_puerto.setToolTip("Puerto FTP (2121 recomendado para evitar permisos admin)")
        grid.addWidget(self._spin_puerto, 0, 1)

        grid.addWidget(QLabel("Usuario:"), 0, 2)
        self._edit_usuario = QLineEdit("admin")
        self._edit_usuario.setFixedWidth(120)
        grid.addWidget(self._edit_usuario, 0, 3)

        grid.addWidget(QLabel("Contraseña:"), 1, 0)
        self._edit_clave = QLineEdit("1234")
        self._edit_clave.setFixedWidth(120)
        grid.addWidget(self._edit_clave, 1, 1)

        nota = QLabel("⚠ Puerto 21 requiere privilegios de administrador en Windows.")
        nota.setStyleSheet(f"color: {COLOR['warning']}; font-size: 11px;")
        grid.addWidget(nota, 1, 2, 1, 2)

        conf_l.addLayout(grid)
        root.addWidget(conf)

        # ── Datos de conexión ──
        conn_frame = QFrame()
        conn_frame.setStyleSheet(f"background:{COLOR['bg_card']}; border-radius:10px; border:1px solid {COLOR['border']};")
        conn_l = QVBoxLayout(conn_frame)
        conn_l.setContentsMargins(16, 14, 16, 14)
        conn_l.setSpacing(10)

        lbl_conn_t = QLabel("DATOS DE CONEXIÓN PARA EL POS")
        lbl_conn_t.setProperty("subtitle", True)
        conn_l.addWidget(lbl_conn_t)

        datos_grid = QGridLayout()
        datos_grid.setHorizontalSpacing(24)
        datos_grid.setVerticalSpacing(6)

        self._datos = {}
        etiquetas = [
            ("Servidor",    "servidor"),
            ("Puerto",      "puerto"),
            ("Usuario",     "usuario"),
            ("Contraseña",  "clave"),
        ]
        for i, (label, key) in enumerate(etiquetas):
            lbl_k = QLabel(f"{label}:")
            lbl_k.setStyleSheet(f"color: {COLOR['text_secondary']};")
            datos_grid.addWidget(lbl_k, i // 2, (i % 2) * 2)

            lbl_v = QLabel("—")
            lbl_v.setStyleSheet(
                f"color: {COLOR['accent']}; font-weight: 700; "
                f"font-family: 'Cascadia Code', 'Consolas', monospace;"
            )
            lbl_v.setTextInteractionFlags(Qt.TextSelectableByMouse)
            datos_grid.addWidget(lbl_v, i // 2, (i % 2) * 2 + 1)
            self._datos[key] = lbl_v

        conn_l.addLayout(datos_grid)

        copiar_row = QHBoxLayout()
        copiar_row.addStretch()
        self._btn_copiar = QPushButton("📋 Copiar Credenciales")
        self._btn_copiar.setProperty("success", True)
        self._btn_copiar.setFixedHeight(34)
        self._btn_copiar.clicked.connect(self._copiar_credenciales)
        copiar_row.addWidget(self._btn_copiar)
        conn_l.addLayout(copiar_row)

        # Android snippet
        snippet = QLabel(
            "Android (código Java):\n"
            "  FTPClient ftp = new FTPClient();\n"
            "  ftp.connect(\"IP\", PUERTO);\n"
            "  ftp.login(\"USUARIO\", \"CLAVE\");\n"
            "  ftp.retrieveFile(\"/archivo.apk\", outputStream);"
        )
        snippet.setStyleSheet(
            f"color: {COLOR['text_secondary']}; font-size: 11px; "
            f"font-family: 'Cascadia Code', 'Consolas', monospace; "
            f"background:{COLOR['bg_surface']}; border-radius:6px; padding:8px;"
        )
        conn_l.addWidget(snippet)
        root.addWidget(conn_frame)

        # ── Progreso ──
        self._progress = ProgressWidget()
        self._progress.vincular_stats(self._servidor.stats)
        root.addWidget(self._progress)

        # ── Botones ──
        btn_row = QHBoxLayout()
        self._btn_iniciar = QPushButton("▶  Iniciar Servidor FTP")
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

    def _make_badge(self, texto: str, color: str) -> QLabel:
        b = QLabel(f"  {texto}  ")
        b.setStyleSheet(
            f"background-color: {color}22; color: {color}; "
            f"border: 1px solid {color}; border-radius: 10px; "
            f"font-size: 11px; font-weight: 700; padding: 2px 6px;"
        )
        return b

    def set_file_info(self, fi: FileInfo):
        self._file_info = fi

    def _copiar_credenciales(self):
        p = self._spin_puerto.value()
        u = self._edit_usuario.text()
        k = self._edit_clave.text()
        texto = (
            f"FTP Servidor: {self._ip}\n"
            f"Puerto: {p}\nUsuario: {u}\nContraseña: {k}"
        )
        QApplication.clipboard().setText(texto)
        self._btn_copiar.setText("✅ ¡Copiado!")
        QTimer.singleShot(2000, lambda: self._btn_copiar.setText("📋 Copiar Credenciales"))

    def _iniciar(self):
        if not self._file_info:
            self.log_signal.emit("⚠️ Selecciona un archivo antes de iniciar el servidor FTP.")
            return

        puerto = self._spin_puerto.value()
        usuario = self._edit_usuario.text() or "admin"
        clave = self._edit_clave.text() or "1234"

        # El servidor FTP sirve el directorio del archivo
        directorio = Path(self._file_info.path).parent

        ok = self._servidor.iniciar(
            puerto=puerto,
            directorio=directorio,
            usuario=usuario,
            clave=clave,
        )
        if ok:
            self._datos["servidor"].setText(self._ip)
            self._datos["puerto"].setText(str(puerto))
            self._datos["usuario"].setText(usuario)
            self._datos["clave"].setText(clave)
            self._set_activo(True)
            self._progress.iniciar_actualizaciones()
            self.log_signal.emit(
                f"✅ Servidor FTP iniciado | Puerto:{puerto} | Usuario:{usuario} | Dir:{directorio}"
            )
        else:
            self.log_signal.emit(
                f"❌ No se pudo iniciar el servidor FTP en puerto {puerto}. "
                "¿Puerto en uso? ¿pyftpdlib instalado?"
            )

    def _detener(self):
        self._servidor.detener()
        self._set_activo(False)
        self._progress.detener_actualizaciones()
        self.log_signal.emit("⏹ Servidor FTP detenido.")

    def _reiniciar(self):
        self._detener()
        QTimer.singleShot(300, self._iniciar)

    def _set_activo(self, activo: bool):
        self._btn_iniciar.setEnabled(not activo)
        self._btn_detener.setEnabled(activo)
        self._btn_reiniciar.setEnabled(activo)
        self._spin_puerto.setEnabled(not activo)
        self._edit_usuario.setEnabled(not activo)
        self._edit_clave.setEnabled(not activo)

        color = COLOR['success'] if activo else COLOR['inactive']
        texto = "  ACTIVO  " if activo else "  INACTIVO  "
        self._badge.setText(texto)
        self._badge.setStyleSheet(
            f"background-color: {color}22; color: {color}; "
            f"border: 1px solid {color}; border-radius: 10px; "
            f"font-size: 11px; font-weight: 700; padding: 2px 6px;"
        )
