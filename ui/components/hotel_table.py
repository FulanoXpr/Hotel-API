"""
Componente de tabla de hoteles para la interfaz de usuario.

Este módulo proporciona una tabla scrollable con selección múltiple
para mostrar y gestionar la lista de hoteles.
"""

from typing import Any, Callable, Dict, List, Optional

import customtkinter as ctk

from ui.utils.icons import get_icon
from ui.utils.theme import FUENTES, TAMANOS, obtener_fuente

# Tipo para representar datos de un hotel
HotelData = Dict[str, Optional[str]]


class HotelTableRow(ctk.CTkFrame):
    """
    Fila individual de la tabla de hoteles.

    Representa un hotel con checkbox, número, nombre, key y estado.

    Attributes:
        hotel_data: Datos del hotel representado.
        indice: Número de fila (1-based).
        seleccionado: Si la fila está seleccionada.
    """

    def __init__(
        self,
        master: Any,
        indice: int,
        hotel_data: HotelData,
        on_select: Optional[Callable[["HotelTableRow", bool], None]] = None,
        on_double_click: Optional[Callable[["HotelTableRow"], None]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Inicializa una fila de la tabla.

        Args:
            master: Widget padre.
            indice: Número de fila (1-based).
            hotel_data: Diccionario con datos del hotel.
            on_select: Callback cuando cambia la selección.
            on_double_click: Callback cuando se hace doble clic.
        """
        super().__init__(master, **kwargs)

        self.hotel_data = hotel_data
        self.indice = indice
        self.seleccionado = False
        self._on_select = on_select
        self._on_double_click = on_double_click

        # Configurar grid
        self.grid_columnconfigure(1, weight=0, minsize=50)  # #
        self.grid_columnconfigure(2, weight=3, minsize=200)  # Hotel
        self.grid_columnconfigure(3, weight=2, minsize=150)  # Key
        self.grid_columnconfigure(4, weight=0, minsize=60)  # Estado

        self._crear_widgets()
        self._bind_eventos()

    def _crear_widgets(self) -> None:
        """Crea los widgets de la fila."""
        # Checkbox de selección
        self.var_seleccion = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.var_seleccion,
            width=20,
            command=self._on_checkbox_change,
            checkbox_width=18,
            checkbox_height=18,
        )
        self.checkbox.grid(row=0, column=0, padx=(5, 2), pady=2, sticky="w")

        # Número de fila
        self.label_numero = ctk.CTkLabel(
            self,
            text=str(self.indice),
            font=obtener_fuente("pequena"),
            width=40,
            anchor="center",
        )
        self.label_numero.grid(row=0, column=1, padx=2, pady=2)

        # Nombre del hotel
        nombre = self.hotel_data.get("nombre", "")
        self.label_nombre = ctk.CTkLabel(
            self, text=nombre, font=obtener_fuente("normal"), anchor="w"
        )
        self.label_nombre.grid(row=0, column=2, padx=5, pady=2, sticky="ew")

        # Key Xotelo
        key = self.hotel_data.get("xotelo_key", "") or ""
        self.label_key = ctk.CTkLabel(
            self, text=key, font=obtener_fuente("codigo"), anchor="w"
        )
        self.label_key.grid(row=0, column=3, padx=5, pady=2, sticky="ew")

        # Estado (icono)
        estado = "✅" if key else "⚠️"
        self.label_estado = ctk.CTkLabel(
            self, text=estado, font=obtener_fuente("normal"), width=40, anchor="center"
        )
        self.label_estado.grid(row=0, column=4, padx=(2, 5), pady=2)

    def _bind_eventos(self) -> None:
        """Configura los eventos de la fila."""
        # Doble clic para editar
        self.bind("<Double-Button-1>", self._on_double_click_event)
        self.label_nombre.bind("<Double-Button-1>", self._on_double_click_event)
        self.label_key.bind("<Double-Button-1>", self._on_double_click_event)

    def _on_checkbox_change(self) -> None:
        """Maneja el cambio en el checkbox."""
        self.seleccionado = self.var_seleccion.get()
        if self._on_select:
            self._on_select(self, self.seleccionado)

    def _on_double_click_event(self, event: Any) -> None:
        """Maneja el doble clic en la fila."""
        if self._on_double_click:
            self._on_double_click(self)

    def seleccionar(self, valor: bool = True) -> None:
        """
        Establece el estado de selección.

        Args:
            valor: True para seleccionar, False para deseleccionar.
        """
        self.seleccionado = valor
        self.var_seleccion.set(valor)

    def actualizar_datos(self, hotel_data: HotelData) -> None:
        """
        Actualiza los datos mostrados en la fila.

        Args:
            hotel_data: Nuevos datos del hotel.
        """
        self.hotel_data = hotel_data
        self.label_nombre.configure(text=hotel_data.get("nombre", ""))
        key = hotel_data.get("xotelo_key", "") or ""
        self.label_key.configure(text=key)
        estado = "✅" if key else "⚠️"
        self.label_estado.configure(text=estado)

    def actualizar_indice(self, nuevo_indice: int) -> None:
        """
        Actualiza el número de fila.

        Args:
            nuevo_indice: Nuevo índice (1-based).
        """
        self.indice = nuevo_indice
        self.label_numero.configure(text=str(nuevo_indice))


class HotelTable(ctk.CTkScrollableFrame):
    """
    Tabla scrollable de hoteles con selección múltiple.

    Muestra una lista de hoteles con columnas para número, nombre,
    key Xotelo y estado. Soporta selección múltiple con checkboxes.

    Attributes:
        hoteles: Lista interna de datos de hoteles.
        filas: Lista de widgets HotelTableRow.
        on_selection_change: Callback cuando cambia la selección.
        on_double_click: Callback cuando se hace doble clic en una fila.
    """

    def __init__(
        self,
        master: Any,
        on_selection_change: Optional[Callable[[List[HotelData]], None]] = None,
        on_double_click: Optional[Callable[[int, HotelData], None]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Inicializa la tabla de hoteles.

        Args:
            master: Widget padre.
            on_selection_change: Callback con lista de hoteles seleccionados.
            on_double_click: Callback con índice y datos del hotel.
        """
        super().__init__(master, **kwargs)

        self.hoteles: List[HotelData] = []
        self.filas: List[HotelTableRow] = []
        self._on_selection_change = on_selection_change
        self._on_double_click = on_double_click

        # Configurar grid de la tabla
        self.grid_columnconfigure(0, weight=1)

        self._crear_encabezados()
        self._crear_empty_state()
        self._actualizar_empty_state()

    def _crear_empty_state(self) -> None:
        """Crea el frame de estado vacío."""
        self.frame_empty_state = ctk.CTkFrame(self, fg_color="transparent")

        icon_label = ctk.CTkLabel(
            self.frame_empty_state,
            text="",
            image=get_icon("list", size=(48, 48)),
        )
        icon_label.pack(pady=(30, 10))

        ctk.CTkLabel(
            self.frame_empty_state,
            text="No hotels added yet",
            font=obtener_fuente("encabezado"),
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            self.frame_empty_state,
            text="Load an Excel file or add hotels manually",
            font=obtener_fuente("pequena"),
            text_color="gray",
        ).pack()

    def _actualizar_empty_state(self) -> None:
        """Muestra u oculta el empty state según la cantidad de hoteles."""
        if len(self.hoteles) == 0:
            self.frame_empty_state.grid(row=2, column=0, sticky="ew", pady=20)
        else:
            self.frame_empty_state.grid_forget()

    def _crear_encabezados(self) -> None:
        """Crea la fila de encabezados."""
        self.frame_headers = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_headers.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        # Configurar columnas igual que las filas
        self.frame_headers.grid_columnconfigure(1, weight=0, minsize=50)
        self.frame_headers.grid_columnconfigure(2, weight=3, minsize=200)
        self.frame_headers.grid_columnconfigure(3, weight=2, minsize=150)
        self.frame_headers.grid_columnconfigure(4, weight=0, minsize=60)

        # Checkbox "seleccionar todos"
        self.var_select_all = ctk.BooleanVar(value=False)
        self.checkbox_all = ctk.CTkCheckBox(
            self.frame_headers,
            text="",
            variable=self.var_select_all,
            width=20,
            command=self._on_select_all,
            checkbox_width=18,
            checkbox_height=18,
        )
        self.checkbox_all.grid(row=0, column=0, padx=(5, 2), pady=2, sticky="w")

        # Headers
        headers = [
            ("#", 1, "center", 40),
            ("Hotel", 2, "w", None),
            ("Key Xotelo", 3, "w", None),
            ("Estado", 4, "center", 40),
        ]

        for texto, col, anchor, width in headers:
            label = ctk.CTkLabel(
                self.frame_headers,
                text=texto,
                font=obtener_fuente("encabezado"),
                anchor=anchor,
                width=width if width else 0,
            )
            sticky = "ew" if anchor == "w" else ""
            label.grid(row=0, column=col, padx=5, pady=2, sticky=sticky)

        # Separador visual
        self.separador = ctk.CTkFrame(self, height=2, fg_color="gray50")
        self.separador.grid(row=1, column=0, sticky="ew", pady=2)

    def _on_select_all(self) -> None:
        """Maneja el checkbox de seleccionar/deseleccionar todos."""
        valor = self.var_select_all.get()
        for fila in self.filas:
            fila.seleccionar(valor)
        self._notificar_cambio_seleccion()

    def _on_fila_select(self, fila: HotelTableRow, seleccionado: bool) -> None:
        """Maneja el cambio de selección de una fila."""
        # Actualizar checkbox "seleccionar todos"
        todos_seleccionados = all(f.seleccionado for f in self.filas)
        self.var_select_all.set(todos_seleccionados)
        self._notificar_cambio_seleccion()

    def _on_fila_double_click(self, fila: HotelTableRow) -> None:
        """Maneja el doble clic en una fila."""
        if self._on_double_click:
            self._on_double_click(fila.indice - 1, fila.hotel_data)

    def _notificar_cambio_seleccion(self) -> None:
        """Notifica el cambio en la selección."""
        if self._on_selection_change:
            seleccionados = [f.hotel_data for f in self.filas if f.seleccionado]
            self._on_selection_change(seleccionados)

    def agregar_hotel(
        self, nombre: str, key: Optional[str] = None, booking_url: Optional[str] = None
    ) -> None:
        """
        Agrega un hotel a la tabla.

        Args:
            nombre: Nombre del hotel.
            key: Key Xotelo (opcional).
            booking_url: URL de Booking (opcional).
        """
        hotel_data: HotelData = {
            "nombre": nombre,
            "xotelo_key": key,
            "booking_url": booking_url,
        }
        self.hoteles.append(hotel_data)
        self._agregar_fila(hotel_data, len(self.hoteles))
        self._actualizar_empty_state()

    def _agregar_fila(self, hotel_data: HotelData, indice: int) -> None:
        """Crea y agrega una fila a la tabla."""
        fila = HotelTableRow(
            self,
            indice=indice,
            hotel_data=hotel_data,
            on_select=self._on_fila_select,
            on_double_click=self._on_fila_double_click,
            fg_color="transparent",
        )
        fila.grid(row=indice + 1, column=0, sticky="ew", pady=1)
        self.filas.append(fila)

    def cargar_hoteles(self, hoteles: List[HotelData]) -> None:
        """
        Carga una lista de hoteles reemplazando los existentes.

        Args:
            hoteles: Lista de diccionarios con datos de hoteles.
        """
        self.limpiar()
        self.hoteles = list(hoteles)

        # Crear filas en lotes para no bloquear el UI
        BATCH_SIZE = 20
        for idx, hotel in enumerate(self.hoteles, start=1):
            self._agregar_fila(hotel, idx)
            if idx % BATCH_SIZE == 0:
                self.update_idletasks()

        self._actualizar_empty_state()

    def eliminar_seleccionados(self) -> int:
        """
        Elimina los hoteles seleccionados de la tabla.

        Returns:
            Número de hoteles eliminados.
        """
        # Obtener índices de filas seleccionadas (en orden inverso)
        indices_a_eliminar = [
            idx for idx, fila in enumerate(self.filas) if fila.seleccionado
        ]

        if not indices_a_eliminar:
            return 0

        # Eliminar en orden inverso para mantener índices válidos
        for idx in reversed(indices_a_eliminar):
            self.filas[idx].destroy()
            del self.filas[idx]
            del self.hoteles[idx]

        # Renumerar filas restantes
        for idx, fila in enumerate(self.filas):
            fila.actualizar_indice(idx + 1)
            fila.grid(row=idx + 2, column=0, sticky="ew", pady=1)

        # Resetear checkbox de seleccionar todos
        self.var_select_all.set(False)
        self._notificar_cambio_seleccion()
        self._actualizar_empty_state()

        return len(indices_a_eliminar)

    def obtener_hoteles(self) -> List[HotelData]:
        """
        Obtiene la lista completa de hoteles.

        Returns:
            Lista de diccionarios con datos de hoteles.
        """
        return list(self.hoteles)

    def obtener_seleccionados(self) -> List[HotelData]:
        """
        Obtiene los hoteles seleccionados.

        Returns:
            Lista de diccionarios con datos de hoteles seleccionados.
        """
        return [f.hotel_data for f in self.filas if f.seleccionado]

    def limpiar(self) -> None:
        """Elimina todos los hoteles de la tabla."""
        for fila in self.filas:
            fila.destroy()
        self.filas.clear()
        self.hoteles.clear()
        self.var_select_all.set(False)
        self._actualizar_empty_state()

    def actualizar_hotel(self, indice: int, hotel_data: HotelData) -> None:
        """
        Actualiza los datos de un hotel específico.

        Args:
            indice: Índice del hotel (0-based).
            hotel_data: Nuevos datos del hotel.
        """
        if 0 <= indice < len(self.filas):
            self.hoteles[indice] = hotel_data
            self.filas[indice].actualizar_datos(hotel_data)

    def obtener_estadisticas(self) -> Dict[str, int]:
        """
        Obtiene estadísticas de la tabla.

        Returns:
            Diccionario con total, con_key, sin_key.
        """
        total = len(self.hoteles)
        con_key = sum(1 for h in self.hoteles if h.get("xotelo_key"))
        sin_key = total - con_key

        return {"total": total, "con_key": con_key, "sin_key": sin_key}
