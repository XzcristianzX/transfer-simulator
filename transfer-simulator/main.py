"""
main.py — Punto de entrada del Simulador POS de Transferencia de Archivos

Uso:
    python main.py

Requisitos:
    pip install -r requirements.txt
"""
from __future__ import annotations

import sys
import os

# Asegurar que el directorio raíz está en el path de importación
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QPalette, QColor, QFont

from ui.main_window import MainWindow
from ui.styles import get_stylesheet, COLOR


def configurar_paleta_oscura(app: QApplication) -> None:
    """Configura la paleta Qt base con colores oscuros (complementa el QSS)."""
    paleta = QPalette()

    oscuro = QColor(COLOR["bg_deep"])
    superficie = QColor(COLOR["bg_surface"])
    texto = QColor(COLOR["text_primary"])
    texto_dis = QColor(COLOR["text_disabled"])
    acento = QColor(COLOR["accent"])

    paleta.setColor(QPalette.Window,          oscuro)
    paleta.setColor(QPalette.WindowText,      texto)
    paleta.setColor(QPalette.Base,            superficie)
    paleta.setColor(QPalette.AlternateBase,   QColor(COLOR["bg_card"]))
    paleta.setColor(QPalette.ToolTipBase,     QColor(COLOR["bg_card"]))
    paleta.setColor(QPalette.ToolTipText,     texto)
    paleta.setColor(QPalette.Text,            texto)
    paleta.setColor(QPalette.Button,          superficie)
    paleta.setColor(QPalette.ButtonText,      texto)
    paleta.setColor(QPalette.BrightText,      acento)
    paleta.setColor(QPalette.Link,            acento)
    paleta.setColor(QPalette.Highlight,       acento)
    paleta.setColor(QPalette.HighlightedText, QColor("#0f0d14"))
    paleta.setColor(QPalette.Disabled, QPalette.Text,       texto_dis)
    paleta.setColor(QPalette.Disabled, QPalette.ButtonText, texto_dis)

    app.setPalette(paleta)


def main() -> int:
    # ── Atributos de alta resolución (antes de crear QApplication) ──
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("POS Transfer Simulator")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("POS Tools")

    # Fuente global
    fuente = QFont("Segoe UI", 10)
    fuente.setHintingPreference(QFont.PreferFullHinting)
    app.setFont(fuente)

    # Paleta oscura
    configurar_paleta_oscura(app)

    # Stylesheet QSS completo
    app.setStyleSheet(get_stylesheet())

    # Ventana principal
    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
