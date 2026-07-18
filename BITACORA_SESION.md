# Bitácora de Sesión - Trading Bot DCA
**Fecha:** 18 de julio de 2025  
**Propósito:** Punto de guardado para retomar el proyecto en un chat futuro sin perder contexto

---

## 1. RESUMEN DEL DÍA

**Qué se hizo hoy (en cristiano):**

1. **Arreglamos el bug de GitHub Actions**  
   El workflow de GitHub Actions (`.github/workflows/dca.yml`) estaba configurado para correr los domingos a las 12:00 UTC, pero **Binance Testnet bloquea las IPs de GitHub Actions** (error 451). Esto no se puede arreglar desde el código; es una restricción de red de Binance. El workflow está listo y funcionaría si no fuera por el bloqueo de IP.

2. **Creamos el acceso directo en el escritorio**  
   Script `comprar_dca.sh` (ejecutable, con `chmod +x`) que:  
   - Activa el venv (`source ~/venv/bin/activate`)  
   - Entra a `~/trading-bot`  
   - Ejecuta `python bot_dca.py`  
   - Espera `Enter` al final para que el usuario lea el resultado  
   Symlink en `~/Escritorio/Bot_DCA` → doble clic y listo. Funciona 100% en local.

3. **Arreglamos el bug del Excel bloqueado (`fcntl`)**  
   **Problema:** Si el usuario tenía `historial_dca.csv` abierto en Excel/Calc, la compra en Binance se ejecutaba bien, pero el bot crasheaba al intentar escribir el CSV (archivo bloqueado por el SO).  
   **Solución en `bot_dca.py` (función `guardar_historial`):**  
   - Import `fcntl` (módulo estándar Linux para bloqueo de archivos)  
   - Bloqueo exclusivo **no bloqueante**: `fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)`  
     - `LOCK_EX`: exclusivo (espera si está libre, falla rápido si está ocupado)  
     - `LOCK_NB`: non-blocking → **NO se cuelga esperando**, falla inmediato con `IOError`  
   - `try/finally` garantiza liberación (`LOCK_UN`) aunque falle la escritura  
   - `try/except` externo captura `IOError`/`OSError`:  
     - Imprime aviso en **ROJO**: *"⚠️ ADVERTENCIA: La compra se ejecutó, pero el Excel está abierto. Ciérralo para registrar la compra."*  
     - Loggea en `errores_dca.log` para auditoría  
     - **NO crashea el bot** (exit code 0) — la compra en Binance ya se hizo  
   **Verificación:** Bot ejecutado 16 veces en testnet, CSV actualizado correctamente. Simulación de bloqueo confirmada: detecta archivo ocupado, muestra aviso rojo, loggea, continúa sin crash.

4. **Cambiamos el bot de BTC a ETH (genérico multi-moneda)**  
   `bot_dca.py` ahora lee `PAR` desde variable de entorno (default `BTC/USDT`).  
   - Variables nuevas: `BASE_CURRENCY = PAR.split('/')[0]`, `QUOTE_CURRENCY = PAR.split('/')[1]`  
   - Funciones renombradas: `obtener_balance_base()` (antes `obtener_balance_btc()`)  
   - Variables genéricas: `cantidad_base`, `base_acumulado`, `{BASE_CURRENCY.lower()}_comprado`  
   - Historial CSV mantiene columnas `btc_comprado` / `btc_acumulado` por compatibilidad, pero guardan la moneda base actual (BTC, ETH, etc.)  
   - En `.env` basta cambiar `PAR=ETH/USDT` (o `SOL/USDT`, `BNB/USDT`, etc.) y el bot compra esa moneda.  
   **Prueba real:** Se compró ETH en testnet (~0.027 ETH por $50 a ~$1845) y quedó registrado en `historial_dca.csv` (líneas 18-24).

---

## 2. ESTADO ACTUAL DEL BOT

| Aspecto | Estado |
|---------|--------|
| **Modo de ejecución** | 100% **manual** — doble clic en `~/Escritorio/Bot_DCA` |
| **Entorno** | **Binance TESTNET** (sandbox mode, dinero ficticio) |
| **Moneda** | Configurable por `PAR` en `.env` (actual: `ETH/USDT`) |
| **Monto por compra** | `$50 USD` (configurable con `MONTO_USD`) |
| **Frecuencia** | Cuando el usuario quiera (diseñado para semanal) |
| **Historial** | `historial_dca.csv` (timestamp, precio, monto, cantidad, acumulado) |
| **Log de errores** | `errores_dca.log` (timestamp + detalle) |
| **Manejo Excel abierto** | ✅ Resuelto con `fcntl` non-blocking — no crashea, avisa en rojo |
| **GitHub Actions** | ⚠️ Configurado (`.github/workflows/dca.yml`) pero **bloqueado por IP de Binance** |
| **API Keys** | En variables de entorno (`.env` local, GitHub Secrets en Actions) — **solo testnet** |

**Archivo `.env` actual (ejemplo, claves reales en gitignore):**
```bash
API_KEY=tu_testnet_api_key
API_SECRET=tu_testnet_api_secret
MONTO_USD=50
PAR=ETH/USDT
TESTNET=true
HISTORIAL_CSV=historial_dca.csv
ERRORES_LOG=errores_dca.log
```

---

## 3. PRÓXIMOS PASOS PENDIENTES

### Fase actual: Descanso + Testnet manual (3-4 semanas)
El usuario va a **tomarse 3-4 semanas de descanso**. Durante ese tiempo:
- **1 clic semanal** en `~/Escritorio/Bot_DCA` (domingos, o cuando quiera)
- El bot compra $50 de ETH en **testnet** (dinero ficticio)
- Objetivo: acostumbrarse al hábito, verificar que no falla, ganar confianza

### Fase siguiente: Dinero real (cuando regrese)
Cuando el usuario vuelva, el plan es:

1. **Limpiar el Excel** (`historial_dca.csv`) → borrar filas de prueba, dejar solo header
2. **Bajar monto a $10 USD** por compra (menos riesgo al empezar)
3. **Crear API Keys REALES en Binance (spot)** con permisos:  
   - ✅ **Leer** (Read Info)  
   - ✅ **Spot Trading** (Enable Spot & Margin Trading)  
   - ❌ **NO** "Enable Withdrawals" (nunca dar permiso de retiro)  
   - ❌ **NO** "Enable Futures"  
   - ❌ **NO** "Enable Options"  
   - IP restrict: opcional, pero recomendable poner IP de la laptop
4. **Actualizar `.env` local** con las keys reales y `TESTNET=false`
5. **Empezar con $5,000 MXN** (≈ $250-300 USD) en spot real  
   - DCA semanal de $10 USD → ~25-30 semanas de dinero  
   - Objetivo: disciplina, quitar emoción, promediar precio de entrada
6. **Monitorear 3 meses mínimo** antes de subir monto o cambiar frecuencia

---

## 4. ARCHIVOS CLAVE DEL PROYECTO

| Archivo | Qué hace | Estado |
|---------|----------|--------|
| `bot_dca.py` | **Cerebro del bot** — compra market, guarda CSV, loggea errores, maneja `fcntl`, genérico multi-moneda | ✅ Funcional, probado 16x testnet |
| `comprar_dca.sh` | **Launcher bash** — activa venv, corre bot, espera Enter | ✅ Ejecutable, symlink en Escritorio |
| `.env` | **Variables locales** (API keys, MONTO_USD, PAR, TESTNET) — **en .gitignore** | ✅ Configurado para ETH/USDT testnet |
| `historial_dca.csv` | **Registro compras** (timestamp, precio, monto_usd, btc_comprado, btc_acumulado) | ✅ 23 filas (17 BTC + 6 ETH testnet) |
| `errores_dca.log` | **Log de errores** con timestamp (ej. Excel bloqueado) | ✅ Funcionando |
| `config.py` | Lee API keys de `os.environ` (compatible `.env` + GitHub Secrets) | ✅ Simple, sin secrets hardcodeados |
| `REGLAS.md` | **7 reglas de oro** del proyecto (no overfitting, costos reales, risk mgmt, API keys, etc.) | ✅ Fuente de verdad |
| `CONTEXTO.md` | **Bitácora maestra** completa: 11 estrategias probadas, 0 alpha real, pivot a DCA, lecciones | ✅ Documentación total |
| `.github/workflows/dca.yml` | GitHub Actions semanal (domingos 12:00 UTC) — **bloqueado por IP Binance** | ⚠️ Listo pero no usable |
| `data/` | CSVs OHLCV (1h/4h, 2-4 años, 5-20 pares) + splits in/out sample | ✅ Datos históricos listos |

---

## 5. CÓMO RETOMAR EN UN CHAT FUTURO

1. **Lee este archivo** (`BITACORA_SESION.md`) + `CONTEXTO.md` + `REGLAS.md`
2. **Verifica estado:** `cd ~/trading-bot && ./comprar_dca.sh` → debe comprar en testnet sin errores
3. **Revisa `.env`** para ver qué moneda y monto están configurados
4. **Decide siguiente acción** según la fase (descanso/testnet o dinero real)

---

> **Nota para el Alan del futuro:**  
> Si estás leyendo esto, significa que te tomaste tu descanso de 3-4 semanas.  
> El bot DCA en testnet funciona perfecto (16 compras probadas, maneja Excel abierto, multi-moneda).  
> Ahora toca decidir: ¿sigues en testnet un tiempo más o pasas a $10 USD reales con keys sin permiso de retiro?  
> Recuerda las **7 reglas en REGLAS.md** — especialmente: **nunca keys reales en git, nunca 100% capital en una orden, 3 meses paper trading mínimo antes de dinero real**.  
> El DCA no busca alpha, busca **disciplina**. Un clic a la semana. Listo.