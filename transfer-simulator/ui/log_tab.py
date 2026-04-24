"""
log_tab.py — Pestaña de logs técnicos con colores y exportación
"""
from __future__ import annotations

import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QTextCharFormat, QColor, QFont, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QPlainTextEdit, QFileDialog,
    QCheckBox,
)

from ui.styles import COLOR


# Colores de nivel para las líneas de log
COLORES_NIVEL = {
    "DEBUG":    "#6b6880",
    "INFO":     "#f0ece4",
    "WARNING":  "#f0a500",
    "ERROR":    "#ff4757",
    "CRITICAL": "#ff4757",
}

PREFIJOS_NIVEL = {
    "DEBUG":    "#9b97a5",
    "INFO":     "#56c596",
    "WARNING":  "#f0a500",
    "ERROR":    "#ff4757",
    "CRITICAL": "#ff4757",
}


class LogTab(QWidget):
    """
    Visor de logs con color por nivel, auto-scroll, filtros y exportación.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lineas: list[tuple[str, str]] = []   # (nivel, texto)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # ── Cabecera ──
        h = QHBoxLayout()
        icono = QLabel("📋")
        icono.setStyleSheet("font-size: 24px;")
        h.addWidget(icono)
        titulo = QLabel("Logs Técnicos")
        titulo.setProperty("title", True)
        h.addWidget(titulo)
        h.addStretch()

        # Filtros de nivel
        self._chk_debug = QCheckBox("DEBUG")
        self._chk_debug.setChecked(False)
        self._chk_debug.stateChanged.connect(self._refiltrar)
        h.addWidget(self._chk_debug)

        self._chk_info = QCheckBox("INFO")
        self._chk_info.setChecked(True)
        self._chk_info.stateChanged.connect(self._refiltrar)
        h.addWidget(self._chk_info)

        self._chk_warn = QCheckBox("WARN")
        self._chk_warn.setChecked(True)
        self._chk_warn.stateChanged.connect(self._refiltrar)
        h.addWidget(self._chk_warn)

        self._chk_error = QCheckBox("ERROR")
        self._chk_error.setChecked(True)
        self._chk_error.stateChanged.connect(self._refiltrar)
        h.addWidget(self._chk_error)

        root.addLayout(h)

        # ── Editor de texto para logs ──
        self._editor = QPlainTextEdit()
        self._editor.setReadOnly(True)
        self._editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._editor.setFont(QFont("Cascadia Code", 11))
        root.addWidget(self._editor, stretch=1)

        # ── Barra inferior ──
        bottom = QHBoxLayout()

        self._lbl_count = QLabel("0 entradas")
        self._lbl_count.setStyleSheet(f"color: {COLOR['text_secondary']}; font-size: 12px;")
        bottom.addWidget(self._lbl_count)
        bottom.addStretch()

        self._chk_auto_scroll = QCheckBox("Auto-scroll")
        self._chk_auto_scroll.setChecked(True)
        bottom.addWidget(self._chk_auto_scroll)

        btn_exportar = QPushButton("💾 Exportar logs")
        btn_exportar.setProperty("success", True)
        btn_exportar.setFixedHeight(34)
        btn_exportar.clicked.connect(self._exportar)
        bottom.addWidget(btn_exportar)

        btn_limpiar = QPushButton("🗑 Limpiar")
        btn_limpiar.setFixedHeight(34)
        btn_limpiar.clicked.connect(self._limpiar)
        bottom.addWidget(btn_limpiar)

        root.addLayout(bottom)

    # ──────────────────────── Slot de log ────────────────────────

    @Slot(str, str)
    def agregar_log(self, nivel: str, mensaje: str):
        """Recibe (nivel, mensaje) desde el QtLogHandler y lo muestra."""
        self._lineas.append((nivel, mensaje))
        self._lbl_count.setText(f"{len(self._lineas)} entradas")

        if self._debe_mostrar(nivel):
            self._append_coloreado(nivel, mensaje)

    def _debe_mostrar(self, nivel: str) -> bool:
        if nivel == "DEBUG" and not self._chk_debug.isChecked():
            return False
        if nivel == "INFO" and not self._chk_info.isChecked():
            return False
        if nivel in ("WARNING",) and not self._chk_warn.isChecked():
            return False
        if nivel in ("ERROR", "CRITICAL") and not self._chk_error.isChecked():
            return False
        return True

    def _append_coloreado(self, nivel: str, mensaje: str):
        color = COLORES_NIVEL.get(nivel, "#f0ece4")
        cursor = self._editor.textCursor()
        cursor.movePosition(QTextCursor.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(mensaje + "\n")

        if self._chk_auto_scroll.isChecked():
            self._editor.setTextCursor(cursor)
            self._editor.ensureCursorVisible()

    def _refiltrar(self):
        """Re-dibuja el log desde cero aplicando los filtros actuales."""
        self._editor.clear()
        for nivel, msg in self._lineas:
            if self._debe_mostrar(nivel):
                self._append_coloreado(nivel, msg)

    def _exportar(self):
        """Guarda todos los logs en un archivo .txt."""
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar logs",
            f"pos_simulator_logs_{now}.txt",
            "Archivos de texto (*.txt)",
        )
        if ruta:
            try:
                with open(ruta, "w", encoding="utf-8") as f:
                    for nivel, msg in self._lineas:
                        f.write(msg + "\n")
            except Exception as e:
                self.agregar_log("ERROR", f"No se pudo exportar: {e}")

    def _limpiar(self):
        self._lineas.clear()
        self._editor.clear()
        self._lbl_count.setText("0 entradas")

    # ──────────────────────── Mensajes directos ────────────────────────

    def agregar_mensaje(self, texto: str):
        """Agrega un mensaje INFO directamente (desde botones de UI)."""
        self.agregar_log("INFO", texto)
