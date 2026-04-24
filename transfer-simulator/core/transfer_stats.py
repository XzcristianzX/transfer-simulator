"""
transfer_stats.py — Cálculo de estadísticas de transferencia en tiempo real
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


# Ventana deslizante de muestras para cálculo de velocidad suavizada
WINDOW_SECONDS = 2.0


@dataclass
class TransferStats:
    """
    Rastrea todas las métricas de una transferencia activa.
    Thread-safe para uso desde hilos de servidor.
    """
    total_bytes: int = 0
    bytes_enviados: int = 0
    inicio: float = field(default_factory=time.time)
    activa: bool = False
    cliente_ip: str = ""
    protocolo: str = ""
    fin: float | None = None

    # Ventana deslizante: lista de tuplas (timestamp, bytes_en_ese_momento)
    _muestras: deque = field(default_factory=lambda: deque(maxlen=200))

    def reset(self, total_bytes: int, protocolo: str = "", cliente_ip: str = ""):
        """Reinicia las estadísticas para una nueva transferencia."""
        self.total_bytes = total_bytes
        self.bytes_enviados = 0
        self.inicio = time.time()
        self.fin = None
        self.activa = True
        self.cliente_ip = cliente_ip
        self.protocolo = protocolo
        self._muestras.clear()
        self._muestras.append((self.inicio, 0))

    def actualizar(self, bytes_enviados: int):
        """Llamar cada vez que se envía un chunk de datos."""
        self.bytes_enviados = bytes_enviados
        self._muestras.append((time.time(), bytes_enviados))

    def finalizar(self):
        self.activa = False
        self.fin = time.time()
        import logging
        log_msg = f"El cliente {self.cliente_ip} se demoró {self.tiempo_transcurrido_str} en la descarga del archivo que tenia {self.total_bytes} bytes por el protocolo {self.protocolo}."
        logging.getLogger("pos_simulator.stats").info(log_msg)

    # ─────────────── Propiedades calculadas ───────────────

    @property
    def porcentaje(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return min(100.0, self.bytes_enviados / self.total_bytes * 100)

    @property
    def velocidad_mbps(self) -> float:
        """MB/s calculado sobre la ventana deslizante de los últimos 2s."""
        ahora = time.time()
        if not self.activa and self.fin is not None:
             ahora = self.fin

        umbral = ahora - WINDOW_SECONDS if self.activa else 0
        if not self.activa:
            umbral = self.inicio

        # Filtrar muestras dentro de la ventana
        recientes = [(t, b) for t, b in self._muestras if t >= umbral]

        if len(recientes) < 2:
            # Fallback: velocidad total promedio
            elapsed = ahora - self.inicio
            if elapsed > 0:
                return self.bytes_enviados / elapsed / (1024 * 1024)
            return 0.0

        dt = recientes[-1][0] - recientes[0][0]
        db = recientes[-1][1] - recientes[0][1]
        if dt <= 0:
            return 0.0
        return db / dt / (1024 * 1024)

    @property
    def velocidad_kbps(self) -> float:
        return self.velocidad_mbps * 1024

    @property
    def tiempo_transcurrido(self) -> float:
        if self.activa or self.fin is None:
            return time.time() - self.inicio
        return self.fin - self.inicio

    @property
    def tiempo_restante(self) -> Optional[float]:
        """Segundos estimados restantes. None si no se puede calcular."""
        v = self.velocidad_mbps
        if v <= 0:
            return None
        restante_mb = (self.total_bytes - self.bytes_enviados) / (1024 * 1024)
        return restante_mb / v

    @property
    def tiempo_restante_str(self) -> str:
        t = self.tiempo_restante
        if t is None:
            return "Calculando..."
        t = int(t)
        if t < 60:
            return f"{t}s"
        m, s = divmod(t, 60)
        if m < 60:
            return f"{m}m {s}s"
        h, m = divmod(m, 60)
        return f"{h}h {m}m {s}s"

    @property
    def tiempo_transcurrido_str(self) -> str:
        t = int(self.tiempo_transcurrido)
        m, s = divmod(t, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    @property
    def bytes_enviados_human(self) -> str:
        return _human_bytes(self.bytes_enviados)

    @property
    def total_bytes_human(self) -> str:
        return _human_bytes(self.total_bytes)


def _human_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    if b < 1024 ** 2:
        return f"{b / 1024:.1f} KB"
    if b < 1024 ** 3:
        return f"{b / (1024**2):.2f} MB"
    return f"{b / (1024**3):.3f} GB"
