"""
network_utils.py — Detección automática de red local e interfaces activas
"""
from __future__ import annotations

import socket
import logging
from dataclasses import dataclass
from typing import List

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger("pos_simulator.network")


@dataclass
class NetworkInterface:
    """Representa una interfaz de red activa."""
    name: str
    ip: str
    tipo: str          # 'WiFi', 'Ethernet', 'Loopback', 'Otro'
    activa: bool


def get_network_interfaces() -> List[NetworkInterface]:
    """
    Devuelve todas las interfaces de red con IP asignada.
    Usa psutil si está disponible, de lo contrario usa socket como fallback.
    """
    interfaces: List[NetworkInterface] = []

    if PSUTIL_AVAILABLE:
        try:
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()

            for name, addr_list in addrs.items():
                for addr in addr_list:
                    # AF_INET = IPv4
                    if addr.family == socket.AF_INET:
                        ip = addr.address
                        if ip == "127.0.0.1":
                            continue  # excluir loopback

                        activa = stats.get(name, None)
                        is_up = activa.isup if activa else False

                        tipo = _clasificar_interfaz(name)
                        interfaces.append(NetworkInterface(
                            name=name,
                            ip=ip,
                            tipo=tipo,
                            activa=is_up,
                        ))
        except Exception as e:
            logger.warning(f"Error al enumerar interfaces con psutil: {e}")

    # Fallback: IP básica con socket
    if not interfaces:
        interfaces.append(NetworkInterface(
            name="Default",
            ip=_get_ip_fallback(),
            tipo="Desconocido",
            activa=True,
        ))

    return interfaces


def get_primary_ip() -> str:
    """Devuelve la IP principal (primera interfaz activa que no sea loopback)."""
    interfaces = get_network_interfaces()
    activas = [i for i in interfaces if i.activa]
    if activas:
        return activas[0].ip
    return "127.0.0.1"


def _clasificar_interfaz(name: str) -> str:
    """Clasifica el tipo de interfaz por su nombre."""
    nl = name.lower()
    if any(k in nl for k in ("wi-fi", "wifi", "wlan", "wireless", "wi_fi")):
        return "WiFi 📶"
    if any(k in nl for k in ("eth", "ethernet", "lan", "local area")):
        return "Ethernet 🔌"
    if any(k in nl for k in ("lo", "loopback")):
        return "Loopback"
    if any(k in nl for k in ("vmnet", "vbox", "virtual", "hyper")):
        return "Virtual 🖥️"
    return "Otro"


def _get_ip_fallback() -> str:
    """Obtiene la IP local usando una conexión UDP simulada."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
