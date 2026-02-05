"""
Pestaña de gestión de hoteles para la aplicación Hotel Price Checker.

Este módulo proporciona la interfaz completa para cargar, agregar,
eliminar y gestionar hoteles con sus keys de Xotelo.
"""

import json
import os
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Callable, Dict, List, Optional, Union

import customtkinter as ctk

# Agregar el directorio raíz al path para imports
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from ui.components.hotel_table import HotelData, HotelTable
from ui.utils.excel_handler import ExcelHandler
from ui.utils.icons import get_icon
from ui.utils.theme import BOTONES, BOTONES_OUTLINED, TAMANOS, obtener_fuente
from ui.utils.tooltip import ToolTip


class EditarHotelDialog(ctk.CTkToplevel):
    """
    Diálogo para editar los datos de un hotel.

    Permite modificar el nombre, key Xotelo y URL de Booking de un hotel.
    """

    def __init__(
        self,
        master: Any,
        hotel_data: HotelData,
        on_save: Callable[[HotelData], None],
        **kwargs: Any,
    ) -> None:
        """
        Inicializa el diálogo de edición.

        Args:
            master: Widget padre.
            hotel_data: Datos actuales del hotel.
            on_save: Callback cuando se guardan los cambios.
        """
        super().__init__(master, **kwargs)

        self.hotel_data = hotel_data
        self._on_save = on_save

        # Importar XoteloAPI aquí para evitar import circular
        try:
            from xotelo_api import XoteloAPI

            self.api = XoteloAPI()
        except ImportError:
            self.api = None

        # Configurar ventana
        self.title("Edit Hotel")
        self.geometry("500x300")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # Centrar en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 300) // 2
        self.geometry(f"+{x}+{y}")

        self._crear_widgets()

    def _crear_widgets(self) -> None:
        """Crea los widgets del diálogo."""
        padding = TAMANOS["padding_medio"]

        # Frame principal
        self.frame_principal = ctk.CTkFrame(self)
        self.frame_principal.pack(fill="both", expand=True, padx=padding, pady=padding)
        self.frame_principal.grid_columnconfigure(1, weight=1)

        # Campo nombre
        ctk.CTkLabel(
            self.frame_principal,
            text="Hotel Name:",
            font=obtener_fuente("normal"),
            anchor="w",
        ).grid(row=0, column=0, padx=padding, pady=padding, sticky="w")

        self.entry_nombre = ctk.CTkEntry(
            self.frame_principal, font=obtener_fuente("normal"), width=300
        )
        self.entry_nombre.grid(row=0, column=1, padx=padding, pady=padding, sticky="ew")
        self.entry_nombre.insert(0, self.hotel_data.get("nombre", ""))

        # Campo key Xotelo
        ctk.CTkLabel(
            self.frame_principal,
            text="Key Xotelo:",
            font=obtener_fuente("normal"),
            anchor="w",
        ).grid(row=1, column=0, padx=padding, pady=padding, sticky="w")

        frame_key = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_key.grid(row=1, column=1, padx=padding, pady=padding, sticky="ew")
        frame_key.grid_columnconfigure(0, weight=1)

        self.entry_key = ctk.CTkEntry(
            frame_key, font=obtener_fuente("codigo"), placeholder_text="g147319-d123456"
        )
        self.entry_key.grid(row=0, column=0, sticky="ew")
        key = self.hotel_data.get("xotelo_key", "") or ""
        self.entry_key.insert(0, key)

        self.btn_buscar = ctk.CTkButton(
            frame_key, text="Search", image=get_icon("search"), compound="left",
            width=80, command=self._buscar_key,
        )
        self.btn_buscar.grid(row=0, column=1, padx=(5, 0))

        # Campo URL
        ctk.CTkLabel(
            self.frame_principal,
            text="URL Booking:",
            font=obtener_fuente("normal"),
            anchor="w",
        ).grid(row=2, column=0, padx=padding, pady=padding, sticky="w")

        self.entry_url = ctk.CTkEntry(
            self.frame_principal,
            font=obtener_fuente("pequena"),
            placeholder_text="https://www.booking.com/...",
        )
        self.entry_url.grid(row=2, column=1, padx=padding, pady=padding, sticky="ew")
        url = self.hotel_data.get("booking_url", "") or ""
        self.entry_url.insert(0, url)

        # Label de estado
        self.label_estado = ctk.CTkLabel(
            self.frame_principal, text="", font=obtener_fuente("pequena")
        )
        self.label_estado.grid(row=3, column=0, columnspan=2, padx=padding, pady=5)

        # Botones
        frame_botones = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_botones.grid(row=4, column=0, columnspan=2, pady=padding)

        ctk.CTkButton(
            frame_botones,
            text="Cancel",
            width=100,
            fg_color=BOTONES["secundario"]["fg"],
            hover_color=BOTONES["secundario"]["hover"],
            command=self.destroy,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame_botones, text="Save", image=get_icon("save"), compound="left",
            width=100, command=self._guardar,
        ).pack(side="left", padx=5)

    def _buscar_key(self) -> None:
        """Busca la key Xotelo para el hotel."""
        if not self.api:
            self.label_estado.configure(
                text="Xotelo API not available", text_color="red"
            )
            return

        nombre = self.entry_nombre.get().strip()
        if not nombre:
            self.label_estado.configure(
                text="Enter a hotel name first", text_color="orange"
            )
            return

        self.label_estado.configure(text="Searching...", text_color="gray")
        self.btn_buscar.configure(state="disabled")

        def buscar() -> None:
            try:
                resultado = self.api.search_hotel(nombre)
                if resultado:
                    self.after(0, lambda: self._actualizar_key(resultado["key"]))
                else:
                    self.after(0, lambda: self._mostrar_no_encontrado())
            except Exception as e:
                self.after(0, lambda: self._mostrar_error(str(e)))

        thread = threading.Thread(target=buscar, daemon=True)
        thread.start()

    def _actualizar_key(self, key: str) -> None:
        """Actualiza el campo de key con el resultado."""
        self.entry_key.delete(0, "end")
        self.entry_key.insert(0, key)
        self.label_estado.configure(
            text=f"✅ Key found: {key}", text_color="green"
        )
        self.btn_buscar.configure(state="normal")

    def _mostrar_no_encontrado(self) -> None:
        """Muestra mensaje de hotel no encontrado."""
        self.label_estado.configure(
            text="⚠️ Hotel not found in Xotelo", text_color="orange"
        )
        self.btn_buscar.configure(state="normal")

    def _mostrar_error(self, error: str) -> None:
        """Muestra mensaje de error."""
        self.label_estado.configure(text=f"❌ Error: {error}", text_color="red")
        self.btn_buscar.configure(state="normal")

    def _guardar(self) -> None:
        """Guarda los cambios y cierra el diálogo."""
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Warning", "Hotel name is required.")
            return

        datos: HotelData = {
            "nombre": nombre,
            "xotelo_key": self.entry_key.get().strip() or None,
            "booking_url": self.entry_url.get().strip() or None,
        }

        self._on_save(datos)
        self.destroy()


class HotelsTab(ctk.CTkFrame):
    """
    Pestaña de gestión de hoteles.

    Proporciona interfaz para:
    - Cargar hoteles desde archivos Excel
    - Cargar hoteles desde hotel_keys_db.json
    - Agregar hoteles manualmente
    - Buscar keys de Xotelo automáticamente
    - Eliminar hoteles seleccionados
    - Editar hoteles existentes

    Attributes:
        tabla: Componente HotelTable con la lista de hoteles.
        excel_handler: Manejador de archivos Excel.
        api: Cliente de la API de Xotelo.
    """

    # Path to hotel keys database (relative to project root)
    HOTEL_DB_FILENAME = "hotel_keys_db.json"

    def __init__(self, master: Any, **kwargs: Any) -> None:
        """
        Inicializa la pestaña de hoteles.

        Args:
            master: Widget padre (normalmente el frame de la pestaña).
        """
        super().__init__(master, fg_color="transparent", **kwargs)

        self.excel_handler = ExcelHandler()
        self._indice_editando: Optional[int] = None

        # Importar XoteloAPI aquí para evitar import circular
        try:
            from xotelo_api import XoteloAPI

            self.api = XoteloAPI()
        except ImportError:
            self.api = None

        # Configurar grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # La tabla se expande

        self._crear_barra_herramientas()
        self._crear_tabla()
        self._crear_panel_agregar()
        self._crear_barra_estado()

    def _crear_barra_herramientas(self) -> None:
        """Crea la barra de herramientas superior en 2 filas."""
        padding = TAMANOS["padding_medio"]

        self.barra_herramientas = ctk.CTkFrame(self, corner_radius=TAMANOS["radio_borde"])
        self.barra_herramientas.grid(
            row=0, column=0, sticky="ew", padx=padding, pady=(padding, 5)
        )

        # --- Fila 1: Data (cargar/guardar) ---
        fila_data = ctk.CTkFrame(self.barra_herramientas, fg_color="transparent")
        fila_data.pack(fill="x", padx=2, pady=(5, 0))

        self.btn_download_cache = ctk.CTkButton(
            fila_data,
            text="Download PR Hotels",
            image=get_icon("download"),
            compound="left",
            width=160,
            fg_color=BOTONES["violeta"]["fg"],
            hover_color=BOTONES["violeta"]["hover"],
            command=self._descargar_cache_hoteles,
        )
        self.btn_download_cache.pack(side="left", padx=5, pady=2)

        self.btn_cargar_db = ctk.CTkButton(
            fila_data,
            text="Load Database",
            image=get_icon("database"),
            compound="left",
            width=TAMANOS["ancho_boton"],
            fg_color=BOTONES["indigo"]["fg"],
            hover_color=BOTONES["indigo"]["hover"],
            command=self._cargar_database,
        )
        self.btn_cargar_db.pack(side="left", padx=5, pady=2)

        self.btn_cargar = ctk.CTkButton(
            fila_data,
            text="Load Excel",
            image=get_icon("folder"),
            compound="left",
            width=TAMANOS["ancho_boton"],
            fg_color=BOTONES["azul"]["fg"],
            hover_color=BOTONES["azul"]["hover"],
            command=self._cargar_excel,
        )
        self.btn_cargar.pack(side="left", padx=5, pady=2)

        self.btn_guardar = ctk.CTkButton(
            fila_data,
            text="Save Excel",
            image=get_icon("save"),
            compound="left",
            width=TAMANOS["ancho_boton"],
            fg_color=BOTONES["exito"]["fg"],
            hover_color=BOTONES["exito"]["hover"],
            command=self._guardar_excel,
        )
        self.btn_guardar.pack(side="left", padx=5, pady=2)

        # --- Fila 2: Actions (buscar/editar/eliminar) ---
        fila_acciones = ctk.CTkFrame(self.barra_herramientas, fg_color="transparent")
        fila_acciones.pack(fill="x", padx=2, pady=(0, 5))

        self.btn_buscar_keys = ctk.CTkButton(
            fila_acciones,
            text="Search All",
            image=get_icon("search"),
            compound="left",
            width=120,
            fg_color=BOTONES_OUTLINED["default"]["fg"],
            hover_color=BOTONES_OUTLINED["default"]["hover"],
            border_color=BOTONES_OUTLINED["default"]["border"],
            text_color=BOTONES_OUTLINED["default"]["text"],
            border_width=2,
            command=self._buscar_keys_faltantes,
        )
        self.btn_buscar_keys.pack(side="left", padx=5, pady=2)

        self.btn_buscar_keys_sel = ctk.CTkButton(
            fila_acciones,
            text="Search Keys (Selection)",
            image=get_icon("search"),
            compound="left",
            width=160,
            fg_color=BOTONES_OUTLINED["peligro"]["fg"],
            hover_color=BOTONES_OUTLINED["peligro"]["hover"],
            border_color=BOTONES_OUTLINED["peligro"]["border"],
            text_color=BOTONES_OUTLINED["peligro"]["text"],
            border_width=2,
            command=self._buscar_keys_seleccionados,
        )
        self.btn_buscar_keys_sel.pack(side="left", padx=5, pady=2)

        # Separador visual
        ctk.CTkFrame(
            fila_acciones, width=2, height=25, fg_color="gray50"
        ).pack(side="left", padx=10, pady=2)

        self.btn_eliminar = ctk.CTkButton(
            fila_acciones,
            text="Delete",
            image=get_icon("trash"),
            compound="left",
            width=100,
            fg_color=BOTONES_OUTLINED["secundario"]["fg"],
            hover_color=BOTONES_OUTLINED["secundario"]["hover"],
            border_color=BOTONES_OUTLINED["secundario"]["border"],
            text_color=BOTONES_OUTLINED["secundario"]["text"],
            border_width=2,
            command=self._eliminar_seleccionados,
        )
        self.btn_eliminar.pack(side="left", padx=5, pady=2)

        self.btn_limpiar = ctk.CTkButton(
            fila_acciones,
            text="Clear All",
            image=get_icon("clear"),
            compound="left",
            width=100,
            fg_color=BOTONES_OUTLINED["secundario"]["fg"],
            hover_color=BOTONES_OUTLINED["secundario"]["hover"],
            border_color=BOTONES_OUTLINED["secundario"]["border"],
            text_color=BOTONES_OUTLINED["secundario"]["text"],
            border_width=2,
            command=self._limpiar_todo,
        )
        self.btn_limpiar.pack(side="left", padx=5, pady=2)

        # Tooltips
        ToolTip(self.btn_download_cache, "Download ~1,100 PR hotels from Xotelo for key matching")
        ToolTip(self.btn_cargar_db, "Load hotels from hotel_keys_db.json")
        ToolTip(self.btn_cargar, "Import hotel list from Excel file")
        ToolTip(self.btn_guardar, "Export current hotel list to Excel")
        ToolTip(self.btn_buscar_keys, "Search Xotelo keys for all hotels without a key")
        ToolTip(self.btn_buscar_keys_sel, "Search Xotelo keys only for selected hotels")
        ToolTip(self.btn_eliminar, "Remove selected hotels from the list")
        ToolTip(self.btn_limpiar, "Remove all hotels from the list")

    def _crear_tabla(self) -> None:
        """Crea la tabla de hoteles."""
        padding = TAMANOS["padding_medio"]

        self.tabla = HotelTable(
            self,
            on_selection_change=self._on_seleccion_cambio,
            on_double_click=self._on_doble_click,
        )
        self.tabla.grid(row=1, column=0, sticky="nsew", padx=padding, pady=5)

    def _crear_panel_agregar(self) -> None:
        """Crea el panel para agregar hoteles manualmente."""
        padding = TAMANOS["padding_medio"]

        # Frame contenedor
        self.panel_agregar = ctk.CTkFrame(self, corner_radius=TAMANOS["radio_borde"])
        self.panel_agregar.grid(row=2, column=0, sticky="ew", padx=padding, pady=5)
        self.panel_agregar.grid_columnconfigure(1, weight=1)
        self.panel_agregar.grid_columnconfigure(3, weight=1)

        # Título del panel
        ctk.CTkLabel(
            self.panel_agregar,
            text="Add Hotel Manually",
            font=obtener_fuente("encabezado"),
        ).grid(row=0, column=0, columnspan=6, pady=(5, 10))

        # Campo nombre
        ctk.CTkLabel(
            self.panel_agregar, text="Name:", font=obtener_fuente("normal")
        ).grid(row=1, column=0, padx=5, pady=5, sticky="e")

        self.entry_nombre = ctk.CTkEntry(
            self.panel_agregar,
            font=obtener_fuente("normal"),
            placeholder_text="e.g., Hilton Ponce Golf & Casino",
        )
        self.entry_nombre.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Campo key (opcional)
        ctk.CTkLabel(
            self.panel_agregar, text="Key Xotelo:", font=obtener_fuente("normal")
        ).grid(row=1, column=2, padx=(20, 5), pady=5, sticky="e")

        self.entry_key = ctk.CTkEntry(
            self.panel_agregar,
            font=obtener_fuente("codigo"),
            placeholder_text="e.g., g147319-d1837036",
        )
        self.entry_key.grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        # Botón buscar key
        self.btn_buscar = ctk.CTkButton(
            self.panel_agregar, text="Search", image=get_icon("search"),
            compound="left", width=80, command=self._buscar_key,
        )
        self.btn_buscar.grid(row=1, column=4, padx=5, pady=5)

        # Botón agregar
        self.btn_agregar = ctk.CTkButton(
            self.panel_agregar,
            text="Add to List",
            image=get_icon("plus"),
            compound="left",
            width=120,
            fg_color=BOTONES["azul"]["fg"],
            hover_color=BOTONES["azul"]["hover"],
            command=self._agregar_hotel,
        )
        self.btn_agregar.grid(row=1, column=5, padx=5, pady=5)

        # Label de estado de búsqueda
        self.label_busqueda = ctk.CTkLabel(
            self.panel_agregar, text="", font=obtener_fuente("pequena")
        )
        self.label_busqueda.grid(row=2, column=0, columnspan=6, pady=5)

    def _crear_barra_estado(self) -> None:
        """Crea la barra de estado inferior."""
        padding = TAMANOS["padding_medio"]

        self.barra_estado = ctk.CTkFrame(self, height=30)
        self.barra_estado.grid(
            row=3, column=0, sticky="ew", padx=padding, pady=(5, padding)
        )

        self.label_contador = ctk.CTkLabel(
            self.barra_estado,
            text="Total: 0 hotels | With key: 0 | Without key: 0",
            font=obtener_fuente("normal"),
        )
        self.label_contador.pack(side="left", padx=10, pady=5)

        self.label_seleccion = ctk.CTkLabel(
            self.barra_estado, text="Selected: 0", font=obtener_fuente("normal")
        )
        self.label_seleccion.pack(side="right", padx=10, pady=5)

        # Progress bar indeterminada (oculta por defecto)
        self.progress_bar = ctk.CTkProgressBar(
            self.barra_estado, mode="indeterminate", height=3
        )
        # No se empaqueta hasta que se necesite

    def _mostrar_loading(self) -> None:
        """Muestra la barra de progreso indeterminada."""
        self.progress_bar.pack(side="bottom", fill="x", padx=5, pady=(2, 0))
        self.progress_bar.start()

    def _ocultar_loading(self) -> None:
        """Oculta la barra de progreso indeterminada."""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

    def _actualizar_contador(self) -> None:
        """Actualiza el contador de hoteles en la barra de estado."""
        stats = self.tabla.obtener_estadisticas()
        self.label_contador.configure(
            text=f"Total: {stats['total']} hotels | "
            f"With key: {stats['con_key']} | Without key: {stats['sin_key']}"
        )

    def _on_seleccion_cambio(self, seleccionados: List[HotelData]) -> None:
        """Callback cuando cambia la selección en la tabla."""
        self.label_seleccion.configure(text=f"Selected: {len(seleccionados)}")

    def _on_doble_click(self, indice: int, hotel_data: HotelData) -> None:
        """Callback cuando se hace doble clic en una fila."""
        self._indice_editando = indice

        def on_save(datos: HotelData) -> None:
            if self._indice_editando is not None:
                self.tabla.actualizar_hotel(self._indice_editando, datos)
                self._actualizar_contador()
            self._indice_editando = None

        EditarHotelDialog(self, hotel_data, on_save)

    def _cargar_excel(self) -> None:
        """Abre un diálogo para seleccionar y cargar un archivo Excel."""
        ruta = filedialog.askopenfilename(
            title="Select Excel file",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*"),
            ],
        )

        if not ruta:
            return

        # Deshabilitar botón y mostrar estado de carga
        self.btn_cargar.configure(state="disabled", text="Loading...")
        self.label_busqueda.configure(
            text=f"Loading {os.path.basename(ruta)}...", text_color="gray"
        )
        self._mostrar_loading()
        self.update_idletasks()

        def cargar_en_background() -> None:
            try:
                hoteles = self.excel_handler.cargar_excel(ruta)
                # Actualizar UI en el thread principal
                self.after(0, lambda: self._excel_cargado(hoteles, ruta))
            except FileNotFoundError as e:
                self.after(0, lambda: self._excel_error(f"File not found: {e}"))
            except ValueError as e:
                self.after(0, lambda: self._excel_error(str(e)))
            except Exception as e:
                self.after(0, lambda: self._excel_error(f"Error loading file: {e}"))

        thread = threading.Thread(target=cargar_en_background, daemon=True)
        thread.start()

    def _excel_cargado(self, hoteles: List[HotelData], ruta: str) -> None:
        """Callback cuando el Excel se cargó exitosamente."""
        self.label_busqueda.configure(
            text=f"Rendering {len(hoteles)} hotels...", text_color="gray"
        )
        self.update_idletasks()
        self.tabla.cargar_hoteles(hoteles)
        self._ocultar_loading()
        self._actualizar_contador()
        self.btn_cargar.configure(state="normal", text="Load Excel")
        self.label_busqueda.configure(
            text=f"✅ Loaded {len(hoteles)} hotels from {os.path.basename(ruta)}",
            text_color="green",
        )

    def _excel_error(self, mensaje: str) -> None:
        """Callback cuando hay error al cargar Excel."""
        self._ocultar_loading()
        self.btn_cargar.configure(state="normal", text="Load Excel")
        self.label_busqueda.configure(text="", text_color="gray")
        messagebox.showerror("Error", mensaje)

    def _encontrar_database(self) -> Optional[Path]:
        """
        Busca el archivo hotel_keys_db.json en ubicaciones comunes.

        Returns:
            Path al archivo si existe, None si no se encuentra.
        """
        # Buscar en orden de prioridad:
        # 1. Directorio de trabajo actual
        # 2. Directorio del ejecutable/script
        # 3. Directorio padre del paquete ui/
        posibles_rutas = [
            Path.cwd() / self.HOTEL_DB_FILENAME,
            Path(sys.executable).parent / self.HOTEL_DB_FILENAME,
            Path(__file__).parent.parent.parent / self.HOTEL_DB_FILENAME,
        ]

        # Si hay _MEIPASS (PyInstaller), buscar también ahí
        if hasattr(sys, "_MEIPASS"):
            posibles_rutas.insert(0, Path(sys._MEIPASS) / self.HOTEL_DB_FILENAME)

        for ruta in posibles_rutas:
            if ruta.exists():
                return ruta

        return None

    def _cargar_database(self) -> None:
        """Carga hoteles desde hotel_keys_db.json."""
        db_path = self._encontrar_database()

        if not db_path:
            messagebox.showwarning(
                "Database Not Found",
                f"Could not find {self.HOTEL_DB_FILENAME}.\n\n"
                "Use 'Load Excel' to load hotels from an Excel file instead.",
            )
            return

        self.btn_cargar_db.configure(state="disabled", text="Loading...")
        self.label_busqueda.configure(text="Loading database...", text_color="gray")
        self._mostrar_loading()
        self.update_idletasks()

        def cargar_en_background() -> None:
            try:
                hoteles = self._parsear_hotel_keys_db(db_path)
                self.after(0, lambda: self._database_cargada(hoteles, db_path))
            except Exception as e:
                self.after(0, lambda: self._database_error(str(e)))

        thread = threading.Thread(target=cargar_en_background, daemon=True)
        thread.start()

    def _parsear_hotel_keys_db(self, ruta: Path) -> List[HotelData]:
        """
        Parsea el archivo hotel_keys_db.json.

        El formato soporta:
        - Valores string: {"Hotel Name": "g147319-d123456"}
        - Valores dict: {"Hotel Name": {"xotelo": "...", "booking_url": "..."}}

        Args:
            ruta: Path al archivo JSON.

        Returns:
            Lista de HotelData.
        """
        with open(ruta, "r", encoding="utf-8") as f:
            data: Dict[str, Union[str, Dict[str, str]]] = json.load(f)

        hoteles: List[HotelData] = []
        for nombre, valor in data.items():
            hotel: HotelData = {"nombre": nombre, "xotelo_key": None, "booking_url": None}

            if isinstance(valor, str):
                # Formato antiguo: valor es directamente la key
                hotel["xotelo_key"] = valor
            elif isinstance(valor, dict):
                # Formato nuevo: valor es un diccionario
                hotel["xotelo_key"] = valor.get("xotelo")
                hotel["booking_url"] = valor.get("booking_url")

            hoteles.append(hotel)

        return hoteles

    def _database_cargada(self, hoteles: List[HotelData], ruta: Path) -> None:
        """Callback cuando la database se cargó exitosamente."""
        self.label_busqueda.configure(
            text=f"Rendering {len(hoteles)} hotels...", text_color="gray"
        )
        self.update_idletasks()
        self.tabla.cargar_hoteles(hoteles)
        self._ocultar_loading()
        self._actualizar_contador()
        self.btn_cargar_db.configure(state="normal", text="Load Database")
        self.label_busqueda.configure(
            text=f"✅ Loaded {len(hoteles)} hotels from {ruta.name}",
            text_color="green",
        )

    def _database_error(self, mensaje: str) -> None:
        """Callback cuando hay error al cargar la database."""
        self._ocultar_loading()
        self.btn_cargar_db.configure(state="normal", text="Load Database")
        self.label_busqueda.configure(text="", text_color="gray")
        messagebox.showerror("Error", f"Error loading database: {mensaje}")

    def cargar_database_auto(self) -> bool:
        """
        Carga automáticamente la database si existe.

        Llamado por la aplicación principal al iniciar.

        Returns:
            True si se cargó exitosamente, False si no se encontró o hubo error.
        """
        db_path = self._encontrar_database()
        if not db_path:
            return False

        try:
            hoteles = self._parsear_hotel_keys_db(db_path)
            self.tabla.cargar_hoteles(hoteles)
            self._actualizar_contador()
            self.label_busqueda.configure(
                text=f"✅ Auto-loaded {len(hoteles)} hotels from {db_path.name}",
                text_color="green",
            )
            return True
        except Exception as e:
            self.label_busqueda.configure(
                text=f"⚠️ Could not auto-load database: {e}",
                text_color="orange",
            )
            return False

    def _guardar_excel(self) -> None:
        """Guarda la lista de hoteles a un archivo Excel."""
        hoteles = self.tabla.obtener_hoteles()

        if not hoteles:
            messagebox.showwarning("Warning", "No hotels to save.")
            return

        ruta = filedialog.asksaveasfilename(
            title="Save Excel file",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )

        if not ruta:
            return

        try:
            self.excel_handler.guardar_excel(ruta, hoteles)
            self.label_busqueda.configure(
                text=f"✅ Saved {len(hoteles)} hotels to {os.path.basename(ruta)}",
                text_color="green",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file: {e}")

    def _eliminar_seleccionados(self) -> None:
        """Elimina los hoteles seleccionados."""
        seleccionados = self.tabla.obtener_seleccionados()

        if not seleccionados:
            messagebox.showinfo("Info", "No hotels selected.")
            return

        confirmacion = messagebox.askyesno(
            "Confirm deletion",
            f"Delete {len(seleccionados)} selected hotel(s)?",
        )

        if confirmacion:
            eliminados = self.tabla.eliminar_seleccionados()
            self._actualizar_contador()
            self.label_busqueda.configure(
                text=f"Deleted {eliminados} hotels", text_color="orange"
            )

    def _limpiar_todo(self) -> None:
        """Limpia todos los hoteles de la lista."""
        if not self.tabla.obtener_hoteles():
            return

        confirmacion = messagebox.askyesno(
            "Confirm", "Delete all hotels from the list?"
        )

        if confirmacion:
            self.tabla.limpiar()
            self._actualizar_contador()
            self.label_busqueda.configure(text="List cleared", text_color="gray")

    def _buscar_key(self) -> None:
        """Busca la key Xotelo para el nombre ingresado."""
        if not self.api:
            self.label_busqueda.configure(
                text="Xotelo API not available", text_color="red"
            )
            return

        nombre = self.entry_nombre.get().strip()
        if not nombre:
            self.label_busqueda.configure(
                text="Enter a hotel name first", text_color="orange"
            )
            return

        self.label_busqueda.configure(text="Searching...", text_color="gray")
        self.btn_buscar.configure(state="disabled")

        def buscar() -> None:
            try:
                resultado = self.api.search_hotel(nombre)
                if resultado:
                    self.after(0, lambda: self._key_encontrada(resultado["key"]))
                else:
                    self.after(0, lambda: self._key_no_encontrada())
            except Exception as e:
                self.after(0, lambda: self._busqueda_error(str(e)))

        thread = threading.Thread(target=buscar, daemon=True)
        thread.start()

    def _key_encontrada(self, key: str) -> None:
        """Callback cuando se encuentra una key."""
        self.entry_key.delete(0, "end")
        self.entry_key.insert(0, key)
        self.label_busqueda.configure(
            text=f"✅ Key found: {key}", text_color="green"
        )
        self.btn_buscar.configure(state="normal")

    def _key_no_encontrada(self) -> None:
        """Callback cuando no se encuentra la key."""
        self.label_busqueda.configure(
            text="⚠️ Hotel not found in Xotelo", text_color="orange"
        )
        self.btn_buscar.configure(state="normal")

    def _busqueda_error(self, error: str) -> None:
        """Callback cuando hay error en la búsqueda."""
        self.label_busqueda.configure(text=f"❌ Error: {error}", text_color="red")
        self.btn_buscar.configure(state="normal")

    def _agregar_hotel(self) -> None:
        """Agrega un hotel manualmente a la lista."""
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Warning", "Enter the hotel name.")
            return

        key = self.entry_key.get().strip() or None

        self.tabla.agregar_hotel(nombre, key)
        self._actualizar_contador()

        # Limpiar campos
        self.entry_nombre.delete(0, "end")
        self.entry_key.delete(0, "end")
        self.label_busqueda.configure(
            text=f"✅ Hotel '{nombre}' added", text_color="green"
        )

    def _buscar_keys_seleccionados(self) -> None:
        """Busca keys de Xotelo solo para los hoteles seleccionados."""
        if not self.api:
            messagebox.showerror("Error", "Xotelo API not available.")
            return

        seleccionados = self.tabla.obtener_seleccionados()

        if not seleccionados:
            messagebox.showinfo("Info", "Select hotels to search keys for.")
            return

        # Filtrar solo los que no tienen key
        sin_key = [h for h in seleccionados if not h.get("xotelo_key")]

        if not sin_key:
            messagebox.showinfo("Info", "All selected hotels already have keys.")
            return

        confirmacion = messagebox.askyesno(
            "Confirm",
            f"Search keys for {len(sin_key)} selected hotel(s)?\n"
            f"({len(seleccionados)} selected, {len(sin_key)} without key)",
        )

        if not confirmacion:
            return

        self.btn_buscar_keys_sel.configure(state="disabled", text="Searching...")
        self._mostrar_loading()
        self._ejecutar_busqueda_keys(seleccionados, self.btn_buscar_keys_sel, "Search Keys (Selection)")

    def _buscar_keys_faltantes(self) -> None:
        """Busca keys de Xotelo para todos los hoteles sin key."""
        if not self.api:
            messagebox.showerror("Error", "Xotelo API not available.")
            return

        hoteles = self.tabla.obtener_hoteles()
        sin_key = [h for h in hoteles if not h.get("xotelo_key")]

        if not sin_key:
            messagebox.showinfo("Info", "All hotels already have keys.")
            return

        confirmacion = messagebox.askyesno(
            "Confirm",
            f"Search keys for ALL {len(sin_key)} hotel(s) without key?\n"
            "This may take several minutes.",
        )

        if not confirmacion:
            return

        self.btn_buscar_keys.configure(state="disabled", text="Searching...")
        self._mostrar_loading()
        self._ejecutar_busqueda_keys(hoteles, self.btn_buscar_keys, "Search All")

    def _ejecutar_busqueda_keys(
        self,
        hoteles_a_buscar: List[HotelData],
        boton: ctk.CTkButton,
        texto_boton_original: str,
    ) -> None:
        """
        Ejecuta la búsqueda de keys en background.

        Args:
            hoteles_a_buscar: Lista de hoteles donde buscar.
            boton: Botón que inició la acción (para actualizar estado).
            texto_boton_original: Texto original del botón para restaurar.
        """
        # Obtener todos los hoteles para encontrar índices correctos
        todos_hoteles = self.tabla.obtener_hoteles()

        # Crear mapa de nombre a índice
        nombre_a_indice = {h.get("nombre", ""): idx for idx, h in enumerate(todos_hoteles)}

        def buscar_todos() -> None:
            encontrados = 0
            sin_key = [h for h in hoteles_a_buscar if not h.get("xotelo_key")]
            total_sin_key = len(sin_key)
            procesados = 0

            for hotel in hoteles_a_buscar:
                if hotel.get("xotelo_key"):
                    continue

                procesados += 1
                nombre = hotel.get("nombre", "")
                idx = nombre_a_indice.get(nombre)

                try:
                    resultado = self.api.search_hotel(nombre)
                    if resultado:
                        hotel["xotelo_key"] = resultado["key"]
                        encontrados += 1
                        # Actualizar UI
                        if idx is not None:
                            self.after(
                                0, lambda i=idx, h=hotel: self.tabla.actualizar_hotel(i, h)
                            )
                except Exception:
                    pass

                # Actualizar progreso
                self.after(
                    0,
                    lambda p=procesados, t=total_sin_key: (
                        boton.configure(text=f"Searching... ({p}/{t})")
                    ),
                )

                # Esperar entre requests
                if self.api:
                    self.api.wait()

            # Finalizar
            self.after(
                0, lambda: self._busqueda_masiva_completada(
                    encontrados, total_sin_key, boton, texto_boton_original
                )
            )

        thread = threading.Thread(target=buscar_todos, daemon=True)
        thread.start()

    def _busqueda_masiva_completada(
        self,
        encontrados: int,
        total: int,
        boton: ctk.CTkButton,
        texto_boton_original: str,
    ) -> None:
        """Callback cuando termina la búsqueda masiva de keys."""
        self._ocultar_loading()
        boton.configure(state="normal", text=texto_boton_original)
        self._actualizar_contador()
        self.label_busqueda.configure(
            text=f"✅ Search complete: {encontrados}/{total} keys found",
            text_color="green",
        )
        messagebox.showinfo(
            "Search complete",
            f"Found keys for {encontrados} of {total} hotels.",
        )

    def obtener_hoteles(self) -> List[HotelData]:
        """
        Obtiene la lista de hoteles para uso externo.

        Returns:
            Lista de diccionarios con datos de hoteles.
        """
        return self.tabla.obtener_hoteles()

    def obtener_hoteles_con_key(self) -> List[HotelData]:
        """
        Obtiene solo los hoteles que tienen key Xotelo.

        Returns:
            Lista filtrada de hoteles con key.
        """
        return [h for h in self.tabla.obtener_hoteles() if h.get("xotelo_key")]

    def _descargar_cache_hoteles(self) -> None:
        """Descarga el cache de todos los hoteles de Puerto Rico desde Xotelo."""
        if not self.api:
            messagebox.showerror("Error", "Xotelo API not available.")
            return

        # Verificar si ya existe el cache
        cache_info = self.api.get_cache_info()
        if cache_info.get("exists") and cache_info.get("count", 0) > 0:
            confirmar = messagebox.askyesno(
                "Cache Exists",
                f"Hotel cache already exists with {cache_info['count']} hotels.\n"
                f"Last updated: {cache_info.get('updated', 'Unknown')}\n\n"
                "Download again to refresh?",
            )
            if not confirmar:
                return

        # Confirmar descarga
        confirmar = messagebox.askyesno(
            "Download PR Hotels",
            "This will download all Puerto Rico hotels from Xotelo (~1,100 hotels).\n\n"
            "This may take 1-2 minutes.\n\n"
            "Continue?",
        )
        if not confirmar:
            return

        self.btn_download_cache.configure(state="disabled", text="Downloading...")
        self.label_busqueda.configure(text="Downloading hotel cache...", text_color="gray")
        self._mostrar_loading()

        def descargar() -> None:
            try:
                def progress_callback(current: int, total: int) -> None:
                    self.after(
                        0,
                        lambda c=current, t=total: self._actualizar_progreso_descarga(c, t),
                    )

                total = self.api.refresh_hotel_cache(progress_callback=progress_callback)
                self.after(0, lambda: self._descarga_completada(total))
            except Exception as e:
                self.after(0, lambda: self._descarga_error(str(e)))

        thread = threading.Thread(target=descargar, daemon=True)
        thread.start()

    def _actualizar_progreso_descarga(self, current: int, total: int) -> None:
        """Actualiza el progreso de descarga en la UI."""
        pct = (current / total * 100) if total > 0 else 0
        self.btn_download_cache.configure(text=f"{current}/{total} ({pct:.0f}%)")
        self.label_busqueda.configure(
            text=f"Downloading: {current} of {total} hotels...",
            text_color="gray",
        )

    def _descarga_completada(self, total: int) -> None:
        """Callback cuando la descarga se completó."""
        self._ocultar_loading()
        self.btn_download_cache.configure(state="normal", text="Download PR Hotels")
        self.label_busqueda.configure(
            text=f"✅ Downloaded {total} Puerto Rico hotels to cache",
            text_color="green",
        )
        messagebox.showinfo(
            "Download Complete",
            f"Successfully downloaded {total} Puerto Rico hotels.\n\n"
            "You can now use 'Search All' or 'Search Keys' to find Xotelo keys "
            "for your imported hotels.",
        )

    def _descarga_error(self, error: str) -> None:
        """Callback cuando hay error en la descarga."""
        self._ocultar_loading()
        self.btn_download_cache.configure(state="normal", text="Download PR Hotels")
        self.label_busqueda.configure(text=f"❌ Download failed: {error}", text_color="red")
        messagebox.showerror("Download Error", f"Failed to download hotel cache:\n\n{error}")

    def verificar_cache_existe(self) -> bool:
        """
        Verifica si el cache de hoteles existe.

        Returns:
            True si existe, False si no.
        """
        if not self.api:
            return False
        cache_info = self.api.get_cache_info()
        return cache_info.get("exists", False) and cache_info.get("count", 0) > 0

    def mostrar_aviso_cache_faltante(self) -> None:
        """Muestra un aviso si el cache no existe."""
        if self.verificar_cache_existe():
            return

        self.label_busqueda.configure(
            text="⚠️ Hotel cache not found. Click 'Download PR Hotels' to enable key search.",
            text_color="orange",
        )
