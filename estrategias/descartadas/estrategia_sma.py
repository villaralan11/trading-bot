import matplotlib
matplotlib.use('Agg')

import backtrader as bt
import pandas as pd
import matplotlib
matplotlib.use('Agg')

# 1. Estrategia SMA Crossover con sizer porcentual
class EstrategiaSMA(bt.Strategy):
    params = (
        ('periodo_rapida', 20),
        ('periodo_lenta', 50),
        ('pct_por_trade', 0.95),  # Usar 95% del capital disponible por trade
    )

    def __init__(self):
        self.sma_rapida = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.periodo_rapida
        )
        self.sma_lenta = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.periodo_lenta
        )
        self.cruce = bt.indicators.CrossOver(self.sma_rapida, self.sma_lenta)
        
        self.valor_inicial = None
        self.trades_cerrados = 0
        self.ganadores = 0
        self.perdedores = 0
        self.orden_pendiente = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f'COMPRA EJECUTADA: Precio={order.executed.price:.2f}, Size={order.executed.size:.6f} BTC, Value=${order.executed.value:.2f}, Commission=${order.executed.comm:.2f}')
            elif order.issell():
                self.log(f'VENTA EJECUTADA: Precio={order.executed.price:.2f}, Size={order.executed.size:.6f} BTC, Value=${order.executed.value:.2f}, Commission=${order.executed.comm:.2f}')
            self.orden_pendiente = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            status_name = {order.Canceled: 'Cancelada', order.Margin: 'Margin (fondos insuficientes)', order.Rejected: 'Rechazada'}
            self.log(f'ORDEN {status_name.get(order.status, order.status)}: Cash=${self.broker.getcash():.2f}')
            self.orden_pendiente = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades_cerrados += 1
            pnl = trade.pnlcomm
            if pnl > 0:
                self.ganadores += 1
            else:
                self.perdedores += 1
            self.log(f'TRADE CERRADO #{self.trades_cerrados}: PnL Neto=${pnl:.2f}, Price=${trade.price:.2f}, Size={trade.size:.6f}')

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def next(self):
        if self.valor_inicial is None:
            self.valor_inicial = self.broker.getvalue()

        # DEBUG cada 2000 barras
        if len(self.data) % 2000 == 0:
            pos = self.position.size if self.position else 0
            print(f"DEBUG barra {len(self.data)}: SMA20={self.sma_rapida[0]:.2f}, SMA50={self.sma_lenta[0]:.2f}, Cruce={self.cruce[0]}, Pos={pos:.6f}, Cash=${self.broker.getcash():.2f}, Value=${self.broker.getvalue():.2f}")

        # Señal de compra: cruce hacia arriba (1) y sin posición
        if self.cruce[0] > 0 and not self.position:
            self.log(f'SEÑAL COMPRA: Cruce={self.cruce[0]}, SMA20={self.sma_rapida[0]:.2f} > SMA50={self.sma_lenta[0]:.2f}, Precio=${self.data.close[0]:.2f}')
            # Calcular tamaño: 95% del valor disponible / precio actual
            cash_disponible = self.broker.getcash()
            size = (cash_disponible * self.params.pct_por_trade) / self.data.close[0]
            self.log(f'  Comprando {size:.6f} BTC (${cash_disponible * self.params.pct_por_trade:.2f} de ${cash_disponible:.2f} disponibles)')
            self.orden_pendiente = self.buy(size=size)
        
        # Señal de venta: cruce hacia abajo (-1) y con posición larga
        elif self.cruce[0] < 0 and self.position:
            self.log(f'SEÑAL VENTA: Cruce={self.cruce[0]}, SMA20={self.sma_rapida[0]:.2f} < SMA50={self.sma_lenta[0]:.2f}, Precio=${self.data.close[0]:.2f}')
            self.orden_pendiente = self.sell(size=self.position.size)

    def stop(self):
        valor_final = self.broker.getvalue()
        ganancia_pct = ((valor_final - self.valor_inicial) / self.valor_inicial) * 100
        
        print(f"\n{'='*50}")
        print(f"RESULTADOS BACKTEST SMA CROSSOVER (20/50)")
        print(f"{'='*50}")
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

# 2. Cargar datos
print("Cargando datos...")
df = pd.read_csv('/home/alancito/trading-bot/datos/historicos/btc_usdt_1h.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)
print(f"Datos cargados: {len(df)} velas")
print(f"Rango: {df.index[0]} a {df.index[-1]}")

# 3. Configurar Cerebro
cerebro = bt.Cerebro()
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)
cerebro.addstrategy(EstrategiaSMA)

cerebro.broker.setcash(10000.0)
cerebro.broker.setcommission(commission=0.001)  # 0.1%
cerebro.broker.set_slippage_perc(0.0005)  # 0.05%

cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.0)
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

print("\nEjecutando backtest...")
resultados = cerebro.run()

# Resultados del analyzer
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

if 'rtot' in returns:
    print(f"Retorno total: {returns['rtot']*100:.2f}%")

# 4. Generar gráfica
print("\nGenerando gráfica...")
try:
    fig = cerebro.plot(style='candlestick', barup='green', bardown='red', 
                       volume=False, 
                       savefig=dict(fname='resultado_sma.png', dpi=150, bbox_inches='tight'))[0][0]
    print("Gráfica guardada como: resultado_sma.png")
except Exception as e:
    print(f"Error generando gráfica: {e}")
