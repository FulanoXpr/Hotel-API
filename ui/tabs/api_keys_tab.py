"""
Pestaña de configuración de API Keys para Hotel Price Checker.
Permite configurar, guardar y probar las credenciales de las diferentes APIs.
"""

from typing import Dict, Tuple

import customtkinter as ctk
import requests

from ui.components.api_key_frame import AmadeusKeyFrame, ApiKeyFrame
from ui.utils.env_manager import EnvManager
from ui.utils.theme import FUENTES, TAMANOS


class ApiKeysTab(ctk.CTkFrame):
    """
    Pestaña para configurar las API keys del pipeline de cascada.

    Incluye:
    - Información sobre Xotelo (no requiere key)
    - Frame para SerpApi
    - Frame para Apify
    - Frame para Amadeus (2 campos)
    - Botón para guardar configuración
    - Barra de estado con APIs configuradas

    Attributes:
        env_manager: Gestor del archivo .env.
        valores_pendientes: Diccionario con valores modificados no guardados.
    """

    def __init__(self, master: ctk.CTkFrame, **kwargs) -> None:
        """
        Inicializa la pestaña de API Keys.

        Args:
            master: Widget padre.
            **kwargs: Argumentos adicionales para CTkFrame.
        """
        super().__init__(master, fg_color="transparent", **kwargs)

        # Inicializar gestor de .env
        self.env_manager = EnvManager()

        # Valores pendientes de guardar
        self.valores_pendientes: Dict[str, str] = {}

        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Crear componentes
        self._crear_encabezado()
        self._crear_contenido_scrollable()
        self._crear_barra_inferior()

        # Cargar valores iniciales
        self._cargar_valores()
        self._actualizar_estado_apis()

    def _crear_encabezado(self) -> None:
        """Crea el encabezado de la pestaña."""
        self.frame_encabezado = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_encabezado.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=TAMANOS["padding_medio"],
            pady=TAMANOS["padding_medio"],
        )

        self.label_titulo = ctk.CTkLabel(
            self.frame_encabezado,
            text="Configuración de API Keys",
            font=FUENTES["subtitulo"],
        )
        self.label_titulo.pack(anchor="w")

        self.label_subtitulo = ctk.CTkLabel(
            self.frame_encabezado,
            text="Configura las credenciales para el pipeline de búsqueda de precios",
            font=FUENTES["normal"],
            text_color="gray",
        )
        self.label_subtitulo.pack(anchor="w", pady=(5, 0))

    def _crear_contenido_scrollable(self) -> None:
        """Crea el área scrollable con los frames de API."""
        # Frame scrollable
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(
            row=1, column=0, sticky="nsew", padx=TAMANOS["padding_medio"], pady=0
        )
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # 1. Frame informativo de Xotelo
        self._crear_frame_xotelo()

        # 2. Frame de SerpApi
        self._crear_frame_serpapi()

        # 3. Frame de Apify
        self._crear_frame_apify()

        # 4. Frame de Amadeus
        self._crear_frame_amadeus()

    def _crear_frame_xotelo(self) -> None:
        """Crea el frame informativo de Xotelo."""
        self.frame_xotelo = ctk.CTkFrame(self.scroll_frame)
        self.frame_xotelo.grid(
            row=0, column=0, sticky="ew", pady=(0, TAMANOS["padding_medio"])
        )
        self.frame_xotelo.grid_columnconfigure(0, weight=1)

        # Contenido
        frame_contenido = ctk.CTkFrame(self.frame_xotelo, fg_color="transparent")
        frame_contenido.pack(
            fill="x", padx=TAMANOS["padding_medio"], pady=TAMANOS["padding_medio"]
        )

        # Título
        label_titulo = ctk.CTkLabel(
            frame_contenido,
            text="Xotelo",
            font=FUENTES["encabezado"],
        )
        label_titulo.pack(anchor="w")

        # Descripción
        label_desc = ctk.CTkLabel(
            frame_contenido,
            text="API gratuita de TripAdvisor - No requiere API key",
            font=FUENTES["normal"],
            text_color="gray",
        )
        label_desc.pack(anchor="w", pady=(5, 0))

        # Estado
        label_estado = ctk.CTkLabel(
            frame_contenido,
            text="✅ Siempre disponible (proveedor principal)",
            font=FUENTES["normal"],
            text_color="green",
        )
        label_estado.pack(anchor="w", pady=(5, 0))

    def _crear_frame_serpapi(self) -> None:
        """Crea el frame de SerpApi."""
        self.frame_serpapi = ApiKeyFrame(
            self.scroll_frame,
            nombre_api="serpapi",
            titulo="SerpApi (Google Hotels)",
            descripcion="250 búsquedas/mes gratis",
            url_obtencion="https://serpapi.com/manage-api-key",
            placeholder="Ingresa tu SerpApi key...",
            on_cambio=self._on_valor_cambio,
            test_funcion=self._test_serpapi,
        )
        self.frame_serpapi.grid(
            row=1, column=0, sticky="ew", pady=(0, TAMANOS["padding_medio"])
        )

    def _crear_frame_apify(self) -> None:
        """Crea el frame de Apify."""
        self.frame_apify = ApiKeyFrame(
            self.scroll_frame,
            nombre_api="apify",
            titulo="Apify (Booking.com)",
            descripcion="$5/mes en créditos gratis",
            url_obtencion="https://console.apify.com/account#/integrations",
            placeholder="Ingresa tu Apify token...",
            on_cambio=self._on_valor_cambio,
            test_funcion=self._test_apify,
        )
        self.frame_apify.grid(
            row=2, column=0, sticky="ew", pady=(0, TAMANOS["padding_medio"])
        )

    def _crear_frame_amadeus(self) -> None:
        """Crea el frame de Amadeus."""
        self.frame_amadeus = AmadeusKeyFrame(
            self.scroll_frame,
            on_cambio=self._on_valor_cambio,
            test_funcion=self._test_amadeus,
        )
        self.frame_amadeus.grid(
            row=3, column=0, sticky="ew", pady=(0, TAMANOS["padding_medio"])
        )

    def _crear_barra_inferior(self) -> None:
        """Crea la barra inferior con botón de guardar y status."""
        self.frame_inferior = ctk.CTkFrame(self)
        self.frame_inferior.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=TAMANOS["padding_medio"],
            pady=TAMANOS["padding_medio"],
        )
        self.frame_inferior.grid_columnconfigure(0, weight=1)

        # Status de APIs configuradas
        self.label_status = ctk.CTkLabel(
            self.frame_inferior,
            text="",
            font=FUENTES["normal"],
        )
        self.label_status.grid(
            row=0, column=0, sticky="w", padx=TAMANOS["padding_medio"]
        )

        # Botón de guardar
        self.boton_guardar = ctk.CTkButton(
            self.frame_inferior,
            text="💾 Guardar Configuración",
            width=180,
            height=35,
            font=FUENTES["normal"],
            command=self._guardar_configuracion,
        )
        self.boton_guardar.grid(
            row=0,
            column=1,
            padx=TAMANOS["padding_medio"],
            pady=TAMANOS["padding_medio"],
        )

        # Label de resultado de guardado
        self.label_guardado = ctk.CTkLabel(
            self.frame_inferior,
            text="",
            font=FUENTES["pequena"],
        )
        self.label_guardado.grid(row=0, column=2, padx=(0, TAMANOS["padding_medio"]))

    def _cargar_valores(self) -> None:
        """Carga los valores del .env en los campos."""
        # SerpApi
        serpapi_key = self.env_manager.obtener("SERPAPI_KEY")
        self.frame_serpapi.establecer_valor(serpapi_key)

        # Apify
        apify_token = self.env_manager.obtener("APIFY_TOKEN")
        self.frame_apify.establecer_valor(apify_token)

        # Amadeus
        client_id = self.env_manager.obtener("AMADEUS_CLIENT_ID")
        client_secret = self.env_manager.obtener("AMADEUS_CLIENT_SECRET")
        self.frame_amadeus.establecer_valores(client_id, client_secret)

    def _on_valor_cambio(self, nombre_campo: str, valor: str) -> None:
        """
        Callback cuando cambia un valor.

        Args:
            nombre_campo: Nombre del campo que cambió.
            valor: Nuevo valor.
        """
        # Mapear nombres de campos a variables de entorno
        mapeo = {
            "serpapi": "SERPAPI_KEY",
            "apify": "APIFY_TOKEN",
            "AMADEUS_CLIENT_ID": "AMADEUS_CLIENT_ID",
            "AMADEUS_CLIENT_SECRET": "AMADEUS_CLIENT_SECRET",
        }

        var_env = mapeo.get(nombre_campo, nombre_campo)
        self.valores_pendientes[var_env] = valor

        # Actualizar estado
        self._actualizar_estado_apis()

        # Mostrar indicador de cambios pendientes
        self.label_guardado.configure(text="Cambios sin guardar", text_color="orange")

    def _guardar_configuracion(self) -> None:
        """Guarda la configuración al archivo .env."""
        # Recopilar valores actuales de los campos
        valores_a_guardar = {
            "SERPAPI_KEY": self.frame_serpapi.obtener_valor(),
            "APIFY_TOKEN": self.frame_apify.obtener_valor(),
        }

        # Amadeus tiene dos campos
        client_id, client_secret = self.frame_amadeus.obtener_valores()
        valores_a_guardar["AMADEUS_CLIENT_ID"] = client_id
        valores_a_guardar["AMADEUS_CLIENT_SECRET"] = client_secret

        # Guardar
        exito = self.env_manager.guardar(valores_a_guardar)

        if exito:
            # Recargar en el entorno del proceso
            self.env_manager.recargar_en_entorno()

            # Limpiar pendientes
            self.valores_pendientes.clear()

            # Mostrar éxito
            self.label_guardado.configure(
                text="✅ Guardado correctamente", text_color="green"
            )

            # Actualizar estado
            self._actualizar_estado_apis()
        else:
            self.label_guardado.configure(text="❌ Error al guardar", text_color="red")

    def _actualizar_estado_apis(self) -> None:
        """Actualiza la barra de estado con las APIs configuradas."""
        # Obtener estado actual (incluyendo valores pendientes)
        apis_configuradas = []

        # SerpApi
        serpapi = self.frame_serpapi.obtener_valor()
        if serpapi:
            apis_configuradas.append("SerpApi")

        # Apify
        apify = self.frame_apify.obtener_valor()
        if apify:
            apis_configuradas.append("Apify")

        # Amadeus
        client_id, client_secret = self.frame_amadeus.obtener_valores()
        if client_id and client_secret:
            apis_configuradas.append("Amadeus")

        # Construir texto de estado
        if apis_configuradas:
            texto = (
                f"APIs configuradas: Xotelo (siempre), {', '.join(apis_configuradas)}"
            )
            color = "green"
        else:
            texto = "APIs configuradas: Solo Xotelo (gratuita)"
            color = "orange"

        self.label_status.configure(text=texto, text_color=color)

    # =========================================================================
    # FUNCIONES DE TEST DE CONEXIÓN
    # =========================================================================

    def _test_serpapi(self, api_key: str) -> Tuple[bool, str]:
        """
        Prueba la conexión con SerpApi.

        Args:
            api_key: API key a probar.

        Returns:
            Tupla (exito, mensaje).
        """
        try:
            url = f"https://serpapi.com/account?api_key={api_key}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Obtener información de la cuenta
                searches_left = data.get("plan_searches_left", "N/A")
                return True, f"OK - {searches_left} búsquedas restantes"
            elif response.status_code == 401:
                return False, "API key inválida"
            else:
                return False, f"Error HTTP {response.status_code}"

        except requests.Timeout:
            return False, "Timeout - Sin respuesta"
        except requests.RequestException as e:
            return False, f"Error de conexión: {str(e)[:30]}"

    def _test_apify(self, api_token: str) -> Tuple[bool, str]:
        """
        Prueba la conexión con Apify.

        Args:
            api_token: Token de API a probar.

        Returns:
            Tupla (exito, mensaje).
        """
        try:
            url = "https://api.apify.com/v2/users/me"
            headers = {"Authorization": f"Bearer {api_token}"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Obtener información del usuario
                username = data.get("data", {}).get("username", "Usuario")
                return True, f"OK - {username}"
            elif response.status_code == 401:
                return False, "Token inválido"
            else:
                return False, f"Error HTTP {response.status_code}"

        except requests.Timeout:
            return False, "Timeout - Sin respuesta"
        except requests.RequestException as e:
            return False, f"Error de conexión: {str(e)[:30]}"

    def _test_amadeus(self, client_id: str, client_secret: str) -> Tuple[bool, str]:
        """
        Prueba la conexión con Amadeus obteniendo un token de acceso.

        Args:
            client_id: Client ID de Amadeus.
            client_secret: Client Secret de Amadeus.

        Returns:
            Tupla (exito, mensaje).
        """
        try:
            # Usar el entorno de test
            url = "https://test.api.amadeus.com/v1/security/oauth2/token"

            data = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            }

            response = requests.post(url, data=data, timeout=15)

            if response.status_code == 200:
                token_data = response.json()
                expires_in = token_data.get("expires_in", 0)
                return True, f"OK - Token válido ({expires_in}s)"
            elif response.status_code == 401:
                return False, "Credenciales inválidas"
            else:
                error_msg = response.json().get(
                    "error_description", f"Error HTTP {response.status_code}"
                )
                return False, error_msg[:40]

        except requests.Timeout:
            return False, "Timeout - Sin respuesta"
        except requests.RequestException as e:
            return False, f"Error de conexión: {str(e)[:30]}"

    def recargar_valores(self) -> None:
        """Recarga los valores del archivo .env."""
        self.env_manager.cargar()
        self._cargar_valores()
        self._actualizar_estado_apis()
        self.valores_pendientes.clear()
        self.label_guardado.configure(text="", text_color="gray")
