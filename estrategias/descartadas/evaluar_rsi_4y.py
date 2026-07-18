import backtrader as bt
import pandas as pd
import matplotlib
matplotlib.use('Agg')

# ============================================================
# ESTRATEGIA RSI MEAN-REVERSION (COPIA EXACTA DE estrategia_rsi.py)
# ============================================================
class EstrategiaRSI(bt.Strategy):
    params = (
        ('periodo_rsi', 14),
        ('rsi_sobreventa', 30),
        ('rsi_salida', 50),
        ('periodo_sma_tendencia', 200),
        ('stop_loss_pct', 0.04),
        ('max_posicion_pct', 0.20),
    )

    def __init__(self):
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.data.close, period=self.params.periodo_rsi
        )
        self.sma_tendencia = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.periodo_sma_tendencia
        )
        
        self.rsi_cruce_30 = bt.indicators.CrossDown(self.rsi, self.params.rsi_sobreventa)
        self.rsi_cruce_50 = bt.indicators.CrossUp(self.rsi, self.params.rsi_salida)
        
        self.valor_inicial = None
        self.trades_cerrados = 0
        self.ganadores = 0
        self.perdedores = 0
        self.orden_principal = None
        self.sl_order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f'COMPRA EJECUTADA: Precio={order.executed.price:.2f}, Size={order.executed.size:.6f} BTC, Value=${order.executed.value:.2f}, Comm=${order.executed.comm:.2f}')
                self.precio_entrada = order.executed.price
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

        if len(self.data) % 2000 == 0:
            pos = self.position.size if self.position else 0
            print(f"DEBUG barra {len(self.data)}: RSI={self.rsi[0]:.1f}, SMA200={self.sma_tendencia[0]:.2f}, Precio={self.data.close[0]:.2f}, Pos={pos:.6f}, Cash=${self.broker.getcash():.2f}, Value=${self.broker.getvalue():.2f}")

        tendencia_alcista = self.data.close[0] > self.sma_tendencia[0]

        if self.rsi_cruce_30[0] and tendencia_alcista and not self.position:
            self.log(f'SEÑAL COMPRA: RSI={self.rsi[0]:.1f} < 30 (sobreventa), Precio={self.data.close[0]:.2f} > SMA200={self.sma_tendencia[0]:.2f} (TENDENCIA ALCISTA)')
            
            cash_disponible = self.broker.getcash()
            valor_operacion = cash_disponible * self.params.max_posicion_pct
            size = valor_operacion / self.data.close[0]
            
            self.log(f'  Comprando {size:.6f} BTC (${valor_operacion:.2f} de ${cash_disponible:.2f} disponibles = {self.params.max_posicion_pct*100:.0f}%)')
            self.orden_principal = self.buy(size=size)
        
        elif self.rsi_cruce_50[0] and self.position and self.position.size > 0:
            self.log(f'SEÑAL VENTA (RSI > 50): RSI={self.rsi[0]:.1f}, Precio={self.data.close[0]:.2f}')
            self.cancelar_sl()
            self.orden_principal = self.close()

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
# FUNCIÓN PARA EJECUTAR BACKTEST EN UN PAR
# ============================================================
def run_backtest(par, csv_path):
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(EstrategiaRSI)
    
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.broker.set_slippage_perc(0.0005)
    
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.0)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    resultados = cerebro.run()
    strat = resultados[0]
    
    trade_analysis = strat.analyzers.trades.get_analysis()
    sharpe = strat.analyzers.sharpe.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    returns = strat.analyzers.returns.get_analysis()
    
    total_trades = trade_analysis.total.total if 'total' in trade_analysis else 0
    won = trade_analysis.won.total if 'won' in trade_analysis else 0
    lost = trade_analysis.lost.total if 'lost' in trade_analysis else 0
    win_rate = (won / total_trades * 100) if total_trades > 0 else 0
    sharpe_ratio = sharpe['sharperatio'] if 'sharperatio' in sharpe and sharpe['sharperatio'] is not None else 0
    max_dd = drawdown['max']['drawdown'] if 'max' in drawdown else 0
    total_return = returns['rtot'] * 100 if 'rtot' in returns else 0
    
    return {
        'par': par,
        'trades': total_trades,
        'ganadores': won,
        'perdedores': lost,
        'win_rate': win_rate,
        'retorno_pct': total_return,
        'sharpe': sharpe_ratio,
        'max_dd_pct': max_dd,
        'capital_final': strat.broker.getvalue()
    }

# ============================================================
# MAIN: EJECUTAR EN IN-SAMPLE DE 4 AÑOS DE LOS 5 PARES
# ============================================================
if __name__ == '__main__':
    pares = [
        ('BTC/USDT', '/home/alancito/trading-bot/datos/historicos/BTC_USDT_4h_4y_in_sample.csv'),
        ('ETH/USDT', '/home/alancito/trading-bot/datos/historicos/ETH_USDT_4h_4y_in_sample.csv'),
        ('BNB/USDT', '/home/alancito/trading-bot/datos/historicos/BNB_USDT_4h_4y_in_sample.csv'),
        ('SOL/USDT', '/home/alancito/trading-bot/datos/historicos/SOL_USDT_4h_4y_in_sample.csv'),
        ('ADA/USDT', '/home/alancito/trading-bot/datos/historicos/ADA_USDT_4h_4y_in_sample.csv'),
    ]
    
    print(f"\n{'='*80}")
    print(f"EVALUACIÓN RSI MEAN-REVERSION EN 5 PARES (IN-SAMPLE 4 AÑOS 4H)")
    print(f"Parámetros: RSI 14, compra <30, vende >50, SL 4%, filtro SMA200, 20% sizing")
    print(f"{'='*80}")
    
    resultados = []
    
    for par, path in pares:
        try:
            print(f"\n--- Procesando {par} ---")
            res = run_backtest(par, path)
            resultados.append(res)
            print(f"  Trades: {res['trades']}, Win rate: {res['win_rate']:.1f}%, Retorno: {res['retorno_pct']:.2f}%, Sharpe: {res['sharpe']:.2f}, Max DD: {res['max_dd_pct']:.2f}%")
        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            resultados.append({
                'par': par, 'trades': 0, 'ganadores': 0, 'perdedores': 0,
                'win_rate': 0, 'retorno_pct': 0, 'sharpe': 0, 'max_dd_pct': 0, 'capital_final': 0
            })
    
    # Tabla comparativa
    print(f"\n{'='*100}")
    print(f"TABLA COMPARATIVA RSI MEAN-REVERSION (IN-SAMPLE 4 AÑOS 4H)")
    print(f"{'='*100}")
    print(f"{'Par':<12} {'Trades':>7} {'Ganados':>8} {'Perdidos':>9} {'Win Rate':>10} {'Retorno %':>11} {'Sharpe':>8} {'Max DD %':>10} {'Capital Final':>14} {'≥30 trades':>10}")
    print(f"{'-'*100}")
    
    for r in resultados:
        trades_30 = "✅ SÍ" if r['trades'] >= 30 else "❌ NO"
        print(f"{r['par']:<12} {r['trades']:>7} {r['ganadores']:>8} {r['perdedores']:>9} {r['win_rate']:>9.1f}% {r['retorno_pct']:>10.2f}% {r['sharpe']:>8.2f} {r['max_dd_pct']:>9.2f}% ${r['capital_final']:>12,.2f} {trades_30:>10}")
    
    print(f"{'='*100}")
    
    # Promedios
    if resultados:
        avg_trades = sum(r['trades'] for r in resultados) / len(resultados)
        avg_retorno = sum(r['retorno_pct'] for r in resultados) / len(resultados)
        avg_sharpe = sum(r['sharpe'] for r in resultados) / len(resultados)
        avg_dd = sum(r['max_dd_pct'] for r in resultados) / len(resultados)
        avg_winrate = sum(r['win_rate'] for r in resultados) / len(resultados)
        pares_30 = sum(1 for r in resultados if r['trades'] >= 30)
        print(f"{'PROMEDIO':<12} {avg_trades:>7.1f} {'':>8} {'':>9} {avg_winrate:>9.1f}% {avg_retorno:>10.2f}% {avg_sharpe:>8.2f} {avg_dd:>9.2f}%")
        print(f"\nPares con ≥30 trades: {pares_30}/5")
    
    print(f"{'='*100}")
