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
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all files for packages that need complete collection
requests_datas, requests_binaries, requests_hiddenimports = collect_all('requests')
urllib3_datas, urllib3_binaries, urllib3_hiddenimports = collect_all('urllib3')
certifi_datas, certifi_binaries, certifi_hiddenimports = collect_all('certifi')

# Detectar plataforma
is_windows = sys.platform == 'win32'
is_mac = sys.platform == 'darwin'

# Configuración básica
app_name = 'HotelPriceChecker'
main_script = 'hotel_price_app.py'

# Check if icon exists
icon_path = Path('ui/assets/icon.ico')
icon_file = str(icon_path) if icon_path.exists() and is_windows else None
icon_path_mac = Path('ui/assets/icon.icns')
icon_file_mac = str(icon_path_mac) if icon_path_mac.exists() and is_mac else None

# Datos adicionales a incluir
datas = [
    # Incluir archivos de configuración si existen
    ('.env.example', '.'),
    # Logo de FPR
    ('ui/assets/fpr_logo.png', 'ui/assets'),
]

# Módulos ocultos que PyInstaller no detecta automáticamente
# Note: requests, urllib3, certifi are collected via collect_all() above
hiddenimports = [
    'customtkinter',
    'tkinter',
    'openpyxl',
    'charset_normalizer',
    # Other dependencies
    'dotenv',
    'packaging',
    'packaging.version',
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
    'ui.utils.updater',
    'ui.utils.icons',
    'ui.utils.tooltip',
    'ui.utils.date_picker',
    'ui.components',
    'ui.components.api_key_frame',
    'ui.components.hotel_table',
    'ui.components.progress_bar',
    'ui.components.log_viewer',
    'ui.components.stats_panel',
    'ui.components.update_dialog',
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
    binaries=requests_binaries + urllib3_binaries + certifi_binaries,
    datas=datas + requests_datas + urllib3_datas + certifi_datas,
    hiddenimports=hiddenimports + requests_hiddenimports + urllib3_hiddenimports + certifi_hiddenimports,
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
    icon=icon_file,  # Uses ui/assets/icon.ico if it exists
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
        icon=icon_file_mac,  # Uses ui/assets/icon.icns if it exists
        bundle_identifier='com.hotelprices.checker',
        info_plist={
            'CFBundleName': app_name,
            'CFBundleDisplayName': 'Hotel Price Checker',
            'CFBundleVersion': '1.2.1',
            'CFBundleShortVersionString': '1.2.1',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,  # Soporte para Dark Mode
        },
    )
