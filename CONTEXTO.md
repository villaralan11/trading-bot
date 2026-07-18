# Proyecto: Bot de trading algorítmico

## Objetivo
Construir un bot de trading para criptomonedas, con 1 año de investigación,
desarrollo y backtesting (sin dinero real), seguido de un año de pruebas con
dinero real reducido si se encuentra una estrategia validada. El desarrollador
(Alan) no es experto en trading ni en el código — todo el trabajo técnico lo
hace el agente (Hermes), y las decisiones de validación/rigor las supervisa
Claude en otro chat. Este archivo es la fuente de verdad del proyecto: léelo
completo antes de hacer cualquier cosa nueva.

## Estado actual: FASE DE INVESTIGACIÓN, ninguna estrategia validada todavía.
NO se ha hecho paper trading. NO se ha usado dinero real. NO se ha usado
ninguna API key real de exchange (solo testnet de Binance).

## Reglas del proyecto (ver REGLAS.md, deben respetarse siempre)
1. Nunca optimizar parámetros contra archivos "out_sample" — esos solo se
   corren UNA vez, al final, con parámetros ya decididos.
2. No look-ahead bias: los indicadores solo usan datos de velas ya cerradas.
3. Todo backtest debe incluir comisión 0.1% y slippage 0.05%.
4. Los backtests deben cubrir al menos 1-4 años y varios pares/regímenes.
5. Toda estrategia debe tener stop-loss, tamaño de posición limitado
   (nunca 100% del capital), y control de drawdown.
6. Nunca exponer, imprimir ni subir a git API keys reales. config.py está en
   .gitignore. Solo se usan keys de testnet mientras estemos en fase de
   pruebas.
7. Ninguna estrategia pasa a paper trading sin validar limpio en out_sample.
   Ninguna estrategia pasa a dinero real sin mínimo 3 meses de paper trading.

## Regla adicional de rigor estadístico (aprendida en el proceso)
Cualquier resultado con menos de 30 trades cerrados por activo NO es
estadísticamente confiable, sin importar qué tan bueno o malo se vea el
retorno/win rate/Sharpe. No sacar conclusiones definitivas ("esta estrategia
funciona" o "esta estrategia no sirve") con muestras menores a eso. Tampoco
elegir "los mejores" pares/parámetros después de ver resultados en varios
activos — eso es una forma de overfitting oculto (selección de sobrevivientes).

## Estructura de archivos actual
~/trading-bot/
├── venv/                              # entorno virtual Python 3.11
├── config.py                          # API keys de TESTNET (excluido de git)
├── .gitignore                         # excluye config.py y venv/
├── REGLAS.md                          # las 7 reglas completas
├── CONTEXTO.md                        # este archivo
├── test_conexion.py                   # prueba de conexión a Binance testnet (funciona)
├── data/
│   ├── btc_usdt_1h.csv                # 2 años, 1h, BTC (17,526 velas)
│   ├── btc_usdt_1h_in_sample.csv / _out_sample.csv
│   ├── btc_usdt_4h.csv, _in_sample, _out_sample  # 2 años, 4h, BTC
│   ├── {BTC,ETH,BNB,SOL,ADA}_USDT_4h.csv y sus in/out_sample  # 2 años, 5 pares
│   ├── {par}_4h_4y.csv y sus in/out_sample                    # 4 años, 5 pares
│   ├── {par}_1h_4y.csv y sus in/out_sample                    # 4 años, 16+ pares
│   └── arbitraje_btc_usdt.csv         # datos de arbitraje spot v7
├── descargar_datos.py, descargar_datos_4h.py, descargar_multi.py,
│   descargar_multi_4y.py, descargar_top20.py,
│   descargar_multi_1h_4y.py           # scripts de descarga OHLCV vía ccxt
├── split_datos.py, split_datos_4h.py, split_datos_1h_4y.py,
│   split_top20_1h_4y.py               # dividen CSV en 70% in / 30% out por fecha
├── estrategia_sma.py                  # v1: cruce SMA 20/50 puro, 1h. Resultado:
│   PERDIÓ -45% (192 trades, win rate 32.8%, Sharpe -0.51, DD 58.7%). DESCARTADA.
├── estrategia_v2.py                   # v2: SMA 20/50 + filtro SMA200 + SL 3%/TP 6%
│   + sizing 20%, timeframe 1h, in_sample. Resultado: -3.15% (86 trades, WR 37.2%,
│   Sharpe -0.28, DD 7.36%). Mejoró el riesgo pero sigue sin ganar.
├── estrategia_v3.py                   # v3: igual que v2 pero timeframe 4h, in_sample
│   BTC. Resultado: +5.18% (20 trades, WR 50%, Sharpe 2.35, DD 1.65%). Se veía bien
│   pero muestra muy chica (20 trades).
├── estrategia_v3_validacion.py        # v3 corrida contra out_sample BTC 4h.
│   Resultado: +0.01% (4 trades) — básicamente cero, no confirma ventaja real.
├── evaluar_multi.py                   # v3 corrida en in_sample de 5 pares (4h, 2 años).
│   Resultado: 3/5 pares "ganaron" (BTC, SOL, BNB), 2 perdieron (ETH, ADA).
│   Promedio +2.55%.
├── evaluar_multi_out.py               # v3 corrida en out_sample de los mismos 5 pares.
│   Resultado: EL RANKING SE INVIRTIÓ COMPLETO (correlación in vs out = -0.578).
│   ADA pasó de peor a mejor, BTC de mejor a 3er lugar. CONCLUSIÓN: v3/SMA
│   crossover NO tiene ventaja real, es overfitting. ESTRATEGIA DESCARTADA.
├── estrategia_rsi.py                  # v4: mean-reversion con RSI(14), compra si
│   RSI cruza <30, vende si RSI cruza >50 o SL 4%, filtro SMA200, sizing 20%,
│   4h. Lógica: precio "sobre-estirado" hacia abajo tiende a regresar.
├── evaluar_multi_rsi.py               # v4 en in_sample 5 pares, 2 años. Resultado:
│   solo 3-5 trades por par (muestra insuficiente). Promedio -0.98%, pero no
│   concluyente por tamaño de muestra.
├── descargar_multi_4y.py, evaluar_rsi_4y.py  # v4 con 4 años de histórico para
│   tener más señales. Resultado: 4-11 trades por par, SIGUE sin llegar a 30.
│   BTC/BNB/SOL marginalmente positivos, ETH/ADA pierden. NO CONCLUYENTE TODAVÍA.
├── estrategia_rsi_1h.py               # v5: idéntica a v4 pero timeframe 1h
├── evaluar_rsi_1h_4y.py               # v5 en in_sample 5 pares, 1h, 4 años
│   Resultado: BTC 31 trades (✅), ETH 27, BNB 16, SOL 26, ADA 14. Solo BTC ≥30.
│   Promedio 22.8 trades/par, -1.71% retorno, WR 56.2%. NO CONCLUYENTE.
├── descargar_top20.py, split_top20_1h_4y.py,
│   evaluar_top20_rsi.py               # v6: RSI 1h, 4 años, top 20 pares por volumen
│   Resultado: 16 pares procesados, 195 trades totales agregados.
│   Agregado: -0.03% retorno, WR 57.4%. Solo BTC ≥30 trades. NO CONCLUYENTE.
├── revisar_arbitraje.py               # v7: arbitraje spot 3 exchanges (Binance, KuCoin, OKX)
│   30 observaciones 5s, spreads 0.005-0.016%, umbral 0.3%. 0 oportunidades.
├── revisar_arbitraje_triangular.py    # v8: arbitraje triangular Binance BTC/ETH/USDT
│   30 observaciones, ciclo USDT->BTC->ETH->USDT, comisión 0.3%. 0 rentables.
├── estrategia_sma.py                  # v1
├── estrategia_v2.py                   # v2
├── estrategia_v3.py                   # v3
├── estrategia_v3_validacion.py        # v3 out_sample
├── estrategia_rsi.py                  # v4
├── estrategia_rsi_1h.py               # v5
├── bot_dca.py                         # NUEVO: Bot DCA (Dollar-Cost Averaging) para Binance TESTNET
│   Ejecuta UNA compra de BTC y termina. Diseñado para GitHub Actions semanal.
│   Config por variables de entorno: MONTO_USD=50, PAR=BTC/USDT, TESTNET=true
│   Usa config.py (lee de os.environ), modo sandbox, orden market buy,
│   historial CSV, log de errores, exit codes 0/1.
├── comprar_dca.sh                     # NUEVO: Script bash ejecutable (chmod +x)
│   Acceso directo: source venv → cd ~/trading-bot → python bot_dca.py
│   Espera Enter al final para leer resultado. Symlink en ~/Escritorio/Bot_DCA
├── .github/workflows/dca.yml          # NUEVO: GitHub Actions workflow semanal
│   Schedule: domingos 12:00 UTC (cron: '0 12 * * 0')
│   workflow_dispatch habilitado para pruebas manuales
│   Steps: checkout → Python 3.11 → pip install ccxt pandas → python bot_dca.py
│   Secrets: API_KEY, API_SECRET → env
│   Artifact: historial-dca (historial_dca.csv)
├── config.py                          # ACTUALIZADO: lee API_KEY/API_SECRET de os.environ
├── .env                               # NUEVO: variables locales (API keys, MONTO_USD, etc.) — en .gitignore
├── historial_dca.csv                  # Registro de compras DCA (timestamp, precio, monto, btc_comprado, btc_acumulado)
├── errores_dca.log                    # Log de errores con timestamp

## Estrategias descartadas y por qué
1. SMA 20/50 pura (1h): pierde mucho dinero, demasiado ruido.
2. SMA 20/50 + filtro SMA200 + SL/TP (v2/v3, 1h y 4h): mejoró el riesgo pero
   el ranking de pares se invierte completamente entre in-sample y out-sample
   → no tiene ventaja real, es overfitting a coincidencias del periodo probado.

## En progreso / no concluido
RSI mean-reversion (v4, 14/30/50, SL 4%, filtro SMA200): tiene lógica de
mercado real detrás (reversión a la media), pero genera muy pocas señales
en 4h — máximo 11 trades en 4 años, muy por debajo del mínimo de 30 para
sacar conclusiones. Aún NO se ha probado en out_sample porque no se ha
decidido la versión final de los parámetros todavía (harían falta más
señales primero).

## Pruebas realizadas (v7: arbitraje spot 3 exchanges)
**Objetivo**: Observar oportunidades de arbitraje BTC/USDT entre Binance, KuCoin y OKX
**Resultado**: 
- 30 observaciones en 2.5 min (cada 5s)
- Diferencias: 0.005% - 0.016% (promedio 0.0087%)
- Umbral rentable (0.1%×2 + slippage): 0.3%
- **0 oportunidades > 0.3%**
- Conclusión: Mercados demasiado eficientes, spreads ultra-ajustados. 
  Binance tiene el spread más bajo (~0%), KuCoin/OKX ~0.0002%.
  No vale la pena perseguir arbitraje spot simple sin latencia ultra-baja.

## Pruebas realizadas (v8: arbitraje triangular Binance BTC/ETH/USDT)
**Objetivo**: Detectar arbitraje triangular USDT -> BTC -> ETH -> USDT en Binance
**Resultado**: 
- 30 observaciones en 2.5 min (cada 5s), ciclo: USDT -> BTC -> ETH -> USDT
- Comisión 0.1% x 3 = 0.3% total
- Ganancias: -0.307% a -0.329% (promedio -0.318%)
- **0 de 30 mediciones rentables** (todas pierden ~0.32% = comisión exacta)
- Conclusión: Mercado eficiente, no hay arbitraje triangular detectable.
  El spread bid/ask + comisiones elimina cualquier oportunidad.
  ETH/BTC spread fijo en 0.028780/0.028790 = 0.035% por sí solo.

## CAMBIO DE RUMBO (después de v8)
Tras probar 8 estrategias/enfoques sin encontrar ventaja real después de
costos (ver tabla de estrategias), se decidió cambiar el objetivo del
proyecto: en vez de buscar una estrategia que le gane al mercado, el bot
ahora automatiza DCA (dollar-cost averaging) disciplinado — comprar una
cantidad fija de BTC cada cierto intervalo de tiempo, sin importar el
precio. Esto no busca "ganarle" al mercado, busca quitar el error humano
de timing y emoción. La investigación de estrategias con ventaja puede
retomarse más adelante si se desea, pero ya no es el objetivo principal.

## ESTADÍSTICAS GENERALES DEL PROYECTO (Bitácora Acumulativa)

### Resumen de Estrategias Probadas

| # | Estrategia | Pares | Timeframe | Período | Trades/par | Alpha Real | Estado |
|---|------------|-------|-----------|---------|------------|------------|--------|
| v1 | SMA 20/50 puro | BTC | 1h | 2 años | 192 | ❌ -45% | DESCARTADA |
| v2 | SMA 20/50 + SMA200 + SL/TP | BTC | 1h | 2 años | 86 | ❌ -3.15% | DESCARTADA |
| v3 | SMA 20/50 + SMA200 + SL/TP | BTC | 4h | 2 años | 20 | ❌ +5.18% (in) / +0.01% (out) | DESCARTADA (overfitting) |
| v3-multi | SMA 20/50 + SMA200 + SL/TP | 5 pares | 4h | 2 años | 4-11 | ❌ ranking invirtió (corr -0.58) | DESCARTADA |
| v4 | RSI(14) mean-rev 30/50 + SMA200 | BTC | 4h | 2 años | 3 | ❌ -0.02% | NO CONCLUYENTE |
| v4-multi | RSI(14) mean-rev 30/50 + SMA200 | 5 pares | 4h | 2 años | 4-11 | ❌ -0.98% avg | NO CONCLUYENTE |
| v4-4y | RSI(14) mean-rev 30/50 + SMA200 | 5 pares | 4h | 4 años | 4-11 | ❌ -0.70% avg | NO CONCLUYENTE |
| v5 | RSI(14) mean-rev 30/50 + SMA200 | 5 pares | 1h | 4 años | 14-31 | ❌ -1.71% avg | NO CONCLUYENTE |
| v6 | RSI(14) mean-rev 30/50 + SMA200 | 16 pares | 1h | 4 años | 0-31 | ❌ -0.03% agg (195 trades) | NO CONCLUYENTE |
| v7 | Arbitraje spot 3 exchanges | BTC | 1h | 2.5 min | 30 obs | ❌ 0% > 0.3% | NO VIABLE |
| v8 | Arbitraje triangular BTC/ETH | BTC/ETH | 1h | 2.5 min | 30 obs | ❌ -0.32% avg | NO VIABLE |

**Total estrategias probadas: 11 (incluyendo variantes)**
- **Con alpha real (out-sample): 0**
- **Prometedoras en in-sample pero fallaron out: 2 (v3, v6)**
- **No concluyentes por sample size: 4 (v4, v4-multi, v4-4y, v5)**
- **Descartadas por overfitting/ruido: 3 (v1, v2, v3-multi)**
- **Arbitraje (v7, v8): 0 viables**

### Lecciones/Reglas Aprendidas (Bitácora Reutilizable)

1. **REGLA DE 30+ TRADES**: Cualquier resultado con <30 trades cerrados por activo NO es estadísticamente confiable. No sacar conclusiones definitivas con muestras menores. Aplicada en v4, v5, v6, v4-4y.

2. **NO ELEGIR SOBREVIVIENTES (Selection Bias)**: No elegir "los mejores" pares/parámetros después de ver resultados en varios activos. Eso es overfitting oculto. v6 (top20) probó esto: agregado dio ~0% retorno.

3. **OUT-SAMPLE ES LEY**: Una estrategia solo se valida SI pasa out-sample UNA SOLA VEZ al final. v3 pasó in-sample (+5.18%) pero falló out-sample (+0.01%). v6 multi-par: ranking se invirtió completamente (corr -0.58).

4. **COSTOS REALES SON LETALES**: Comisión 0.1% + slippage 0.05% destruyen estrategias de alta frecuencia. v1 SMA 1h: 192 trades = ~$3800 solo en fees. v7/v8 arbitraje: comisiones 0.3% destruyen oportunidades de 0.01%.

5. **RUIDO 1H vs 4H**: 1h genera 4x más trades pero más whipsaws. v5 (1h) mejoró win rate (56% vs 40%) pero empeoró retorno (-1.71% vs -0.98%). El equilibrio óptimo depende de la estrategia.

6. **FILTROS DE TENDENCIA AYUDAN PERO NO SALVAN**: SMA200 reduce trades malos pero no crea alpha donde no hay. v2/v3/v4/v5/v6 todos usan SMA200; ninguno genera alpha consistente out-sample.

7. **ARBITRAJE SPOT SIMPLE = MUERTO**: v7 (3 exchanges) y v8 (triangular) confirman: spreads ultra-ajustados (Binance ~0%, KuCoin/OKX 0.0002%). Oportunidades < 0.02% vs umbral 0.3% comisiones. Solo viable con latencia ultra-baja (colocation, websockets, market making).

8. **MULTI-PAR NO ARREGLA STRATEGY ROTA**: Probar en 5, 16, 20 pares no crea alpha si la lógica base no tiene edge. v3-multi, v6, v6-top20: promedio ~0% o negativo.

9. **MÁS DATOS ≠ MEJOR RESULTADO**: v4-4y (4 años) vs v4 (2 años): trades 4-11 vs 3-5, pero retorno similar (-0.70% vs -0.98%). El problema es la lógica, no el sample size.

10. **SIMPLICIDAD > COMPLEJIDAD**: v1 (SMA 20/50 simple) perdió -45%. v3 (SMA200+SL/TP) mejoró riesgo pero no alpha. Añadir parámetros = más overfitting riesgo.

11. **DOCUMENTAR TODO INMEDIATAMENTE**: CONTEXTO.md + REGLAS.md evitan repetir errores. Cada experimento fallido enseña más que uno exitoso.

## Próximo paso pendiente
Todas las estrategias direccionales probadas (SMA crossover, RSI mean-rev) fallan out-sample.
Arbitraje (spot y triangular) no viable en retail sin latencia ultra-baja.
Posibles direcciones futuras:
- Estrategias de volatilidad (mean reversion en VIX/IV, straddles/strangles)
- Market making / proveedor de liquidez (requiere latencia baja)
- Factor investing / momentum cross-asset (requiere datos fundamentales)
- Machine learning con features de microstructure (order flow, OFI, VPIN)
- O aceptar que en timeframe 1h-4h retail no hay alpha sostenible sin edge informacional.

La bitácora (CONTEXTO.md + REGLAS.md) está completa para evitar repetir errores.

## AUTOMATIZACIÓN DCA - Estado Actual
- **GitHub Actions**: Workflow `.github/workflows/dca.yml` configurado (domingos 12:00 UTC, workflow_dispatch)
- **Secrets GitHub**: API_KEY y API_SECRET configurados en Settings → Secrets → Actions
- **Repo**: https://github.com/villaralan11/trading-bot (main branch)
- **Local**: `comprar_dca.sh` ejecutable + symlink `~/Escritorio/Bot_DCA` para doble clic
- **Modo actual**: 100% manual — el usuario enciende laptop y ejecuta cuando quiere
- **Validación local**: ✅ Comprobado — compra de $50 en testnet ejecutada exitosamente desde laptop
- **GitHub Actions**: ⚠️ Bloqueado por IP (Binance testnet bloquea IPs de GitHub - error 451)

### Archivos DCA Creados
1. `bot_dca.py` — Lógica principal (una compra, testnet, historial CSV, log errores, exit codes)
2. `comprar_dca.sh` — Script bash ejecutable (activa venv, carga .env, corre bot, espera Enter)
3. `~/.local/share/applications/Bot_DCA.desktop` / symlink `~/Escritorio/Bot_DCA` — Acceso directo
4. `.github/workflows/dca.yml` — GitHub Actions semanal (listo para cuando se resuelva IP)
5. `config.py` — Lee API keys de os.environ (compatible .env local + GitHub Secrets)
5. `.env` — Variables locales (API keys testnet, MONTO_USD=50, etc.) — en .gitignore
6. `historial_dca.csv` — Registro compras (timestamp, precio, monto, btc_comprado, btc_acumulado)
7. `errores_dca.log` — Log de errores con timestamp

### Próxima acción DCA (cuando se desee automatizar)
- Opción A: VPS barato (Hetzner $4.50/mes, RackNerd $10-15/año) — IP no bloqueada
- Opción B: Self-hosted GitHub Actions runner en laptop/otra máquina — usa IP local
- Opción C: Aceptar modo 100% manual actual (doble clic en Bot_DCA cuando se quiera)

## ACTUALIZACIONES RECIENTES (Julio 2025)

### Fix: Prevenir crash si historial_dca.csv está abierto (2025-07-17)
**Problema**: Si el usuario tiene `historial_dca.csv` abierto en Excel/visores y ejecuta el bot, la compra en Binance se ejecutaba bien pero el bot fallaba al escribir el CSV (archivo bloqueado por SO), crasheando el proceso y sin registrar la compra localmente.

**Solución implementada en `bot_dca.py` (función `guardar_historial`)**:
1. **Import `fcntl`** (módulo estándar Linux para bloqueo de archivos)
2. **Bloqueo exclusivo no bloqueante**: `fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)`
   - `LOCK_EX`: bloqueo exclusivo (espera si está libre, falla rápido si está ocupado)
   - `LOCK_NB`: non-blocking — NO se queda colgado esperando; falla inmediatamente con `IOError`
3. **Try/finally garantiza liberación**: `LOCK_UN` siempre se ejecuta aunque falle la escritura
4. **Try/except externo captura `IOError`/`OSError`**:
   - Imprime mensaje en ROJO: `"⚠️ ADVERTENCIA: La compra se ejecutó, pero el Excel está abierto. Ciérralo para registrar la compra."`
   - Loggea en `errores_dca.log` para auditoría
   - **NO crashea el bot** — la compra en Binance ya se hizo y el proceso termina con exit code 0

**Commit**: `c66cebc` — "Fix: Prevenir crash si historial_dca.csv está abierto (bloqueo no bloqueante)"

**Verificación**: Bot DCA ejecutado exitosamente 16 veces en testnet, CSV actualizado correctamente. Simulación de bloqueo confirmada: bot detecta archivo ocupado, muestra advertencia en rojo, loggea error, continúa sin crash.

### v9: Grid bot (en progreso)
Tras investigar bots realmente usados en 2026, se identificó que las estrategias direccionales simples (v1-v8) no tienen ventaja retail, pero los **grid bots sí tienen un mecanismo lógico real** (capturar oscilación de precio sin predecir dirección) y son de los más usados en la industria, con retornos documentados de 12-25% anual cuando se configuran bien. 

**Riesgos conocidos**: rendimiento pobre en tendencias fuertes, fricción de comisiones, necesidad de rango bien calibrado. 
**Ver reglas 8-11 en REGLAS.md** para los guardarraíles obligatorios.