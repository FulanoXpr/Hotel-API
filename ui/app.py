"""
Aplicación principal de Hotel Price Checker.
Interfaz gráfica de escritorio usando CustomTkinter.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import customtkinter as ctk
from PIL import Image

from ui.utils.icons import get_icon
from ui.utils.theme import TAMANOS, TemaMode, aplicar_tema, obtener_fuente
from ui.utils.tooltip import ToolTip

logger = logging.getLogger(__name__)


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource, works for dev and PyInstaller bundle.

    Args:
        relative_path: Path relative to the application root.

    Returns:
        Absolute path to the resource.
    """
    if hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running in development
        base_path = Path(__file__).parent.parent
    return base_path / relative_path


class HotelPriceApp(ctk.CTk):
    """
    Aplicación principal para consultar precios de hoteles.

    Attributes:
        modo_tema: Modo de tema actual ("dark" o "light").
        tabview: Widget de pestañas principal.
    """

    # Configuración de la ventana
    TITULO_APP: str = "Hotel Price Checker"
    ANCHO_VENTANA: int = 1100
    ALTO_VENTANA: int = 700
    ANCHO_MINIMO: int = 1000
    ALTO_MINIMO: int = 600

    # Altura del logo (el path se calcula dinámicamente para PyInstaller)
    LOGO_HEIGHT: int = 35

    # Tab names (clean text — icons are on buttons, not tab labels)
    PESTANAS: Dict[str, str] = {
        "api_keys": "API Keys",
        "hoteles": "Hotels",
        "ejecutar": "Execute",
        "resultados": "Results",
    }

    def __init__(self) -> None:
        """Inicializa la aplicación principal."""
        super().__init__()

        # Log startup info for debugging
        logger.info(f"Starting Hotel Price Checker")
        logger.info(f"Python: {sys.version}")
        logger.info(f"Running as bundle: {hasattr(sys, '_MEIPASS')}")
        if hasattr(sys, '_MEIPASS'):
            logger.info(f"Bundle path: {sys._MEIPASS}")
        logger.info(f"Working directory: {Path.cwd()}")

        # Estado inicial
        self.modo_tema: TemaMode = "dark"

        # Referencias a las pestañas
        self.tab_api_keys: Optional[Any] = None
        self.tab_hoteles: Optional[Any] = None
        self.tab_ejecutar: Optional[Any] = None
        self.tab_resultados: Optional[Any] = None

        # Configurar ventana
        self._configurar_ventana()

        # Aplicar tema inicial
        aplicar_tema(self.modo_tema)

        # Crear interfaz
        self._crear_barra_superior()
        self._crear_tabview()
        self._crear_contenido_pestanas()

        # Auto-cargar hotel database si existe
        self._cargar_database_inicial()

        # Check for updates (async, non-blocking)
        self._check_for_updates()

        # Keyboard shortcuts
        self._configurar_atajos()

    def _configurar_atajos(self) -> None:
        """Configura atajos de teclado globales."""
        # Cmd/Ctrl modifier según plataforma
        mod = "Command" if sys.platform == "darwin" else "Control"

        self.bind_all(f"<{mod}-o>", lambda e: self._atajo_cargar_excel())
        self.bind_all(f"<{mod}-s>", lambda e: self._atajo_guardar_excel())
        self.bind_all(f"<{mod}-Key-1>", lambda e: self.cambiar_pestana("api_keys"))
        self.bind_all(f"<{mod}-Key-2>", lambda e: self.cambiar_pestana("hoteles"))
        self.bind_all(f"<{mod}-Key-3>", lambda e: self.cambiar_pestana("ejecutar"))
        self.bind_all(f"<{mod}-Key-4>", lambda e: self.cambiar_pestana("resultados"))

    def _atajo_cargar_excel(self) -> None:
        """Atajo Cmd/Ctrl+O: abre Excel en pestaña Hotels."""
        self.cambiar_pestana("hoteles")
        if self.tab_hoteles and hasattr(self.tab_hoteles, '_cargar_excel'):
            self.tab_hoteles._cargar_excel()

    def _atajo_guardar_excel(self) -> None:
        """Atajo Cmd/Ctrl+S: guarda Excel desde pestaña Hotels."""
        if self.tab_hoteles and hasattr(self.tab_hoteles, '_guardar_excel'):
            self.tab_hoteles._guardar_excel()

    def _configurar_ventana(self) -> None:
        """Configura las propiedades de la ventana principal."""
        self.title(self.TITULO_APP)
        self.geometry(f"{self.ANCHO_VENTANA}x{self.ALTO_VENTANA}")
        self.minsize(self.ANCHO_MINIMO, self.ALTO_MINIMO)

        # Centrar ventana en pantalla
        self._centrar_ventana()

        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _centrar_ventana(self) -> None:
        """Centra la ventana en la pantalla."""
        self.update_idletasks()
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()
        x = (ancho_pantalla - self.ANCHO_VENTANA) // 2
        y = (alto_pantalla - self.ALTO_VENTANA) // 2
        self.geometry(f"{self.ANCHO_VENTANA}x{self.ALTO_VENTANA}+{x}+{y}")

    def _crear_barra_superior(self) -> None:
        """Crea la barra superior con logo, título y toggle de tema."""
        # Frame de la barra superior
        self.barra_superior = ctk.CTkFrame(self, height=50, corner_radius=0)
        self.barra_superior.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.barra_superior.grid_columnconfigure(1, weight=1)

        # Logo de FPR
        logo_path = get_resource_path("ui/assets/fpr_logo.png")
        if logo_path.exists():
            logo_img = Image.open(logo_path)
            # Calcular ancho proporcional
            aspect_ratio = logo_img.width / logo_img.height
            logo_width = int(self.LOGO_HEIGHT * aspect_ratio)
            self.logo_image = ctk.CTkImage(
                light_image=logo_img,
                dark_image=logo_img,
                size=(logo_width, self.LOGO_HEIGHT),
            )
            self.label_logo = ctk.CTkLabel(
                self.barra_superior, image=self.logo_image, text=""
            )
            self.label_logo.grid(row=0, column=0, padx=(TAMANOS["padding_grande"], 10), pady=8)

        # Título con versión integrada
        try:
            from ui.utils.updater import APP_VERSION
            titulo_texto = f"{self.TITULO_APP}  v{APP_VERSION}"
        except ImportError:
            titulo_texto = self.TITULO_APP

        self.label_titulo = ctk.CTkLabel(
            self.barra_superior, text=titulo_texto, font=obtener_fuente("subtitulo")
        )
        self.label_titulo.grid(row=0, column=1, padx=0, pady=10, sticky="w")

        # Check updates button
        self.btn_updates = ctk.CTkButton(
            self.barra_superior,
            text="",
            image=get_icon("refresh"),
            width=30,
            height=30,
            command=self._manual_check_updates,
            fg_color="transparent",
            hover_color="gray30",
        )
        self.btn_updates.grid(row=0, column=2, padx=5, pady=10)
        ToolTip(self.btn_updates, "Check for updates")

        # Toggle de tema (dark/light)
        self.toggle_tema = ctk.CTkSwitch(
            self.barra_superior,
            text="Dark Mode",
            command=self._alternar_tema,
            onvalue=True,
            offvalue=False,
        )
        self.toggle_tema.grid(row=0, column=3, padx=TAMANOS["padding_grande"], pady=10)
        self.toggle_tema.select()  # Iniciar en modo oscuro

    def _crear_tabview(self) -> None:
        """Crea el widget de pestañas principal."""
        self.tabview = ctk.CTkTabview(self, corner_radius=TAMANOS["radio_borde"])
        self.tabview.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=TAMANOS["padding_grande"],
            pady=(0, TAMANOS["padding_grande"]),
        )

        # Agregar pestañas
        for nombre_interno, titulo in self.PESTANAS.items():
            self.tabview.add(titulo)

    def _crear_contenido_pestanas(self) -> None:
        """Crea el contenido de cada pestaña."""
        # Importar tabs aquí para evitar imports circulares
        from ui.tabs.api_keys_tab import ApiKeysTab
        from ui.tabs.hotels_tab import HotelsTab

        # Pestaña API Keys
        tab_api_keys_frame = self.tabview.tab(self.PESTANAS["api_keys"])
        tab_api_keys_frame.grid_columnconfigure(0, weight=1)
        tab_api_keys_frame.grid_rowconfigure(0, weight=1)
        self.tab_api_keys = ApiKeysTab(tab_api_keys_frame)
        self.tab_api_keys.grid(row=0, column=0, sticky="nsew")

        # Pestaña Hoteles
        tab_hoteles_frame = self.tabview.tab(self.PESTANAS["hoteles"])
        tab_hoteles_frame.grid_columnconfigure(0, weight=1)
        tab_hoteles_frame.grid_rowconfigure(0, weight=1)
        self.tab_hoteles = HotelsTab(tab_hoteles_frame)
        self.tab_hoteles.grid(row=0, column=0, sticky="nsew")

        # Pestaña Ejecutar
        tab_ejecutar_frame = self.tabview.tab(self.PESTANAS["ejecutar"])
        tab_ejecutar_frame.grid_columnconfigure(0, weight=1)
        tab_ejecutar_frame.grid_rowconfigure(0, weight=1)
        try:
            from ui.tabs.execute_tab import ExecuteTab

            self.tab_ejecutar = ExecuteTab(
                tab_ejecutar_frame,
                modo_tema=self.modo_tema,
                obtener_hoteles=self._obtener_hoteles_para_busqueda,
                on_busqueda_completada=self._on_busqueda_completada,
            )
            self.tab_ejecutar.grid(row=0, column=0, sticky="nsew")
        except ImportError as e:
            label_placeholder = ctk.CTkLabel(
                tab_ejecutar_frame,
                text=f"Pestaña Ejecutar\n\n(Error: {e})",
                font=obtener_fuente("encabezado"),
            )
            label_placeholder.grid(row=0, column=0, pady=50)

        # Pestaña Resultados
        tab_resultados_frame = self.tabview.tab(self.PESTANAS["resultados"])
        tab_resultados_frame.grid_columnconfigure(0, weight=1)
        tab_resultados_frame.grid_rowconfigure(0, weight=1)
        try:
            from ui.tabs.results_tab import ResultsTab

            self.tab_resultados = ResultsTab(
                tab_resultados_frame,
                modo_tema=self.modo_tema,
            )
            self.tab_resultados.grid(row=0, column=0, sticky="nsew")
        except ImportError as e:
            label_placeholder = ctk.CTkLabel(
                tab_resultados_frame,
                text=f"Pestaña Resultados\n\n(Error: {e})",
                font=obtener_fuente("encabezado"),
            )
            label_placeholder.grid(row=0, column=0, pady=50)

    def _cargar_database_inicial(self) -> None:
        """
        Verifica el estado inicial y muestra avisos necesarios.

        - Verifica si existe el cache de hoteles de Xotelo
        - Muestra aviso si falta el cache
        """
        if self.tab_hoteles:
            # Verificar si existe el cache de hoteles PR
            if hasattr(self.tab_hoteles, "mostrar_aviso_cache_faltante"):
                self.tab_hoteles.mostrar_aviso_cache_faltante()

    def _check_for_updates(self) -> None:
        """
        Check for application updates asynchronously.

        Shows a dialog if an update is available.
        """
        try:
            from ui.utils.updater import get_updater, UpdateInfo
            from ui.components.update_dialog import show_update_dialog

            updater = get_updater()

            def on_update_available(info: UpdateInfo) -> None:
                """Called when an update is found."""
                logger.info(f"Update available: {info.version}")
                # Show dialog on main thread
                self.after(0, lambda: show_update_dialog(self, info))

            def on_no_update() -> None:
                """Called when no update is available."""
                logger.debug("No update available")

            def on_error(error: str) -> None:
                """Called when update check fails."""
                logger.warning(f"Update check failed: {error}")

            # Check for updates in background
            updater.check_for_update(
                on_update_available=on_update_available,
                on_no_update=on_no_update,
                on_error=on_error,
            )

        except ImportError as e:
            logger.warning(f"Could not import updater: {e}")

    def _obtener_hoteles_para_busqueda(self):
        """
        Callback para obtener la lista de hoteles desde la pestaña Hoteles.

        Returns:
            Lista de hoteles para búsqueda.
        """
        if self.tab_hoteles:
            return self.tab_hoteles.obtener_hoteles()
        return []

    def _on_busqueda_completada(self, resultados: list):
        """
        Callback cuando la búsqueda de precios termina.

        Args:
            resultados: Lista de resultados de la búsqueda.
        """
        # Pasar resultados a la pestaña de resultados
        if self.tab_resultados and hasattr(self.tab_resultados, "cargar_resultados"):
            self.tab_resultados.cargar_resultados(resultados)
            # Cambiar a la pestaña de resultados
            self.cambiar_pestana("resultados")

    def _manual_check_updates(self) -> None:
        """Manually check for updates and show result."""
        from tkinter import messagebox

        try:
            from ui.utils.updater import get_updater, UpdateInfo
            from ui.components.update_dialog import show_update_dialog

            self.btn_updates.configure(state="disabled")
            updater = get_updater()

            def on_update_available(info: UpdateInfo) -> None:
                self.after(0, lambda: self.btn_updates.configure(state="normal"))
                self.after(0, lambda: show_update_dialog(self, info))

            def on_no_update() -> None:
                self.after(0, lambda: self.btn_updates.configure(state="normal"))
                self.after(0, lambda: messagebox.showinfo(
                    "No Updates",
                    f"You're running the latest version ({updater.get_current_version()}).",
                    parent=self
                ))

            def on_error(error: str) -> None:
                self.after(0, lambda: self.btn_updates.configure(state="normal"))
                self.after(0, lambda: messagebox.showerror(
                    "Update Check Failed",
                    f"Could not check for updates:\n\n{error}",
                    parent=self
                ))

            updater.check_for_update(
                on_update_available=on_update_available,
                on_no_update=on_no_update,
                on_error=on_error,
            )

        except ImportError as e:
            self.btn_updates.configure(state="normal")
            messagebox.showerror("Error", f"Updater not available: {e}", parent=self)

    def _alternar_tema(self) -> None:
        """Alterna entre modo oscuro y claro."""
        if self.toggle_tema.get():
            self.modo_tema = "dark"
            self.toggle_tema.configure(text="Dark Mode")
        else:
            self.modo_tema = "light"
            self.toggle_tema.configure(text="Light Mode")

        aplicar_tema(self.modo_tema)

        # Propagar tema a pestañas que manejan colores propios
        if self.tab_ejecutar and hasattr(self.tab_ejecutar, 'cambiar_tema'):
            self.tab_ejecutar.cambiar_tema(self.modo_tema)
        if self.tab_resultados and hasattr(self.tab_resultados, 'cambiar_tema'):
            self.tab_resultados.cambiar_tema(self.modo_tema)

    def cambiar_pestana(self, nombre: str) -> None:
        """
        Cambia a una pestaña específica programáticamente.

        Args:
            nombre: Nombre interno de la pestaña ("api_keys", "hoteles",
                   "ejecutar", "resultados").
        """
        if nombre in self.PESTANAS:
            titulo = self.PESTANAS[nombre]
            self.tabview.set(titulo)
        else:
            raise ValueError(
                f"Pestaña '{nombre}' no existe. "
                f"Opciones válidas: {list(self.PESTANAS.keys())}"
            )

    def obtener_pestana_actual(self) -> str:
        """
        Obtiene el nombre interno de la pestaña actual.

        Returns:
            Nombre interno de la pestaña activa.
        """
        titulo_actual = self.tabview.get()
        for nombre, titulo in self.PESTANAS.items():
            if titulo == titulo_actual:
                return nombre
        return ""

    def obtener_frame_pestana(self, nombre: str) -> ctk.CTkFrame:
        """
        Obtiene el frame de una pestaña para agregar contenido.

        Args:
            nombre: Nombre interno de la pestaña.

        Returns:
            Frame de la pestaña.
        """
        if nombre in self.PESTANAS:
            return self.tabview.tab(self.PESTANAS[nombre])
        raise ValueError(f"Pestaña '{nombre}' no existe.")

    def ejecutar(self) -> None:
        """Inicia el loop principal de la aplicación."""
        self.mainloop()


def main() -> None:
    """Función principal para ejecutar la aplicación."""
    app = HotelPriceApp()
    app.ejecutar()


if __name__ == "__main__":
    main()
