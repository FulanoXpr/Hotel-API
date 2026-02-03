"""
Componente reutilizable para configurar una API key.
Incluye campo de entrada, botón de visibilidad, test de conexión y estado.
"""

import threading
import webbrowser
from typing import Callable, Literal, Optional, Tuple

import customtkinter as ctk

from ui.utils.theme import FUENTES, TAMANOS

# Tipo para el estado de la API
EstadoApi = Literal["configurado", "vacio", "probando", "error", "exito"]


class ApiKeyFrame(ctk.CTkFrame):
    """
    Frame reutilizable para configurar una API key individual.

    Incluye:
    - Título del proveedor con descripción
    - Campo de texto con toggle de visibilidad
    - Botón de test de conexión
    - Indicador de estado
    - Link a la página de obtención

    Attributes:
        nombre_api: Nombre interno de la API (ej: "serpapi").
        titulo: Título visible del proveedor.
        descripcion: Descripción con límites (ej: "250 búsquedas/mes gratis").
        url_obtencion: URL para obtener la API key.
        valor_actual: Valor actual del campo.
        on_cambio: Callback cuando cambia el valor.
    """

    def __init__(
        self,
        master: ctk.CTkFrame,
        nombre_api: str,
        titulo: str,
        descripcion: str,
        url_obtencion: str,
        valor_inicial: str = "",
        placeholder: str = "Ingresa tu API key...",
        on_cambio: Optional[Callable[[str, str], None]] = None,
        test_funcion: Optional[Callable[[str], Tuple[bool, str]]] = None,
        **kwargs,
    ) -> None:
        """
        Inicializa el frame de API key.

        Args:
            master: Widget padre.
            nombre_api: Nombre interno de la API.
            titulo: Título visible del proveedor.
            descripcion: Descripción con límites de uso.
            url_obtencion: URL para obtener la key.
            valor_inicial: Valor inicial del campo.
            placeholder: Texto placeholder del campo.
            on_cambio: Callback(nombre_api, nuevo_valor) cuando cambia el valor.
            test_funcion: Función para probar la conexión. Recibe la key y
                         retorna (exito: bool, mensaje: str).
            **kwargs: Argumentos adicionales para CTkFrame.
        """
        super().__init__(master, **kwargs)

        self.nombre_api = nombre_api
        self.titulo = titulo
        self.descripcion = descripcion
        self.url_obtencion = url_obtencion
        self.on_cambio = on_cambio
        self.test_funcion = test_funcion

        # Estado interno
        self._mostrar_key: bool = False
        self._estado: EstadoApi = "vacio" if not valor_inicial else "configurado"

        # Configurar grid
        self.grid_columnconfigure(1, weight=1)

        # Crear widgets
        self._crear_encabezado()
        self._crear_campo_entrada(valor_inicial, placeholder)
        self._crear_botones()
        self._crear_estado()

        # Actualizar estado visual
        self._actualizar_indicador_estado()

    def _crear_encabezado(self) -> None:
        """Crea el encabezado con título, descripción y link."""
        # Frame del encabezado
        self.frame_encabezado = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_encabezado.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=TAMANOS["padding_medio"],
            pady=(TAMANOS["padding_medio"], 5),
        )
        self.frame_encabezado.grid_columnconfigure(1, weight=1)

        # Título
        self.label_titulo = ctk.CTkLabel(
            self.frame_encabezado,
            text=self.titulo,
            font=FUENTES["encabezado"],
        )
        self.label_titulo.grid(row=0, column=0, sticky="w")

        # Descripción / límites
        self.label_descripcion = ctk.CTkLabel(
            self.frame_encabezado,
            text=f"({self.descripcion})",
            font=FUENTES["pequena"],
            text_color="gray",
        )
        self.label_descripcion.grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Link para obtener key
        self.link_obtener = ctk.CTkButton(
            self.frame_encabezado,
            text="Obtener key",
            font=FUENTES["pequena"],
            fg_color="transparent",
            text_color=("#2980b9", "#3498db"),
            hover_color=("gray90", "gray20"),
            width=80,
            height=20,
            command=self._abrir_url_obtencion,
        )
        self.link_obtener.grid(row=0, column=2, sticky="e")

    def _crear_campo_entrada(self, valor_inicial: str, placeholder: str) -> None:
        """Crea el campo de entrada con botón de visibilidad."""
        # Frame para entrada y botón de ojo
        self.frame_entrada = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_entrada.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=TAMANOS["padding_medio"],
            pady=5,
        )
        self.frame_entrada.grid_columnconfigure(0, weight=1)

        # Campo de entrada
        self.entrada_key = ctk.CTkEntry(
            self.frame_entrada,
            placeholder_text=placeholder,
            show="*",  # Oculto por defecto
            font=FUENTES["codigo"],
            height=35,
        )
        self.entrada_key.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Insertar valor inicial
        if valor_inicial:
            self.entrada_key.insert(0, valor_inicial)

        # Vincular evento de cambio
        self.entrada_key.bind("<KeyRelease>", self._on_key_release)

        # Botón de mostrar/ocultar
        self.boton_ojo = ctk.CTkButton(
            self.frame_entrada,
            text="👁",
            width=35,
            height=35,
            command=self._toggle_visibilidad,
        )
        self.boton_ojo.grid(row=0, column=1)

    def _crear_botones(self) -> None:
        """Crea los botones de acción (Test)."""
        # Frame de botones
        self.frame_botones = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botones.grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="w",
            padx=TAMANOS["padding_medio"],
            pady=5,
        )

        # Botón de test
        self.boton_test = ctk.CTkButton(
            self.frame_botones,
            text="🔗 Test Conexión",
            width=120,
            height=28,
            font=FUENTES["pequena"],
            command=self._ejecutar_test,
        )
        self.boton_test.grid(row=0, column=0)

        # Label de resultado del test
        self.label_test_resultado = ctk.CTkLabel(
            self.frame_botones,
            text="",
            font=FUENTES["pequena"],
        )
        self.label_test_resultado.grid(row=0, column=1, padx=(10, 0))

    def _crear_estado(self) -> None:
        """Crea el indicador de estado."""
        # Frame de estado (alineado a la derecha)
        self.frame_estado = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_estado.grid(
            row=2, column=2, sticky="e", padx=TAMANOS["padding_medio"], pady=5
        )

        # Indicador de estado
        self.label_estado = ctk.CTkLabel(
            self.frame_estado,
            text="",
            font=FUENTES["normal"],
        )
        self.label_estado.grid(row=0, column=0)

    def _toggle_visibilidad(self) -> None:
        """Alterna la visibilidad de la API key."""
        self._mostrar_key = not self._mostrar_key

        if self._mostrar_key:
            self.entrada_key.configure(show="")
            self.boton_ojo.configure(text="🔒")
        else:
            self.entrada_key.configure(show="*")
            self.boton_ojo.configure(text="👁")

    def _on_key_release(self, event) -> None:
        """Maneja el evento de cambio en el campo."""
        valor = self.entrada_key.get()

        # Actualizar estado
        self._estado = "configurado" if valor else "vacio"
        self._actualizar_indicador_estado()

        # Llamar callback si existe
        if self.on_cambio:
            self.on_cambio(self.nombre_api, valor)

    def _actualizar_indicador_estado(self) -> None:
        """Actualiza el indicador visual de estado."""
        estados_texto = {
            "configurado": ("✅ Configurado", "green"),
            "vacio": ("⚠️ Vacío", "orange"),
            "probando": ("🔄 Probando...", "gray"),
            "error": ("❌ Error", "red"),
            "exito": ("✅ Conectado", "green"),
        }

        texto, color = estados_texto.get(self._estado, ("", "gray"))
        self.label_estado.configure(text=texto, text_color=color)

    def _ejecutar_test(self) -> None:
        """Ejecuta el test de conexión en un hilo separado."""
        if not self.test_funcion:
            self.label_test_resultado.configure(
                text="Test no disponible", text_color="gray"
            )
            return

        valor = self.entrada_key.get()
        if not valor:
            self.label_test_resultado.configure(
                text="Ingresa una key primero", text_color="orange"
            )
            return

        # Cambiar estado a probando
        self._estado = "probando"
        self._actualizar_indicador_estado()
        self.boton_test.configure(state="disabled")
        self.label_test_resultado.configure(text="Conectando...", text_color="gray")

        # Ejecutar en hilo separado
        def ejecutar_test_async():
            try:
                exito, mensaje = self.test_funcion(valor)

                # Actualizar UI en el hilo principal
                self.after(0, lambda: self._mostrar_resultado_test(exito, mensaje))

            except Exception as e:
                self.after(0, lambda: self._mostrar_resultado_test(False, str(e)))

        hilo = threading.Thread(target=ejecutar_test_async, daemon=True)
        hilo.start()

    def _mostrar_resultado_test(self, exito: bool, mensaje: str) -> None:
        """Muestra el resultado del test en la UI."""
        self.boton_test.configure(state="normal")

        if exito:
            self._estado = "exito"
            self.label_test_resultado.configure(text=mensaje, text_color="green")
        else:
            self._estado = "error"
            self.label_test_resultado.configure(text=mensaje, text_color="red")

        self._actualizar_indicador_estado()

    def _abrir_url_obtencion(self) -> None:
        """Abre la URL de obtención en el navegador."""
        webbrowser.open(self.url_obtencion)

    def obtener_valor(self) -> str:
        """Obtiene el valor actual del campo."""
        return self.entrada_key.get()

    def establecer_valor(self, valor: str) -> None:
        """Establece el valor del campo."""
        self.entrada_key.delete(0, "end")
        if valor:
            self.entrada_key.insert(0, valor)

        # Actualizar estado
        self._estado = "configurado" if valor else "vacio"
        self._actualizar_indicador_estado()

    def obtener_estado(self) -> EstadoApi:
        """Obtiene el estado actual de la API."""
        return self._estado


class AmadeusKeyFrame(ctk.CTkFrame):
    """
    Frame especializado para Amadeus que requiere dos campos:
    Client ID y Client Secret.

    Attributes:
        on_cambio: Callback cuando cambia cualquier valor.
    """

    def __init__(
        self,
        master: ctk.CTkFrame,
        valor_client_id: str = "",
        valor_client_secret: str = "",
        on_cambio: Optional[Callable[[str, str], None]] = None,
        test_funcion: Optional[Callable[[str, str], Tuple[bool, str]]] = None,
        **kwargs,
    ) -> None:
        """
        Inicializa el frame de Amadeus.

        Args:
            master: Widget padre.
            valor_client_id: Valor inicial del Client ID.
            valor_client_secret: Valor inicial del Client Secret.
            on_cambio: Callback(campo, nuevo_valor) cuando cambia un valor.
            test_funcion: Función para probar la conexión. Recibe (client_id, client_secret)
                         y retorna (exito: bool, mensaje: str).
            **kwargs: Argumentos adicionales para CTkFrame.
        """
        super().__init__(master, **kwargs)

        self.on_cambio = on_cambio
        self.test_funcion = test_funcion
        self._mostrar_keys: bool = False
        self._estado: EstadoApi = "vacio"

        # Configurar grid
        self.grid_columnconfigure(1, weight=1)

        # Crear widgets
        self._crear_encabezado()
        self._crear_campos(valor_client_id, valor_client_secret)
        self._crear_botones()

        # Actualizar estado inicial
        self._actualizar_estado()

    def _crear_encabezado(self) -> None:
        """Crea el encabezado con título y link."""
        self.frame_encabezado = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_encabezado.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=TAMANOS["padding_medio"],
            pady=(TAMANOS["padding_medio"], 5),
        )
        self.frame_encabezado.grid_columnconfigure(1, weight=1)

        # Título
        self.label_titulo = ctk.CTkLabel(
            self.frame_encabezado,
            text="Amadeus GDS",
            font=FUENTES["encabezado"],
        )
        self.label_titulo.grid(row=0, column=0, sticky="w")

        # Descripción
        self.label_descripcion = ctk.CTkLabel(
            self.frame_encabezado,
            text="(500 llamadas/mes gratis)",
            font=FUENTES["pequena"],
            text_color="gray",
        )
        self.label_descripcion.grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Link
        self.link_obtener = ctk.CTkButton(
            self.frame_encabezado,
            text="Obtener credenciales",
            font=FUENTES["pequena"],
            fg_color="transparent",
            text_color=("#2980b9", "#3498db"),
            hover_color=("gray90", "gray20"),
            width=120,
            height=20,
            command=lambda: webbrowser.open("https://developers.amadeus.com/"),
        )
        self.link_obtener.grid(row=0, column=2, sticky="e")

    def _crear_campos(self, valor_client_id: str, valor_client_secret: str) -> None:
        """Crea los campos de entrada para Client ID y Secret."""
        # Frame de campos
        self.frame_campos = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_campos.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=TAMANOS["padding_medio"],
            pady=5,
        )
        self.frame_campos.grid_columnconfigure(1, weight=1)
        self.frame_campos.grid_columnconfigure(3, weight=1)

        # Client ID
        self.label_client_id = ctk.CTkLabel(
            self.frame_campos,
            text="Client ID:",
            font=FUENTES["normal"],
        )
        self.label_client_id.grid(row=0, column=0, sticky="w", padx=(0, 5))

        self.entrada_client_id = ctk.CTkEntry(
            self.frame_campos,
            placeholder_text="Tu Client ID...",
            show="*",
            font=FUENTES["codigo"],
            height=35,
        )
        self.entrada_client_id.grid(row=0, column=1, sticky="ew", padx=(0, 15))
        if valor_client_id:
            self.entrada_client_id.insert(0, valor_client_id)
        self.entrada_client_id.bind("<KeyRelease>", self._on_cambio)

        # Client Secret
        self.label_client_secret = ctk.CTkLabel(
            self.frame_campos,
            text="Client Secret:",
            font=FUENTES["normal"],
        )
        self.label_client_secret.grid(row=0, column=2, sticky="w", padx=(0, 5))

        self.entrada_client_secret = ctk.CTkEntry(
            self.frame_campos,
            placeholder_text="Tu Client Secret...",
            show="*",
            font=FUENTES["codigo"],
            height=35,
        )
        self.entrada_client_secret.grid(row=0, column=3, sticky="ew", padx=(0, 5))
        if valor_client_secret:
            self.entrada_client_secret.insert(0, valor_client_secret)
        self.entrada_client_secret.bind("<KeyRelease>", self._on_cambio)

        # Botón de visibilidad
        self.boton_ojo = ctk.CTkButton(
            self.frame_campos,
            text="👁",
            width=35,
            height=35,
            command=self._toggle_visibilidad,
        )
        self.boton_ojo.grid(row=0, column=4)

    def _crear_botones(self) -> None:
        """Crea los botones de acción."""
        self.frame_botones = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botones.grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=TAMANOS["padding_medio"],
            pady=5,
        )
        self.frame_botones.grid_columnconfigure(2, weight=1)

        # Botón de test
        self.boton_test = ctk.CTkButton(
            self.frame_botones,
            text="🔗 Test Conexión",
            width=120,
            height=28,
            font=FUENTES["pequena"],
            command=self._ejecutar_test,
        )
        self.boton_test.grid(row=0, column=0)

        # Resultado del test
        self.label_test_resultado = ctk.CTkLabel(
            self.frame_botones,
            text="",
            font=FUENTES["pequena"],
        )
        self.label_test_resultado.grid(row=0, column=1, padx=(10, 0))

        # Indicador de estado
        self.label_estado = ctk.CTkLabel(
            self.frame_botones,
            text="",
            font=FUENTES["normal"],
        )
        self.label_estado.grid(row=0, column=2, sticky="e")

    def _toggle_visibilidad(self) -> None:
        """Alterna la visibilidad de las keys."""
        self._mostrar_keys = not self._mostrar_keys

        if self._mostrar_keys:
            self.entrada_client_id.configure(show="")
            self.entrada_client_secret.configure(show="")
            self.boton_ojo.configure(text="🔒")
        else:
            self.entrada_client_id.configure(show="*")
            self.entrada_client_secret.configure(show="*")
            self.boton_ojo.configure(text="👁")

    def _on_cambio(self, event) -> None:
        """Maneja cambios en los campos."""
        self._actualizar_estado()

        if self.on_cambio:
            # Determinar qué campo cambió
            widget = event.widget
            if widget == self.entrada_client_id:
                self.on_cambio("AMADEUS_CLIENT_ID", self.entrada_client_id.get())
            else:
                self.on_cambio(
                    "AMADEUS_CLIENT_SECRET", self.entrada_client_secret.get()
                )

    def _actualizar_estado(self) -> None:
        """Actualiza el indicador de estado."""
        client_id = self.entrada_client_id.get()
        client_secret = self.entrada_client_secret.get()

        if client_id and client_secret:
            self._estado = "configurado"
            self.label_estado.configure(text="✅ Configurado", text_color="green")
        elif client_id or client_secret:
            self._estado = "vacio"
            self.label_estado.configure(text="⚠️ Incompleto", text_color="orange")
        else:
            self._estado = "vacio"
            self.label_estado.configure(text="⚠️ Vacío", text_color="orange")

    def _ejecutar_test(self) -> None:
        """Ejecuta el test de conexión."""
        if not self.test_funcion:
            self.label_test_resultado.configure(
                text="Test no disponible", text_color="gray"
            )
            return

        client_id = self.entrada_client_id.get()
        client_secret = self.entrada_client_secret.get()

        if not client_id or not client_secret:
            self.label_test_resultado.configure(
                text="Completa ambos campos", text_color="orange"
            )
            return

        # Cambiar estado
        self.label_estado.configure(text="🔄 Probando...", text_color="gray")
        self.boton_test.configure(state="disabled")
        self.label_test_resultado.configure(text="Conectando...", text_color="gray")

        def ejecutar_test_async():
            try:
                exito, mensaje = self.test_funcion(client_id, client_secret)
                self.after(0, lambda: self._mostrar_resultado_test(exito, mensaje))
            except Exception as e:
                self.after(0, lambda: self._mostrar_resultado_test(False, str(e)))

        hilo = threading.Thread(target=ejecutar_test_async, daemon=True)
        hilo.start()

    def _mostrar_resultado_test(self, exito: bool, mensaje: str) -> None:
        """Muestra el resultado del test."""
        self.boton_test.configure(state="normal")

        if exito:
            self._estado = "exito"
            self.label_estado.configure(text="✅ Conectado", text_color="green")
            self.label_test_resultado.configure(text=mensaje, text_color="green")
        else:
            self._estado = "error"
            self.label_estado.configure(text="❌ Error", text_color="red")
            self.label_test_resultado.configure(text=mensaje, text_color="red")

    def obtener_valores(self) -> Tuple[str, str]:
        """Obtiene los valores de Client ID y Client Secret."""
        return (self.entrada_client_id.get(), self.entrada_client_secret.get())

    def establecer_valores(self, client_id: str, client_secret: str) -> None:
        """Establece los valores de los campos."""
        self.entrada_client_id.delete(0, "end")
        self.entrada_client_secret.delete(0, "end")

        if client_id:
            self.entrada_client_id.insert(0, client_id)
        if client_secret:
            self.entrada_client_secret.insert(0, client_secret)

        self._actualizar_estado()

    def obtener_estado(self) -> EstadoApi:
        """Obtiene el estado actual."""
        return self._estado
