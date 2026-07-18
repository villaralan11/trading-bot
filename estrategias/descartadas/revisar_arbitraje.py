import ccxt
import time
import pandas as pd

# ============================================================
# EXPLORACIÓN DE ARBITRAJE ENTRE EXCHANGES (v7)
# Solo lectura de precios públicos - SIN API keys
# ============================================================

# Configurar exchanges (solo datos públicos)
exchanges = {
    'binance': ccxt.binance({'enableRateLimit': True}),
    'kucoin': ccxt.kucoin({'enableRateLimit': True}),
    'okx': ccxt.okx({'enableRateLimit': True}),
}

symbol = 'BTC/USDT'
intervalo_segundos = 5
num_mediciones = 30

# Umbral de arbitraje (comisión 0.1% cada lado = 0.2% mínimo, más slippage/fees = 0.3% realista)
UMBRAL_ARBITRAJE = 0.3  # 0.3%

resultados = []
print(f"Iniciando monitoreo de arbitraje BTC/USDT entre {list(exchanges.keys())}")
print(f"Intervalo: {intervalo_segundos}s, Mediciones: {num_mediciones}")
print(f"Umbral arbitraje (comisión 0.1% x 2 + slippage): {UMBRAL_ARBITRAJE*100:.1f}%")
print("="*80)

for i in range(num_mediciones):
    timestamp = pd.Timestamp.now()
    precios = {}
    
    # Obtener precios de cada exchange
    for nombre, exchange in exchanges.items():
        try:
            ticker = exchange.fetch_ticker(symbol)
            precios[nombre] = {
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'spread': ticker['ask'] - ticker['bid'],
                'spread_pct': (ticker['ask'] - ticker['bid']) / ticker['bid'] * 100
            }
        except Exception as e:
            print(f"  Error en {nombre}: {e}")
            precios[nombre] = None
    
    # Calcular arbitraje si tenemos datos de todos
    validos = {k: v for k, v in precios.items() if v is not None}
    
    if len(validos) >= 2:
        # Encontrar ask más bajo (mejor precio para comprar) y bid más alto (mejor precio para vender)
        min_ask = min(validos.values(), key=lambda x: x['ask'])
        max_bid = max(validos.values(), key=lambda x: x['bid'])
        
        exchange_compra = [k for k, v in validos.items() if v['ask'] == min_ask['ask']][0]
        exchange_venta = [k for k, v in validos.items() if v['bid'] == max_bid['bid']][0]
        
        # Diferencia porcentual
        diff_pct = (max_bid['bid'] - min_ask['ask']) / min_ask['ask'] * 100
        
        arbitraje_posible = diff_pct > UMBRAL_ARBITRAJE * 100
        
        resultado = {
            'timestamp': timestamp,
            'num_exchanges': len(validos),
            'exchange_compra': exchange_compra,
            'ask_compra': min_ask['ask'],
            'exchange_venta': exchange_venta,
            'bid_venta': max_bid['bid'],
            'diff_pct': diff_pct,
            'arbitraje': arbitraje_posible
        }
        
        resultados.append(resultado)
        
        # Mostrar en consola
        status = "🟢 ARBITRAJE!" if arbitraje_posible else "⚪"
        print(f"[{i+1:2d}/{num_mediciones}] {status} Diff: {diff_pct:.4f}% | "
              f"Comprar en {exchange_compra} @ ${min_ask['ask']:,.2f} | "
              f"Vender en {exchange_venta} @ ${max_bid['bid']:,.2f}")
        
        # Mostrar todos los precios para debug
        for ex, p in validos.items():
            print(f"      {ex}: bid=${p['bid']:,.2f} ask=${p['ask']:,.2f} spread={p['spread_pct']:.4f}%")
    else:
        print(f"[{i+1:2d}/{num_mediciones}] ❌ Datos insuficientes (solo {len(validos)} exchanges)")
    
    # Esperar antes de la siguiente medición (excepto en la última)
    if i < num_mediciones - 1:
        time.sleep(intervalo_segundos)

# ============================================================
# RESULTADOS FINALES
# ============================================================
print("\n" + "="*80)
print("RESUMEN DE ARBITRAJE BTC/USDT (30 mediciones, 2.5 min)")
print("="*80)

if resultados:
    diffs = [r['diff_pct'] for r in resultados]
    arbitrajes = [r for r in resultados if r['arbitraje']]
    
    print(f"Total mediciones válidas: {len(resultados)}")
    print(f"Diferencia promedio: {sum(diffs)/len(diffs):.4f}%")
    print(f"Diferencia máxima:   {max(diffs):.4f}%")
    print(f"Diferencia mínima:   {min(diffs):.4f}%")
    print(f"Umbral arbitraje:    {UMBRAL_ARBITRAJE*100:.1f}%")
    print(f"Oportunidades > umbral: {len(arbitrajes)} de {len(resultados)} ({len(arbitrajes)/len(resultados)*100:.1f}%)")
    
    if arbitrajes:
        print("\n⚠️  OPORTUNIDADES DE ARBITRAJE DETECTADAS:")
        for r in arbitrajes:
            print(f"  {r['timestamp']}: {r['diff_pct']:.4f}% - "
                  f"Comprar {r['exchange_compra']} @ ${r['ask_compra']:,.2f} | "
                  f"Vender {r['exchange_venta']} @ ${r['bid_venta']:,.2f}")
    else:
        print("\n❌ NO se detectaron oportunidades de arbitraje rentables")
        print(f"   (ninguna diferencia superó {UMBRAL_ARBITRAJE*100:.1f}%)")
    
    # Estadísticas por exchange
    print("\n--- Estadísticas de spreads por exchange ---")
    for ex_name in exchanges.keys():
        spreads = []
        for r in resultados:
            # Buscar el spread de este exchange en la medición original
            pass  # Se puede mejorar guardando spreads originales
    
    # Guardar CSV
    df_resultados = pd.DataFrame(resultados)
    csv_path = '/home/alancito/trading-bot/datos/historicos/arbitraje_btc_usdt.csv'
    df_resultados.to_csv(csv_path, index=False)
    print(f"\nDatos guardados en: {csv_path}")
    
else:
    print("No se obtuvieron datos válidos")

# Cerrar conexiones
for exchange in exchanges.values():
    try:
        exchange.close()
    except:
        pass
