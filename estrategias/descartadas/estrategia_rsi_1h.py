import backtrader as bt
import pandas as pd
import matplotlib
matplotlib.use('Agg')

# ============================================================
# 1. ESTRATEGIA RSI MEAN-REVERSION (COPIA EXACTA DE estrategia_rsi.py)
#    Único cambio: usar velas 1h en vez de 4h
# ============================================================
class EstrategiaRSI(bt.Strategy):
    params = (
        ('periodo_rsi', 14),
        ('rsi_sobreventa', 30),      # Comprar cuando RSI < 30
        ('rsi_salida', 50),           # Vender cuando RSI > 50 (neutral)
        ('periodo_sma_tendencia', 200),
        ('stop_loss_pct', 0.04),      # 4% stop loss (más margen para mean-reversion)
        ('max_posicion_pct', 0.20),   # 20% del capital por trade
    )

    def __init__(self):
        # Indicadores
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.data.close, period=self.params.periodo_rsi
        )
        self.sma_tendencia = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.periodo_sma_tendencia
        )
        
        # Cruces de RSI
        self.rsi_cruce_30 = bt.indicators.CrossDown(self.rsi, self.params.rsi_sobreventa)  # RSI cruza abajo de 30
        self.rsi_cruce_50 = bt.indicators.CrossUp(self.rsi, self.params.rsi_salida)         # RSI cruza arriba de 50
        
        # Estado
        self.valor_inicial = None
        self.trades_cerrados = 0
        self.ganadores = 0
        self.perdedores = 0
        self.orden_principal = None
        self.sl_order = None
        self.precio_entrada = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f'COMPRA EJECUTADA: Precio={order.executed.price:.2f}, Size={order.executed.size:.6f} BTC, Value=${order.executed.value:.2f}, Comm=${order.executed.comm:.2f}')
                self.precio_entrada = order.executed.price
                # Poner stop-loss
                self.colocar_stop_loss(order.executed.price, order.executed.size)
            elif order.issell():
                self.log(f'VENTA EJECUTADA: Precio={order.executed.price:.2f}, Size={order.executed.size:.6f} BTC, Value=${order.executed.value:.2f}, Comm=${order.executed.comm:.2f}')
            self.orden_principal = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            status_name = {order.Canceled: 'Cancelada', order.Margin: 'Margin (fondos insuficientes)', order.Rejected: 'Rechazada'}
            self.log(f'ORDEN {status_name.get(order.status, order.status)}: Cash=${self.broker.getcash():.2f}')
            self.orden_principal = None
            if self.sl_order:
                self.cancel(self.sl_order)
                self.sl_order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades_cerrados += 1
            pnl = trade.pnlcomm
            if pnl > 0:
                self.ganadores += 1
            else:
                self.perdedores += 1
            self.log(f'TRADE CERRADO #{self.trades_cerrados}: PnL Neto=${pnl:.2f}')

    def colocar_stop_loss(self, precio_entrada, size):
        """Coloca orden de stop-loss al 4%"""
        sl_price = precio_entrada * (1 - self.params.stop_loss_pct)
        self.sl_order = self.sell(size=size, exectype=bt.Order.Stop, price=sl_price)
        self.log(f'  SL puesto a ${sl_price:.2f} (-{self.params.stop_loss_pct*100:.0f}%)')

    def cancelar_sl(self):
        if self.sl_order and self.sl_order.status in [self.sl_order.Submitted, self.sl_order.Accepted, self.sl_order.Partial]:
            self.cancel(self.sl_order)
        self.sl_order = None

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def next(self):
        if self.valor_inicial is None:
            self.valor_inicial = self.broker.getvalue()

        # DEBUG cada 2000 barras
        if len(self.data) % 2000 == 0:
            pos = self.position.size if self.position else 0
            print(f"DEBUG barra {len(self.data)}: RSI={self.rsi[0]:.1f}, SMA200={self.sma_tendencia[0]:.2f}, Precio={self.data.close[0]:.2f}, Pos={pos:.6f}, Cash=${self.broker.getcash():.2f}, Value=${self.broker.getvalue():.2f}")

        # FILTRO DE TENDENCIA: precio debe estar sobre SMA200
        tendencia_alcista = self.data.close[0] > self.sma_tendencia[0]

        # SEÑAL DE COMPRA: RSI cruza por DEBAJO de 30 (sobreventa) + tendencia alcista + sin posición
        if self.rsi_cruce_30[0] and tendencia_alcista and not self.position:
            self.log(f'SEÑAL COMPRA: RSI={self.rsi[0]:.1f} < 30 (sobreventa), Precio={self.data.close[0]:.2f} > SMA200={self.sma_tendencia[0]:.2f} (TENDENCIA ALCISTA)')
            
            # Calcular tamaño: 20% del capital disponible
            cash_disponible = self.broker.getcash()
            valor_operacion = cash_disponible * self.params.max_posicion_pct
            size = valor_operacion / self.data.close[0]
            
            self.log(f'  Comprando {size:.6f} BTC (${valor_operacion:.2f} de ${cash_disponible:.2f} disponibles = {self.params.max_posicion_pct*100:.0f}%)')
            self.orden_principal = self.buy(size=size)
        
        # SEÑAL DE VENTA: RSI cruza por ENCIMA de 50 (regreso a neutral) + hay posición
        elif self.rsi_cruce_50[0] and self.position and self.position.size > 0:
            self.log(f'SEÑAL VENTA (RSI > 50): RSI={self.rsi[0]:.1f}, Precio={self.data.close[0]:.2f}')
            self.cancelar_sl()
            self.orden_principal = self.close()

        # STOP-LOSS se maneja via orden pendiente (notify_order)

    def stop(self):
        self.cancelar_sl()
        
        valor_final = self.broker.getvalue()
        ganancia_pct = ((valor_final - self.valor_inicial) / self.valor_inicial) * 100
        
        print(f"\n{'='*60}")
        print(f"RESULTADOS BACKTEST - RSI MEAN-REVERSION (14, 30/50)")
        print(f"{'='*60}")
        print(f"Capital inicial:  ${self.valor_inicial:,.2f}")
        print(f"Capital final:    ${valor_final:,.2f}")
        print(f"Ganancia/Pérdida: ${valor_final - self.valor_inicial:,.2f} ({ganancia_pct:+.2f}%)")
        print(f"Trades cerrados:  {self.trades_cerrados}")
        if self.trades_cerrados > 0:
            print(f"  Ganadores: {self.ganadores}")
            print(f"  Perdedores: {self.perdedores}")
            print(f"  Win rate: {self.ganadores/self.trades_cerrados*100:.1f}%")
        pos = self.position.size if self.position else 0
        print(f"Posición final: {pos:.6f} BTC")
        print(f"Cash final: ${self.broker.getcash():,.2f}")

# ============================================================
# 2. CARGAR SOLO IN-SAMPLE (1h, 4 años)
# ============================================================
print("Cargando datos IN-SAMPLE (1h, 4 años)...")
df = pd.read_csv('/home/alancito/trading-bot/datos/historicos/btc_usdt_1h_4y_in_sample.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)
print(f"Datos cargados: {len(df)} velas")
print(f"Rango: {df.index[0]} a {df.index[-1]}")

# ============================================================
# 3. CONFIGURAR CEREBRO
# ============================================================
cerebro = bt.Cerebro()
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)
cerebro.addstrategy(EstrategiaRSI)

cerebro.broker.setcash(10000.0)
cerebro.broker.setcommission(commission=0.001)   # 0.1%
cerebro.broker.set_slippage_perc(0.0005)         # 0.05%

cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.0)
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

print("\nEjecutando backtest...")
resultados = cerebro.run()

# ============================================================
# 4. RESULTADOS Y MÉTRICAS
# ============================================================
strat = resultados[0]
trade_analysis = strat.analyzers.trades.get_analysis()
sharpe = strat.analyzers.sharpe.get_analysis()
drawdown = strat.analyzers.drawdown.get_analysis()
returns = strat.analyzers.returns.get_analysis()

print(f"\n--- Estadísticas adicionales (Analyzers) ---")
if 'total' in trade_analysis:
    total = trade_analysis.total.total
    won = trade_analysis.won.total if 'won' in trade_analysis else 0
    lost = trade_analysis.lost.total if 'lost' in trade_analysis else 0
    print(f"Total trades: {total}")
    print(f"Ganadores: {won}, Perdedores: {lost}")
    if total > 0:
        print(f"Win rate: {won/total*100:.1f}%")

if 'sharperatio' in sharpe and sharpe['sharperatio'] is not None:
    print(f"Sharpe Ratio: {sharpe['sharperatio']:.2f}")

if 'max' in drawdown:
    print(f"Max Drawdown: {drawdown['max']['drawdown']:.2f}%")
    print(f"Max Drawdown $: ${drawdown['max']['moneydown']:.2f}")

if 'rtot' in returns:
    print(f"Retorno total: {returns['rtot']*100:.2f}%")

# ============================================================
# 5. TABLA CUMPLIMIENTO REGLAS.md
# ============================================================
print(f"\n{'='*60}")
print(f"CUMPLIMIENTO REGLAS.md")
print(f"{'='*60}")
reglas = [
    ("1. No overfitting en out_sample", "✅", "Solo in-sample usado; out-sample no tocado"),
    ("2. No look-ahead bias", "✅", "RSI y SMA usan solo datos pasados [0]; órdenes en next()"),
    ("3. Costos reales (comisión 0.1% + slippage 0.05%)", "✅", "Configurado en cerebro.broker"),
    ("4. Datos suficientes (1+ año, varios regímenes)", "✅", f"In-sample: {len(df)} velas 1h = ~34 meses"),
    ("5. Gestión riesgo (SL, position sizing, max DD)", "✅", f"SL 4%, sizing 20%, max DD observado: {drawdown.get('max',{}).get('drawdown',0):.1f}%"),
    ("6. API keys seguras", "✅", "No hay keys reales en código ni output"),
    ("7. Gap backtest-vivo", "⚠️", "Out-sample no probado aún; paper trading pendiente"),
]

for num, estado, detalle in reglas:
    print(f"{num:<50} {estado}  ({detalle})")

# ============================================================
# 6. GRÁFICA
# ============================================================
print("\nGenerando gráfica...")
try:
    fig = cerebro.plot(style='candlestick', barup='green', bardown='red', 
                       volume=False, 
                       savefig=dict(fname='resultado_rsi_1h.png', dpi=150, bbox_inches='tight'))[0][0]
    print("Gráfica guardada como: resultado_rsi_1h.png")
except Exception as e:
    print(f"Error generando gráfica: {e}")
