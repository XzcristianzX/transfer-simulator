"""
logger.py — Bridge thread-safe entre logging estándar de Python y señales Qt
"""
from __future__ import annotations

import logging
from PySide6.QtCore import QObject, Signal


class QtLogSignalEmitter(QObject):
    """Objeto Qt que emite señales de log desde cualquier hilo."""
    log_signal = Signal(str, str)   # (nivel, mensaje)


# Instancia global compartida entre módulos
_emitter: QtLogSignalEmitter | None = None


def get_emitter() -> QtLogSignalEmitter:
    global _emitter
    if _emitter is None:
        _emitter = QtLogSignalEmitter()
    return _emitter


class QtLogHandler(logging.Handler):
    """
    Handler de logging que reenvía mensajes al hilo Qt vía señales.
    Seguro para usar desde hilos de servidor.
    """

    NIVEL_EMOJI = {
        "DEBUG":    "🔍",
        "INFO":     "ℹ️",
        "WARNING":  "⚠️",
        "ERROR":    "❌",
        "CRITICAL": "🔴",
    }

    def __init__(self):
        super().__init__()
        self.emitter = get_emitter()

    def emit(self, record: logging.LogRecord):
        try:
            nivel = record.levelname
            emoji = self.NIVEL_EMOJI.get(nivel, "")
            msg = self.format(record)
            self.emitter.log_signal.emit(nivel, f"{emoji} {msg}")
        except Exception:
            self.handleError(record)


def configurar_logging(nivel: int = logging.DEBUG) -> None:
    """Configura el sistema de logging con formateador y handler Qt."""
    formato = logging.Formatter(
        fmt="%(asctime)s  [%(name)s]  %(message)s",
        datefmt="%H:%M:%S",
    )

    qt_handler = QtLogHandler()
    qt_handler.setFormatter(formato)
    qt_handler.setLevel(nivel)

    consola = logging.StreamHandler()
    consola.setFormatter(formato)
    consola.setLevel(nivel)

    root = logging.getLogger("pos_simulator")
    root.setLevel(nivel)
    root.addHandler(qt_handler)
    root.addHandler(consola)

    # Suprimir logs verbosos de pyftpdlib salvo warnings
    logging.getLogger("pyftpdlib").setLevel(logging.WARNING)
