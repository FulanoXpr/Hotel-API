"""
Componente LogViewer para mostrar logs en tiempo real con colores.

Proporciona un visor de logs con soporte para diferentes tipos
de mensajes (info, success, warning, error) con colores distintivos
y timestamps automáticos.
"""

from datetime import datetime
from typing import List, Literal, Optional, Tuple

import customtkinter as ctk

from ui.utils.theme import FUENTES, TemaMode, obtener_tema

# Tipo para los diferentes niveles de log
TipoLog = Literal["info", "success", "warning", "error"]


class LogViewer(ctk.CTkFrame):
    """
    Visor de logs en tiempo real con soporte para colores y temas.

    Características:
    - Colores por tipo de mensaje (info, success, warning, error)
    - Timestamp automático en cada línea
    - Auto-scroll al fondo cuando llegan nuevos mensajes
    - Soporte para tema oscuro/claro
    - Exportación de logs a archivo
    """

    # Mapeo de tipos de log a colores del tema
    _MAPEO_COLORES = {
        "info": "info",
        "success": "exito",
        "warning": "warning",
        "error": "error",
    }

    # Prefijos para cada tipo de log
    _PREFIJOS = {
        "info": "[INFO]",
        "success": "[OK]",
        "warning": "[WARN]",
        "error": "[ERROR]",
    }

    def __init__(
        self,
        master: ctk.CTkFrame,
        modo_tema: TemaMode = "dark",
        altura: int = 200,
        ancho: int = 600,
        **kwargs,
    ) -> None:
        """
        Inicializa el visor de logs.

        Args:
            master: Widget padre.
            modo_tema: Modo de tema ("dark" o "light").
            altura: Altura del componente en píxeles.
            ancho: Ancho del componente en píxeles.
        """
        self._modo_tema = modo_tema
        self._tema = obtener_tema(modo_tema)

        super().__init__(
            master, fg_color=self._tema["fondo_secundario"], corner_radius=8, **kwargs
        )

        # Almacenamiento de logs
        self._logs: List[Tuple[str, str, TipoLog]] = []

        # Configurar el textbox
        self._textbox = ctk.CTkTextbox(
            self,
            height=altura,
            width=ancho,
            font=FUENTES.get("codigo", ("Consolas", 11)),
            fg_color=self._tema["fondo_principal"],
            text_color=self._tema["texto_principal"],
            corner_radius=6,
            wrap="word",
            state="disabled",
        )
        self._textbox.pack(fill="both", expand=True, padx=8, pady=8)

        # Configurar tags de colores para cada tipo
        self._configurar_tags()

    def _configurar_tags(self) -> None:
        """Configura los tags de color para el textbox."""
        estados = self._tema["estados"]

        for tipo_log, clave_color in self._MAPEO_COLORES.items():
            color = estados.get(clave_color, self._tema["texto_principal"])
            self._textbox._textbox.tag_configure(
                tipo_log,
                foreground=color,
            )

        # Tag especial para timestamps (gris)
        color_timestamp = "#888888" if self._modo_tema == "dark" else "#666666"
        self._textbox._textbox.tag_configure(
            "timestamp",
            foreground=color_timestamp,
        )

    def agregar_log(self, mensaje: str, tipo: TipoLog = "info") -> None:
        """
        Agrega un mensaje al visor de logs.

        Args:
            mensaje: Texto del mensaje a mostrar.
            tipo: Tipo de log ("info", "success", "warning", "error").
        """
        # Generar timestamp
        ahora = datetime.now()
        timestamp = ahora.strftime("%H:%M:%S")

        # Almacenar en la lista interna
        self._logs.append((timestamp, mensaje, tipo))

        # Habilitar edición temporalmente
        self._textbox.configure(state="normal")

        # Obtener prefijo
        prefijo = self._PREFIJOS.get(tipo, "[INFO]")

        # Insertar timestamp con su tag
        texto_timestamp = f"[{timestamp}] "
        self._textbox._textbox.insert("end", texto_timestamp, "timestamp")

        # Insertar prefijo y mensaje con el tag del tipo
        texto_mensaje = f"{prefijo} {mensaje}\n"
        self._textbox._textbox.insert("end", texto_mensaje, tipo)

        # Deshabilitar edición
        self._textbox.configure(state="disabled")

        # Auto-scroll al fondo
        self._textbox.see("end")

    def limpiar(self) -> None:
        """Limpia todos los logs del visor."""
        self._logs.clear()

        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.configure(state="disabled")

    def exportar_logs(self, ruta_archivo: Optional[str] = None) -> str:
        """
        Exporta los logs a un archivo o retorna como string.

        Args:
            ruta_archivo: Ruta del archivo donde guardar. Si es None,
                         retorna los logs como string.

        Returns:
            String con todos los logs formateados.
        """
        lineas = []

        for timestamp, mensaje, tipo in self._logs:
            prefijo = self._PREFIJOS.get(tipo, "[INFO]")
            linea = f"[{timestamp}] {prefijo} {mensaje}"
            lineas.append(linea)

        contenido = "\n".join(lineas)

        if ruta_archivo:
            with open(ruta_archivo, "w", encoding="utf-8") as archivo:
                archivo.write(contenido)

        return contenido

    def obtener_logs(self) -> List[Tuple[str, str, TipoLog]]:
        """
        Obtiene la lista de logs almacenados.

        Returns:
            Lista de tuplas (timestamp, mensaje, tipo).
        """
        return self._logs.copy()

    def cambiar_tema(self, modo: TemaMode) -> None:
        """
        Cambia el tema del visor de logs.

        Args:
            modo: Nuevo modo de tema ("dark" o "light").
        """
        self._modo_tema = modo
        self._tema = obtener_tema(modo)

        self.configure(fg_color=self._tema["fondo_secundario"])

        self._textbox.configure(
            fg_color=self._tema["fondo_principal"],
            text_color=self._tema["texto_principal"],
        )

        self._configurar_tags()

    @property
    def cantidad_logs(self) -> int:
        """Retorna la cantidad de logs almacenados."""
        return len(self._logs)
