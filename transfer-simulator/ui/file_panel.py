"""
file_panel.py — Panel de selección de archivo con drag & drop
Muestra metadata completa del archivo seleccionado.
"""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QSizePolicy,
)

from core.file_info import FileInfo
from ui.styles import COLOR


class FilePanel(QFrame):
    """
    Panel que permite seleccionar un archivo vía botón o drag & drop.
    Emite la señal `archivo_cambiado` con el FileInfo del archivo.
    """

    archivo_cambiado = Signal(object)   # emite FileInfo

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_info: FileInfo | None = None
        self._build_ui()
        self.setAcceptDrops(True)

    # ──────────────────────────── UI ────────────────────────────

    def _build_ui(self):
        self.setObjectName("FilePanel")
        self.setStyleSheet(f"""
            #FilePanel {{
                background-color: {COLOR['bg_surface']};
                border: 2px dashed {COLOR['border']};
                border-radius: 12px;
            }}
            #FilePanel:hover {{
                border-color: {COLOR['accent']};
            }}
        """)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # ── Cabecera ──
        header = QHBoxLayout()
        titulo = QLabel("📁  Archivo Seleccionado")
        titulo.setProperty("title", True)
        header.addWidget(titulo)
        header.addStretch()

        self.btn_seleccionar = QPushButton("  Seleccionar archivo")
        self.btn_seleccionar.setProperty("primary", True)
        self.btn_seleccionar.setFixedHeight(38)
        self.btn_seleccionar.setMinimumWidth(180)
        self.btn_seleccionar.setCursor(Qt.PointingHandCursor)
        self.btn_seleccionar.clicked.connect(self._abrir_dialogo)
        header.addWidget(self.btn_seleccionar)
        root.addLayout(header)

        # ── Separador ──
        sep = QFrame()
        sep.setProperty("separator", True)
        sep.setFixedHeight(1)
        root.addWidget(sep)

        # ── Zona de info / drop ──
        self._zona_drop = QLabel("⬆️  Arrastra un archivo aquí  o  usa el botón")
        self._zona_drop.setAlignment(Qt.AlignCenter)
        self._zona_drop.setStyleSheet(
            f"color: {COLOR['text_secondary']}; font-size: 14px; padding: 12px;"
        )
        root.addWidget(self._zona_drop)

        # ── Grid de metadata (oculto hasta selección) ──
        self._meta_frame = QWidget()
        self._meta_frame.hide()
        meta_layout = QHBoxLayout(self._meta_frame)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.setSpacing(24)

        self._lbl_icono = QLabel("📁")
        self._lbl_icono.setFont(QFont("Segoe UI Emoji", 28))
        self._lbl_icono.setFixedWidth(50)
        meta_layout.addWidget(self._lbl_icono)

        info_col = QVBoxLayout()
        info_col.setSpacing(4)

        self._lbl_nombre = QLabel("—")
        self._lbl_nombre.setStyleSheet(
            f"color: {COLOR['text_primary']}; font-size: 15px; font-weight: 700;"
        )
        info_col.addWidget(self._lbl_nombre)

        self._lbl_ruta = QLabel("—")
        self._lbl_ruta.setStyleSheet(
            f"color: {COLOR['text_secondary']}; font-size: 11px;"
        )
        self._lbl_ruta.setWordWrap(True)
        info_col.addWidget(self._lbl_ruta)

        meta_layout.addLayout(info_col, stretch=1)

        # Tarjetas de propiedades
        self._tarjetas = {}
        for clave, label in [
            ("tamaño",  "Tamaño"),
            ("tipo",    "Tipo"),
            ("fecha",   "Modificado"),
        ]:
            card = self._crear_tarjeta(label)
            self._tarjetas[clave] = card
            meta_layout.addWidget(card)

        root.addWidget(self._meta_frame)

    def _crear_tarjeta(self, titulo: str) -> QFrame:
        """Crea una mini-tarjeta de propiedad con título y valor."""
        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR['bg_card']};
                border: 1px solid {COLOR['border']};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        f.setFixedWidth(130)
        v = QVBoxLayout(f)
        v.setContentsMargins(10, 6, 10, 6)
        v.setSpacing(2)

        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet(f"color: {COLOR['text_secondary']}; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        v.addWidget(lbl_t)

        lbl_v = QLabel("—")
        lbl_v.setStyleSheet(f"color: {COLOR['accent']}; font-size: 13px; font-weight: 700;")
        lbl_v.setWordWrap(True)
        f.valor_label = lbl_v   # acceso directo
        v.addWidget(lbl_v)

        return f

    # ──────────────── Drag & Drop ────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(f"""
                #FilePanel {{
                    background-color: {COLOR['bg_hover']};
                    border: 2px dashed {COLOR['accent']};
                    border-radius: 12px;
                }}
            """)

    def dragLeaveEvent(self, event):
        self._restaurar_estilo()

    def dropEvent(self, event: QDropEvent):
        self._restaurar_estilo()
        urls = event.mimeData().urls()
        if urls:
            ruta = urls[0].toLocalFile()
            if os.path.isfile(ruta):
                self._cargar_archivo(ruta)

    def _restaurar_estilo(self):
        self.setStyleSheet(f"""
            #FilePanel {{
                background-color: {COLOR['bg_surface']};
                border: 2px dashed {COLOR['border']};
                border-radius: 12px;
            }}
            #FilePanel:hover {{
                border-color: {COLOR['accent']};
            }}
        """)

    # ──────────────── Selección ────────────────

    def _abrir_dialogo(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo para transferir",
            "",
            "Todos los archivos (*.*)",
        )
        if ruta:
            self._cargar_archivo(ruta)

    def _cargar_archivo(self, ruta: str):
        try:
            fi = FileInfo.from_path(ruta)
            self._file_info = fi
            self._actualizar_ui(fi)
            self.archivo_cambiado.emit(fi)
        except Exception as e:
            self._lbl_nombre.setText(f"Error: {e}")

    def _actualizar_ui(self, fi: FileInfo):
        self._zona_drop.hide()
        self._meta_frame.show()

        self._lbl_icono.setText(fi.icon)
        self._lbl_nombre.setText(fi.name)
        self._lbl_ruta.setText(str(fi.path))

        self._tarjetas["tamaño"].valor_label.setText(fi.size_human)
        self._tarjetas["tipo"].valor_label.setText(fi.extension.upper() or "N/A")
        self._tarjetas["fecha"].valor_label.setText(fi.modified_date.split("  ")[0])

    # ──────────────── Público ────────────────

    @property
    def file_info(self) -> FileInfo | None:
        return self._file_info
