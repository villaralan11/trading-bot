import ccxt
import pandas as pd
from datetime import datetime, timedelta
import os
import time

project_dir = '/home/alancito/trading-bot'
data_dir = os.path.join(project_dir, 'datos', 'historicos')
os.makedirs(data_dir, exist_ok=True)

# Create exchange
exchange = ccxt.binance({
    'enableRateLimit': True,
})

# Get top 20 USDT pairs by volume (excluding stablecoins)
print("Obteniendo lista de pares USDT por volumen...")
tickers = exchange.fetch_tickers()

# Filter USDT pairs, exclude stablecoins
stablecoins = {'USDC', 'USDT', 'BUSD', 'TUSD', 'USDP', 'FDUSD', 'PYUSD', 'EUR', 'GBP', 'AUD', 'DAI', 'FRAX', 'LUSD', 'USTC', 'USDD', 'USDN', 'MIM', 'ALUSD', 'XAUT', 'PAXG'}
usdt_pairs = []
for symbol, ticker in tickers.items():
    if symbol.endswith('/USDT'):
        base = symbol.split('/')[0]
        if base not in stablecoins:
            quote_vol = ticker.get('quoteVolume')
            if quote_vol is not None and quote_vol > 0:
                usdt_pairs.append((symbol, float(quote_vol)))
            else:
                # Fallback: baseVolume * last price
                base_vol = ticker.get('baseVolume')
                last = ticker.get('last')
                if base_vol is not None and last is not None and base_vol > 0 and last > 0:
                    usdt_pairs.append((symbol, float(base_vol) * float(last)))

# Sort by volume descending
usdt_pairs.sort(key=lambda x: x[1], reverse=True)
top20 = [p[0] for p in usdt_pairs[:20]]

print(f"\nTop 20 pares por volumen:")
for i, (sym, vol) in enumerate(usdt_pairs[:20], 1):
    print(f"  {i:2d}. {sym}: ${vol:,.0f}")

# Check which already exist
existing_files = set(os.listdir(data_dir))
pares_a_descargar = []
for symbol in top20:
    symbol_filename = symbol.replace('/', '_')
    csv_name = f'{symbol_filename}_1h_4y.csv'
    if csv_name in existing_files:
        print(f"  ✓ {symbol} ya existe: {csv_name}")
    else:
        pares_a_descargar.append(symbol)

if not pares_a_descargar:
    print("\nTodos los 20 pares ya están descargados.")
else:
    print(f"\nDescargando {len(pares_a_descargar)} pares faltantes...")
    
    timeframe = '1h'
    limit = 1000
    since = exchange.parse8601((datetime.now() - timedelta(days=4*365)).strftime('%Y-%m-%dT%H:%M:%SZ'))
    print(f"Descargando desde: {datetime.fromtimestamp(since/1000)}")

    for symbol in pares_a_descargar:
        print(f"\n{'='*50}")
        print(f"Descargando {symbol}...")
        print(f"{'='*50}")
        
        all_ohlcv = []
        fetch_count = 0
        current_since = since
        
        while True:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=limit)
                fetch_count += 1
                
                if not ohlcv:
                    print(f"  Llamada {fetch_count}: sin datos")
                    break
                    
                print(f"  Llamada {fetch_count}: {len(ohlcv)} velas, hasta {datetime.fromtimestamp(ohlcv[-1][0]/1000)}")
                all_ohlcv.extend(ohlcv)
                
                current_since = ohlcv[-1][0] + 1
                
                if len(ohlcv) < limit:
                    break
                    
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  Error: {e}")
                time.sleep(1)
                continue
        
        if not all_ohlcv:
            print(f"  No se descargaron datos para {symbol}")
            continue
        
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        df = df[~df.index.duplicated(keep='first')]
        df.sort_index(inplace=True)
        
        print(f"  Total velas: {len(df)}")
        print(f"  Rango: {df.index[0]} a {df.index[-1]}")
        
        symbol_filename = symbol.replace('/', '_')
        output_path = os.path.join(data_dir, f'{symbol_filename}_1h_4y.csv')
        df.to_csv(output_path)
        print(f"  Guardado en: {output_path}")

print("\n¡Descarga completa!")
