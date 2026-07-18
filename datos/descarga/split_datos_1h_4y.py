import pandas as pd
import os

project_dir = '/home/alancito/trading-bot'
data_dir = os.path.join(project_dir, 'datos', 'historicos')

# Find all 1h 4y files
files_1h_4y = [f for f in os.listdir(data_dir) if f.endswith('_1h_4y.csv')]

for filename in files_1h_4y:
    filepath = os.path.join(data_dir, filename)
    print(f"\nProcesando: {filename}")
    
    df = pd.read_csv(filepath)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    print(f"  Total filas: {len(df)}")
    print(f"  Rango: {df.index[0]} a {df.index[-1]}")
    
    # Dividir 70/30 cronológicamente
    split_idx = int(len(df) * 0.7)
    df_in = df.iloc[:split_idx]
    df_out = df.iloc[split_idx:]
    
    # Guardar
    base_name = filename.replace('_1h_4y.csv', '')
    in_path = os.path.join(data_dir, f'{base_name}_1h_4y_in_sample.csv')
    out_path = os.path.join(data_dir, f'{base_name}_1h_4y_out_sample.csv')
    
    df_in.to_csv(in_path)
    df_out.to_csv(out_path)
    
    print(f"  IN: {len(df_in)} filas ({df_in.index[0]} a {df_in.index[-1]}) -> {in_path}")
    print(f"  OUT: {len(df_out)} filas ({df_out.index[0]} a {df_out.index[-1]}) -> {out_path}")

print("\n¡Split completo!")
