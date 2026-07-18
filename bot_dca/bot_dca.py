#!/usr/bin/env python3
"""
Bot DCA (Dollar-Cost Averaging) para Binance TESTNET
Ejecuta UNA compra y termina. Diseñado para GitHub Actions semanal.
"""

import ccxt
import pandas as pd
from datetime import datetime
import traceback
import os
import sys
import fcntl

# ============================================================
# CONFIGURACIÓN (leída desde variables de entorno con defaults)
# ============================================================
MONTO_USD = float(os.environ.get('MONTO_USD', '50.0'))      # USD por compra
PAR = os.environ.get('PAR', 'BTC/USDT')                     # Par a comprar
BASE_CURRENCY = PAR.split('/')[0]                           # Moneda base (BTC, ETH, etc.)
QUOTE_CURRENCY = PAR.split('/')[1]                          # Moneda cotizada (USDT)
TESTNET = os.environ.get('TESTNET', 'true').lower() == 'true'

# Archivos de registro (relativos al directorio raíz del proyecto para que funcionen en GitHub Actions)
HISTORIAL_CSV = os.environ.get('HISTORIAL_CSV', 'resultados/historial_dca.csv')
ERRORES_LOG = os.environ.get('ERRORES_LOG', 'resultados/errores_dca.log')

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
def guardar_historial(timestamp, precio, monto_usd, base_comprado, base_acumulado):
    """Guarda una compra en el CSV de historial con bloqueo exclusivo"""
    fila = pd.DataFrame([{
        'timestamp': timestamp,
        'precio': precio,
        'monto_usd': monto_usd,
        'btc_comprado': base_comprado,      # compatibilidad con histórico (guarda cantidad de moneda base)
        'btc_acumulado': base_acumulado     # compatibilidad con histórico (guarda balance acumulado base)
    }])
    
    try:
        # Abrir en modo append (crea si no existe)
        with open(HISTORIAL_CSV, 'a', newline='') as f:
            # Bloqueo exclusivo NO BLOQUEANTE (falla rápido si está ocupado)
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                # Escribir header solo si el archivo está vacío
                if f.tell() == 0:
                    fila.to_csv(f, index=False)
                else:
                    fila.to_csv(f, mode='a', header=False, index=False)
            finally:
                # Liberar bloqueo siempre
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (IOError, OSError) as e:
        # El archivo está bloqueado por otro proceso (Excel, visor, etc.)
        # NO hacer crash: la compra ya se ejecutó en Binance
        print(f"\033[91m⚠️ ADVERTENCIA: La compra se ejecutó, pero el Excel está abierto. Ciérralo para registrar la compra.\033[0m")
        print(f"   Detalle técnico: {e}")
        # Loguear el error en el log de errores para auditoría
        log_error(f"No se pudo escribir en CSV (archivo bloqueado): {e}")

# ============================================================
# FUNCIÓN: OBTENER BALANCE ACTUAL DE LA MONEDA BASE
# ============================================================
def obtener_balance_base():
    """Obtiene balance actual de la moneda base (BTC, ETH, etc.) en la cuenta"""
    try:
        balance = exchange.fetch_balance()
        return balance.get(BASE_CURRENCY, {}).get('free', 0.0)
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
        
        # Calcular cantidad a comprar (redondear a 6 decimales típico)
        cantidad_base = MONTO_USD / precio_actual
        cantidad_base = round(cantidad_base, 6)
        
        print(f"Cantidad a comprar: {cantidad_base:.6f} {BASE_CURRENCY}")
        
        # Ejecutar orden de MERCADO (market buy)
        orden = exchange.create_market_buy_order(PAR, cantidad_base)
        
        # Extraer info de la orden ejecutada
        precio_ejecucion = orden.get('average', precio_actual)
        cantidad_ejecutada = orden.get('filled', cantidad_base)
        costo_total = orden.get('cost', MONTO_USD)
        comision = orden.get('fee', {}).get('cost', 0)
        
        # Obtener balance acumulado después de la compra
        base_acumulado = obtener_balance_base()
        
        # Timestamp de la compra
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Mostrar resultado
        print(f"\n✅ COMPRA EJECUTADA EXITOSAMENTE")
        print(f"   Precio ejecución: ${precio_ejecucion:,.2f}")
        print(f"   Cantidad {BASE_CURRENCY}: {cantidad_ejecutada:.6f}")
        print(f"   Costo total: ${costo_total:.2f}")
        print(f"   Comisión: ${comision:.4f}")
        print(f"   {BASE_CURRENCY} acumulado: {base_acumulado:.6f}")
        print(f"{'='*60}\n")
        
        # Guardar en historial
        guardar_historial(timestamp, precio_ejecucion, MONTO_USD, cantidad_ejecutada, base_acumulado)
        
        return True, {
            'timestamp': timestamp,
            'precio': precio_ejecucion,
            'monto_usd': MONTO_USD,
            f'{BASE_CURRENCY.lower()}_comprado': cantidad_ejecutada,
            f'{BASE_CURRENCY.lower()}_acumulado': base_acumulado,
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
        base_balance = balance.get(BASE_CURRENCY, {}).get('free', 0)
        print(f"💰 Balance inicial:")
        print(f"   USDT: ${usdt_balance:,.2f}")
        print(f"   {BASE_CURRENCY}: {base_balance:.6f}")
        
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