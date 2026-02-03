"""
Gestor de archivo .env para Hotel Price Checker.
Permite cargar, guardar y modificar variables de entorno de forma segura.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class EnvManager:
    """
    Gestiona la lectura y escritura del archivo .env.

    Preserva comentarios y formato del archivo original.
    Crea el archivo si no existe.

    Attributes:
        ruta_env: Ruta al archivo .env.
        lineas: Lista de líneas del archivo (incluye comentarios).
        variables: Diccionario de variables cargadas.
    """

    # Variables de API que gestionamos
    VARIABLES_API: Tuple[str, ...] = (
        "SERPAPI_KEY",
        "APIFY_TOKEN",
        "AMADEUS_CLIENT_ID",
        "AMADEUS_CLIENT_SECRET",
    )

    def __init__(self, ruta_env: Optional[str] = None) -> None:
        """
        Inicializa el gestor de .env.

        Args:
            ruta_env: Ruta al archivo .env. Si no se especifica,
                     busca en el directorio raíz del proyecto.
        """
        if ruta_env:
            self.ruta_env = Path(ruta_env)
        else:
            # Buscar .env en el directorio del proyecto
            directorio_actual = Path(__file__).resolve().parent
            # Subir dos niveles: ui/utils -> ui -> proyecto
            self.ruta_env = directorio_actual.parent.parent / ".env"

        self.lineas: List[str] = []
        self.variables: Dict[str, str] = {}

        # Cargar archivo si existe
        self.cargar()

    def cargar(self) -> Dict[str, str]:
        """
        Lee el archivo .env actual y carga las variables.

        Si el archivo no existe, crea uno con plantilla básica.

        Returns:
            Diccionario con las variables cargadas.
        """
        if not self.ruta_env.exists():
            self._crear_archivo_plantilla()

        self.lineas = []
        self.variables = {}

        try:
            with open(self.ruta_env, "r", encoding="utf-8") as f:
                self.lineas = f.readlines()

            # Parsear variables
            for linea in self.lineas:
                linea_limpia = linea.strip()

                # Ignorar líneas vacías y comentarios
                if not linea_limpia or linea_limpia.startswith("#"):
                    continue

                # Parsear KEY=VALUE
                if "=" in linea_limpia:
                    # Dividir solo en el primer =
                    partes = linea_limpia.split("=", 1)
                    if len(partes) == 2:
                        clave = partes[0].strip()
                        valor = partes[1].strip()
                        # Remover comillas si existen
                        valor = valor.strip("'\"")
                        self.variables[clave] = valor

        except IOError as e:
            print(f"Error leyendo .env: {e}")

        return self.variables

    def guardar(self, keys: Optional[Dict[str, str]] = None) -> bool:
        """
        Guarda las keys al archivo .env.

        Preserva comentarios y estructura del archivo original.

        Args:
            keys: Diccionario con las keys a guardar. Si no se especifica,
                 guarda las variables actuales.

        Returns:
            True si se guardó correctamente, False en caso de error.
        """
        if keys:
            # Actualizar variables con las nuevas
            for clave, valor in keys.items():
                self.establecer(clave, valor, guardar=False)

        try:
            # Reconstruir líneas con las nuevas variables
            nuevas_lineas: List[str] = []
            variables_escritas: set = set()

            for linea in self.lineas:
                linea_limpia = linea.strip()

                # Verificar si es una línea de variable que debemos actualizar
                es_variable = False
                if (
                    linea_limpia
                    and not linea_limpia.startswith("#")
                    and "=" in linea_limpia
                ):
                    clave = linea_limpia.split("=", 1)[0].strip()
                    if clave in self.variables:
                        # Reemplazar con el nuevo valor
                        nuevas_lineas.append(f"{clave}={self.variables[clave]}\n")
                        variables_escritas.add(clave)
                        es_variable = True

                if not es_variable:
                    nuevas_lineas.append(linea)

            # Agregar variables nuevas que no estaban en el archivo
            for clave, valor in self.variables.items():
                if clave not in variables_escritas:
                    # Agregar al final con un comentario si es una API key
                    if clave in self.VARIABLES_API:
                        nuevas_lineas.append(
                            f"\n# {self._obtener_comentario_api(clave)}\n"
                        )
                    nuevas_lineas.append(f"{clave}={valor}\n")

            # Escribir archivo
            with open(self.ruta_env, "w", encoding="utf-8") as f:
                f.writelines(nuevas_lineas)

            # Actualizar líneas en memoria
            self.lineas = nuevas_lineas

            return True

        except IOError as e:
            print(f"Error escribiendo .env: {e}")
            return False

    def obtener(self, nombre: str) -> str:
        """
        Obtiene el valor de una variable.

        Args:
            nombre: Nombre de la variable.

        Returns:
            Valor de la variable o cadena vacía si no existe.
        """
        return self.variables.get(nombre, "")

    def establecer(self, nombre: str, valor: str, guardar: bool = True) -> bool:
        """
        Establece el valor de una variable.

        Args:
            nombre: Nombre de la variable.
            valor: Valor a establecer.
            guardar: Si True, guarda inmediatamente al archivo.

        Returns:
            True si se estableció correctamente.
        """
        self.variables[nombre] = valor

        if guardar:
            return self.guardar()

        return True

    def obtener_estado_apis(self) -> Dict[str, bool]:
        """
        Obtiene el estado de configuración de cada API.

        Returns:
            Diccionario con el nombre de la API y si está configurada.
        """
        return {
            "serpapi": bool(self.obtener("SERPAPI_KEY")),
            "apify": bool(self.obtener("APIFY_TOKEN")),
            "amadeus": bool(
                self.obtener("AMADEUS_CLIENT_ID")
                and self.obtener("AMADEUS_CLIENT_SECRET")
            ),
        }

    def _crear_archivo_plantilla(self) -> None:
        """Crea un archivo .env con plantilla básica si no existe."""
        plantilla = """# Hotel Price Updater - Environment Variables
# Configuración de API Keys para el pipeline de cascada

# =============================================================================
# CASCADE PIPELINE API KEYS
# =============================================================================

# SerpApi (Google Hotels)
# Obtén tu key en: https://serpapi.com/manage-api-key
# Tier gratuito: 250 búsquedas/mes
SERPAPI_KEY=

# Apify (Booking.com Scraper)
# Obtén tu token en: https://console.apify.com/account#/integrations
# Tier gratuito: $5/mes en créditos
APIFY_TOKEN=

# Amadeus (GDS Hotel Search)
# Obtén credenciales en: https://developers.amadeus.com/
# Tier gratuito: 500 llamadas/mes
AMADEUS_CLIENT_ID=
AMADEUS_CLIENT_SECRET=

# =============================================================================
# CASCADE SETTINGS (opcional)
# =============================================================================

# Habilitar pipeline de cascada (default: true)
CASCADE_ENABLED=true

# Cache TTL en horas (default: 24)
CACHE_TTL_HOURS=24
"""
        try:
            with open(self.ruta_env, "w", encoding="utf-8") as f:
                f.write(plantilla)

            # Cargar las líneas recién creadas
            self.lineas = plantilla.splitlines(keepends=True)

        except IOError as e:
            print(f"Error creando .env: {e}")

    def _obtener_comentario_api(self, clave: str) -> str:
        """Obtiene un comentario descriptivo para una variable de API."""
        comentarios = {
            "SERPAPI_KEY": "SerpApi (Google Hotels) - 250 búsquedas/mes gratis",
            "APIFY_TOKEN": "Apify (Booking.com) - $5/mes en créditos gratis",
            "AMADEUS_CLIENT_ID": "Amadeus (GDS) - 500 llamadas/mes gratis",
            "AMADEUS_CLIENT_SECRET": "Amadeus Client Secret",
        }
        return comentarios.get(clave, clave)

    def recargar_en_entorno(self) -> None:
        """
        Recarga las variables en el entorno actual del proceso.

        Útil después de guardar cambios para que los proveedores
        de precios puedan usar las nuevas keys sin reiniciar.
        """
        for clave, valor in self.variables.items():
            if valor:
                os.environ[clave] = valor
