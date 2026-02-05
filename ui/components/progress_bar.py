"""
Componente de barra de progreso con tiempo estimado.

Muestra el progreso de búsqueda con porcentaje y ETA calculado
basado en la velocidad promedio de procesamiento.
"""

import time
from typing import List, Optional

import customtkinter as ctk

from ui.utils.theme import FUENTES, TemaMode, obtener_tema


class ProgressBar(ctk.CTkFrame):
    """
    Barra de progreso con indicador de porcentaje y tiempo estimado.

    Calcula el ETA basado en el tiempo transcurrido y la cantidad
    de items procesados, actualizando dinámicamente la estimación.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        modo_tema: TemaMode = "dark",
        altura_barra: int = 20,
        mostrar_porcentaje: bool = True,
        mostrar_eta: bool = True,
        **kwargs,
    ) -> None:
        """
        Inicializa el componente de barra de progreso.

        Args:
            master: Widget padre donde se colocará la barra.
            modo_tema: Modo de tema ("dark" o "light").
            altura_barra: Altura de la barra de progreso en píxeles.
            mostrar_porcentaje: Si se muestra el label de porcentaje.
            mostrar_eta: Si se muestra el label de tiempo estimado.
            **kwargs: Argumentos adicionales para CTkFrame.
        """
        self._modo_tema = modo_tema
        self._tema = obtener_tema(modo_tema)

        super().__init__(master, fg_color=self._tema["fondo_secundario"], **kwargs)

        # Variables de estado
        self._tiempo_inicio: Optional[float] = None
        self._items_procesados: int = 0
        self._total_items: int = 0
        self._velocidad_promedio: float = 0.0
        self._historial_velocidades: List[float] = []
        self._max_historial: int = 10

        # Configurar grid
        self.grid_columnconfigure(0, weight=1)

        # Crear widgets
        self._crear_widgets(altura_barra, mostrar_porcentaje, mostrar_eta)

    def _crear_widgets(
        self, altura_barra: int, mostrar_porcentaje: bool, mostrar_eta: bool
    ) -> None:
        """Crea los widgets internos de la barra de progreso."""
        fila_actual = 0

        # Frame superior para porcentaje y ETA
        if mostrar_porcentaje or mostrar_eta:
            frame_info = ctk.CTkFrame(self, fg_color="transparent")
            frame_info.grid(row=fila_actual, column=0, sticky="ew", pady=(0, 5))
            frame_info.grid_columnconfigure(1, weight=1)
            fila_actual += 1

            # Label de porcentaje (izquierda)
            if mostrar_porcentaje:
                self._label_porcentaje = ctk.CTkLabel(
                    frame_info,
                    text="0%",
                    font=FUENTES.get("normal", ("Segoe UI", 12)),
                )
                self._label_porcentaje.grid(row=0, column=0, sticky="w")
            else:
                self._label_porcentaje = None

            # Label de ETA (derecha)
            if mostrar_eta:
                self._label_eta = ctk.CTkLabel(
                    frame_info,
                    text="Estimated time: --:--",
                    font=FUENTES.get("pequena", ("Segoe UI", 10)),
                )
                self._label_eta.grid(row=0, column=2, sticky="e")
            else:
                self._label_eta = None
        else:
            self._label_porcentaje = None
            self._label_eta = None

        # Barra de progreso
        self._progress_bar = ctk.CTkProgressBar(
            self,
            height=altura_barra,
            progress_color=self._tema["acento"],
            fg_color=self._tema["fondo_principal"],
            corner_radius=altura_barra // 2,
        )
        self._progress_bar.grid(row=fila_actual, column=0, sticky="ew")
        self._progress_bar.set(0)

    def actualizar(self, actual: int, total: int) -> None:
        """
        Actualiza el progreso de la barra.

        Args:
            actual: Número de items procesados hasta ahora.
            total: Total de items a procesar.
        """
        # Iniciar temporizador en la primera actualización
        if self._tiempo_inicio is None:
            self._tiempo_inicio = time.time()
            self._items_procesados = 0

        self._items_procesados = actual
        self._total_items = total

        # Calcular porcentaje
        porcentaje = (actual / total) if total > 0 else 0
        porcentaje_mostrar = min(porcentaje, 1.0)

        # Actualizar barra visual
        self._progress_bar.set(porcentaje_mostrar)

        # Actualizar label de porcentaje
        if self._label_porcentaje is not None:
            texto_porcentaje = f"{int(porcentaje_mostrar * 100)}%"
            self._label_porcentaje.configure(text=texto_porcentaje)

        # Calcular y mostrar ETA
        if self._label_eta is not None:
            eta_texto = self._calcular_eta_texto()
            self._label_eta.configure(text=f"Estimated time: {eta_texto}")

        # Forzar actualización visual
        self.update_idletasks()

    def _calcular_eta_texto(self) -> str:
        """Calcula el texto del tiempo estimado restante."""
        if self._tiempo_inicio is None or self._items_procesados == 0:
            return "--:--"

        tiempo_transcurrido = time.time() - self._tiempo_inicio

        if tiempo_transcurrido < 0.001:
            return "--:--"

        # Calcular velocidad actual
        velocidad_actual = self._items_procesados / tiempo_transcurrido

        # Agregar al historial para promedio móvil
        self._historial_velocidades.append(velocidad_actual)
        if len(self._historial_velocidades) > self._max_historial:
            self._historial_velocidades.pop(0)

        # Calcular velocidad promedio
        self._velocidad_promedio = sum(self._historial_velocidades) / len(
            self._historial_velocidades
        )

        # Calcular items restantes
        items_restantes = self._total_items - self._items_procesados

        if items_restantes <= 0:
            return "00:00"

        if self._velocidad_promedio <= 0:
            return "--:--"

        # Calcular tiempo restante en segundos
        segundos_restantes = items_restantes / self._velocidad_promedio

        return self._formatear_tiempo(segundos_restantes)

    def _formatear_tiempo(self, segundos: float) -> str:
        """Formatea segundos a un string legible."""
        if segundos < 0:
            return "--:--"

        segundos = int(segundos)

        if segundos >= 3600:
            horas = segundos // 3600
            minutos = (segundos % 3600) // 60
            segs = segundos % 60
            return f"{horas:02d}:{minutos:02d}:{segs:02d}"
        elif segundos >= 60:
            minutos = segundos // 60
            segs = segundos % 60
            return f"{minutos:02d}:{segs:02d}"
        else:
            return f"00:{segundos:02d}"

    def reiniciar(self) -> None:
        """Reinicia la barra de progreso a su estado inicial."""
        self._tiempo_inicio = None
        self._items_procesados = 0
        self._total_items = 0
        self._velocidad_promedio = 0.0
        self._historial_velocidades.clear()

        self._progress_bar.set(0)

        if self._label_porcentaje is not None:
            self._label_porcentaje.configure(text="0%")

        if self._label_eta is not None:
            self._label_eta.configure(text="Estimated time: --:--")

        self.update_idletasks()

    def obtener_porcentaje(self) -> float:
        """Obtiene el porcentaje actual de progreso (0.0 a 1.0)."""
        if self._total_items == 0:
            return 0.0
        return min(self._items_procesados / self._total_items, 1.0)

    def obtener_tiempo_transcurrido(self) -> float:
        """Obtiene el tiempo transcurrido desde el inicio en segundos."""
        if self._tiempo_inicio is None:
            return 0.0
        return time.time() - self._tiempo_inicio

    def obtener_velocidad(self) -> float:
        """Obtiene la velocidad promedio de procesamiento (items/segundo)."""
        return self._velocidad_promedio

    def esta_completo(self) -> bool:
        """Verifica si el progreso está completo."""
        return self._total_items > 0 and self._items_procesados >= self._total_items

    def cambiar_tema(self, modo_tema: TemaMode) -> None:
        """Cambia el tema del componente."""
        self._modo_tema = modo_tema
        self._tema = obtener_tema(modo_tema)

        self.configure(fg_color=self._tema["fondo_secundario"])

        self._progress_bar.configure(
            progress_color=self._tema["acento"], fg_color=self._tema["fondo_principal"]
        )
