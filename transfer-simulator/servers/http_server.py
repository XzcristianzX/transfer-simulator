"""
http_server.py — Servidor HTTP local para transferencia de archivos al POS
Soporta Range headers (reanudación), transferencias simultáneas y archivos >2 GB.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from http import HTTPStatus
from pathlib import Path
from typing import Callable, Optional
from socketserver import ThreadingMixIn

from core.transfer_stats import TransferStats
from core.logger import get_emitter

logger = logging.getLogger("pos_simulator.http")

# Tamaño de chunk para streaming (512 KB, balanceo rendimiento/memoria)
CHUNK_SIZE = 512 * 1024

# Callbacks globales (se asignan desde el servidor)
_archivo_path: Optional[Path] = None
_progress_cb: Optional[Callable] = None
_stats: Optional[TransferStats] = None
_lock = threading.Lock()


class POSHTTPHandler(BaseHTTPRequestHandler):
    """Handler HTTP personalizado que sirve el archivo seleccionado."""

    protocol_version = "HTTP/1.1"

    # ── Silenciar logs de acceso de BaseHTTPRequestHandler ──
    def log_message(self, format, *args):
        logger.info(f"HTTP | {self.client_address[0]} | {format % args}")

    def log_error(self, format, *args):
        logger.error(f"HTTP | {self.client_address[0]} | {format % args}")

    def do_GET(self):
        global _archivo_path, _progress_cb, _stats

        if _archivo_path is None or not _archivo_path.exists():
            self._send_error(404, "No hay archivo seleccionado en el servidor.")
            return

        ruta = self.path.lstrip("/")

        # Permitir cualquier ruta o la ruta raíz (redirige al archivo)
        if ruta == "" or ruta == _archivo_path.name:
            self._servir_archivo()
        elif ruta == "favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            # Listar archivo disponible como HTML simple
            self._servir_indice()

    def do_HEAD(self):
        """Responde a HEAD sin body (soporte para clientes FTP/HTTP avanzados)."""
        global _archivo_path
        if _archivo_path is None or not _archivo_path.exists():
            self._send_error(404, "Sin archivo.")
            return
        self._enviar_cabeceras(_archivo_path.stat().st_size, 0)

    def _servir_archivo(self):
        global _archivo_path, _stats, _progress_cb

        archivo = _archivo_path
        total = archivo.stat().st_size

        # Soporte Range headers para reanudación
        rango = self.headers.get("Range", "")
        inicio = 0
        fin = total - 1

        if rango.startswith("bytes="):
            try:
                partes = rango[6:].split("-")
                inicio = int(partes[0]) if partes[0] else 0
                fin = int(partes[1]) if len(partes) > 1 and partes[1] else total - 1
            except ValueError:
                pass

        longitud = fin - inicio + 1
        codigo = HTTPStatus.PARTIAL_CONTENT if inicio > 0 else HTTPStatus.OK

        logger.info(
            f"Descarga iniciada | cliente={self.client_address[0]} | "
            f"archivo={archivo.name} | tamaño={longitud:,} bytes"
        )

        with _lock:
            if _stats:
                _stats.reset(total, "HTTP", self.client_address[0])

        try:
            self.send_response(codigo)
            self._enviar_cabeceras(longitud, inicio, fin, total, codigo)

            with open(archivo, "rb") as f:
                f.seek(inicio)
                enviados = inicio
                tiempo_inicio = time.time()

                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    enviados += len(chunk)

                    with _lock:
                        if _stats:
                            _stats.actualizar(enviados)
                    if _progress_cb:
                        _progress_cb(enviados, total)

            tiempo_total = time.time() - tiempo_inicio
            velocidad = (longitud / tiempo_total / (1024**2)) if tiempo_total > 0 else 0
            logger.info(
                f"Descarga completada | cliente={self.client_address[0]} | "
                f"tiempo={tiempo_total:.1f}s | velocidad={velocidad:.2f} MB/s"
            )
            with _lock:
                if _stats:
                    _stats.finalizar()

        except (BrokenPipeError, ConnectionResetError):
            logger.warning(f"Conexión interrumpida | cliente={self.client_address[0]}")
        except Exception as e:
            logger.error(f"Error en transferencia HTTP: {e}")

    def _enviar_cabeceras(self, longitud: int, inicio: int = 0,
                          fin: int = None, total: int = None,
                          codigo: HTTPStatus = HTTPStatus.OK):
        global _archivo_path
        nombre = _archivo_path.name if _archivo_path else "archivo"

        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(longitud))
        self.send_header(
            "Content-Disposition", f'attachment; filename="{nombre}"'
        )
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Connection", "close")
        if fin is not None and total is not None:
            self.send_header(
                "Content-Range", f"bytes {inicio}-{fin}/{total}"
            )
        self.end_headers()

    def _servir_indice(self):
        global _archivo_path
        nombre = _archivo_path.name if _archivo_path else "sin archivo"
        html = (
            f"<!DOCTYPE html><html><head>"
            f"<meta charset='utf-8'><title>POS File Server</title>"
            f"<style>body{{background:#141219;color:#f0ece4;"
            f"font-family:monospace;padding:2rem;}}"
            f"a{{color:#ff8c42;font-size:1.4rem;}}</style></head>"
            f"<body><h2>🚀 POS File Transfer Server</h2>"
            f"<p>Archivo disponible:</p>"
            f"<a href='/{nombre}'>⬇️ {nombre}</a></body></html>"
        ).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def _send_error(self, code: int, message: str):
        body = message.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Servidor HTTP multi-hilo para conexiones simultáneas."""
    daemon_threads = True
    allow_reuse_address = True


class ServidorHTTP:
    """
    Controlador del ciclo de vida del servidor HTTP.
    Hilo daemon que no bloquea la UI.
    """

    def __init__(self):
        self._server: Optional[ThreadedHTTPServer] = None
        self._hilo: Optional[threading.Thread] = None
        self.stats = TransferStats()

    def iniciar(self, puerto: int, archivo: Path,
                progress_cb: Optional[Callable] = None) -> bool:
        global _archivo_path, _progress_cb, _stats

        if self._server is not None:
            return False  # Ya activo

        _archivo_path = archivo
        _progress_cb = progress_cb
        _stats = self.stats

        try:
            self._server = ThreadedHTTPServer(("0.0.0.0", puerto), POSHTTPHandler)
            self._hilo = threading.Thread(
                target=self._server.serve_forever,
                name="HTTPServer",
                daemon=True,
            )
            self._hilo.start()
            logger.info(f"Servidor HTTP iniciado en puerto {puerto}")
            return True
        except OSError as e:
            logger.error(f"No se pudo iniciar servidor HTTP: {e}")
            self._server = None
            return False

    def detener(self):
        global _archivo_path, _progress_cb, _stats

        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
            self._hilo = None
            _archivo_path = None
            _progress_cb = None
            logger.info("Servidor HTTP detenido")

    @property
    def activo(self) -> bool:
        return self._server is not None
