# Hotel Price Checker - Aplicación de Escritorio

Aplicación de escritorio multiplataforma (Windows/Mac) para consultar precios de hoteles usando múltiples proveedores de datos.

## Características

- **Interfaz moderna** con CustomTkinter y soporte para tema oscuro/claro
- **4 pestañas funcionales:**
  - 🔑 **API Keys**: Configurar credenciales con test de conexión
  - 📋 **Hoteles**: Cargar Excel, agregar/editar/eliminar hoteles
  - ▶ **Ejecutar**: Búsqueda con progreso en vivo y estadísticas
  - 📊 **Resultados**: Filtrar, ordenar y exportar a Excel
- **Threading**: Búsquedas en background sin bloquear la UI
- **Cascade de proveedores**: Xotelo → SerpApi → Apify → Amadeus
- **Cache de 24 horas** para evitar consultas duplicadas

## Requisitos

- **Python 3.10+** con Tkinter (recomendado: Python 3.12)
- **macOS**: Requiere `python-tk` de Homebrew para versiones modernas
- **Windows**: Python estándar incluye Tkinter

### Dependencias

```
customtkinter>=5.2.0
openpyxl>=3.1.0
requests>=2.28.0
python-dotenv>=1.0.0
```

## Instalación

### macOS

```bash
# Instalar Python con Tkinter (si no lo tienes)
brew install python@3.12 python-tk@3.12

# Instalar dependencias
/opt/homebrew/bin/python3.12 -m pip install --break-system-packages -r requirements-app.txt
```

### Windows

```bash
# Instalar dependencias (Python incluye Tkinter)
pip install -r requirements-app.txt
```

## Ejecución

### macOS

```bash
cd "/Users/ricardorivera/Documents/Hotel API/Hotel-API"
/opt/homebrew/bin/python3.12 hotel_price_app.py
```

### Windows

```bash
python hotel_price_app.py
```

## Uso de la Aplicación

### 1. Pestaña API Keys

Configura las credenciales de los proveedores:

| Proveedor | Descripción | Cómo obtener |
|-----------|-------------|--------------|
| **Xotelo** | Gratuito, no requiere key | Información incluida |
| **SerpApi** | Google Hotels, 100 búsquedas/mes gratis | [serpapi.com](https://serpapi.com) |
| **Apify** | Booking.com scraper, $5/mes gratis | [apify.com](https://apify.com) |
| **Amadeus** | GDS oficial, tier gratuito disponible | [developers.amadeus.com](https://developers.amadeus.com) |

- Usa el botón **"Probar"** para verificar cada conexión
- Haz clic en **"Guardar Configuración"** para persistir en `.env`

### 2. Pestaña Hoteles

Gestiona la lista de hoteles a buscar:

- **Cargar Excel**: Importa desde archivo `.xlsx` (detecta columnas automáticamente)
- **Agregar**: Añade hoteles manualmente con nombre y key Xotelo
- **Editar**: Doble-clic en una fila para modificar
- **Eliminar**: Selecciona y elimina hoteles
- **Buscar Key**: Consulta la API de Xotelo para obtener el identificador

**Formato Excel esperado:**
| Hotel | Key Xotelo | URL Booking |
|-------|------------|-------------|
| Hotel Example | g123456 | https://booking.com/... |

### 3. Pestaña Ejecutar

Configura y ejecuta la búsqueda:

**Parámetros:**
- Fecha de entrada (YYYY-MM-DD)
- Número de noches (1-14)
- Habitaciones (1-5)
- Adultos por habitación (1-4)
- Niños (0-4)
- Checkbox "Usar cascade" para probar todos los proveedores

**Durante la ejecución:**
- Barra de progreso con tiempo estimado
- Log en vivo con colores (info, éxito, error)
- Panel de estadísticas por proveedor
- Botón "Detener" para cancelar

### 4. Pestaña Resultados

Visualiza y exporta los resultados:

- **Métricas**: Total, con precio, sin precio, precio mín/máx
- **Filtros**: Todos, con precio, sin precio
- **Ordenamiento**: Clic en encabezados de columna
- **Exportar Excel**: Genera archivo `.xlsx` con resultados
- **Copiar**: Copia al portapapeles en formato tabla

## Estructura del Proyecto

```
Hotel-API/
├── hotel_price_app.py          # Entry point
├── hotel_app.spec              # Configuración PyInstaller
├── requirements-app.txt        # Dependencias UI
├── ui/
│   ├── app.py                  # Aplicación principal
│   ├── components/
│   │   ├── api_key_frame.py    # Frame de configuración API
│   │   ├── hotel_table.py      # Tabla de hoteles
│   │   ├── progress_bar.py     # Barra de progreso con ETA
│   │   ├── log_viewer.py       # Visor de logs con colores
│   │   └── stats_panel.py      # Panel de estadísticas
│   ├── tabs/
│   │   ├── api_keys_tab.py     # Pestaña API Keys
│   │   ├── hotels_tab.py       # Pestaña Hoteles
│   │   ├── execute_tab.py      # Pestaña Ejecutar
│   │   └── results_tab.py      # Pestaña Resultados
│   └── utils/
│       ├── theme.py            # Configuración de tema
│       ├── env_manager.py      # Gestión de .env
│       └── excel_handler.py    # Carga/guardado Excel
└── price_providers/            # Proveedores de precios (existente)
    ├── cascade.py
    ├── xotelo.py
    ├── serpapi.py
    ├── apify.py
    └── amadeus.py
```

## Generar Ejecutable

### Requisitos

```bash
pip install pyinstaller
```

### Generar

```bash
# Desde el directorio del proyecto
pyinstaller hotel_app.spec
```

### Resultado

- **Windows**: `dist/HotelPriceChecker/HotelPriceChecker.exe`
- **macOS**: `dist/HotelPriceChecker.app`

## Solución de Problemas

### Error: "No module named 'customtkinter'"

```bash
pip install customtkinter
```

### Error: "No module named '_tkinter'" (macOS)

```bash
brew install python-tk@3.12
```

### Error: "macOS XX or later required"

Usar Python 3.12 con python-tk de Homebrew:

```bash
brew install python@3.12 python-tk@3.12
/opt/homebrew/bin/python3.12 hotel_price_app.py
```

### La ventana no aparece

Verificar que Tkinter funciona:

```bash
python3 -c "import tkinter; tkinter.Tk().mainloop()"
```

### Búsqueda muy lenta

- Verificar conexión a internet
- Algunos proveedores tienen rate limits
- Usar menos hoteles para pruebas iniciales

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    HotelPriceApp (CTk)                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │API Keys │ │ Hoteles │ │Ejecutar │ │Resultados│  ← Tabs  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       │           │           │           │                 │
│       ▼           ▼           ▼           ▼                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │EnvMgr   │ │ExcelHdlr│ │Thread   │ │ExcelExp │           │
│  │.env R/W │ │.xlsx I/O│ │Queue    │ │Filter   │           │
│  └─────────┘ └─────────┘ └────┬────┘ └─────────┘           │
│                               │                             │
│                               ▼                             │
│                    ┌──────────────────┐                     │
│                    │CascadePriceProvider│                   │
│                    └────────┬─────────┘                     │
│         ┌──────────┬───────┴───────┬──────────┐            │
│         ▼          ▼               ▼          ▼            │
│    ┌────────┐ ┌────────┐    ┌────────┐ ┌────────┐          │
│    │ Xotelo │ │SerpApi │    │ Apify  │ │Amadeus │          │
│    └────────┘ └────────┘    └────────┘ └────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Contribuir

1. Fork del repositorio
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -m 'Agregar nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## Licencia

Uso interno - Foundation for Puerto Rico
