#!/usr/bin/env python3
"""
Hotel Price Checker - Aplicación de Escritorio
Entry point principal para la interfaz gráfica.

Uso:
    python hotel_price_app.py

Este script configura los paths necesarios y ejecuta la aplicación
de escritorio para consultar precios de hoteles.
"""

import logging
import sys
from pathlib import Path

# Configure logging early for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)


def configurar_paths() -> None:
    """
    Configura el sistema de paths para imports.
    Agrega el directorio raíz del proyecto al PYTHONPATH.
    """
    # Obtener directorio raíz del proyecto
    directorio_raiz = Path(__file__).parent.resolve()

    # Agregar al path si no está presente
    if str(directorio_raiz) not in sys.path:
        sys.path.insert(0, str(directorio_raiz))


def verificar_dependencias() -> bool:
    """
    Verifica que las dependencias necesarias estén instaladas.

    Returns:
        True si todas las dependencias están disponibles.

    Raises:
        ImportError: Si falta alguna dependencia crítica.
    """
    dependencias_faltantes = []

    try:
        import customtkinter
    except ImportError:
        dependencias_faltantes.append("customtkinter")

    try:
        import packaging
    except ImportError:
        dependencias_faltantes.append("packaging")

    if dependencias_faltantes:
        mensaje = (
            "Faltan dependencias necesarias para la UI:\n"
            f"  {', '.join(dependencias_faltantes)}\n\n"
            "Instálalas con:\n"
            "  pip install -r requirements-app.txt"
        )
        print(f"Error: {mensaje}", file=sys.stderr)
        return False

    return True


def main() -> int:
    """
    Función principal del entry point.

    Returns:
        Código de salida (0 = éxito, 1 = error).
    """
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("Hotel Price Checker - Starting")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Executable: {sys.executable}")
    logger.info(f"Frozen: {getattr(sys, 'frozen', False)}")
    if hasattr(sys, '_MEIPASS'):
        logger.info(f"PyInstaller bundle: {sys._MEIPASS}")
    logger.info("=" * 50)

    # Configurar paths
    configurar_paths()

    # Verificar dependencias
    if not verificar_dependencias():
        return 1

    try:
        # Importar y ejecutar la aplicación
        from ui.app import HotelPriceApp

        print("Iniciando Hotel Price Checker...")
        app = HotelPriceApp()
        app.ejecutar()

        return 0

    except KeyboardInterrupt:
        print("\nAplicación cerrada por el usuario.")
        return 0

    except Exception as error:
        print(f"Error al ejecutar la aplicación: {error}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
