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
        self.title("Editar Hotel")
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
            text="Nombre del Hotel:",
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
            frame_key, text="🔍 Buscar", width=80, command=self._buscar_key
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
            text="Cancelar",
            width=100,
            fg_color="gray50",
            command=self.destroy,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame_botones, text="💾 Guardar", width=100, command=self._guardar
        ).pack(side="left", padx=5)

    def _buscar_key(self) -> None:
        """Busca la key Xotelo para el hotel."""
        if not self.api:
            self.label_estado.configure(
                text="API de Xotelo no disponible", text_color="red"
            )
            return

        nombre = self.entry_nombre.get().strip()
        if not nombre:
            self.label_estado.configure(
                text="Ingrese un nombre de hotel primero", text_color="orange"
            )
            return

        self.label_estado.configure(text="Buscando...", text_color="gray")
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
            text=f"✅ Key encontrada: {key}", text_color="green"
        )
        self.btn_buscar.configure(state="normal")

    def _mostrar_no_encontrado(self) -> None:
        """Muestra mensaje de hotel no encontrado."""
        self.label_estado.configure(
            text="⚠️ No se encontró el hotel en Xotelo", text_color="orange"
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
            messagebox.showwarning("Advertencia", "El nombre del hotel es requerido.")
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
            text="📂 Cargar Excel",
            width=TAMANOS["ancho_boton"],
            command=self._cargar_excel,
        )
        self.btn_cargar.pack(side="left", padx=5, pady=5)

        # Botón Guardar Excel
        self.btn_guardar = ctk.CTkButton(
            self.barra_herramientas,
            text="💾 Guardar Excel",
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
            text="🗑️ Eliminar",
            width=100,
            fg_color="firebrick",
            hover_color="darkred",
            command=self._eliminar_seleccionados,
        )
        self.btn_eliminar.pack(side="left", padx=5, pady=5)

        # Botón Limpiar todo
        self.btn_limpiar = ctk.CTkButton(
            self.barra_herramientas,
            text="Limpiar Todo",
            width=100,
            fg_color="gray50",
            command=self._limpiar_todo,
        )
        self.btn_limpiar.pack(side="left", padx=5, pady=5)

        # Botón Buscar Keys (a la derecha)
        self.btn_buscar_keys = ctk.CTkButton(
            self.barra_herramientas,
            text="🔍 Buscar Keys Faltantes",
            width=160,
            fg_color="green",
            hover_color="darkgreen",
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
            text="➕ Agregar Hotel Manualmente",
            font=obtener_fuente("encabezado"),
        ).grid(row=0, column=0, columnspan=6, pady=(5, 10))

        # Campo nombre
        ctk.CTkLabel(
            self.panel_agregar, text="Nombre:", font=obtener_fuente("normal")
        ).grid(row=1, column=0, padx=5, pady=5, sticky="e")

        self.entry_nombre = ctk.CTkEntry(
            self.panel_agregar,
            font=obtener_fuente("normal"),
            placeholder_text="Nombre del hotel",
        )
        self.entry_nombre.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Campo key (opcional)
        ctk.CTkLabel(
            self.panel_agregar, text="Key Xotelo:", font=obtener_fuente("normal")
        ).grid(row=1, column=2, padx=(20, 5), pady=5, sticky="e")

        self.entry_key = ctk.CTkEntry(
            self.panel_agregar,
            font=obtener_fuente("codigo"),
            placeholder_text="(opcional) g147319-d123456",
        )
        self.entry_key.grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        # Botón buscar key
        self.btn_buscar = ctk.CTkButton(
            self.panel_agregar, text="🔍 Buscar", width=80, command=self._buscar_key
        )
        self.btn_buscar.grid(row=1, column=4, padx=5, pady=5)

        # Botón agregar
        self.btn_agregar = ctk.CTkButton(
            self.panel_agregar,
            text="Agregar a Lista",
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
            text="Total: 0 hoteles | Con key: 0 | Sin key: 0",
            font=obtener_fuente("normal"),
        )
        self.label_contador.pack(side="left", padx=10, pady=5)

        self.label_seleccion = ctk.CTkLabel(
            self.barra_estado, text="Seleccionados: 0", font=obtener_fuente("normal")
        )
        self.label_seleccion.pack(side="right", padx=10, pady=5)

    def _actualizar_contador(self) -> None:
        """Actualiza el contador de hoteles en la barra de estado."""
        stats = self.tabla.obtener_estadisticas()
        self.label_contador.configure(
            text=f"Total: {stats['total']} hoteles | "
            f"Con key: {stats['con_key']} | Sin key: {stats['sin_key']}"
        )

    def _on_seleccion_cambio(self, seleccionados: List[HotelData]) -> None:
        """Callback cuando cambia la selección en la tabla."""
        self.label_seleccion.configure(text=f"Seleccionados: {len(seleccionados)}")

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
            title="Seleccionar archivo Excel",
            filetypes=[
                ("Archivos Excel", "*.xlsx *.xls"),
                ("Todos los archivos", "*.*"),
            ],
        )

        if not ruta:
            return

        try:
            hoteles = self.excel_handler.cargar_excel(ruta)
            self.tabla.cargar_hoteles(hoteles)
            self._actualizar_contador()
            self.label_busqueda.configure(
                text=f"✅ Cargados {len(hoteles)} hoteles desde {os.path.basename(ruta)}",
                text_color="green",
            )
        except FileNotFoundError as e:
            messagebox.showerror("Error", f"Archivo no encontrado: {e}")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar archivo: {e}")

    def _guardar_excel(self) -> None:
        """Guarda la lista de hoteles a un archivo Excel."""
        hoteles = self.tabla.obtener_hoteles()

        if not hoteles:
            messagebox.showwarning("Advertencia", "No hay hoteles para guardar.")
            return

        ruta = filedialog.asksaveasfilename(
            title="Guardar archivo Excel",
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")],
        )

        if not ruta:
            return

        try:
            self.excel_handler.guardar_excel(ruta, hoteles)
            self.label_busqueda.configure(
                text=f"✅ Guardados {len(hoteles)} hoteles en {os.path.basename(ruta)}",
                text_color="green",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar archivo: {e}")

    def _eliminar_seleccionados(self) -> None:
        """Elimina los hoteles seleccionados."""
        seleccionados = self.tabla.obtener_seleccionados()

        if not seleccionados:
            messagebox.showinfo("Info", "No hay hoteles seleccionados.")
            return

        confirmacion = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar {len(seleccionados)} hotel(es) seleccionado(s)?",
        )

        if confirmacion:
            eliminados = self.tabla.eliminar_seleccionados()
            self._actualizar_contador()
            self.label_busqueda.configure(
                text=f"🗑️ Eliminados {eliminados} hoteles", text_color="orange"
            )

    def _limpiar_todo(self) -> None:
        """Limpia todos los hoteles de la lista."""
        if not self.tabla.obtener_hoteles():
            return

        confirmacion = messagebox.askyesno(
            "Confirmar", "¿Eliminar todos los hoteles de la lista?"
        )

        if confirmacion:
            self.tabla.limpiar()
            self._actualizar_contador()
            self.label_busqueda.configure(text="Lista limpiada", text_color="gray")

    def _buscar_key(self) -> None:
        """Busca la key Xotelo para el nombre ingresado."""
        if not self.api:
            self.label_busqueda.configure(
                text="API de Xotelo no disponible", text_color="red"
            )
            return

        nombre = self.entry_nombre.get().strip()
        if not nombre:
            self.label_busqueda.configure(
                text="Ingrese un nombre de hotel primero", text_color="orange"
            )
            return

        self.label_busqueda.configure(text="Buscando...", text_color="gray")
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
            text=f"✅ Key encontrada: {key}", text_color="green"
        )
        self.btn_buscar.configure(state="normal")

    def _key_no_encontrada(self) -> None:
        """Callback cuando no se encuentra la key."""
        self.label_busqueda.configure(
            text="⚠️ No se encontró el hotel en Xotelo", text_color="orange"
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
            messagebox.showwarning("Advertencia", "Ingrese el nombre del hotel.")
            return

        key = self.entry_key.get().strip() or None

        self.tabla.agregar_hotel(nombre, key)
        self._actualizar_contador()

        # Limpiar campos
        self.entry_nombre.delete(0, "end")
        self.entry_key.delete(0, "end")
        self.label_busqueda.configure(
            text=f"✅ Hotel '{nombre}' agregado", text_color="green"
        )

    def _buscar_keys_faltantes(self) -> None:
        """Busca keys de Xotelo para todos los hoteles sin key."""
        if not self.api:
            messagebox.showerror("Error", "API de Xotelo no disponible.")
            return

        hoteles = self.tabla.obtener_hoteles()
        sin_key = [h for h in hoteles if not h.get("xotelo_key")]

        if not sin_key:
            messagebox.showinfo("Info", "Todos los hoteles ya tienen key.")
            return

        confirmacion = messagebox.askyesno(
            "Confirmar",
            f"¿Buscar keys para {len(sin_key)} hotel(es)?\n"
            "Esto puede tomar varios minutos.",
        )

        if not confirmacion:
            return

        self.btn_buscar_keys.configure(state="disabled", text="Buscando...")

        def buscar_todos() -> None:
            encontrados = 0
            total_sin_key = len([h for h in hoteles if not h.get("xotelo_key")])
            procesados = 0

            for idx, hotel in enumerate(hoteles):
                if hotel.get("xotelo_key"):
                    continue

                procesados += 1

                try:
                    resultado = self.api.search_hotel(hotel.get("nombre", ""))
                    if resultado:
                        hotel["xotelo_key"] = resultado["key"]
                        encontrados += 1
                        # Actualizar UI
                        self.after(
                            0, lambda i=idx, h=hotel: self.tabla.actualizar_hotel(i, h)
                        )
                except Exception:
                    pass

                # Actualizar progreso
                self.after(
                    0,
                    lambda p=procesados, t=total_sin_key: (
                        self.btn_buscar_keys.configure(text=f"Buscando... ({p}/{t})")
                    ),
                )

            # Finalizar
            self.after(
                0, lambda: self._busqueda_masiva_completada(encontrados, total_sin_key)
            )

        thread = threading.Thread(target=buscar_todos, daemon=True)
        thread.start()

    def _busqueda_masiva_completada(self, encontrados: int, total: int) -> None:
        """Callback cuando termina la búsqueda masiva de keys."""
        self.btn_buscar_keys.configure(state="normal", text="🔍 Buscar Keys Faltantes")
        self._actualizar_contador()
        self.label_busqueda.configure(
            text=f"✅ Búsqueda completada: {encontrados}/{total} keys encontradas",
            text_color="green",
        )
        messagebox.showinfo(
            "Búsqueda completada",
            f"Se encontraron keys para {encontrados} de {total} hoteles.",
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
