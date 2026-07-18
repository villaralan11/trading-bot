# Reglas del proyecto - errores a evitar

1. OVERFITTING: nunca ajustar/optimizar parámetros contra out_sample.csv.
   Ese archivo solo se corre UNA vez, al final, cuando ya haya una estrategia
   decidida. Si se prueban muchas combinaciones de parámetros, avisar que
   hay riesgo de overfitting.

2. LOOK-AHEAD BIAS: ninguna señal puede usar datos de una vela que aún no
   ha cerrado. Verificar que los indicadores solo usen datos pasados
   respecto a la barra donde se ejecuta la orden.

3. COSTOS REALES: todo backtest debe incluir comisión (0.1%) y slippage
   (0.05%) simulados. Nunca reportar resultados sin costos.

4. DATOS SUFICIENTES: cualquier backtest debe cubrir al menos un año y
   distintas condiciones de mercado (alcista, bajista, lateral), no solo
   un tramo corto o favorable.

5. GESTIÓN DE RIESGO: toda estrategia debe definir stop-loss, tamaño de
   posición como fracción del capital (nunca todo el capital en una orden),
   y un límite de drawdown máximo aceptable.

6. SEGURIDAD DE API KEYS: nunca escribir, imprimir, ni subir a git las
   API keys reales (solo las de testnet mientras estemos en fase de
   pruebas). El .gitignore debe seguir excluyendo config.py.

7. BRECHA BACKTEST-VIVO: ninguna estrategia pasa a paper trading sin antes
   correr limpio contra out_sample.csv. Ninguna estrategia pasa a dinero
   real sin antes correr en paper trading un mínimo de 3 meses.
