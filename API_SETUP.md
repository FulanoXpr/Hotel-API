# API Setup Guide / Guía de Configuración de APIs

This guide explains how to obtain API keys for the Hotel Price Checker cascade pipeline.

Esta guía explica cómo obtener las claves API para el pipeline de Hotel Price Checker.

---

## Table of Contents / Índice

- [Xotelo](#xotelo) - No key required / No requiere clave
- [SerpApi](#serpapi) - Google Hotels
- [Apify](#apify) - Booking.com
- [Amadeus](#amadeus) - GDS (Global Distribution System)

---

## Xotelo

### English

Xotelo aggregates hotel prices from TripAdvisor. **No API key is required** - it works out of the box.

- **Free tier**: Unlimited requests
- **Rate limit**: 0.5 seconds between requests (handled automatically)
- **Coverage**: ~64% of Puerto Rico hotels

### Español

Xotelo agrega precios de hoteles de TripAdvisor. **No se requiere clave API** - funciona sin configuración.

- **Plan gratuito**: Solicitudes ilimitadas
- **Límite de velocidad**: 0.5 segundos entre solicitudes (manejado automáticamente)
- **Cobertura**: ~64% de los hoteles de Puerto Rico

---

## SerpApi

### English

SerpApi provides Google Hotels search results.

**Free tier**: 100 searches/month

#### Steps to get your API key:

1. Go to [https://serpapi.com](https://serpapi.com)
2. Click **"Register"** (top right)
3. Create an account with email or Google sign-in
4. Verify your email address
5. Go to [Dashboard](https://serpapi.com/dashboard)
6. Your **API Key** is displayed on the dashboard
7. Copy the key and add it to your `.env` file:

```bash
SERPAPI_KEY=your_api_key_here
```

#### Free tier limits:
- 100 searches per month
- No credit card required
- Searches reset on the 1st of each month

---

### Español

SerpApi proporciona resultados de búsqueda de Google Hotels.

**Plan gratuito**: 100 búsquedas/mes

#### Pasos para obtener tu clave API:

1. Ve a [https://serpapi.com](https://serpapi.com)
2. Haz clic en **"Register"** (arriba a la derecha)
3. Crea una cuenta con email o inicio de sesión con Google
4. Verifica tu dirección de email
5. Ve al [Dashboard](https://serpapi.com/dashboard)
6. Tu **API Key** se muestra en el dashboard
7. Copia la clave y agrégala a tu archivo `.env`:

```bash
SERPAPI_KEY=tu_clave_api_aqui
```

#### Límites del plan gratuito:
- 100 búsquedas por mes
- No se requiere tarjeta de crédito
- Las búsquedas se reinician el 1ro de cada mes

---

## Apify

### English

Apify runs the Booking.com scraper to extract hotel prices.

**Free tier**: $5/month in credits (~1,700 searches)

#### Steps to get your API token:

1. Go to [https://apify.com](https://apify.com)
2. Click **"Sign up"** (top right)
3. Create an account with email, Google, or GitHub
4. Verify your email address
5. Go to [Settings → Integrations](https://console.apify.com/settings/integrations)
6. Find your **Personal API Token**
7. Copy the token and add it to your `.env` file:

```bash
APIFY_TOKEN=your_api_token_here
```

#### Free tier limits:
- $5 free credits per month
- Each Booking.com search costs ~$0.003
- Approximately 1,700 searches per month
- Credits reset monthly

#### Note:
The app uses the Booking.com scraper actor. On first use, you may need to approve its usage in your Apify console.

---

### Español

Apify ejecuta el scraper de Booking.com para extraer precios de hoteles.

**Plan gratuito**: $5/mes en créditos (~1,700 búsquedas)

#### Pasos para obtener tu token API:

1. Ve a [https://apify.com](https://apify.com)
2. Haz clic en **"Sign up"** (arriba a la derecha)
3. Crea una cuenta con email, Google o GitHub
4. Verifica tu dirección de email
5. Ve a [Settings → Integrations](https://console.apify.com/settings/integrations)
6. Encuentra tu **Personal API Token**
7. Copia el token y agrégalo a tu archivo `.env`:

```bash
APIFY_TOKEN=tu_token_api_aqui
```

#### Límites del plan gratuito:
- $5 en créditos gratis por mes
- Cada búsqueda de Booking.com cuesta ~$0.003
- Aproximadamente 1,700 búsquedas por mes
- Los créditos se reinician mensualmente

#### Nota:
La aplicación usa el actor scraper de Booking.com. En el primer uso, es posible que necesites aprobar su uso en tu consola de Apify.

---

## Amadeus

### English

Amadeus provides access to the Global Distribution System (GDS) used by travel agents.

**Free tier**: 500 API calls/month (test environment)

#### Steps to get your credentials:

1. Go to [https://developers.amadeus.com](https://developers.amadeus.com)
2. Click **"Register"** or **"Get Started"**
3. Fill in the registration form:
   - First/Last name
   - Email address
   - Company name (can be personal)
   - Password
4. Verify your email address
5. Log in and go to [My Apps](https://developers.amadeus.com/my-apps)
6. Click **"Create new app"**
7. Fill in:
   - **App name**: Hotel Price Checker (or any name)
   - **Description**: Optional
8. Select the APIs you need (Hotel Search is included by default)
9. Click **"Create"**
10. Your app will show:
    - **API Key** (Client ID)
    - **API Secret** (Client Secret)
11. Copy both and add to your `.env` file:

```bash
AMADEUS_CLIENT_ID=your_client_id_here
AMADEUS_CLIENT_SECRET=your_client_secret_here
AMADEUS_USE_PRODUCTION=false
```

#### Free tier limits:
- 500 API calls per month
- Test environment only (limited hotel inventory)
- ~21 Puerto Rico hotels available in test mode
- Production access requires Amadeus approval

#### Test vs Production:
- **Test** (`AMADEUS_USE_PRODUCTION=false`): Free, limited data, for development
- **Production** (`AMADEUS_USE_PRODUCTION=true`): Requires business approval from Amadeus

---

### Español

Amadeus proporciona acceso al Sistema Global de Distribución (GDS) utilizado por agentes de viajes.

**Plan gratuito**: 500 llamadas API/mes (ambiente de prueba)

#### Pasos para obtener tus credenciales:

1. Ve a [https://developers.amadeus.com](https://developers.amadeus.com)
2. Haz clic en **"Register"** o **"Get Started"**
3. Completa el formulario de registro:
   - Nombre y apellido
   - Dirección de email
   - Nombre de empresa (puede ser personal)
   - Contraseña
4. Verifica tu dirección de email
5. Inicia sesión y ve a [My Apps](https://developers.amadeus.com/my-apps)
6. Haz clic en **"Create new app"**
7. Completa:
   - **App name**: Hotel Price Checker (o cualquier nombre)
   - **Description**: Opcional
8. Selecciona las APIs que necesitas (Hotel Search está incluida por defecto)
9. Haz clic en **"Create"**
10. Tu aplicación mostrará:
    - **API Key** (Client ID)
    - **API Secret** (Client Secret)
11. Copia ambos y agrégalos a tu archivo `.env`:

```bash
AMADEUS_CLIENT_ID=tu_client_id_aqui
AMADEUS_CLIENT_SECRET=tu_client_secret_aqui
AMADEUS_USE_PRODUCTION=false
```

#### Límites del plan gratuito:
- 500 llamadas API por mes
- Solo ambiente de prueba (inventario de hoteles limitado)
- ~21 hoteles de Puerto Rico disponibles en modo de prueba
- Acceso a producción requiere aprobación de Amadeus

#### Prueba vs Producción:
- **Prueba** (`AMADEUS_USE_PRODUCTION=false`): Gratis, datos limitados, para desarrollo
- **Producción** (`AMADEUS_USE_PRODUCTION=true`): Requiere aprobación comercial de Amadeus

---

## Complete .env Example / Ejemplo completo de .env

```bash
# SerpApi - Google Hotels (100 free/month)
SERPAPI_KEY=your_serpapi_key

# Apify - Booking.com ($5 free/month)
APIFY_TOKEN=your_apify_token

# Amadeus - GDS (500 free/month)
AMADEUS_CLIENT_ID=your_client_id
AMADEUS_CLIENT_SECRET=your_client_secret
AMADEUS_USE_PRODUCTION=false

# Optional settings / Configuración opcional
CASCADE_ENABLED=true
CACHE_TTL_HOURS=24
REQUEST_DELAY=0.5
```

---

## Testing Your Keys / Probando tus Claves

### In the Desktop App / En la Aplicación de Escritorio

1. Open Hotel Price Checker
2. Go to the **"API Keys"** tab
3. Enter your keys
4. Click **"Test Connection"** for each API
5. A green checkmark means the key is valid

### From Command Line / Desde Línea de Comandos

```bash
# Run API smoke tests (requires keys in .env)
# Ejecutar pruebas de API (requiere claves en .env)

# Linux/macOS
RUN_API_SMOKE=1 python -m pytest tests/test_api_smoke.py -v -m smoke

# Windows PowerShell
$env:RUN_API_SMOKE=1; python -m pytest tests/test_api_smoke.py -v -m smoke
```

---

## Troubleshooting / Solución de Problemas

### "Invalid API Key" error / Error "Clave API inválida"

- Double-check you copied the entire key without extra spaces
- Verify the key is in the correct `.env` variable
- Make sure your `.env` file is in the project root folder

---

- Verifica que copiaste la clave completa sin espacios extra
- Verifica que la clave está en la variable `.env` correcta
- Asegúrate de que tu archivo `.env` está en la carpeta raíz del proyecto

### "Rate limit exceeded" / "Límite de velocidad excedido"

- Wait for your monthly quota to reset
- Use `--limit` flag to test with fewer hotels
- Consider upgrading to a paid plan if you need more requests

---

- Espera a que tu cuota mensual se reinicie
- Usa el flag `--limit` para probar con menos hoteles
- Considera actualizar a un plan de pago si necesitas más solicitudes

### Amadeus returns no hotels / Amadeus no devuelve hoteles

- The test environment has limited inventory (~21 PR hotels)
- This is normal - production requires business approval
- The cascade will use other sources for remaining hotels

---

- El ambiente de prueba tiene inventario limitado (~21 hoteles de PR)
- Esto es normal - producción requiere aprobación comercial
- El cascade usará otras fuentes para los hoteles restantes
