"""
Script de prueba para Alpha Vantage API.
Verifica que la API key esté configurada y que el servicio funcione correctamente.
"""
import asyncio
import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.alpha_vantage_service import AlphaVantageService
from app.core.config import settings


async def test_alpha_vantage():
    """Probar servicio Alpha Vantage"""
    
    print("=" * 60)
    print("Prueba de Alpha Vantage API")
    print("=" * 60)
    print()
    
    # Verificar configuración
    print("1. Verificando configuración...")
    api_key = getattr(settings, "ALPHA_VANTAGE_API_KEY", None)
    if not api_key:
        print("❌ ERROR: ALPHA_VANTAGE_API_KEY no está configurada en .env")
        print("   Agrega: ALPHA_VANTAGE_API_KEY=tu_api_key")
        return
    
    print(f"✅ API Key configurada: {api_key[:8]}...")
    print(f"✅ Servicio habilitado: {getattr(settings, 'ALPHA_VANTAGE_ENABLED', True)}")
    print()
    
    # Inicializar servicio
    print("2. Inicializando servicio...")
    service = AlphaVantageService()
    
    if not service.enabled:
        print("❌ ERROR: Servicio no está habilitado")
        return
    
    print("✅ Servicio inicializado correctamente")
    print()
    
    # Probar obtener tasa USD/COP
    print("3. Probando obtener tasa USD/COP...")
    try:
        rate = await service.get_forex_realtime("USD", "COP")
        if rate:
            print(f"✅ Tasa USD/COP: {rate:,.2f}")
        else:
            print("⚠️  No se pudo obtener la tasa (puede ser rate limit)")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    print()
    
    # Probar obtener RSI
    print("4. Probando obtener RSI para USD/COP...")
    try:
        # Nota: Alpha Vantage requiere formato específico para símbolos Forex
        # Para Forex, el formato puede ser diferente, pero intentemos
        rsi_data = await service.get_rsi("USDCOP", interval="daily")
        if rsi_data:
            latest_rsi = list(rsi_data.values())[0] if rsi_data else None
            print(f"✅ RSI obtenido: {len(rsi_data)} puntos de datos")
            if latest_rsi:
                print(f"   Último valor RSI: {latest_rsi:.2f}")
        else:
            print("⚠️  No se pudo obtener RSI (puede requerir formato de símbolo diferente)")
    except Exception as e:
        print(f"⚠️  Error obteniendo RSI: {str(e)}")
        print("   (Esto puede ser normal si el formato del símbolo no es correcto)")
    print()
    
    # Probar obtener datos históricos
    print("5. Probando obtener datos históricos USD/COP...")
    try:
        historical = await service.get_forex_daily("USD", "COP", outputsize="compact")
        if historical:
            print(f"✅ Datos históricos obtenidos: {len(historical)} días")
            # Mostrar las últimas 3 fechas
            dates = sorted(historical.keys(), reverse=True)[:3]
            for date in dates:
                data = historical[date]
                print(f"   {date}: Open={data['open']:.2f}, High={data['high']:.2f}, Low={data['low']:.2f}, Close={data['close']:.2f}")
        else:
            print("⚠️  No se pudo obtener datos históricos")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    print()
    
    print("=" * 60)
    print("Prueba completada")
    print("=" * 60)
    print()
    print("Notas:")
    print("- Alpha Vantage Free Tier: 25 requests/día")
    print("- El servicio usa caché de 15 minutos para reducir requests")
    print("- Si ves errores de rate limit, espera hasta el día siguiente")
    print()


if __name__ == "__main__":
    asyncio.run(test_alpha_vantage())

