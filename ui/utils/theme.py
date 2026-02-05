"""
Configuración de tema para Hotel Price Checker.
Define colores, fuentes y funciones para aplicar temas oscuro/claro.
"""

import platform
from typing import Dict, Literal, TypedDict

import customtkinter as ctk

# Tipo para modo de tema
TemaMode = Literal["dark", "light"]


class ColoresEstado(TypedDict):
    """Colores para estados de la aplicación."""

    exito: str
    error: str
    warning: str
    info: str


class ConfiguracionTema(TypedDict):
    """Configuración completa de un tema."""

    fondo_principal: str
    fondo_secundario: str
    texto_principal: str
    texto_secundario: str
    acento: str
    acento_hover: str
    borde: str
    estados: ColoresEstado


# Colores de marca FPR (Foundation for Puerto Rico)
FPR_BLUE = "#3189A1"
FPR_BLUE_LIGHT = "#62D4DA"
FPR_GREEN = "#B0CA5F"
FPR_GREEN_LIGHT = "#D7F346"
FPR_YELLOW = "#FCAF17"
FPR_RED = "#F04E37"
FPR_GREY = "#3E4242"
FPR_GREY_LIGHT = "#7E7E7E"

# Configuración del tema oscuro
TEMA_OSCURO: ConfiguracionTema = {
    "fondo_principal": "#1a2528",
    "fondo_secundario": FPR_GREY,
    "texto_principal": "#f0f4f5",
    "texto_secundario": "#c4cfd2",
    "acento": FPR_BLUE,
    "acento_hover": FPR_BLUE_LIGHT,
    "borde": "#4a5354",
    "estados": {
        "exito": FPR_GREEN,
        "error": FPR_RED,
        "warning": FPR_YELLOW,
        "info": FPR_BLUE_LIGHT,
    },
}

# Configuración del tema claro
TEMA_CLARO: ConfiguracionTema = {
    "fondo_principal": "#f5f7f7",
    "fondo_secundario": "#ffffff",
    "texto_principal": FPR_GREY,
    "texto_secundario": FPR_GREY_LIGHT,
    "acento": FPR_BLUE,
    "acento_hover": "#287a8f",
    "borde": "#d1d5d6",
    "estados": {
        "exito": "#8fb34a",  # FPR Green más oscuro para contraste
        "error": "#d94432",  # FPR Red más oscuro para contraste
        "warning": "#e09a10",  # FPR Yellow más oscuro para contraste
        "info": FPR_BLUE,
    },
}

# Fuentes por plataforma
_SISTEMA = platform.system()
_FUENTE_UI = (
    "SF Pro Display" if _SISTEMA == "Darwin"
    else "Segoe UI" if _SISTEMA == "Windows"
    else "Ubuntu"
)
_FUENTE_MONO = (
    "Menlo" if _SISTEMA == "Darwin"
    else "Consolas" if _SISTEMA == "Windows"
    else "Ubuntu Mono"
)

# Constantes de fuentes
FUENTES: Dict[str, tuple] = {
    "titulo": (_FUENTE_UI, 24, "bold"),
    "subtitulo": (_FUENTE_UI, 18, "bold"),
    "encabezado": (_FUENTE_UI, 14, "bold"),
    "normal": (_FUENTE_UI, 12),
    "pequena": (_FUENTE_UI, 10),
    "codigo": (_FUENTE_MONO, 11),
}

# Colores de botones por rol
BOTONES: Dict[str, Dict[str, str]] = {
    "primario": {"fg": FPR_BLUE, "hover": FPR_BLUE_LIGHT},
    "peligro": {"fg": FPR_RED, "hover": "#c0392b"},
    "secundario": {"fg": FPR_GREY, "hover": "#555555"},
    "exito": {"fg": FPR_GREEN, "hover": "#8fb34a"},
    "advertencia": {"fg": FPR_YELLOW, "hover": "#e09a10"},
}

# Constantes de tamaño
TAMANOS: Dict[str, int] = {
    "padding_grande": 20,
    "padding_medio": 10,
    "padding_pequeno": 5,
    "radio_borde": 8,
    "ancho_boton": 120,
    "alto_boton": 32,
}


def obtener_tema(modo: TemaMode) -> ConfiguracionTema:
    """
    Obtiene la configuración del tema según el modo.

    Args:
        modo: "dark" para tema oscuro, "light" para tema claro.

    Returns:
        Diccionario con la configuración del tema.
    """
    return TEMA_OSCURO if modo == "dark" else TEMA_CLARO


def aplicar_tema(modo: TemaMode) -> None:
    """
    Aplica el tema a CustomTkinter globalmente.

    Args:
        modo: "dark" para tema oscuro, "light" para tema claro.
    """
    ctk.set_appearance_mode(modo)
    ctk.set_default_color_theme("blue")


def obtener_color_estado(estado: str, modo: TemaMode) -> str:
    """
    Obtiene el color para un estado específico.

    Args:
        estado: Uno de "exito", "error", "warning", "info".
        modo: El modo de tema actual.

    Returns:
        Código de color hexadecimal.
    """
    tema = obtener_tema(modo)
    return tema["estados"].get(estado, tema["texto_principal"])


def obtener_fuente(tipo: str) -> tuple:
    """
    Obtiene la configuración de fuente para un tipo específico.

    Args:
        tipo: Uno de "titulo", "subtitulo", "encabezado", "normal", "pequena", "codigo".

    Returns:
        Tupla con (familia, tamaño, peso) de la fuente.
    """
    return FUENTES.get(tipo, FUENTES["normal"])
