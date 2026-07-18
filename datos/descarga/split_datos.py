import pandas as pd
import os

project_dir = '/home/alancito/trading-bot'
data_path = os.path.join(project_dir, 'datos/historicos/btc_usdt_1h.csv')

# Leer datos
df = pd.read_csv(data_path)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

print(f"Total filas: {len(df)}")
print(f"Rango completo: {df.index[0]} a {df.index[-1]}")

# Dividir 70% / 30% cronológicamente
split_idx = int(len(df) * 0.7)

df_in = df.iloc[:split_idx]
df_out = df.iloc[split_idx:]

# Guardar
in_path = os.path.join(project_dir, 'datos/historicos/btc_usdt_1h_in_sample.csv')
out_path = os.path.join(project_dir, 'datos/historicos/btc_usdt_1h_out_sample.csv')

df_in.to_csv(in_path)
df_out.to_csv(out_path)

print(f"\n--- IN SAMPLE (70%) ---")
print(f"Archivo: {in_path}")
print(f"Filas: {len(df_in)}")
print(f"Rango: {df_in.index[0]} a {df_in.index[-1]}")

print(f"\n--- OUT SAMPLE (30%) ---")
print(f"Archivo: {out_path}")
print(f"Filas: {len(df_out)}")
print(f"Rango: {df_out.index[0]} a {df_out.index[-1]}")
