# Trading Bot DCA — Dollar-Cost Averaging para Binance

Bot disciplinado de compra periódica (DCA) para criptomonedas en Binance Testnet/Mainnet.
Diseñado para eliminar el error humano de *timing* y emoción: una compra fija, sin decisión de precio.

---

## Qué hace este bot

- **Ejecuta una compra market** de `MONTO_USD` en el par `PAR` (ej: `ETH/USDT`)
- **Guarda historial** en CSV: timestamp, precio, monto, cantidad, balance acumulado
- **Loggea errores** con timestamp (archivo bloqueado, red, fondos insuficientes, etc.)
- **Maneja Excel/CSV abierto sin crashear** — usa `fcntl` non-blocking en Linux
- **Multi-moneda configurable** — cambia `PAR` en `.env` (BTC, ETH, SOL, BNB, etc.)
- **Solo testnet por defecto** — `TESTNET=true` usa sandbox de Binance (dinero ficticio)

---

## Por qué DCA y no estrategias direccionales (v1–v9)

Tras 11 variantes probadas (SMA crossover, RSI mean-reversion, arbitraje spot/triangular) **ninguna generó alpha real out-of-sample**:

| Estrategia | Trades/par | In-sample | Out-sample | Estado |
|------------|------------|-----------|------------|--------|
| v1 SMA 20/50 (1h) | 192 | −45% | — | ❌ Ruido puro |
| v2 SMA + SMA200 + SL/TP (1h) | 86 | −3% | — | ❌ Sin edge |
| v3 SMA + SMA200 (4h) | 20 | +5% | +0.01% | ❌ Overfitting |
| v3 multi-par (4h) | 4–11 | +2.5% | Ranking invirtió (ρ=−0.58) | ❌ Selección de sobrevivientes |
| v4–v6 RSI mean-rev | 3–31 | −1% a +0% | No concluyente (<30 trades) | ⚠️ Sample insuficiente |
| v7 Arbitraje spot 3 exchanges | 30 obs | 0% > 0.3% umbral | — | ❌ Spreads ultra-ajustados |
| v8 Arbitraje triangular | 30 obs | −0.32% (solo comisiones) | — | ❌ Mercado eficiente |

**Lecciones clave** (documentadas en `CONTEXTO.md` y `REGLAS.md`):
1. **Regla de 30+ trades**: <30 trades/par → no es estadísticamente confiable
2. **Out-sample es ley**: solo se valida UNA vez al final; v3 pasó in-sample pero falló out
3. **Costos reales son letales**: 0.1% fee + 0.05% slippage destruyen alta frecuencia
4. **Más datos ≠ mejor resultado**: 4 años vs 2 años no arregló la lógica base
5. **Simplicidad > complejidad**: añadir parámetros = más overfitting

**Pivot**: El objetivo cambió de "ganarle al mercado" a "automatizar disciplina". DCA no busca alpha, busca **consistencia sin emoción**.

---

## Estructura del proyecto

```
~/trading-bot/
├── README.md                  # Este archivo
├── LICENSE                    # MIT License
├── REGLAS.md                  # 11 reglas de oro (obligatorias)
├── CONTEXTO.md                # Bitácora maestra: 11 estrategias, lecciones, pivot
├── BITACORA_SESION.md         # Punto de guardado para retomar el proyecto
├── .gitignore                 # Excluye .env, venv/, __pycache__/, datos/, resultados/
├── .env                       # Variables locales (API keys, MONTO_USD, PAR, TESTNET) — en .gitignore
├── config.py                  # Lee API keys de os.environ (compatible .env + GitHub Secrets) — en .gitignore
├── bot_dca/
│   ├── bot_dca.py             # Cerebro: compra market, guarda CSV, loggea, fcntl, multi-moneda
│   └── comprar_dca.sh         # Launcher bash: activa venv, corre bot, espera Enter
├── estrategias/
│   ├── descartadas/           # 16 archivos: v1–v8 + evaluaciones (evidencia del proceso)
│   └── activas/               # Placeholder para futuras estrategias (grid bot v9)
├── datos/
│   └── descarga/              # Scripts descargar_*.py, split_*.py (generan CSVs en datos/historicos/)
├── resultados/                # Generados en runtime (en .gitignore)
│   ├── historial_dca.csv      # Registro compras (timestamp, precio, monto, cantidad, acumulado)
│   └── errores_dca.log        # Log errores con timestamp
├── scripts/
│   └── test_conexion.py       # Prueba rápida de conectividad Binance testnet
└── .github/workflows/
    └── dca.yml.disabled       # GitHub Actions semanal (desactivado: Binance bloquea IPs de GH Actions)
```

---

## Inicio rápido

### 1. Requisitos
- Python 3.11+
- Entorno virtual en `~/venv` (o ajusta la ruta en `comprar_dca.sh`)
- Dependencias: `ccxt`, `pandas`

```bash
# Crear venv e instalar
python3 -m venv ~/venv
source ~/venv/bin/activate
pip install ccxt pandas
```

### 2. Configurar `.env` (en la raíz del repo, **nunca en git**)

```bash
cp .env.example .env   # o crea uno nuevo
```

```ini
# .env — SOLO TESTNET MIENTRAS APRENDES
API_KEY=tu_testnet_api_key
API_SECRET=tu_testnet_api_secret
MONTO_USD=50
PAR=ETH/USDT
TESTNET=true
HISTORIAL_CSV=resultados/historial_dca.csv
ERRORES_LOG=resultados/errores_dca.log
```

> **Seguridad**: `.env` y `config.py` están en `.gitignore`. **Nunca** subas API keys reales. Solo testnet en este repo.

### 3. Ejecutar (modo manual actual)

```bash
# Opción 1: Script directo
cd ~/trading-bot
./bot_dca/comprar_dca.sh

# Opción 2: Python directo (venv activado)
source ~/venv/bin/activate
python bot_dca/bot_dca.py
```

El script:
1. Activa el venv
2. Carga `.env`
3. Ejecuta **una compra** en Binance Testnet
4. Guarda en `resultados/historial_dca.csv`
5. Loggea errores en `resultados/errores_dca.log`
6. Espera `Enter` para cerrar (lee el resultado)

---

## GitHub Actions (desactivado)

`/.github/workflows/dca.yml.disabled` está listo para correr domingos 12:00 UTC, pero **Binance Testnet bloquea las IPs de GitHub Actions (error 451)**.

**Opciones para reactivar**:
- **VPS barato** (Hetzner $4.50/mes, RackNerd $10–15/año) — IP no bloqueada
- **Self-hosted runner** en tu laptop/otra máquina — usa tu IP local
- **Aceptar modo 100% manual** (doble clic en `comprar_dca.sh` cuando quieras)

Para reactivar: renombra a `dca.yml` y configura `API_KEY` / `API_SECRET` en GitHub Secrets.

---

## Pasar a dinero real (cuando estés listo)

**Solo después de 3–4 semanas en testnet sin errores**:

1. Limpia `historial_dca.csv` (borra filas de prueba, deja header)
2. Baja monto a `$10 USD` (`MONTO_USD=10`)
3. Crea **API Keys REALES en Binance Spot** con permisos:
   - ✅ **Read Info**
   - ✅ **Spot Trading**
   - ❌ **NO** Enable Withdrawals
   - ❌ **NO** Futures / Options
   - IP restrict: tu IP (recomendado)
4. Actualiza `.env`:
   ```ini
   API_KEY=tu_real_api_key
   API_SECRET=tu_real_secret
   TESTNET=false
   MONTO_USD=10
   ```
5. Empieza con ~$250–300 USD en spot real
6. **Monitorea 3 meses mínimo** antes de cambiar monto/frecuencia

> Ver `REGLAS.md` reglas 6–7: **nunca keys reales en git, nunca 100% capital en una orden, 3 meses paper trading mínimo**.

---

## Documentación clave

| Archivo | Qué contiene |
|---------|--------------|
| `REGLAS.md` | 11 reglas de oro (no overfitting, costos reales, risk mgmt, grid bot guardrails) |
| `CONTEXTO.md` | Bitácora completa: 11 estrategias probadas, tabla resultados, lecciones reutilizables |
| `BITACORA_SESION.md` | Punto de guardado: estado actual, próximos pasos, cómo retomar |
| `estrategias/descartadas/` | 16 archivos — evidencia del proceso de investigación (no borrar) |

---

## Estado actual

- ✅ **Bot DCA funcional 100% en testnet** (16+ compras probadas)
- ✅ Multi-moneda por `PAR` en `.env`
- ✅ Maneja Excel/CSV abierto sin crash (`fcntl` non-blocking)
- ✅ Historial CSV + log de errores automático
- ⚠️ GitHub Actions configurado pero **bloqueado por IP Binance**
- 📋 **Fase actual**: 3–4 semanas testnet manual → dinero real $10/semana → 3 meses paper trading

---

## Licencia

MIT License — ver `LICENSE`.

---

## Autor

Alan Antonio Molina Villar — proyecto de aprendizaje/portafolio técnico.  
Todo el código técnico desarrollado con asistencia de IA (Hermes Agent).  
Decisiones de validación y rigor supervisadas por revisión humana (Claude).
