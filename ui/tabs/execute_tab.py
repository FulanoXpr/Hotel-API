"""
Pestaña de ejecución de búsqueda de precios.

Este módulo proporciona la interfaz para configurar y ejecutar
búsquedas de precios de hoteles con barra de progreso, log en vivo
y estadísticas en tiempo real.
"""

import os
import queue
import sys
import threading
from datetime import datetime, timedelta
from tkinter import messagebox
from typing import Any, Callable, Dict, List, Optional

import customtkinter as ctk

# Agregar el directorio raíz al path para imports
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from ui.components.log_viewer import LogViewer
from ui.components.progress_bar import ProgressBar
from ui.components.stats_panel import StatsPanel
from ui.utils.date_picker import DateEntry
from ui.utils.icons import get_icon
from ui.utils.theme import BOTONES, FUENTES, TAMANOS, TemaMode, obtener_tema


class ExecuteTab(ctk.CTkFrame):
    """
    Pestaña de ejecución de búsqueda de precios de hoteles.

    Características:
    - Configuración de parámetros de búsqueda (fecha, noches, habitaciones, etc.)
    - Barra de progreso con tiempo estimado
    - Log en vivo con colores por tipo de mensaje
    - Panel de estadísticas en tiempo real
    - Threading para no bloquear la UI
    - Botones Iniciar/Detener búsqueda
    """

    def __init__(
        self,
        master: ctk.CTkFrame,
        modo_tema: TemaMode = "dark",
        on_busqueda_completada: Optional[Callable[[List[Dict]], None]] = None,
        obtener_hoteles: Optional[Callable[[], List[Dict]]] = None,
        **kwargs,
    ) -> None:
        """
        Inicializa la pestaña de ejecución.

        Args:
            master: Widget padre.
            modo_tema: Modo de tema ("dark" o "light").
            on_busqueda_completada: Callback cuando termina la búsqueda.
            obtener_hoteles: Función para obtener lista de hoteles a buscar.
        """
        self.modo_tema = modo_tema
        self.tema = obtener_tema(modo_tema)

        super().__init__(master, fg_color="transparent", **kwargs)

        # Callbacks
        self._on_busqueda_completada = on_busqueda_completada
        self._obtener_hoteles = obtener_hoteles

        # Estado de búsqueda
        self._buscando = False
        self._cancelar = False
        self._thread_busqueda: Optional[threading.Thread] = None
        self._queue = queue.Queue()
        self._resultados: List[Dict] = []

        # Configurar layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Crear secciones
        self._crear_seccion_configuracion()
        self._crear_seccion_progreso()
        self._crear_seccion_log_stats()

        # Iniciar polling de la cola
        self._poll_queue()

    def _crear_seccion_configuracion(self) -> None:
        """Crea la sección de configuración de búsqueda."""
        self.frame_config = ctk.CTkFrame(
            self,
            fg_color=self.tema["fondo_secundario"],
            corner_radius=TAMANOS["radio_borde"],
        )
        self.frame_config.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # Título con icono
        ctk.CTkLabel(
            self.frame_config,
            text="Search Configuration",
            font=FUENTES.get("encabezado", ("Segoe UI", 14, "bold")),
            image=get_icon("calendar"),
            compound="left",
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Frame de parámetros
        frame_params = ctk.CTkFrame(self.frame_config, fg_color="transparent")
        frame_params.pack(fill="x", padx=15, pady=(0, 15))

        # Single row: Check-in, Nights, Rooms, Adults, Children
        fila1 = ctk.CTkFrame(frame_params, fg_color="transparent")
        fila1.pack(fill="x", pady=5)

        # Check-in
        ctk.CTkLabel(
            fila1,
            text="Check-in:",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
        ).pack(side="left", padx=(0, 5))

        fecha_default = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.date_entry = DateEntry(
            fila1,
            initial_date=fecha_default,
            modo_tema=self.modo_tema,
            width=150,
        )
        self.date_entry.pack(side="left", padx=(0, 15))
        self.entry_fecha = self.date_entry

        # Nights
        ctk.CTkLabel(
            fila1,
            text="Nights:",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
        ).pack(side="left", padx=(0, 5))

        self.combo_noches = ctk.CTkComboBox(
            fila1,
            values=[str(i) for i in range(1, 15)],
            width=60,
            font=FUENTES.get("normal", ("Segoe UI", 12)),
        )
        self.combo_noches.pack(side="left", padx=(0, 15))
        self.combo_noches.set("1")

        # Rooms
        ctk.CTkLabel(
            fila1,
            text="Rooms:",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
        ).pack(side="left", padx=(0, 5))

        self.combo_habitaciones = ctk.CTkComboBox(
            fila1,
            values=[str(i) for i in range(1, 6)],
            width=60,
            font=FUENTES.get("normal", ("Segoe UI", 12)),
        )
        self.combo_habitaciones.pack(side="left", padx=(0, 15))
        self.combo_habitaciones.set("1")

        # Adults
        ctk.CTkLabel(
            fila1,
            text="Adults:",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
        ).pack(side="left", padx=(0, 5))

        self.combo_adultos = ctk.CTkComboBox(
            fila1,
            values=[str(i) for i in range(1, 5)],
            width=60,
            font=FUENTES.get("normal", ("Segoe UI", 12)),
        )
        self.combo_adultos.pack(side="left", padx=(0, 15))
        self.combo_adultos.set("2")

        # Children
        ctk.CTkLabel(
            fila1,
            text="Children:",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
        ).pack(side="left", padx=(0, 5))

        self.combo_ninos = ctk.CTkComboBox(
            fila1,
            values=[str(i) for i in range(0, 5)],
            width=60,
            font=FUENTES.get("normal", ("Segoe UI", 12)),
        )
        self.combo_ninos.pack(side="left")
        self.combo_ninos.set("0")

        # Options and buttons row
        fila3 = ctk.CTkFrame(frame_params, fg_color="transparent")
        fila3.pack(fill="x", pady=(10, 0))

        self.var_cascade = ctk.BooleanVar(value=True)
        self.check_cascade = ctk.CTkCheckBox(
            fila3,
            text="Use cascade (all providers)",
            variable=self.var_cascade,
            font=FUENTES.get("normal", ("Segoe UI", 12)),
        )
        self.check_cascade.pack(side="left", padx=(0, 20))

        self.boton_detener = ctk.CTkButton(
            fila3,
            text="Stop",
            image=get_icon("stop"),
            compound="left",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            fg_color=self.tema["estados"]["error"],
            hover_color="#c0392b",
            width=100,
            command=self._detener_busqueda,
            state="disabled",
        )
        self.boton_detener.pack(side="right", padx=(10, 0))

        self.boton_iniciar = ctk.CTkButton(
            fila3,
            text="Start Search",
            image=get_icon("play"),
            compound="left",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            fg_color=BOTONES["exito"]["fg"],
            hover_color=BOTONES["exito"]["hover"],
            width=140,
            command=self._iniciar_busqueda,
        )
        self.boton_iniciar.pack(side="right")

    def _crear_seccion_progreso(self) -> None:
        """Crea la sección de barra de progreso."""
        self.frame_progreso = ctk.CTkFrame(
            self,
            fg_color=self.tema["fondo_secundario"],
            corner_radius=TAMANOS["radio_borde"],
        )
        self.frame_progreso.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        ctk.CTkLabel(
            self.frame_progreso,
            text="Progress",
            font=FUENTES.get("encabezado", ("Segoe UI", 14, "bold")),
            image=get_icon("chart"),
            compound="left",
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.progress_bar = ProgressBar(
            self.frame_progreso,
            modo_tema=self.modo_tema,
            altura_barra=20,
        )
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 15))

    def _crear_seccion_log_stats(self) -> None:
        """Crea la sección de log y estadísticas."""
        self.frame_log_stats = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_log_stats.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.frame_log_stats.grid_columnconfigure(0, weight=2)
        self.frame_log_stats.grid_columnconfigure(1, weight=1)
        self.frame_log_stats.grid_rowconfigure(0, weight=1)

        # Log viewer (izquierda)
        self.frame_log = ctk.CTkFrame(
            self.frame_log_stats,
            fg_color=self.tema["fondo_secundario"],
            corner_radius=TAMANOS["radio_borde"],
        )
        self.frame_log.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        ctk.CTkLabel(
            self.frame_log,
            text="Search Log",
            font=FUENTES.get("encabezado", ("Segoe UI", 14, "bold")),
            image=get_icon("list"),
            compound="left",
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.log_viewer = LogViewer(
            self.frame_log,
            modo_tema=self.modo_tema,
            altura=250,
        )
        self.log_viewer.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Stats panel (derecha)
        self.stats_panel = StatsPanel(
            self.frame_log_stats,
            modo_tema=self.modo_tema,
        )
        self.stats_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

    def _validar_fecha(self, fecha_str: str) -> bool:
        """Valida el formato de fecha YYYY-MM-DD."""
        try:
            datetime.strptime(fecha_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _iniciar_busqueda(self) -> None:
        """Inicia la búsqueda de precios en un thread separado."""
        if self._buscando:
            return

        # Validar fecha
        fecha = self.entry_fecha.get().strip()
        if not self._validar_fecha(fecha):
            messagebox.showerror(
                "Error", "Invalid date format. Use YYYY-MM-DD (e.g., 2024-12-25)"
            )
            return

        # Obtener hoteles
        hoteles = []
        if self._obtener_hoteles:
            hoteles = self._obtener_hoteles()

        if not hoteles:
            messagebox.showwarning(
                "No hotels",
                "No hotels to search. Add hotels in the 'Hotels' tab.",
            )
            return

        # Preparar parámetros
        noches = int(self.combo_noches.get())
        check_in = fecha
        check_out = (
            datetime.strptime(fecha, "%Y-%m-%d") + timedelta(days=noches)
        ).strftime("%Y-%m-%d")
        habitaciones = int(self.combo_habitaciones.get())
        adultos = int(self.combo_adultos.get())
        usar_cascade = self.var_cascade.get()

        # Reiniciar UI
        self._buscando = True
        self._cancelar = False
        self._resultados = []
        self.progress_bar.reiniciar()
        self.log_viewer.limpiar()
        self.stats_panel.reiniciar()

        # Actualizar botones
        self.boton_iniciar.configure(state="disabled")
        self.boton_detener.configure(state="normal")

        # Log inicio
        self.log_viewer.agregar_log(
            f"Starting search for {len(hoteles)} hotels...", "info"
        )
        self.log_viewer.agregar_log(
            f"Dates: {check_in} → {check_out} ({noches} nights)", "info"
        )
        self.log_viewer.agregar_log(
            f"Cascade: {'ON' if usar_cascade else 'OFF'} — Initializing providers...", "info"
        )

        # Iniciar thread
        self._thread_busqueda = threading.Thread(
            target=self._ejecutar_busqueda,
            args=(hoteles, check_in, check_out, habitaciones, adultos, usar_cascade),
            daemon=True,
        )
        self._thread_busqueda.start()

    def _ejecutar_busqueda(
        self,
        hoteles: List[Dict],
        check_in: str,
        check_out: str,
        habitaciones: int,
        adultos: int,
        usar_cascade: bool,
    ) -> None:
        """Ejecuta la búsqueda en un thread separado."""
        try:
            # Importar el provider aquí para evitar imports circulares
            from price_providers.amadeus import AmadeusProvider
            from price_providers.apify import ApifyProvider
            from price_providers.cache import PriceCache
            from price_providers.cascade import CascadePriceProvider
            from price_providers.serpapi import SerpApiProvider
            from price_providers.xotelo import XoteloProvider

            # Crear providers y reportar disponibilidad
            providers = []
            provider_classes = [
                ("Xotelo", XoteloProvider),
                ("SerpApi", SerpApiProvider),
                ("Apify", ApifyProvider),
                ("Amadeus", AmadeusProvider),
            ]

            if usar_cascade:
                for name, cls in provider_classes:
                    try:
                        p = cls()
                        if p.is_available():
                            providers.append(p)
                            self._queue.put(("log", f"  ✓ {name}: ready", "success"))
                        else:
                            # Distinguish between missing package and missing key
                            pkg_flags = {
                                "Xotelo": True,
                                "SerpApi": getattr(__import__("price_providers.serpapi", fromlist=["SERPAPI_AVAILABLE"]), "SERPAPI_AVAILABLE", False),
                                "Apify": getattr(__import__("price_providers.apify", fromlist=["APIFY_AVAILABLE"]), "APIFY_AVAILABLE", False),
                                "Amadeus": getattr(__import__("price_providers.amadeus", fromlist=["AMADEUS_AVAILABLE"]), "AMADEUS_AVAILABLE", False),
                            }
                            if not pkg_flags.get(name, True):
                                self._queue.put(("log", f"  ✗ {name}: pip package not installed", "warning"))
                            else:
                                self._queue.put(("log", f"  ✗ {name}: missing API key (check API Keys tab)", "warning"))
                    except Exception as e:
                        self._queue.put(("log", f"  ✗ {name}: init error — {e}", "warning"))
            else:
                # Solo Xotelo cuando cascade está desactivado
                try:
                    p = XoteloProvider()
                    if p.is_available():
                        providers.append(p)
                        self._queue.put(("log", "  ✓ Xotelo: available", "success"))
                except Exception as e:
                    self._queue.put(("log", f"  ✗ Xotelo: init error — {e}", "warning"))

            self._queue.put(("log", f"Active providers: {len(providers)} of {len(provider_classes) if usar_cascade else 1}", "info"))

            if not providers:
                self._queue.put(("log", "No providers available. Check API Keys tab.", "error"))
                self._queue.put(("done", None, None))
                return

            cache = PriceCache()
            cascade = CascadePriceProvider(providers, cache)

            total = len(hoteles)

            for i, hotel in enumerate(hoteles):
                if self._cancelar:
                    self._queue.put(
                        ("log", "Search cancelled by user", "warning")
                    )
                    break

                nombre = hotel.get("nombre", "Unknown hotel")
                key = hotel.get("xotelo_key", "")
                booking_url = hotel.get("booking_url", "")

                self._queue.put(("log", f"Searching: {nombre}...", "info"))
                self._queue.put(("progress", i, total))

                try:
                    result = cascade.get_price(
                        hotel_name=nombre,
                        hotel_key=key if key else None,
                        check_in=check_in,
                        check_out=check_out,
                        rooms=habitaciones,
                        adults=adultos,
                        booking_url=booking_url if booking_url else None,
                    )

                    if result:
                        precio = result.get("price", 0)
                        proveedor = result.get("provider", "unknown")

                        self._queue.put(
                            (
                                "log",
                                f"✓ {nombre}: ${precio:.2f} (via {proveedor})",
                                "success",
                            )
                        )

                        self._resultados.append(
                            {
                                "hotel": nombre,
                                "precio": precio,
                                "proveedor": proveedor,
                                "check_in": check_in,
                                "check_out": check_out,
                                "moneda": result.get("currency", "USD"),
                            }
                        )
                    else:
                        self._queue.put(
                            ("log", f"✗ {nombre}: Not found", "warning")
                        )
                        self._resultados.append(
                            {
                                "hotel": nombre,
                                "precio": None,
                                "proveedor": None,
                                "check_in": check_in,
                                "check_out": check_out,
                                "moneda": None,
                            }
                        )

                    # Actualizar stats
                    stats = cascade.get_stats()
                    self._queue.put(("stats", stats, None))

                except Exception as e:
                    self._queue.put(("log", f"✗ {nombre}: Error - {str(e)}", "error"))

            # Progreso final
            self._queue.put(("progress", total, total))

            # Resumen final
            stats = cascade.get_stats()
            self._queue.put(("stats", stats, None))
            self._queue.put(("log", cascade.get_stats_summary(), "info"))

        except Exception as e:
            self._queue.put(("log", f"Critical error: {str(e)}", "error"))

        finally:
            self._queue.put(("done", None, None))

    def _detener_busqueda(self) -> None:
        """Detiene la búsqueda en progreso."""
        if self._buscando:
            self._cancelar = True
            self.log_viewer.agregar_log("Stopping search...", "warning")

    def _poll_queue(self) -> None:
        """Procesa mensajes de la cola del thread de búsqueda."""
        try:
            while True:
                msg_type, data1, data2 = self._queue.get_nowait()

                if msg_type == "log":
                    self.log_viewer.agregar_log(data1, data2)

                elif msg_type == "progress":
                    self.progress_bar.actualizar(data1, data2)

                elif msg_type == "stats":
                    self.stats_panel.actualizar_stats(data1)

                elif msg_type == "done":
                    self._finalizar_busqueda()

        except queue.Empty:
            pass

        # Continuar polling
        self.after(100, self._poll_queue)

    def _finalizar_busqueda(self) -> None:
        """Finaliza la búsqueda y actualiza la UI."""
        self._buscando = False

        # Actualizar botones
        self.boton_iniciar.configure(state="normal")
        self.boton_detener.configure(state="disabled")

        # Log completado
        total = len(self._resultados)
        con_precio = sum(1 for r in self._resultados if r.get("precio") is not None)

        self.log_viewer.agregar_log(
            f"Search complete: {con_precio}/{total} hotels with price",
            "success" if con_precio > 0 else "warning",
        )

        # Callback con resultados
        if self._on_busqueda_completada and self._resultados:
            self._on_busqueda_completada(self._resultados)

    def obtener_resultados(self) -> List[Dict]:
        """Retorna los resultados de la última búsqueda."""
        return self._resultados.copy()

    def esta_buscando(self) -> bool:
        """Indica si hay una búsqueda en progreso."""
        return self._buscando

    def cambiar_tema(self, modo_tema: TemaMode) -> None:
        """Cambia el tema de la pestaña."""
        self.modo_tema = modo_tema
        self.tema = obtener_tema(modo_tema)

        # Actualizar frames
        self.frame_config.configure(fg_color=self.tema["fondo_secundario"])
        self.frame_progreso.configure(fg_color=self.tema["fondo_secundario"])
        self.frame_log.configure(fg_color=self.tema["fondo_secundario"])

        # Actualizar componentes
        self.progress_bar.cambiar_tema(modo_tema)
        self.log_viewer.cambiar_tema(modo_tema)
        self.stats_panel.cambiar_tema(modo_tema)
        self.date_entry.cambiar_tema(modo_tema)

    def set_obtener_hoteles(self, callback: Callable[[], List[Dict]]) -> None:
        """Establece el callback para obtener hoteles."""
        self._obtener_hoteles = callback

    def set_on_busqueda_completada(
        self, callback: Callable[[List[Dict]], None]
    ) -> None:
        """Establece el callback de búsqueda completada."""
        self._on_busqueda_completada = callback
