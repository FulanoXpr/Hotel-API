# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file para Hotel Price Checker.

Genera ejecutables para Windows (.exe) y Mac (.app).

Uso:
    Windows: pyinstaller hotel_app.spec
    Mac:     pyinstaller hotel_app.spec

El ejecutable resultante estará en dist/HotelPriceChecker/
"""

import sys
from pathlib import Path

# Detectar plataforma
is_windows = sys.platform == 'win32'
is_mac = sys.platform == 'darwin'

# Configuración básica
app_name = 'HotelPriceChecker'
main_script = 'hotel_price_app.py'

# Datos adicionales a incluir
datas = [
    # Incluir archivos de configuración si existen
    ('.env.example', '.'),
    # Logo de FPR
    ('ui/assets/fpr_logo.png', 'ui/assets'),
]

# Módulos ocultos que PyInstaller no detecta automáticamente
hiddenimports = [
    'customtkinter',
    'tkinter',
    'openpyxl',
    'requests',
    'dotenv',
    'packaging',
    'PIL',
    'PIL.Image',
    # Proveedores de precios
    'price_providers',
    'price_providers.base',
    'price_providers.cache',
    'price_providers.cascade',
    'price_providers.xotelo',
    'price_providers.serpapi',
    'price_providers.apify',
    'price_providers.amadeus',
    # UI modules
    'ui',
    'ui.app',
    'ui.utils',
    'ui.utils.theme',
    'ui.utils.env_manager',
    'ui.utils.excel_handler',
    'ui.components',
    'ui.components.api_key_frame',
    'ui.components.hotel_table',
    'ui.components.progress_bar',
    'ui.components.log_viewer',
    'ui.components.stats_panel',
    'ui.tabs',
    'ui.tabs.api_keys_tab',
    'ui.tabs.hotels_tab',
    'ui.tabs.execute_tab',
    'ui.tabs.results_tab',
]

# Excluir módulos innecesarios para reducir tamaño
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'cv2',
    'torch',
    'tensorflow',
]

# Análisis del script principal
a = Analysis(
    [main_script],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

# Crear archivo PYZ (Python Zip)
pyz = PYZ(a.pure)

# Configuración del ejecutable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Sin ventana de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Agregar icono aquí si se tiene: icon='assets/icon.ico'
)

# Recopilar todos los archivos
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)

# Configuración específica para Mac (.app bundle)
if is_mac:
    app = BUNDLE(
        coll,
        name=f'{app_name}.app',
        icon=None,  # Agregar icono aquí si se tiene: icon='assets/icon.icns'
        bundle_identifier='com.hotelprices.checker',
        info_plist={
            'CFBundleName': app_name,
            'CFBundleDisplayName': 'Hotel Price Checker',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,  # Soporte para Dark Mode
        },
    )
