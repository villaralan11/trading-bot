#!/usr/bin/env python3
"""
Bot DCA (Dollar-Cost Averaging) para Binance TESTNET
Ejecuta UNA compra de BTC y termina. Diseñado para GitHub Actions semanal.
"""

import ccxt
import pandas as pd
from datetime import datetime
import traceback
import os
import sys

# ============================================================
# CONFIGURACIÓN (leída desde variables de entorno con defaults)
# ============================================================
MONTO_USD = float(os.environ.get('MONTO_USD', '50.0'))      # USD por compra
PAR = os.environ.get('PAR', 'BTC/USDT')                     # Par a comprar
TESTNET = os.environ.get('TESTNET', 'true').lower() == 'true'

# Archivos de registro (relativos para que funcionen en GitHub Actions)
HISTORIAL_CSV = os.environ.get('HISTORIAL_CSV', 'historial_dca.csv')
ERRORES_LOG = os.environ.get('ERRORES_LOG', 'errores_dca.log')

# ============================================================
# CARGAR CREDENCIALES DE VARIABLES DE ENTORNO
# ============================================================
API_KEY = os.environ.get('API_KEY', '')
API_SECRET = os.environ.get('API_SECRET', '')

if not API_KEY or not API_SECRET:
    print("❌ ERROR: API_KEY y API_SECRET deben estar en variables de entorno")
    sys.exit(1)

# ============================================================
# INICIALIZAR EXCHANGE (TESTNET)
# ============================================================
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot',
    },
})

if TESTNET:
    exchange.set_sandbox_mode(True)
    print("🔧 MODO TESTNET ACTIVADO (sandbox)")

# ============================================================
# FUNCIÓN: LOG DE ERRORES
# ============================================================
def log_error(mensaje):
    """Registra error en archivo de log con timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(ERRORES_LOG, 'a') as f:
        f.write(f"[{timestamp}] {mensaje}\n")
    print(f"❌ ERROR: {mensaje}")

# ============================================================
# FUNCIÓN: GUARDAR COMPRA EN HISTORIAL CSV
# ============================================================
def guardar_historial(timestamp, precio, monto_usd, btc_comprado, btc_acumulado):
    """Guarda una compra en el CSV de historial"""
    fila = pd.DataFrame([{
        'timestamp': timestamp,
        'precio': precio,
        'monto_usd': monto_usd,
        'btc_comprado': btc_comprado,
        'btc_acumulado': btc_acumulado
    }])
    
    # Crear archivo con header si no existe, sino append
    if not os.path.exists(HISTORIAL_CSV):
        fila.to_csv(HISTORIAL_CSV, index=False)
    else:
        fila.to_csv(HISTORIAL_CSV, mode='a', header=False, index=False)

# ============================================================
# FUNCIÓN: OBTENER BALANCE ACTUAL DE BTC
# ============================================================
def obtener_balance_btc():
    """Obtiene balance actual de BTC en la cuenta"""
    try:
        balance = exchange.fetch_balance()
        return balance.get('BTC', {}).get('free', 0.0)
    except Exception as e:
        log_error(f"Error obteniendo balance: {e}")
        return 0.0

# ============================================================
# FUNCIÓN PRINCIPAL: COMPRAR
# ============================================================
def comprar():
    """
    Ejecuta una orden de mercado de compra por MONTO_USD
    Retorna: (exitoso: bool, info: dict)
    """
    try:
        # Obtener precio actual (ticker)
        ticker = exchange.fetch_ticker(PAR)
        precio_actual = ticker['last']
        
        print(f"\n{'='*60}")
        print(f"📈 INICIANDO COMPRA DCA")
        print(f"{'='*60}")
        print(f"Par: {PAR}")
        print(f"Precio actual: ${precio_actual:,.2f}")
        print(f"Monto a invertir: ${MONTO_USD:.2f}")
        
        # Calcular cantidad de BTC a comprar (redondear a 6 decimales típico)
        cantidad_btc = MONTO_USD / precio_actual
        cantidad_btc = round(cantidad_btc, 6)
        
        print(f"Cantidad a comprar: {cantidad_btc:.6f} BTC")
        
        # Ejecutar orden de MERCADO (market buy)
        orden = exchange.create_market_buy_order(PAR, cantidad_btc)
        
        # Extraer info de la orden ejecutada
        precio_ejecucion = orden.get('average', precio_actual)
        cantidad_ejecutada = orden.get('filled', cantidad_btc)
        costo_total = orden.get('cost', MONTO_USD)
        comision = orden.get('fee', {}).get('cost', 0)
        
        # Obtener balance acumulado después de la compra
        btc_acumulado = obtener_balance_btc()
        
        # Timestamp de la compra
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Mostrar resultado
        print(f"\n✅ COMPRA EJECUTADA EXITOSAMENTE")
        print(f"   Precio ejecución: ${precio_ejecucion:,.2f}")
        print(f"   Cantidad BTC: {cantidad_ejecutada:.6f}")
        print(f"   Costo total: ${costo_total:.2f}")
        print(f"   Comisión: ${comision:.4f}")
        print(f"   BTC acumulado: {btc_acumulado:.6f}")
        print(f"{'='*60}\n")
        
        # Guardar en historial
        guardar_historial(timestamp, precio_ejecucion, MONTO_USD, cantidad_ejecutada, btc_acumulado)
        
        return True, {
            'timestamp': timestamp,
            'precio': precio_ejecucion,
            'monto_usd': MONTO_USD,
            'btc_comprado': cantidad_ejecutada,
            'btc_acumulado': btc_acumulado,
            'comision': comision
        }
        
    except ccxt.InsufficientFunds as e:
        error_msg = f"Fondos insuficientes: {e}"
        log_error(error_msg)
        return False, {'error': error_msg}
    
    except ccxt.NetworkError as e:
        error_msg = f"Error de red: {e}"
        log_error(error_msg)
        return False, {'error': error_msg}
    
    except ccxt.ExchangeError as e:
        error_msg = f"Error del exchange: {e}"
        log_error(error_msg)
        return False, {'error': error_msg}
    
    except Exception as e:
        error_msg = f"Error inesperado: {e}\n{traceback.format_exc()}"
        log_error(error_msg)
        return False, {'error': error_msg}

# ============================================================
# MAIN: EJECUTAR UNA SOLA COMPRA Y TERMINAR
# ============================================================
if __name__ == '__main__':
    print("="*60)
    print("BOT DCA - EJECUCIÓN SEMANAL (TESTNET)")
    print("="*60)
    print(f"Configuración:")
    print(f"  MONTO_USD = ${MONTO_USD}")
    print(f"  PAR = {PAR}")
    print(f"  TESTNET = {TESTNET}")
    print(f"  Historial CSV: {HISTORIAL_CSV}")
    print(f"  Errores log: {ERRORES_LOG}")
    print()
    
    # Verificar conexión y balance inicial
    try:
        balance = exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        btc_balance = balance.get('BTC', {}).get('free', 0)
        print(f"💰 Balance inicial:")
        print(f"   USDT: ${usdt_balance:,.2f}")
        print(f"   BTC: {btc_balance:.6f}")
        
        if usdt_balance < MONTO_USD:
            print(f"\n⚠️ ADVERTENCIA: Balance USDT (${usdt_balance:.2f}) < Monto compra (${MONTO_USD:.2f})")
            print(f"   La compra fallará por fondos insuficientes")
    except Exception as e:
        print(f"❌ Error conectando a exchange: {e}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print("EJECUTANDO COMPRA SEMANAL...")
    print(f"{'='*60}")
    
    # Ejecutar UNA sola compra
    exito, info = comprar()
    
    if exito:
        print(f"\n✅ COMPRA SEMANAL COMPLETADA - Bot DCA funcionando correctamente")
        sys.exit(0)
    else:
        print(f"\n❌ COMPRA FALLÓ - Revisar {ERRORES_LOG}")
        sys.exit(1)
