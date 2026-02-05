# API Setup Guide / Guía de Configuración de APIs

This guide explains how to obtain free API keys to enable all price sources in Hotel Price Checker.

Esta guía explica cómo obtener claves API gratuitas para habilitar todas las fuentes de precios en Hotel Price Checker.

---

## Why do I need API keys? / ¿Por qué necesito claves API?

Hotel Price Checker searches multiple sources to find the best hotel prices. Without API keys, only **Xotelo** (TripAdvisor) is available, covering about 64% of hotels. Adding more APIs increases coverage to **97%**.

Hotel Price Checker busca en múltiples fuentes para encontrar los mejores precios de hoteles. Sin claves API, solo **Xotelo** (TripAdvisor) está disponible, cubriendo aproximadamente el 64% de los hoteles. Agregar más APIs aumenta la cobertura al **97%**.

| Source / Fuente | Coverage / Cobertura | Free Tier / Plan Gratuito |
|-----------------|---------------------|---------------------------|
| Xotelo (TripAdvisor) | ~64% | Unlimited / Ilimitado |
| SerpApi (Google Hotels) | +15% | 100/month / 100/mes |
| Apify (Booking.com) | +12% | ~1,700/month / ~1,700/mes |
| Amadeus (GDS) | +6% | 500/month / 500/mes |

---

## How to enter your keys / Cómo ingresar tus claves

1. Open Hotel Price Checker / Abre Hotel Price Checker
2. Go to the **"API Keys"** tab / Ve a la pestaña **"API Keys"**
3. Enter each key in its corresponding field / Ingresa cada clave en su campo correspondiente
4. Click **"Test"** to verify each key works / Haz clic en **"Test"** para verificar que cada clave funciona
5. Click **"Save"** to store your keys / Haz clic en **"Save"** para guardar tus claves

---

## SerpApi (Google Hotels)

**Free tier / Plan gratuito:** 100 searches per month / 100 búsquedas por mes

### English

1. Go to [https://serpapi.com](https://serpapi.com)
2. Click **"Register"** (top right corner)
3. Create an account using your email or Google
4. Check your email and click the verification link
5. Once logged in, you'll see your dashboard
6. Your **API Key** is displayed at the top of the dashboard
7. Copy the key and paste it in Hotel Price Checker

**Note:** No credit card required. Your 100 searches reset on the 1st of each month.

### Español

1. Ve a [https://serpapi.com](https://serpapi.com)
2. Haz clic en **"Register"** (esquina superior derecha)
3. Crea una cuenta usando tu email o Google
4. Revisa tu email y haz clic en el enlace de verificación
5. Una vez dentro, verás tu dashboard
6. Tu **API Key** aparece en la parte superior del dashboard
7. Copia la clave y pégala en Hotel Price Checker

**Nota:** No se requiere tarjeta de crédito. Tus 100 búsquedas se reinician el 1ro de cada mes.

---

## Apify (Booking.com)

**Free tier / Plan gratuito:** $5 in credits per month (~1,700 searches) / $5 en créditos por mes (~1,700 búsquedas)

### English

1. Go to [https://apify.com](https://apify.com)
2. Click **"Sign up"** (top right corner)
3. Create an account using email, Google, or GitHub
4. Check your email and click the verification link
5. Once logged in, click your profile icon (top right)
6. Select **"Settings"**
7. Click **"Integrations"** in the left menu
8. Find **"Personal API Token"**
9. Click **"Copy"** to copy your token
10. Paste the token in Hotel Price Checker

**Note:** No credit card required. Each hotel search costs about $0.003, so $5 covers approximately 1,700 searches per month.

### Español

1. Ve a [https://apify.com](https://apify.com)
2. Haz clic en **"Sign up"** (esquina superior derecha)
3. Crea una cuenta usando email, Google o GitHub
4. Revisa tu email y haz clic en el enlace de verificación
5. Una vez dentro, haz clic en tu icono de perfil (arriba a la derecha)
6. Selecciona **"Settings"**
7. Haz clic en **"Integrations"** en el menú izquierdo
8. Encuentra **"Personal API Token"**
9. Haz clic en **"Copy"** para copiar tu token
10. Pega el token en Hotel Price Checker

**Nota:** No se requiere tarjeta de crédito. Cada búsqueda de hotel cuesta aproximadamente $0.003, así que $5 cubre aproximadamente 1,700 búsquedas por mes.

---

## Amadeus (GDS - Travel Agent System)

**Free tier / Plan gratuito:** 500 searches per month (test environment) / 500 búsquedas por mes (ambiente de prueba)

### English

1. Go to [https://developers.amadeus.com](https://developers.amadeus.com)
2. Click **"Register"** or **"Get Started"**
3. Fill in the registration form:
   - Your name
   - Email address
   - Company name (you can use your own name)
   - Create a password
4. Check your email and click the verification link
5. Log in and click **"My Self-Service Workspace"**
6. Click **"Create new app"**
7. Enter an app name (e.g., "Hotel Price Checker")
8. Click **"Create"**
9. Your app page will show two values:
   - **API Key** (also called Client ID)
   - **API Secret** (also called Client Secret)
10. Copy both values and paste them in Hotel Price Checker

**Note:** The free tier uses a test environment with limited hotels (~21 in Puerto Rico). This is normal - other APIs will cover the remaining hotels.

### Español

1. Ve a [https://developers.amadeus.com](https://developers.amadeus.com)
2. Haz clic en **"Register"** o **"Get Started"**
3. Completa el formulario de registro:
   - Tu nombre
   - Dirección de email
   - Nombre de empresa (puedes usar tu propio nombre)
   - Crea una contraseña
4. Revisa tu email y haz clic en el enlace de verificación
5. Inicia sesión y haz clic en **"My Self-Service Workspace"**
6. Haz clic en **"Create new app"**
7. Ingresa un nombre para la app (ej: "Hotel Price Checker")
8. Haz clic en **"Create"**
9. La página de tu app mostrará dos valores:
   - **API Key** (también llamado Client ID)
   - **API Secret** (también llamado Client Secret)
10. Copia ambos valores y pégalos en Hotel Price Checker

**Nota:** El plan gratuito usa un ambiente de prueba con hoteles limitados (~21 en Puerto Rico). Esto es normal - las otras APIs cubrirán los hoteles restantes.

---

## Troubleshooting / Solución de Problemas

### "Invalid API Key" / "Clave API inválida"

- Make sure you copied the entire key without extra spaces
- Try generating a new key from the provider's website

---

- Asegúrate de que copiaste la clave completa sin espacios extra
- Intenta generar una nueva clave desde el sitio web del proveedor

### "Test failed" / "Prueba fallida"

- Check your internet connection
- The service might be temporarily unavailable, try again later

---

- Verifica tu conexión a internet
- El servicio podría estar temporalmente no disponible, intenta más tarde

### Not finding all hotels / No encuentra todos los hoteles

- This is normal - some small hotels aren't listed on major platforms
- The cascade system finds prices for ~97% of hotels
- Hotels without online presence may need manual price entry

---

- Esto es normal - algunos hoteles pequeños no están listados en plataformas grandes
- El sistema encuentra precios para ~97% de los hoteles
- Hoteles sin presencia en línea pueden necesitar entrada manual de precios

---

## Quick Reference / Referencia Rápida

| API | Website | What to copy / Qué copiar |
|-----|---------|---------------------------|
| SerpApi | serpapi.com | API Key |
| Apify | apify.com | Personal API Token |
| Amadeus | developers.amadeus.com | API Key + API Secret |
