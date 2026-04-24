"""
ftp_server.py — Servidor FTP local usando pyftpdlib
Modo pasivo, autenticación configurable, soporte >2 GB.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Callable, Optional

from core.transfer_stats import TransferStats
from core.logger import get_emitter

logger = logging.getLogger("pos_simulator.ftp")

# Rango de puertos para modo pasivo (evita conflictos con puertos del sistema)
PASV_PORTS = (60000, 60100)


class ServidorFTP:
    """
    Controlador del servidor FTP usando pyftpdlib.
    Ejecuta en hilo daemon. Soporte para múltiples conexiones simultáneas.
    """

    def __init__(self):
        self._servidor = None
        self._hilo: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.stats = TransferStats()

    def iniciar(
        self,
        puerto: int,
        directorio: Path,
        usuario: str = "admin",
        clave: str = "1234",
        progress_cb: Optional[Callable] = None,
    ) -> bool:
        if self._servidor is not None:
            return False

        try:
            from pyftpdlib.handlers import FTPHandler, ThrottledDTPHandler
            from pyftpdlib.servers import FTPServer
            from pyftpdlib.authorizers import DummyAuthorizer
        except ImportError:
            logger.error(
                "pyftpdlib no está instalado. Ejecuta: pip install pyftpdlib"
            )
            return False

        self._stop_event.clear()

        try:
            # ── Autorizador: un solo usuario con acceso de lectura ──
            auth = DummyAuthorizer()
            auth.add_user(
                username=usuario,
                password=clave,
                homedir=str(directorio),
                perm="elradfmwMT",   # todos los permisos (lectura esencial)
            )

            # ── Handler FTP ──
            _stats_ref = self.stats
            _progress_cb_ref = progress_cb

            class CustomFTPHandler(FTPHandler):
                def ftp_RETR(self, file):
                    try:
                        _stats_ref.reset(0, "FTP", self.remote_ip)
                    except Exception:
                        pass
                    return super().ftp_RETR(file)
                    
                def on_file_sent(self, file):
                    logger.info(f"FTP | Archivo enviado: {file} | cliente={self.remote_ip}")
                    try:
                        size = Path(file).stat().st_size
                        if not _stats_ref.activa:
                            _stats_ref.reset(size, "FTP", self.remote_ip)
                        _stats_ref.total_bytes = size
                        _stats_ref.actualizar(size)
                        _stats_ref.finalizar()
                        if _progress_cb_ref:
                            _progress_cb_ref(size, size)
                    except Exception:
                        pass
                    super().on_file_sent(file)

            handler = CustomFTPHandler
            handler.authorizer = auth
            handler.passive_ports = range(PASV_PORTS[0], PASV_PORTS[1])
            handler.use_encoding_utf8 = True
            handler.timeout = 120
            handler.masquerade_address = None  # detectar IP automáticamente

            # ── Servidor ──
            self._servidor = FTPServer(("0.0.0.0", puerto), handler)
            self._servidor.max_cons = 50
            self._servidor.max_cons_per_ip = 5

            self._hilo = threading.Thread(
                target=self._run_forever,
                name="FTPServer",
                daemon=True,
            )
            self._hilo.start()

            logger.info(
                f"Servidor FTP iniciado | puerto={puerto} | "
                f"usuario={usuario} | dir={directorio}"
            )
            return True

        except OSError as e:
            logger.error(f"No se pudo iniciar servidor FTP: {e}")
            self._servidor = None
            return False
        except Exception as e:
            logger.error(f"Error inesperado al iniciar FTP: {e}")
            self._servidor = None
            return False

    def _run_forever(self):
        """Loop principal del servidor FTP."""
        try:
            self._servidor.serve_forever(timeout=1)
        except Exception as e:
            if not self._stop_event.is_set():
                logger.error(f"FTP loop error: {e}")


    def detener(self):
        if self._servidor:
            self._stop_event.set()
            try:
                self._servidor.close_all()
            except Exception:
                pass
            self._servidor = None
            self._hilo = None
            logger.info("Servidor FTP detenido")

    @property
    def activo(self) -> bool:
        return self._servidor is not None
