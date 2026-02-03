# Cambios recientes (para Claude)

## Resumen
- Se reforzó el manejo de tarifas inválidas para evitar errores al calcular la tarifa mínima.
- Se aseguró una espera (`REQUEST_DELAY`) entre hoteles también en modo `--multi-date`.
- Se parametrizó `xotelo_price_fixer.py` para evitar fechas/archivos fijos y permitir ejecución futura sin ajustes manuales.

## Detalles
- `xotelo_api.py`
  - Se filtran tarifas con `rate` no numérico o `None` antes de calcular el mínimo.
  - El valor retornado de `rate` es numérico.
- `xotelo_price_updater.py`
  - Se agrega `api.wait()` después de procesar cada hotel con clave, incluso en `--multi-date`.
- `xotelo_price_fixer.py`
  - Se añadieron argumentos CLI:
    - `--input`, `--output`
    - `--check-in`, `--check-out`
    - `--days-ahead`, `--nights`
  - Si no se pasan fechas explícitas, se calculan en base a `days-ahead` y `nights`.

## Ejemplos
```bash
# Usar fechas explícitas
python xotelo_price_fixer.py --check-in 2026-03-15 --check-out 2026-03-16

# Usar fechas relativas (por defecto)
python xotelo_price_fixer.py --days-ahead 45 --nights 2

# Cambiar archivos de entrada/salida
python xotelo_price_fixer.py --input "archivo.xlsx" --output "salida.xlsx"

# Smoke tests de API (requieren red y variable de entorno)
cd "/Users/ricardorivera/Documents/Hotel API/Hotel-API"
RUN_API_SMOKE=1 python3 -m pytest tests/test_api_smoke.py -v -m smoke
```
