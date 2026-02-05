"""
Panel de estadísticas de búsqueda en vivo.

Muestra contadores visuales para el progreso de búsqueda de hoteles,
incluyendo totales, éxitos, fallos, cache hits y desglose por proveedor.
"""

from typing import Dict

import customtkinter as ctk

from ui.utils.icons import get_icon
from ui.utils.theme import FUENTES, TAMANOS, TemaMode, obtener_tema


class StatsPanel(ctk.CTkFrame):
    """
    Panel de estadísticas para búsquedas de hoteles.

    Muestra contadores visuales para Total, Éxitos, Fallos, Cache hits
    y desglose por proveedor con barras de progreso.
    """

    # Colores específicos para cada proveedor
    COLORES_PROVEEDORES = {
        "xotelo": "#3498db",  # Azul
        "serpapi": "#9b59b6",  # Púrpura
        "apify": "#e67e22",  # Naranja
        "amadeus": "#1abc9c",  # Verde azulado
    }

    def __init__(
        self, master: ctk.CTkFrame, modo_tema: TemaMode = "dark", **kwargs
    ) -> None:
        """
        Inicializa el panel de estadísticas.

        Args:
            master: Widget padre.
            modo_tema: Modo de tema ("dark" o "light").
            **kwargs: Argumentos adicionales para CTkFrame.
        """
        self.modo_tema = modo_tema
        self.tema = obtener_tema(modo_tema)

        super().__init__(
            master, fg_color=self.tema["fondo_secundario"], corner_radius=TAMANOS["radio_borde"], **kwargs
        )

        # Inicializar estadísticas en cero
        self._stats: Dict[str, int] = {
            "total": 0,
            "cache": 0,
            "not_found": 0,
            "xotelo": 0,
            "serpapi": 0,
            "apify": 0,
            "amadeus": 0,
        }

        # Referencias a widgets
        self._labels_valores: Dict[str, ctk.CTkLabel] = {}
        self._progress_bars: Dict[str, ctk.CTkProgressBar] = {}
        self._labels_proveedores: Dict[str, ctk.CTkLabel] = {}

        # Crear la interfaz
        self._crear_encabezado()
        self._crear_contadores_principales()
        self._crear_seccion_proveedores()

    def _crear_encabezado(self) -> None:
        """Crea el encabezado del panel."""
        self.frame_encabezado = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_encabezado.pack(fill="x", padx=15, pady=(15, 10))

        self.label_titulo = ctk.CTkLabel(
            self.frame_encabezado,
            text="Search Statistics",
            font=FUENTES.get("encabezado", ("Segoe UI", 14, "bold")),
            image=get_icon("chart"),
            compound="left",
        )
        self.label_titulo.pack(side="left")

        self.boton_reiniciar = ctk.CTkButton(
            self.frame_encabezado,
            text="Reset",
            font=FUENTES.get("pequena", ("Segoe UI", 10)),
            width=70,
            height=26,
            fg_color=self.tema["acento"],
            hover_color=self.tema["acento_hover"],
            command=self.reiniciar,
        )
        self.boton_reiniciar.pack(side="right")

    def _crear_contadores_principales(self) -> None:
        """Crea los contadores principales (Total, Éxitos, Fallos, Cache)."""
        self.frame_contadores = ctk.CTkFrame(
            self,
            fg_color=self.tema["fondo_principal"],
            corner_radius=8,
        )
        self.frame_contadores.pack(fill="x", padx=15, pady=5)

        for i in range(4):
            self.frame_contadores.grid_columnconfigure(i, weight=1)

        contadores_config = [
            ("total", "Total", self.tema["texto_principal"]),
            ("exitos", "Success", self.tema["estados"]["exito"]),
            ("not_found", "Failures", self.tema["estados"]["error"]),
            ("cache", "Cache", self.tema["estados"]["info"]),
        ]

        for col, (key, label, color) in enumerate(contadores_config):
            frame_contador = ctk.CTkFrame(
                self.frame_contadores,
                fg_color="transparent",
            )
            frame_contador.grid(row=0, column=col, padx=10, pady=10)

            label_valor = ctk.CTkLabel(
                frame_contador,
                text="0",
                font=FUENTES.get("titulo", ("Segoe UI", 24, "bold")),
                text_color=color,
            )
            label_valor.pack()

            label_nombre = ctk.CTkLabel(
                frame_contador,
                text=label,
                font=FUENTES.get("pequena", ("Segoe UI", 10)),
            )
            label_nombre.pack()

            self._labels_valores[key] = label_valor

    def _crear_seccion_proveedores(self) -> None:
        """Crea la sección de desglose por proveedor."""
        self.separador = ctk.CTkFrame(
            self,
            fg_color=self.tema["borde"],
            height=1,
        )
        self.separador.pack(fill="x", padx=15, pady=10)

        self.label_proveedores = ctk.CTkLabel(
            self,
            text="By Provider",
            font=FUENTES.get("encabezado", ("Segoe UI", 14, "bold")),
        )
        self.label_proveedores.pack(anchor="w", padx=15, pady=(0, 5))

        self.frame_proveedores = ctk.CTkFrame(
            self,
            fg_color=self.tema["fondo_principal"],
            corner_radius=8,
        )
        self.frame_proveedores.pack(fill="x", padx=15, pady=(0, 15))

        proveedores = [
            ("xotelo", "Xotelo"),
            ("serpapi", "SerpApi"),
            ("apify", "Apify"),
            ("amadeus", "Amadeus"),
        ]

        for idx, (key, nombre) in enumerate(proveedores):
            self._crear_fila_proveedor(key, nombre, idx)

    def _crear_fila_proveedor(self, key: str, nombre: str, row: int) -> None:
        """Crea una fila para un proveedor con nombre, barra y contador."""
        frame_fila = ctk.CTkFrame(
            self.frame_proveedores,
            fg_color="transparent",
        )
        frame_fila.pack(fill="x", padx=10, pady=5)

        label_nombre = ctk.CTkLabel(
            frame_fila,
            text=nombre,
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            width=70,
            anchor="w",
        )
        label_nombre.pack(side="left", padx=(0, 10))

        color_proveedor = self.COLORES_PROVEEDORES.get(key, self.tema["acento"])
        progress_bar = ctk.CTkProgressBar(
            frame_fila,
            width=150,
            height=12,
            corner_radius=6,
            fg_color=self.tema["borde"],
            progress_color=color_proveedor,
        )
        progress_bar.pack(side="left", padx=5, expand=True, fill="x")
        progress_bar.set(0)

        label_contador = ctk.CTkLabel(
            frame_fila,
            text="0",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            text_color=color_proveedor,
            width=40,
            anchor="e",
        )
        label_contador.pack(side="right", padx=(10, 0))

        self._progress_bars[key] = progress_bar
        self._labels_proveedores[key] = label_contador

    def actualizar_stats(self, stats_dict: Dict[str, int]) -> None:
        """
        Actualiza las estadísticas mostradas en el panel.

        Args:
            stats_dict: Diccionario con las estadísticas.
        """
        for key, valor in stats_dict.items():
            if key in self._stats:
                self._stats[key] = valor

        total = self._stats.get("total", 0)
        not_found = self._stats.get("not_found", 0)
        cache = self._stats.get("cache", 0)

        # Éxitos = encontrados por proveedores (no cache, no fallos)
        exitos = sum(
            [
                self._stats.get("xotelo", 0),
                self._stats.get("serpapi", 0),
                self._stats.get("apify", 0),
                self._stats.get("amadeus", 0),
            ]
        )

        # Actualizar contadores principales
        if "total" in self._labels_valores:
            self._labels_valores["total"].configure(text=str(total))
        if "exitos" in self._labels_valores:
            self._labels_valores["exitos"].configure(text=str(exitos))
        if "not_found" in self._labels_valores:
            self._labels_valores["not_found"].configure(text=str(not_found))
        if "cache" in self._labels_valores:
            self._labels_valores["cache"].configure(text=str(cache))

        # Calcular total de proveedores para proporciones
        total_proveedores = exitos if exitos > 0 else 1

        # Actualizar barras de progreso y contadores de proveedores
        for proveedor in ["xotelo", "serpapi", "apify", "amadeus"]:
            valor = self._stats.get(proveedor, 0)

            if proveedor in self._labels_proveedores:
                self._labels_proveedores[proveedor].configure(text=str(valor))

            if proveedor in self._progress_bars:
                proporcion = valor / total_proveedores if total_proveedores > 0 else 0
                self._progress_bars[proveedor].set(proporcion)

    def reiniciar(self) -> None:
        """Reinicia todas las estadísticas a cero."""
        self._stats = {
            "total": 0,
            "cache": 0,
            "not_found": 0,
            "xotelo": 0,
            "serpapi": 0,
            "apify": 0,
            "amadeus": 0,
        }
        self.actualizar_stats(self._stats)

    def obtener_resumen(self) -> Dict[str, int]:
        """Obtiene un resumen de las estadísticas actuales."""
        exitos = sum(
            [
                self._stats.get("xotelo", 0),
                self._stats.get("serpapi", 0),
                self._stats.get("apify", 0),
                self._stats.get("amadeus", 0),
            ]
        )

        return {
            "total": self._stats.get("total", 0),
            "exitos": exitos,
            "cache": self._stats.get("cache", 0),
            "not_found": self._stats.get("not_found", 0),
            "xotelo": self._stats.get("xotelo", 0),
            "serpapi": self._stats.get("serpapi", 0),
            "apify": self._stats.get("apify", 0),
            "amadeus": self._stats.get("amadeus", 0),
        }

    def cambiar_tema(self, modo_tema: TemaMode) -> None:
        """Cambia el tema del panel."""
        self.modo_tema = modo_tema
        self.tema = obtener_tema(modo_tema)

        self.configure(fg_color=self.tema["fondo_secundario"])
        self.frame_contadores.configure(fg_color=self.tema["fondo_principal"])
        self.frame_proveedores.configure(fg_color=self.tema["fondo_principal"])
        self.separador.configure(fg_color=self.tema["borde"])

        self.boton_reiniciar.configure(
            fg_color=self.tema["acento"],
            hover_color=self.tema["acento_hover"],
        )

        colores_contadores = {
            "total": self.tema["texto_principal"],
            "exitos": self.tema["estados"]["exito"],
            "not_found": self.tema["estados"]["error"],
            "cache": self.tema["estados"]["info"],
        }
        for key, label in self._labels_valores.items():
            if key in colores_contadores:
                label.configure(text_color=colores_contadores[key])

        for proveedor, progress_bar in self._progress_bars.items():
            progress_bar.configure(fg_color=self.tema["borde"])
