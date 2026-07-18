#!/bin/bash
# ============================================================
# ACCESO DIRECTO DCA - Compra semanal manual de BTC/ETH/etc.
# Ejecuta: source venv -> python bot_dca.py -> espera Enter
# ============================================================

# Ir al directorio del proyecto (raíz del repo, NO donde está este script)
cd "$(dirname "$0")/.."

echo "============================================================"
echo "  BOT DCA - COMPRA SEMANAL MANUAL"
echo "============================================================"
echo ""

# Activar entorno virtual
if [ -f "/home/alancito/venv/bin/activate" ]; then
    source /home/alancito/venv/bin/activate
    echo "✅ Entorno virtual activado: $(which python)"
else
    echo "❌ ERROR: No se encuentra /home/alancito/venv/bin/activate"
    read -p "Presiona Enter para cerrar..."
    exit 1
fi

# Cargar variables de entorno desde .env si existe (en la raíz del proyecto)
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo "✅ Variables .env cargadas"
else
    echo "⚠️  Archivo .env no encontrado (usando defaults)"
fi

echo ""
echo "🚀 Ejecutando bot_dca/bot_dca.py..."
echo "----------------------------------------------------------"
echo ""

# Ejecutar el bot
python bot_dca/bot_dca.py

# Capturar código de salida
EXIT_CODE=$?

echo ""
echo "----------------------------------------------------------"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ COMPRA COMPLETADA EXITOSAMENTE"
else
    echo "❌ HUBO UN ERROR (código: $EXIT_CODE)"
    echo "   Revisa resultados/errores_dca.log para más detalles"
fi
echo ""

# Esperar a que el usuario presione Enter antes de cerrar
read -p "Presiona Enter para cerrar esta ventana..."
