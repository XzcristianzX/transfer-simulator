"""
styles.py — Tema cálido y profesional para el Simulador POS
Paleta: Fondo oscuro-cálido + acentos naranja ámbar + texto crema
"""

# ─────────────────────────────────────────────────────────────────────────────
# PALETA DE COLORES
# ─────────────────────────────────────────────────────────────────────────────
COLOR = {
    # Fondos
    "bg_deep":       "#0f0d14",   # Fondo principal — casi negro cálido
    "bg_surface":    "#1a1726",   # Superficie de tarjetas / paneles
    "bg_card":       "#221f30",   # Tarjetas internas
    "bg_input":      "#1a1726",   # Campos de texto
    "bg_hover":      "#2a2640",   # Hover sobre elementos

    # Acentos principales
    "accent":        "#ff8c42",   # Naranja ámbar — acción principal
    "accent_light":  "#ffb347",   # Ámbar claro — hover sobre acento
    "accent_dark":   "#e07030",   # Naranja oscuro — pressed

    # Acentos secundarios
    "secondary":     "#c77dff",   # Morado lavanda — secundario
    "teal":          "#2ec4b6",   # Teal — info / velocidad

    # Estado
    "success":       "#56c596",   # Verde
    "warning":       "#f0a500",   # Amarillo ámbar
    "error":         "#ff4757",   # Rojo coral
    "inactive":      "#6b6880",   # Gris apagado

    # Texto
    "text_primary":  "#f0ece4",   # Blanco crema
    "text_secondary":"#9b97a5",   # Gris lavanda
    "text_disabled": "#4a4758",   # Muy oscuro

    # Bordes
    "border":        "#2d2a3e",   # Borde sutil
    "border_focus":  "#ff8c42",   # Borde activo
}

# ─────────────────────────────────────────────────────────────────────────────
# STYLESHEET QSS COMPLETO
# ─────────────────────────────────────────────────────────────────────────────

def get_stylesheet() -> str:
    c = COLOR
    return f"""
/* ═══════════════════════════════════════════════════════════
   BASE — Ventana y widgets globales
═══════════════════════════════════════════════════════════ */
QMainWindow, QDialog, QWidget {{
    background-color: {c['bg_deep']};
    color: {c['text_primary']};
    font-family: "Segoe UI", "Inter", "Arial", sans-serif;
    font-size: 13px;
}}

QFrame {{
    background-color: transparent;
}}

/* ═══════════════════════════════════════════════════════════
   LABELS
═══════════════════════════════════════════════════════════ */
QLabel {{
    color: {c['text_primary']};
    background: transparent;
}}
QLabel[secondary="true"] {{
    color: {c['text_secondary']};
    font-size: 11px;
}}
QLabel[title="true"] {{
    font-size: 16px;
    font-weight: 700;
    color: {c['accent']};
}}
QLabel[subtitle="true"] {{
    font-size: 13px;
    font-weight: 600;
    color: {c['text_secondary']};
    letter-spacing: 1px;
    text-transform: uppercase;
}}

/* ═══════════════════════════════════════════════════════════
   PESTAÑAS (QTabWidget / QTabBar)
═══════════════════════════════════════════════════════════ */
QTabWidget::pane {{
    border: 1px solid {c['border']};
    border-radius: 8px;
    background-color: {c['bg_surface']};
    margin-top: -1px;
}}
QTabBar {{
    background: transparent;
}}
QTabBar::tab {{
    background: {c['bg_card']};
    color: {c['text_secondary']};
    border: 1px solid {c['border']};
    border-bottom: none;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
    font-size: 12px;
    min-width: 90px;
}}
QTabBar::tab:selected {{
    background: {c['bg_surface']};
    color: {c['accent']};
    border-color: {c['border_focus']};
    border-bottom-color: {c['bg_surface']};
}}
QTabBar::tab:hover:!selected {{
    background: {c['bg_hover']};
    color: {c['text_primary']};
}}

/* ═══════════════════════════════════════════════════════════
   BOTONES
═══════════════════════════════════════════════════════════ */
QPushButton {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
    min-height: 36px;
}}
QPushButton:hover {{
    background-color: {c['bg_hover']};
    border-color: {c['text_secondary']};
}}
QPushButton:pressed {{
    background-color: {c['bg_surface']};
}}
QPushButton:disabled {{
    color: {c['text_disabled']};
    border-color: {c['text_disabled']};
    background-color: {c['bg_deep']};
}}

/* Botón primario — Iniciar / Acción principal */
QPushButton[primary="true"] {{
    background-color: {c['accent']};
    color: #0f0d14;
    border: none;
    font-weight: 700;
}}
QPushButton[primary="true"]:hover {{
    background-color: {c['accent_light']};
}}
QPushButton[primary="true"]:pressed {{
    background-color: {c['accent_dark']};
}}
QPushButton[primary="true"]:disabled {{
    background-color: #3a3050;
    color: {c['text_disabled']};
}}

/* Botón peligro — Detener */
QPushButton[danger="true"] {{
    background-color: transparent;
    color: {c['error']};
    border: 1px solid {c['error']};
}}
QPushButton[danger="true"]:hover {{
    background-color: {c['error']};
    color: {c['text_primary']};
}}

/* Botón éxito / copiar */
QPushButton[success="true"] {{
    background-color: transparent;
    color: {c['success']};
    border: 1px solid {c['success']};
}}
QPushButton[success="true"]:hover {{
    background-color: {c['success']};
    color: {c['bg_deep']};
}}

/* ═══════════════════════════════════════════════════════════
   LINE EDIT / SPIN BOX / CAMPOS DE TEXTO
═══════════════════════════════════════════════════════════ */
QLineEdit, QSpinBox, QComboBox {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    selection-background-color: {c['accent']};
    selection-color: #0f0d14;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {c['border_focus']};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background: {c['bg_card']};
    border: none;
    width: 18px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {c['bg_hover']};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    selection-background-color: {c['accent']};
    selection-color: #0f0d14;
}}

/* ═══════════════════════════════════════════════════════════
   BARRA DE PROGRESO
═══════════════════════════════════════════════════════════ */
QProgressBar {{
    background-color: {c['bg_card']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    text-align: center;
    color: {c['text_primary']};
    font-weight: 700;
    font-size: 12px;
    min-height: 22px;
}}
QProgressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0   {c['accent_dark']},
        stop:0.5 {c['accent']},
        stop:1.0 {c['accent_light']}
    );
    border-radius: 9px;
}}

/* ═══════════════════════════════════════════════════════════
   TEXTO PLANO (LOGS)
═══════════════════════════════════════════════════════════ */
QPlainTextEdit, QTextEdit {{
    background-color: {c['bg_surface']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 8px;
    selection-background-color: {c['accent']};
    selection-color: #0f0d14;
}}

/* ═══════════════════════════════════════════════════════════
   SCROLLBARS
═══════════════════════════════════════════════════════════ */
QScrollBar:vertical {{
    background: {c['bg_deep']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {c['inactive']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c['accent']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {c['bg_deep']};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {c['inactive']};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {c['accent']};
}}

/* ═══════════════════════════════════════════════════════════
   TABLAS
═══════════════════════════════════════════════════════════ */
QTableWidget {{
    background-color: {c['bg_surface']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    gridline-color: {c['border']};
    selection-background-color: {c['accent']};
    selection-color: #0f0d14;
}}
QTableWidget::item {{
    padding: 6px 10px;
}}
QHeaderView::section {{
    background-color: {c['bg_card']};
    color: {c['accent']};
    font-weight: 700;
    font-size: 12px;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid {c['border']};
    border-bottom: 1px solid {c['border']};
}}

/* ═══════════════════════════════════════════════════════════
   STATUS BAR
═══════════════════════════════════════════════════════════ */
QStatusBar {{
    background-color: {c['bg_surface']};
    color: {c['text_secondary']};
    border-top: 1px solid {c['border']};
    font-size: 12px;
    padding: 2px 8px;
}}

/* ═══════════════════════════════════════════════════════════
   SEPARATOR
═══════════════════════════════════════════════════════════ */
QFrame[separator="true"] {{
    background-color: {c['border']};
    max-height: 1px;
    border: none;
}}

/* ═══════════════════════════════════════════════════════════
   TOOL TIPS
═══════════════════════════════════════════════════════════ */
QToolTip {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
    border: 1px solid {c['accent']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ═══════════════════════════════════════════════════════════
   MENU BAR
═══════════════════════════════════════════════════════════ */
QMenuBar {{
    background-color: {c['bg_surface']};
    color: {c['text_primary']};
    border-bottom: 1px solid {c['border']};
    padding: 2px;
}}
QMenuBar::item:selected {{
    background-color: {c['bg_hover']};
    border-radius: 4px;
}}
QMenu {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{
    padding: 8px 20px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {c['accent']};
    color: #0f0d14;
}}
QMenu::separator {{
    height: 1px;
    background: {c['border']};
    margin: 4px 8px;
}}

/* ═══════════════════════════════════════════════════════════
   CHECK BOX
═══════════════════════════════════════════════════════════ */
QCheckBox {{
    color: {c['text_primary']};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {c['border']};
    border-radius: 4px;
    background: {c['bg_input']};
}}
QCheckBox::indicator:checked {{
    background-color: {c['accent']};
    border-color: {c['accent']};
}}
"""
