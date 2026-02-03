"""
Configuración de tema para Hotel Price Checker.
Define colores, fuentes y funciones para aplicar temas oscuro/claro.
"""

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


# Configuración del tema oscuro
TEMA_OSCURO: ConfiguracionTema = {
    "fondo_principal": "#1a1a2e",
    "fondo_secundario": "#16213e",
    "texto_principal": "#eaeaea",
    "texto_secundario": "#a0a0a0",
    "acento": "#0f4c75",
    "acento_hover": "#3282b8",
    "borde": "#2d2d44",
    "estados": {
        "exito": "#2ecc71",
        "error": "#e74c3c",
        "warning": "#f39c12",
        "info": "#3498db",
    },
}

# Configuración del tema claro
TEMA_CLARO: ConfiguracionTema = {
    "fondo_principal": "#f5f5f5",
    "fondo_secundario": "#ffffff",
    "texto_principal": "#2c3e50",
    "texto_secundario": "#7f8c8d",
    "acento": "#3498db",
    "acento_hover": "#2980b9",
    "borde": "#dcdcdc",
    "estados": {
        "exito": "#27ae60",
        "error": "#c0392b",
        "warning": "#d68910",
        "info": "#2471a3",
    },
}

# Constantes de fuentes
FUENTES: Dict[str, tuple] = {
    "titulo": ("Segoe UI", 24, "bold"),
    "subtitulo": ("Segoe UI", 18, "bold"),
    "encabezado": ("Segoe UI", 14, "bold"),
    "normal": ("Segoe UI", 12),
    "pequena": ("Segoe UI", 10),
    "codigo": ("Consolas", 11),
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
