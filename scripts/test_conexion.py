import ccxt
import config

exchange = ccxt.binance({
    'apiKey': config.API_KEY,
    'secret': config.API_SECRET,
})
exchange.set_sandbox_mode(True)

# Obtener balance de la cuenta testnet
balance = exchange.fetch_balance()
print("Balance:")
print(balance)

# Obtener precio actual de BTC/USDT
ticker = exchange.fetch_ticker('BTC/USDT')
print("\nTicker BTC/USDT:")
print(ticker)
