# Trading Bot DCA - Dollar Cost Averaging para Binance

Bot simple y disciplinado para compra periódica de criptomonedas (DCA) en Binance Testnet/Mainnet.

## Estructura del proyecto

```
~/trading-bot/
├── README.md                  # Este archivo
├── REGLAS.md                  # Reglas de oro del proyecto (obligatorias)
├── CONTEXTO.md                # Bitácora maestra: estrategias probadas, lecciones, estado
├── BITACORA_SESION.md         # Punto de guardado para retomar el proyecto
├── .env                       # Variables locales (API keys, MONTO_USD, PAR, TESTNET) — en .gitignore
├── .gitignore                 # Excluye .env, venv/, __pycache__/
├── config.py                  # Lee API keys de os.environ (compatible .env + GitHub Secrets)
├── venv/                      # Entorno virtual Python 3.11
├── bot_dca/
│   ├── bot_dca.py             # Cerebro: compra market, guarda CSV, loggea errores, fcntl, multi-moneda
│   └── comprar_dca.sh         # Launcher bash: activa venv, corre bot, espera Enter
├── estrategias/
│   ├── descartadas/           # Todas las estrategias v1-v8 probadas y descartadas
│   └── activas/               # Aquí irán las nuevas (v9 grid bot)
├── datos/
│   ├── descarga/              # Scripts descargar_*.py, split_*.py
│   └── historicos/            # CSVs OHLCV (1h/4h, 2-4 años, 5-20 pares) + in/out sample
├── resultados/
│   ├── historial_dca.csv      # Registro compras (timestamp, precio, monto, cantidad, acumulado)
│   └── errores_dca.log        # Log errores con timestamp (ej. Excel bloqueado)
└── .github/workflows/dca.yml  # GitHub Actions semanal (bloqueado por IP Binance testnet)
```

## Uso rápido (modo manual actual)

```bash
# Opción 1: Doble clic en el acceso directo del escritorio
~/Escritorio/Bot_DCA

# Opción 2: Terminal
cd ~/trading-bot
./bot_dca/comprar_dca.sh
```

El script:
1. Activa el venv (`~/venv`)
2. Carga variables de `.env`
3. Ejecuta `python bot_dca/bot_dca.py`
4. Compra **una vez** en Binance Testnet (orden market)
5. Guarda en `resultados/historial_dca.csv`
6. Loggea errores en `resultados/errores_dca.log`
7. Espera `Enter` para cerrar (puedes leer el resultado)

## Configuración (`.env`)

```bash
API_KEY=tu_testnet_api_key
API_SECRET=tu_testnet_api_secret
MONTO_USD=50           # USD por compra
PAR=ETH/USDT           # Par a comprar (BTC/USDT, ETH/USDT, SOL/USDT, etc.)
TESTNET=true           # true = testnet, false = mainnet real
HISTORIAL_CSV=resultados/historial_dca.csv
ERRORES_LOG=resultados/errores_dca.log
```

**Seguridad:** `.env` está en `.gitignore`. **Nunca** subas API keys reales a git.

## Estado actual

- ✅ **Bot DCA funcionando 100% en testnet** (16+ compras probadas)
- ✅ Maneja Excel/CSV abierto sin crashear (`fcntl` non-blocking)
- ✅ Multi-moneda configurable por `PAR` en `.env`
- ⚠️ GitHub Actions configurado pero **bloqueado por IP** (Binance testnet bloquea IPs de GitHub)
- 📋 Próximo: 3-4 semanas testnet manual → dinero real $10/semana → 3 meses paper trading

## Reglas del proyecto (ver `REGLAS.md`)

1. No overfitting (out-sample solo 1 vez al final)
2. No look-ahead bias (solo velas cerradas)
3. Costos reales: 0.1% comisión + 0.05% slippage
4. Datos: 1-4 años, multi-régimen
5. Risk mgmt: SL/TP, sizing <100%, max DD
6. API keys solo testnet en git
7. 3 meses paper trading mínimo antes de real
8. **Grid bot: rango basado en volatilidad real (ATR/STD), nunca "a ojo"**
9. **Grid bot: stop-loss fuera del rango inferior**
10. **Grid bot: fricción comisiones — ganancia por nivel > 2-3x comisión ida+vuelta**
11. **Grid bot: detección tendencia (ADX/ruptura rango) → pausa/alerta automática**

## Datos históricos disponibles

En `datos/historicos/`:
- 16+ pares, timeframes 1h y 4h
- 2 y 4 años de historia
- Splits in/out sample (70/30 cronológico)

## Cómo retomar en un chat futuro

1. Lee `BITACORA_SESION.md` + `CONTEXTO.md` + `REGLAS.md`
2. Verifica estado: `cd ~/trading-bot && ./bot_dca/comprar_dca.sh` → debe comprar en testnet sin errores
3. Revisa `.env` para ver qué moneda y monto están configurados
4. Decide siguiente acción según la fase (descanso/testnet o dinero real)