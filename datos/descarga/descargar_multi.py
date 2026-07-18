import ccxt
import pandas as pd
from datetime import datetime, timedelta
import os
import time

project_dir = '/home/alancito/trading-bot'
data_dir = os.path.join(project_dir, 'datos', 'historicos')

# Crear exchange
exchange = ccxt.binance({
    'enableRateLimit': True,
})

pares = ['ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT']
timeframe = '4h'
limit = 1000

# Calcular timestamp de hace 2 años
since = exchange.parse8601((datetime.now() - timedelta(days=730)).strftime('%Y-%m-%dT%H:%M:%SZ'))
print(f"Descargando desde: {datetime.fromtimestamp(since/1000)}")

for symbol in pares:
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
                
            time.sleep(0.1)  # Rate limit
            
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(1)
            continue
    
    if not all_ohlcv:
        print(f"  No se descargaron datos para {symbol}")
        continue
    
    # Convertir a DataFrame
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    # Eliminar duplicados
    df = df[~df.index.duplicated(keep='first')]
    df.sort_index(inplace=True)
    
    print(f"  Total velas: {len(df)}")
    print(f"  Rango: {df.index[0]} a {df.index[-1]}")
    
    # Guardar CSV
    symbol_filename = symbol.replace('/', '_')
    output_path = os.path.join(data_dir, f'{symbol_filename}_4h.csv')
    df.to_csv(output_path)
    print(f"  Guardado en: {output_path}")

print("\n¡Descarga completa!")
