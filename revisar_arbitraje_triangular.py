import ccxt
import time
import pandas as pd

# ============================================================
# ARBITRAJE TRIANGULAR EN BINANCE (v8)
# Solo datos públicos - SIN API keys
# Ciclo: USDT -> BTC -> ETH -> USDT
# ============================================================

exchange = ccxt.binance({'enableRateLimit': True})

# Pares para el triángulo: USDT -> BTC -> ETH -> USDT
pares = ['BTC/USDT', 'ETH/USDT', 'ETH/BTC']

intervalo_segundos = 5
num_mediciones = 30
capital_inicial = 1000.0  # USDT inicial para cálculo
comision = 0.001  # 0.1% por operación
comision_total = comision * 3  # 3 operaciones = 0.3%

resultados = []

print("Iniciando monitoreo de arbitraje triangular BINANCE")
print(f"Ciclo: USDT -> BTC -> ETH -> USDT")
print(f"Capital inicial teórico: {capital_inicial} USDT")
print(f"Comisión por operación: {comision*100:.1f}% (total 3 ops: {comision_total*100:.1f}%)")
print(f"Intervalo: {intervalo_segundos}s, Mediciones: {num_mediciones}")
print("="*90)

for i in range(num_mediciones):
    timestamp = pd.Timestamp.now()
    precios = {}
    
    # Obtener precios de los 3 pares
    for par in pares:
        try:
            ticker = exchange.fetch_ticker(par)
            precios[par] = {
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'spread_pct': (ticker['ask'] - ticker['bid']) / ticker['bid'] * 100
            }
        except Exception as e:
            print(f"  Error en {par}: {e}")
            precios[par] = None
    
    # Verificar que tenemos todos los precios
    if all(precios[p] is not None for p in pares):
        # Extraer precios
        btc_usdt_bid = precios['BTC/USDT']['bid']
        btc_usdt_ask = precios['BTC/USDT']['ask']
        eth_usdt_bid = precios['ETH/USDT']['bid']
        eth_usdt_ask = precios['ETH/USDT']['ask']
        eth_btc_bid = precios['ETH/BTC']['bid']
        eth_btc_ask = precios['ETH/BTC']['ask']
        
        # ============================================================
        # CÁLCULO DEL CICLO TRIANGULAR
        # USDT -> BTC (comprar BTC con USDT = pagar ask)
        # BTC -> ETH (comprar ETH con BTC = pagar ask de ETH/BTC)
        # ETH -> USDT (vender ETH por USDT = recibir bid)
        # ============================================================
        
        # Paso 1: USDT -> BTC (comprar BTC, pagamos ask)
        btc_obtenido = capital_inicial / btc_usdt_ask
        btc_despues_comision1 = btc_obtenido * (1 - comision)
        
        # Paso 2: BTC -> ETH (comprar ETH con BTC, pagamos ask de ETH/BTC)
        eth_obtenido = btc_despues_comision1 / eth_btc_ask
        eth_despues_comision2 = eth_obtenido * (1 - comision)
        
        # Paso 3: ETH -> USDT (vender ETH por USDT, recibimos bid)
        usdt_final = eth_despues_comision2 * eth_usdt_bid
        usdt_despues_comision3 = usdt_final * (1 - comision)
        
        # Ganancia/pérdida
        ganancia_usdt = usdt_despues_comision3 - capital_inicial
        ganancia_pct = (ganancia_usdt / capital_inicial) * 100
        rentable = ganancia_pct > 0
        
        resultado = {
            'timestamp': timestamp,
            'btc_usdt_bid': btc_usdt_bid,
            'btc_usdt_ask': btc_usdt_ask,
            'eth_usdt_bid': eth_usdt_bid,
            'eth_usdt_ask': eth_usdt_ask,
            'eth_btc_bid': eth_btc_bid,
            'eth_btc_ask': eth_btc_ask,
            'usdt_final': usdt_despues_comision3,
            'ganancia_usdt': ganancia_usdt,
            'ganancia_pct': ganancia_pct,
            'rentable': rentable
        }
        
        resultados.append(resultado)
        
        # Mostrar en consola
        status = "🟢 RENTABLE" if rentable else "🔴 PERDIDA"
        print(f"[{i+1:2d}/30] {status} Ganancia: {ganancia_pct:+.6f}% | "
              f"USDT final: ${usdt_despues_comision3:.2f}")
        print(f"      BTC/USDT: bid={btc_usdt_bid:.2f} ask={btc_usdt_ask:.2f} | "
              f"ETH/USDT: bid={eth_usdt_bid:.2f} ask={eth_usdt_ask:.2f} | "
              f"ETH/BTC: bid={eth_btc_bid:.6f} ask={eth_btc_ask:.6f}")
    else:
        print(f"[{i+1:2d}/30] ❌ Datos incompletos")
    
    # Esperar antes de la siguiente medición
    if i < num_mediciones - 1:
        time.sleep(intervalo_segundos)

# ============================================================
# RESULTADOS FINALES
# ============================================================
print("\n" + "="*90)
print("RESUMEN ARBITRAJE TRIANGULAR BINANCE (USDT -> BTC -> ETH -> USDT)")
print("="*90)

if resultados:
    ganancias = [r['ganancia_pct'] for r in resultados]
    rentables = [r for r in resultados if r['rentable']]
    
    print(f"Total mediciones: {len(resultados)}")
    print(f"Ganancia promedio: {sum(ganancias)/len(ganancias):+.6f}%")
    print(f"Ganancia máxima:   {max(ganancias):+.6f}%")
    print(f"Ganancia mínima:   {min(ganancias):+.6f}%")
    print(f"Mediciones rentables: {len(rentables)} de {len(resultados)} ({len(rentables)/len(resultados)*100:.1f}%)")
    print(f"Comisión total (3 ops x 0.1%): 0.3%")
    
    if rentables:
        print("\n🟢 Mediciones rentables:")
        for r in rentables:
            print(f"  {r['timestamp']}: {r['ganancia_pct']:+.6f}%")
    else:
        print("\n🔴 NINGUNA medición fue rentable después de comisiones")
        print(f"   (El mercado es eficiente: no hay arbitraje triangular detectable)")
    
    # Guardar CSV
    df_resultados = pd.DataFrame(resultados)
    csv_path = '/home/alancito/trading-bot/data/arbitraje_triangular_btc_eth.csv'
    df_resultados.to_csv(csv_path, index=False)
    print(f"\nDatos guardados en: {csv_path}")
else:
    print("No se obtuvieron datos válidos")

exchange.close()
