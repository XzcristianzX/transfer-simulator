"""
comparator_widget.py — Tabla de comparación de protocolos
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
)

from ui.styles import COLOR


class ComparatorWidget(QWidget):
    """Tabla visual comparando HTTP, Socket TCP y FTP."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # ── Cabecera ──
        h = QHBoxLayout()
        icono = QLabel("📊")
        icono.setStyleSheet("font-size: 24px;")
        h.addWidget(icono)
        titulo = QLabel("Comparador de Protocolos")
        titulo.setProperty("title", True)
        h.addWidget(titulo)
        h.addStretch()
        root.addLayout(h)

        desc = QLabel(
            "Comparativa técnica de los tres protocolos disponibles para transferir archivos hacia el POS. "
            "Úsala para elegir el método más conveniente según tu entorno."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLOR['text_secondary']}; font-size: 12px;")
        root.addWidget(desc)

        sep = QFrame(); sep.setProperty("separator", True); root.addWidget(sep)

        # ── Tabla ──
        headers = ["Protocolo", "Velocidad", "Seguridad", "Facilidad", "Arch. Grandes", "Multi-Conn.", "Recomendado", "Caso de Uso"]
        datos = [
            {
                "Protocolo":   ("🌐  HTTP",       COLOR['accent']),
                "Velocidad":   ("Alta ★★★★☆",     COLOR['success']),
                "Seguridad":   ("Media ★★★☆☆",    COLOR['warning']),
                "Facilidad":   ("Alta ★★★★★",     COLOR['success']),
                "Arch. Grandes": ("✅ Sí (Range)", COLOR['success']),
                "Multi-Conn.": ("✅ Sí",           COLOR['success']),
                "Recomendado": ("✅ Sí",           COLOR['success']),
                "Caso de Uso": ("APK, ZIP, APPs de POS. Android lo soporta nativamente.", COLOR['text_primary']),
            },
            {
                "Protocolo":   ("⚡ Socket TCP",   COLOR['teal']),
                "Velocidad":   ("Muy Alta ★★★★★", COLOR['success']),
                "Seguridad":   ("Baja ★★☆☆☆",     COLOR['error']),
                "Facilidad":   ("Media ★★★☆☆",    COLOR['warning']),
                "Arch. Grandes": ("✅ Sí (chunks)",COLOR['success']),
                "Multi-Conn.": ("✅ Sí",           COLOR['success']),
                "Recomendado": ("✅ Sí",           COLOR['success']),
                "Caso de Uso": ("Máxima velocidad en red interna. Ideal para binarios grandes.", COLOR['text_primary']),
            },
            {
                "Protocolo":   ("📡 FTP",          COLOR['secondary']),
                "Velocidad":   ("Media ★★★☆☆",    COLOR['warning']),
                "Seguridad":   ("Baja ★★☆☆☆",     COLOR['error']),
                "Facilidad":   ("Alta ★★★★☆",     COLOR['success']),
                "Arch. Grandes": ("✅ Sí",         COLOR['success']),
                "Multi-Conn.": ("✅ Sí",           COLOR['success']),
                "Recomendado": ("Opcional",         COLOR['warning']),
                "Caso de Uso": ("Compatibilidad con clientes FTP estándar y equipos legacy.", COLOR['text_primary']),
            },
        ]

        tabla = QTableWidget(len(datos), len(headers))
        tabla.setHorizontalHeaderLabels(headers)
        tabla.verticalHeader().setVisible(False)
        tabla.setAlternatingRowColors(True)
        tabla.setStyleSheet(f"""
            QTableWidget {{
                alternate-background-color: {COLOR['bg_hover']};
            }}
        """)
        tabla.horizontalHeader().setStretchLastSection(True)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        tabla.setShowGrid(True)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        tabla.setSelectionMode(QTableWidget.NoSelection)
        tabla.setFixedHeight(180)

        for row, fila in enumerate(datos):
            for col, header in enumerate(headers):
                texto, color = fila[header]
                item = QTableWidgetItem(texto)
                item.setForeground(QColor(color))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                tabla.setItem(row, col, item)

        tabla.setRowHeight(0, 52)
        tabla.setRowHeight(1, 52)
        tabla.setRowHeight(2, 52)

        root.addWidget(tabla)

        # ── Tarjetas de recomendación ──
        sep2 = QFrame(); sep2.setProperty("separator", True); root.addWidget(sep2)

        lbl_rec = QLabel("RECOMENDACIÓN PARA PRUEBAS")
        lbl_rec.setProperty("subtitle", True)
        root.addWidget(lbl_rec)

        tarjetas_row = QHBoxLayout()
        tarjetas_row.setSpacing(12)

        tarjetas = [
            ("🌐 HTTP",
             "Mejor opción para empezar.",
             "Android tiene soporte nativo. Basta con una URL. Sin código extra en el POS.",
             COLOR['accent']),
            ("⚡ Socket",
             "Máxima velocidad bruta.",
             "Requiere código de recepción en el POS, pero ofrece la mayor tasa de transferencia.",
             COLOR['teal']),
            ("📡 FTP",
             "Compatibilidad universal.",
             "Compatible con clientes FTP estándar. Útil si el POS ya tiene un cliente FTP.",
             COLOR['secondary']),
        ]

        for proto, bold_text, detail, color in tarjetas:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {color}18;
                    border: 1px solid {color}55;
                    border-radius: 10px;
                }}
            """)
            v = QVBoxLayout(card)
            v.setContentsMargins(14, 12, 14, 12)
            v.setSpacing(6)

            lbl_p = QLabel(proto)
            lbl_p.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 700;")
            v.addWidget(lbl_p)

            lbl_b = QLabel(bold_text)
            lbl_b.setStyleSheet(f"color: {COLOR['text_primary']}; font-weight: 600; font-size: 12px;")
            v.addWidget(lbl_b)

            lbl_d = QLabel(detail)
            lbl_d.setWordWrap(True)
            lbl_d.setStyleSheet(f"color: {COLOR['text_secondary']}; font-size: 11px;")
            v.addWidget(lbl_d)

            tarjetas_row.addWidget(card)

        root.addLayout(tarjetas_row)
        root.addStretch()
