import ccxt
import pandas as pd
from datetime import datetime, timedelta
import os

project_dir = '/home/alancito/trading-bot'
data_dir = os.path.join(project_dir, 'datos', 'historicos')
output_path = os.path.join(data_dir, 'btc_usdt_4h.csv')

# Crear exchange
exchange = ccxt.binance({
    'enableRateLimit': True,
})

symbol = 'BTC/USDT'
timeframe = '4h'
limit = 1000  # máximo por llamada en Binance

# Calcular timestamp de hace 2 años
since = exchange.parse8601((datetime.now() - timedelta(days=730)).strftime('%Y-%m-%dT%H:%M:%SZ'))
print(f"Descargando desde: {datetime.fromtimestamp(since/1000)}")

all_ohlcv = []
fetch_count = 0

while True:
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
    fetch_count += 1
    print(f"Llamada {fetch_count}: {len(ohlcv)} velas, hasta {datetime.fromtimestamp(ohlcv[-1][0]/1000) if ohlcv else 'N/A'}")
    
    if not ohlcv:
        break
        
    all_ohlcv.extend(ohlcv)
    
    # Avanzar 'since' al timestamp de la última vela + 1ms
    since = ohlcv[-1][0] + 1
    
    # Si recibimos menos de 1000, ya no hay más datos
    if len(ohlcv) < limit:
        break

print(f"\nTotal velas descargadas: {len(all_ohlcv)}")

# Convertir a DataFrame
df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

# Eliminar duplicados (por si acaso)
df = df[~df.index.duplicated(keep='first')]
df.sort_index(inplace=True)

print(f"Rango final: {df.index[0]} a {df.index[-1]}")

# Guardar CSV
df.to_csv(output_path)
print(f"Guardado en: {output_path}")
