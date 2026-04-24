"""
socket_server.py — Servidor TCP Socket para transferencia binaria al POS
Multi-conexión simultánea, sin dependencias externas.
"""
from __future__ import annotations

import logging
import socket
import threading
import time
from pathlib import Path
from typing import Callable, List, Optional

from core.transfer_stats import TransferStats

logger = logging.getLogger("pos_simulator.socket")

# Tamaño de chunk TCP (64 KB — óptimo para transferencias locales)
CHUNK_SIZE = 64 * 1024

# Cabecera de protocolo simple: nombre + tamaño para que el POS sepa cuánto leer
# Formato: "POSFILE:<nombre>:<tamaño_bytes>\n"
HEADER_TEMPLATE = "POSFILE:{nombre}:{size}\n"


class ClienteSocket(threading.Thread):
    """Hilo per-cliente que transfiere el archivo completo."""

    def __init__(self, conn: socket.socket, addr: tuple,
                 archivo: Path, stats: TransferStats,
                 progress_cb: Optional[Callable],
                 on_finish: Optional[Callable]):
        super().__init__(daemon=True, name=f"SocketCliente-{addr[0]}")
        self.conn = conn
        self.addr = addr
        self.archivo = archivo
        self.stats = stats
        self.progress_cb = progress_cb
        self.on_finish = on_finish

    def run(self):
        ip = self.addr[0]
        total = self.archivo.stat().st_size
        nombre = self.archivo.name

        logger.info(f"Socket | Cliente conectado: {ip} | archivo={nombre} | tamaño={total:,} bytes")

        self.stats.reset(total, "Socket TCP", ip)

        try:
            # Enviar cabecera de protocolo
            header = HEADER_TEMPLATE.format(nombre=nombre, size=total).encode("utf-8")
            self.conn.sendall(header)

            tiempo_inicio = time.time()
            enviados = 0

            with open(self.archivo, "rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    self.conn.sendall(chunk)
                    enviados += len(chunk)
                    self.stats.actualizar(enviados)
                    if self.progress_cb:
                        self.progress_cb(enviados, total)

            tiempo_total = time.time() - tiempo_inicio
            velocidad = (total / tiempo_total / (1024**2)) if tiempo_total > 0 else 0
            logger.info(
                f"Socket | Transferencia completada | cliente={ip} | "
                f"tiempo={tiempo_total:.1f}s | velocidad={velocidad:.2f} MB/s"
            )
            self.stats.finalizar()

        except (BrokenPipeError, ConnectionResetError, OSError):
            logger.warning(f"Socket | Conexión interrumpida con {ip}")
        except Exception as e:
            logger.error(f"Socket | Error en transferencia: {e}")
        finally:
            try:
                self.conn.close()
            except Exception:
                pass
            if self.on_finish:
                self.on_finish(ip)


class ServidorSocket:
    """
    Controlador del servidor TCP Socket con soporte multi-cliente.
    Cada cliente recibe el archivo en su propio hilo.
    """

    def __init__(self):
        self._socket: Optional[socket.socket] = None
        self._hilo_aceptar: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._clientes_activos: List[str] = []
        self._clientes_lock = threading.Lock()
        self.stats = TransferStats()

    def iniciar(self, puerto: int, archivo: Path,
                progress_cb: Optional[Callable] = None) -> bool:
        if self._socket is not None:
            return False

        self._stop_event.clear()
        self._archivo = archivo

        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Buffer de envío grande para alto rendimiento
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4 * 1024 * 1024)
            srv.bind(("0.0.0.0", puerto))
            srv.listen(10)
            srv.settimeout(1.0)   # timeout para comprobar stop_event
            self._socket = srv

            self._hilo_aceptar = threading.Thread(
                target=self._aceptar_clientes,
                args=(archivo, progress_cb),
                name="SocketAceptar",
                daemon=True,
            )
            self._hilo_aceptar.start()
            logger.info(f"Servidor Socket TCP iniciado en puerto {puerto}")
            return True

        except OSError as e:
            logger.error(f"No se pudo iniciar servidor Socket: {e}")
            return False

    def _aceptar_clientes(self, archivo: Path, progress_cb: Optional[Callable]):
        while not self._stop_event.is_set():
            try:
                conn, addr = self._socket.accept()
                with self._clientes_lock:
                    self._clientes_activos.append(addr[0])

                cliente = ClienteSocket(
                    conn=conn,
                    addr=addr,
                    archivo=archivo,
                    stats=self.stats,
                    progress_cb=progress_cb,
                    on_finish=self._cliente_finalizado,
                )
                cliente.start()

            except socket.timeout:
                continue
            except OSError:
                break

    def _cliente_finalizado(self, ip: str):
        with self._clientes_lock:
            if ip in self._clientes_activos:
                self._clientes_activos.remove(ip)

    def detener(self):
        self._stop_event.set()
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
        self._hilo_aceptar = None
        logger.info("Servidor Socket TCP detenido")

    @property
    def activo(self) -> bool:
        return self._socket is not None

    @property
    def clientes_activos(self) -> List[str]:
        with self._clientes_lock:
            return list(self._clientes_activos)
