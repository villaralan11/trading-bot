import backtrader as bt
import pandas as pd
import matplotlib
matplotlib.use('Agg')

# ============================================================
# ESTRATEGIA IDÉNTICA A estrategia_v3.py (SIN CAMBIOS)
# ============================================================
class EstrategiaTendenciaSMA(bt.Strategy):
    params = (
        ('periodo_rapida', 20),
        ('periodo_lenta', 50),
        ('periodo_tendencia', 200),
        ('stop_loss_pct', 0.03),
        ('take_profit_pct', 0.06),
        ('max_posicion_pct', 0.20),
    )

    def __init__(self):
        self.sma_rapida = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.periodo_rapida
        )
        self.sma_lenta = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.periodo_lenta
        )
        self.sma_tendencia = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.periodo_tendencia
        )
        self.cruce = bt.indicators.CrossOver(self.sma_rapida, self.sma_lenta)
        
        self.valor_inicial = None
        self.trades_cerrados = 0
        self.ganadores = 0
        self.perdedores = 0
        self.bracket_orders = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f'COMPRA EJECUTADA: Precio={order.executed.price:.2f}, Size={order.executed.size:.6f}, Value=${order.executed.value:.2f}, Comm=${order.executed.comm:.2f}')
            elif order.issell():
                self.log(f'VENTA EJECUTADA: Precio={order.executed.price:.2f}, Size={order.executed.size:.6f}, Value=${order.executed.value:.2f}, Comm=${order.executed.comm:.2f}')
            self.bracket_orders = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            status_name = {order.Canceled: 'Cancelada', order.Margin: 'Margin (fondos insuficientes)', order.Rejected: 'Rechazada'}
            self.log(f'ORDEN {status_name.get(order.status, order.status)}: Cash=${self.broker.getcash():.2f}')
            self.bracket_orders = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades_cerrados += 1
            pnl = trade.pnlcomm
            if pnl > 0:
                self.ganadores += 1
            else:
                self.perdedores += 1
            self.log(f'TRADE CERRADO #{self.trades_cerrados}: PnL Neto=${pnl:.2f}')

    def cancelar_bracket(self):
        if self.bracket_orders:
            for o in self.bracket_orders:
                if o and o.status in [o.Submitted, o.Accepted, o.Partial]:
                    self.cancel(o)
            self.bracket_orders = None

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def next(self):
        if self.valor_inicial is None:
            self.valor_inicial = self.broker.getvalue()

        if len(self.data) % 2000 == 0:
            pos = self.position.size if self.position else 0
            print(f"DEBUG barra {len(self.data)}: SMA20={self.sma_rapida[0]:.2f}, SMA50={self.sma_lenta[0]:.2f}, SMA200={self.sma_tendencia[0]:.2f}, Cruce={self.cruce[0]}, Precio={self.data.close[0]:.2f}, Pos={pos:.6f}, Cash=${self.broker.getcash():.2f}, Value=${self.broker.getvalue():.2f}")

        tendencia_alcista = self.data.close[0] > self.sma_tendencia[0]

        if self.cruce[0] > 0 and tendencia_alcista and not self.position:
            self.log(f'SEÑAL COMPRA: Cruce={self.cruce[0]}, SMA20={self.sma_rapida[0]:.2f} > SMA50={self.sma_lenta[0]:.2f}, Precio={self.data.close[0]:.2f} > SMA200={self.sma_tendencia[0]:.2f} (TENDENCIA ALCISTA)')
            
            cash_disponible = self.broker.getcash()
            valor_operacion = cash_disponible * self.params.max_posicion_pct
            size = valor_operacion / self.data.close[0]
            
            self.log(f'  Comprando {size:.6f} (${valor_operacion:.2f} de ${cash_disponible:.2f} disponibles = {self.params.max_posicion_pct*100:.0f}%)')
            
            stop_price = self.data.close[0] * (1 - self.params.stop_loss_pct)
            limit_price = self.data.close[0] * (1 + self.params.take_profit_pct)
            
            self.log(f'  SL a ${stop_price:.2f} (-{self.params.stop_loss_pct*100:.0f}%), TP a ${limit_price:.2f} (+{self.params.take_profit_pct*100:.0f}%)')
            
            self.bracket_orders = self.buy_bracket(
                size=size,
                stopprice=stop_price,
                limitprice=limit_price,
            )
        
        elif self.cruce[0] < 0 and self.position and self.position.size > 0:
            self.log(f'SEÑAL VENTA (cruce abajo): Cruce={self.cruce[0]}, SMA20={self.sma_rapida[0]:.2f} < SMA50={self.sma_lenta[0]:.2f}, Precio={self.data.close[0]:.2f}')
            self.cancelar_bracket()
            self.close()

    def stop(self):
        self.cancelar_bracket()
        
        valor_final = self.broker.getvalue()
        ganancia_pct = ((valor_final - self.valor_inicial) / self.valor_inicial) * 100
        
        print(f"\n{'='*60}")
        print(f"RESULTADOS BACKTEST - TENDENCIA SMA 4H + CRUCE + SL/TP")
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
        print(f"Posición final: {pos:.6f}")
        print(f"Cash final: ${self.broker.getcash():,.2f}")

# ============================================================
# FUNCIÓN PARA EJECUTAR BACKTEST EN UN PAR
# ============================================================
def run_backtest(par, csv_path):
    # Cargar datos
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # Configurar Cerebro
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(EstrategiaTendenciaSMA)
    
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.broker.set_slippage_perc(0.0005)
    
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.0)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    resultados = cerebro.run()
    strat = resultados[0]
    
    # Extraer métricas
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
# MAIN: EJECUTAR EN OUT-SAMPLE DE LOS 5 PARES
# ============================================================
if __name__ == '__main__':
    pares = [
        ('BTC/USDT', '/home/alancito/trading-bot/datos/historicos/btc_usdt_4h_out_sample.csv'),
        ('ETH/USDT', '/home/alancito/trading-bot/datos/historicos/ETH_USDT_4h_out_sample.csv'),
        ('BNB/USDT', '/home/alancito/trading-bot/datos/historicos/BNB_USDT_4h_out_sample.csv'),
        ('SOL/USDT', '/home/alancito/trading-bot/datos/historicos/SOL_USDT_4h_out_sample.csv'),
        ('ADA/USDT', '/home/alancito/trading-bot/datos/historicos/ADA_USDT_4h_out_sample.csv'),
    ]
    
    # Resultados in-sample previos (de evaluar_multi.py)
    in_sample_results = {
        'BTC/USDT': 5.18,
        'ETH/USDT': 1.71,
        'BNB/USDT': 3.36,
        'SOL/USDT': 4.71,
        'ADA/USDT': -2.21,
    }
    
    print(f"\n{'='*80}")
    print(f"EVALUACIÓN OUT-SAMPLE - MISMA ESTRATEGIA (SMA20/50/200, SL 3%, TP 6%, 20% sizing)")
    print(f"{'='*80}")
    
    out_results = []
    
    for par, path in pares:
        try:
            print(f"\n--- Procesando {par} ---")
            res = run_backtest(par, path)
            out_results.append(res)
            print(f"  Retorno: {res['retorno_pct']:.2f}%")
        except Exception as e:
            print(f"  Error: {e}")
            out_results.append({
                'par': par, 'trades': 0, 'ganadores': 0, 'perdedores': 0,
                'win_rate': 0, 'retorno_pct': 0, 'sharpe': 0, 'max_dd_pct': 0, 'capital_final': 0
            })
    
    # Tabla comparativa
    print(f"\n{'='*100}")
    print(f"TABLA COMPARATIVA: IN-SAMPLE vs OUT-SAMPLE")
    print(f"{'='*100}")
    print(f"{'Par':<12} {'In-Sample %':>14} {'Out-Sample %':>14} {'Diferencia':>12} {'Rank In':>8} {'Rank Out':>8} {'Rank Δ':>8}")
    print(f"{'-'*100}")
    
    # Calcular rankings
    in_sorted = sorted(in_sample_results.items(), key=lambda x: x[1], reverse=True)
    in_ranks = {par: i+1 for i, (par, _) in enumerate(in_sorted)}
    
    out_sorted = sorted([(r['par'], r['retorno_pct']) for r in out_results], key=lambda x: x[1], reverse=True)
    out_ranks = {par: i+1 for i, (par, _) in enumerate(out_sorted)}
    
    for r in out_results:
        par = r['par']
        in_ret = in_sample_results.get(par, 0)
        out_ret = r['retorno_pct']
        diff = out_ret - in_ret
        rank_in = in_ranks.get(par, 0)
        rank_out = out_ranks.get(par, 0)
        rank_delta = rank_out - rank_in
        delta_str = f"{rank_delta:+d}" if rank_delta != 0 else "="
        print(f"{par:<12} {in_ret:>13.2f}% {out_ret:>13.2f}% {diff:>+11.2f}% {rank_in:>8d} {rank_out:>8d} {delta_str:>8}")
    
    print(f"{'='*100}")
    
    # Análisis de ranking
    print(f"\n{'='*100}")
    print(f"ANÁLISIS DE RANKING IN-SAMPLE vs OUT-SAMPLE")
    print(f"{'='*100}")
    
    # Verificar si el ranking se mantiene
    ranking_mismo = True
    for par in in_ranks:
        if in_ranks[par] != out_ranks.get(par, 0):
            ranking_mismo = False
            break
    
    if ranking_mismo:
        print(f"✅ El ranking de pares se MANTIENE IDÉNTICO entre in-sample y out-sample.")
    else:
        print(f"❌ El ranking de pares CAMBIA entre in-sample y out-sample.")
        print(f"   Cambios de posición:")
        for par in in_ranks:
            delta = out_ranks.get(par, 0) - in_ranks[par]
            if delta != 0:
                direccion = "sube" if delta < 0 else "baja"
                print(f"   - {par}: puesto {in_ranks[par]} → {out_ranks.get(par, 'N/A')} ({direccion} {abs(delta)} posiciones)")
    
    # Correlación
    in_vals = [in_sample_results[r['par']] for r in out_results]
    out_vals = [r['retorno_pct'] for r in out_results]
    
    import numpy as np
    if len(in_vals) > 1:
        corr = np.corrcoef(in_vals, out_vals)[0,1]
        print(f"\n   Correlación Pearson (In vs Out retornos): {corr:.3f}")
        if corr > 0.7:
            print(f"   → Alta correlación: los pares que ganan en in-sample tienden a ganar en out-sample")
        elif corr > 0.3:
            print(f"   → Correlación moderada: cierta persistencia pero con ruido")
        else:
            print(f"   → Baja correlación: el rendimiento in-sample no predice bien el out-sample")
    
    print(f"{'='*100}")
