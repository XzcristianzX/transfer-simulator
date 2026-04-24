"""
file_info.py — Información y metadatos de archivo seleccionado
"""
from __future__ import annotations

import os
import mimetypes
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


# Mapeo de extensiones a íconos de texto
EXTENSION_ICONS: dict[str, str] = {
    ".apk": "📦",
    ".zip": "🗜️",
    ".tar": "🗜️",
    ".gz":  "🗜️",
    ".rar": "🗜️",
    ".txt": "📄",
    ".log": "📋",
    ".bin": "⚙️",
    ".exe": "⚙️",
    ".bat": "⚙️",
    ".sh":  "⚙️",
    ".pdf": "📕",
    ".jpg": "🖼️",
    ".jpeg":"🖼️",
    ".png": "🖼️",
    ".mp4": "🎬",
    ".mp3": "🎵",
    ".iso": "💿",
    ".img": "💿",
    ".csv": "📊",
    ".json":"📋",
    ".xml": "📋",
}


@dataclass
class FileInfo:
    """Contiene toda la información relevante de un archivo seleccionado."""

    path: Path
    name: str = field(init=False)
    extension: str = field(init=False)
    size_bytes: int = field(init=False)
    size_mb: float = field(init=False)
    size_gb: float = field(init=False)
    mime_type: str = field(init=False)
    modified_date: str = field(init=False)
    icon: str = field(init=False)

    def __post_init__(self):
        p = Path(self.path)
        stat = p.stat()

        self.name = p.name
        self.extension = p.suffix.lower()
        self.size_bytes = stat.st_size
        self.size_mb = self.size_bytes / (1024 * 1024)
        self.size_gb = self.size_bytes / (1024 * 1024 * 1024)
        self.mime_type = self._get_mime()
        self.modified_date = datetime.fromtimestamp(stat.st_mtime).strftime(
            "%d/%m/%Y  %H:%M:%S"
        )
        self.icon = EXTENSION_ICONS.get(self.extension, "📁")

    def _get_mime(self) -> str:
        mime, _ = mimetypes.guess_type(str(self.path))
        return mime or "application/octet-stream"

    @property
    def size_human(self) -> str:
        """Tamaño legible: bytes / KB / MB / GB."""
        b = self.size_bytes
        if b < 1024:
            return f"{b} B"
        if b < 1024 ** 2:
            return f"{b / 1024:.1f} KB"
        if b < 1024 ** 3:
            return f"{b / (1024 ** 2):.2f} MB"
        return f"{b / (1024 ** 3):.3f} GB"

    @classmethod
    def from_path(cls, path: str | Path) -> "FileInfo":
        return cls(path=Path(path))
