"""
Pestaña de gestión de hoteles para la aplicación Hotel Price Checker.

Este módulo proporciona la interfaz completa para cargar, agregar,
eliminar y gestionar hoteles con sus keys de Xotelo.
"""

import os
import sys
import threading
from tkinter import filedialog, messagebox
from typing import Any, Callable, Dict, List, Optional

import customtkinter as ctk

# Agregar el directorio raíz al path para imports
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from ui.components.hotel_table import HotelData, HotelTable
from ui.utils.excel_handler import ExcelHandler
from ui.utils.theme import TAMANOS, obtener_fuente


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
            frame_key, text="🔍 Search", width=80, command=self._buscar_key
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
            fg_color="gray50",
            command=self.destroy,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame_botones, text="💾 Save", width=100, command=self._guardar
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
    - Agregar hoteles manualmente
    - Buscar keys de Xotelo automáticamente
    - Eliminar hoteles seleccionados
    - Editar hoteles existentes

    Attributes:
        tabla: Componente HotelTable con la lista de hoteles.
        excel_handler: Manejador de archivos Excel.
        api: Cliente de la API de Xotelo.
    """

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
        """Crea la barra de herramientas superior."""
        padding = TAMANOS["padding_medio"]

        self.barra_herramientas = ctk.CTkFrame(self)
        self.barra_herramientas.grid(
            row=0, column=0, sticky="ew", padx=padding, pady=(padding, 5)
        )

        # Botón Cargar Excel
        self.btn_cargar = ctk.CTkButton(
            self.barra_herramientas,
            text="📂 Load Excel",
            width=TAMANOS["ancho_boton"],
            command=self._cargar_excel,
        )
        self.btn_cargar.pack(side="left", padx=5, pady=5)

        # Botón Guardar Excel
        self.btn_guardar = ctk.CTkButton(
            self.barra_herramientas,
            text="💾 Save Excel",
            width=TAMANOS["ancho_boton"],
            command=self._guardar_excel,
        )
        self.btn_guardar.pack(side="left", padx=5, pady=5)

        # Separador visual
        ctk.CTkFrame(
            self.barra_herramientas, width=2, height=25, fg_color="gray50"
        ).pack(side="left", padx=10, pady=5)

        # Botón Eliminar seleccionados
        self.btn_eliminar = ctk.CTkButton(
            self.barra_herramientas,
            text="🗑️ Delete",
            width=100,
            fg_color="firebrick",
            hover_color="darkred",
            command=self._eliminar_seleccionados,
        )
        self.btn_eliminar.pack(side="left", padx=5, pady=5)

        # Botón Limpiar todo
        self.btn_limpiar = ctk.CTkButton(
            self.barra_herramientas,
            text="Clear All",
            width=100,
            fg_color="gray50",
            command=self._limpiar_todo,
        )
        self.btn_limpiar.pack(side="left", padx=5, pady=5)

        # Botón Buscar Keys de seleccionados (a la derecha)
        self.btn_buscar_keys_sel = ctk.CTkButton(
            self.barra_herramientas,
            text="🔍 Search Keys (Selection)",
            width=160,
            fg_color="green",
            hover_color="darkgreen",
            command=self._buscar_keys_seleccionados,
        )
        self.btn_buscar_keys_sel.pack(side="right", padx=5, pady=5)

        # Botón Buscar Keys de todos los faltantes
        self.btn_buscar_keys = ctk.CTkButton(
            self.barra_herramientas,
            text="🔍 Search All",
            width=120,
            fg_color="gray50",
            hover_color="gray40",
            command=self._buscar_keys_faltantes,
        )
        self.btn_buscar_keys.pack(side="right", padx=5, pady=5)

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
        self.panel_agregar = ctk.CTkFrame(self)
        self.panel_agregar.grid(row=2, column=0, sticky="ew", padx=padding, pady=5)
        self.panel_agregar.grid_columnconfigure(1, weight=1)
        self.panel_agregar.grid_columnconfigure(3, weight=1)

        # Título del panel
        ctk.CTkLabel(
            self.panel_agregar,
            text="➕ Add Hotel Manually",
            font=obtener_fuente("encabezado"),
        ).grid(row=0, column=0, columnspan=6, pady=(5, 10))

        # Campo nombre
        ctk.CTkLabel(
            self.panel_agregar, text="Name:", font=obtener_fuente("normal")
        ).grid(row=1, column=0, padx=5, pady=5, sticky="e")

        self.entry_nombre = ctk.CTkEntry(
            self.panel_agregar,
            font=obtener_fuente("normal"),
            placeholder_text="Hotel name",
        )
        self.entry_nombre.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Campo key (opcional)
        ctk.CTkLabel(
            self.panel_agregar, text="Key Xotelo:", font=obtener_fuente("normal")
        ).grid(row=1, column=2, padx=(20, 5), pady=5, sticky="e")

        self.entry_key = ctk.CTkEntry(
            self.panel_agregar,
            font=obtener_fuente("codigo"),
            placeholder_text="(optional) g147319-d123456",
        )
        self.entry_key.grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        # Botón buscar key
        self.btn_buscar = ctk.CTkButton(
            self.panel_agregar, text="🔍 Search", width=80, command=self._buscar_key
        )
        self.btn_buscar.grid(row=1, column=4, padx=5, pady=5)

        # Botón agregar
        self.btn_agregar = ctk.CTkButton(
            self.panel_agregar,
            text="Add to List",
            width=120,
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
        self.btn_cargar.configure(state="disabled", text="⏳ Loading...")
        self.label_busqueda.configure(
            text=f"Loading {os.path.basename(ruta)}...", text_color="gray"
        )
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
        self.tabla.cargar_hoteles(hoteles)
        self._actualizar_contador()
        self.btn_cargar.configure(state="normal", text="📂 Load Excel")
        self.label_busqueda.configure(
            text=f"✅ Loaded {len(hoteles)} hotels from {os.path.basename(ruta)}",
            text_color="green",
        )

    def _excel_error(self, mensaje: str) -> None:
        """Callback cuando hay error al cargar Excel."""
        self.btn_cargar.configure(state="normal", text="📂 Load Excel")
        self.label_busqueda.configure(text="", text_color="gray")
        messagebox.showerror("Error", mensaje)

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
                text=f"🗑️ Deleted {eliminados} hotels", text_color="orange"
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
        self._ejecutar_busqueda_keys(seleccionados, self.btn_buscar_keys_sel, "🔍 Search Keys (Selection)")

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
        self._ejecutar_busqueda_keys(hoteles, self.btn_buscar_keys, "🔍 Search All")

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
