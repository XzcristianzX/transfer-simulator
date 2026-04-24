"""
progress_widget.py — Widget reutilizable de progreso de transferencia en tiempo real
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar,
)

from core.transfer_stats import TransferStats
from ui.styles import COLOR


class ProgressWidget(QFrame):
    """
    Tarjeta de progreso que muestra estadísticas de transferencia en tiempo real.
    Se actualiza automáticamente cada 300 ms mientras hay una transferencia activa.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stats: TransferStats | None = None
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(300)
        self._timer.timeout.connect(self._actualizar)

    # ──────────────────────── UI ────────────────────────

    def _build_ui(self):
        self.setStyleSheet(f"""
            ProgressWidget {{
                background-color: {COLOR['bg_card']};
                border: 1px solid {COLOR['border']};
                border-radius: 12px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # ── Fila de estado ──
        fila_estado = QHBoxLayout()

        self._lbl_protocolo = QLabel("—")
        self._lbl_protocolo.setStyleSheet(
            f"color: {COLOR['accent']}; font-size: 14px; font-weight: 700;"
        )
        fila_estado.addWidget(self._lbl_protocolo)
        fila_estado.addStretch()

        self._lbl_estado = QLabel("En espera")
        self._lbl_estado.setStyleSheet(
            f"color: {COLOR['text_secondary']}; font-size: 12px;"
        )
        fila_estado.addWidget(self._lbl_estado)
        root.addLayout(fila_estado)

        # ── Barra de progreso ──
        self._barra = QProgressBar()
        self._barra.setRange(0, 100)
        self._barra.setValue(0)
        self._barra.setFormat("%p%")
        self._barra.setFixedHeight(24)
        root.addWidget(self._barra)

        # ── Grid de métricas ──
        grid = QHBoxLayout()
        grid.setSpacing(12)

        self._velocidad_card = self._card("🚀 Velocidad", "0.00 MB/s", COLOR['teal'])
        self._tiempo_card    = self._card("⏱ Transcurrido", "00:00", COLOR['text_primary'])
        self._eta_card       = self._card("⏳ Restante", "—", COLOR['warning'])
        self._bytes_card     = self._card("📊 Transferido", "0 B / 0 B", COLOR['text_secondary'])
        self._cliente_card   = self._card("🌐 Cliente", "—", COLOR['secondary'])

        for c in [self._velocidad_card, self._tiempo_card, self._eta_card,
                  self._bytes_card, self._cliente_card]:
            grid.addWidget(c)

        root.addLayout(grid)

    def _card(self, titulo: str, valor_inicial: str, color_valor: str) -> QFrame:
        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR['bg_surface']};
                border: 1px solid {COLOR['border']};
                border-radius: 8px;
            }}
        """)
        v = QVBoxLayout(f)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(2)

        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet(f"color: {COLOR['text_secondary']}; font-size: 10px; font-weight: 600;")
        v.addWidget(lbl_t)

        lbl_v = QLabel(valor_inicial)
        lbl_v.setStyleSheet(f"color: {color_valor}; font-size: 13px; font-weight: 700;")
        lbl_v.setWordWrap(True)
        f._valor = lbl_v
        v.addWidget(lbl_v)

        return f

    # ──────────────────────── Control ────────────────────────

    def vincular_stats(self, stats: TransferStats):
        """Vincula este widget a un objeto TransferStats."""
        self._stats = stats

    def iniciar_actualizaciones(self):
        self._timer.start()

    def detener_actualizaciones(self):
        self._timer.stop()
        self._reset_display()

    def _reset_display(self):
        self._barra.setValue(0)
        self._lbl_estado.setText("En espera")
        self._velocidad_card._valor.setText("0.00 MB/s")
        self._tiempo_card._valor.setText("00:00")
        self._eta_card._valor.setText("—")
        self._bytes_card._valor.setText("0 B / 0 B")
        self._cliente_card._valor.setText("—")
        self._lbl_protocolo.setText("—")

    # ──────────────────────── Update loop ────────────────────────

    def _actualizar(self):
        if self._stats is None:
            return

        s = self._stats

        if not s.activa and s.bytes_enviados == 0:
            return

        self._lbl_protocolo.setText(s.protocolo or "—")
        self._lbl_estado.setText(
            "✅ Completado" if not s.activa and s.bytes_enviados > 0
            else "🔄 Transfiriendo..."
        )

        pct = int(s.porcentaje)
        self._barra.setValue(pct)

        self._velocidad_card._valor.setText(f"{s.velocidad_mbps:.2f} MB/s")
        self._tiempo_card._valor.setText(s.tiempo_transcurrido_str)
        self._eta_card._valor.setText(s.tiempo_restante_str)
        self._bytes_card._valor.setText(
            f"{s.bytes_enviados_human} / {s.total_bytes_human}"
        )
        self._cliente_card._valor.setText(s.cliente_ip or "—")
