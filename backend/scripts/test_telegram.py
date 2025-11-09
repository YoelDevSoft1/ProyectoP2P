#!/usr/bin/env python3
"""
Script de diagnóstico para el bot de Telegram.
Verifica la configuración y prueba el envío de mensajes.
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.services.telegram_service import telegram_service


async def test_telegram():
    """Probar el servicio de Telegram"""
    print("=" * 60)
    print("DIAGNÓSTICO DEL BOT DE TELEGRAM")
    print("=" * 60)
    print()
    
    # 1. Verificar configuración
    print("1. Verificando configuración...")
    print(f"   ENABLE_NOTIFICATIONS: {settings.ENABLE_NOTIFICATIONS}")
    print(f"   TELEGRAM_BOT_TOKEN: {'✅ Configurado' if settings.TELEGRAM_BOT_TOKEN else '❌ No configurado'}")
    print(f"   TELEGRAM_CHAT_ID: {'✅ Configurado' if settings.TELEGRAM_CHAT_ID else '❌ No configurado'}")
    print()
    
    if not settings.ENABLE_NOTIFICATIONS:
        print("❌ ERROR: Las notificaciones están deshabilitadas")
        print("   Configura ENABLE_NOTIFICATIONS=true en tu archivo .env")
        return False
    
    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN no está configurado")
        print("   Obtén un token de @BotFather en Telegram y configúralo en .env")
        return False
    
    if not settings.TELEGRAM_CHAT_ID:
        print("❌ ERROR: TELEGRAM_CHAT_ID no está configurado")
        print("   Obtén tu chat ID y configúralo en .env")
        return False
    
    # 2. Verificar estado del servicio
    print("2. Verificando estado del servicio...")
    print(f"   Servicio habilitado: {'✅ Sí' if telegram_service.enabled else '❌ No'}")
    print(f"   Chat IDs configurados: {len(telegram_service.chat_ids)}")
    if telegram_service.chat_ids:
        print(f"   Chat IDs: {', '.join(telegram_service.chat_ids)}")
    print()
    
    if not telegram_service.enabled:
        print("❌ ERROR: El servicio de Telegram no está habilitado")
        print("   Revisa los logs para más detalles")
        return False
    
    # 3. Verificar salud del bot
    print("3. Verificando salud del bot...")
    try:
        health = await telegram_service.health_check()
        if health:
            print("   ✅ Bot está saludable")
        else:
            print("   ⚠️  Bot no está saludable")
    except Exception as e:
        print(f"   ❌ Error en health check: {e}")
    print()
    
    # 4. Probar conexión
    print("4. Probando conexión...")
    try:
        result = await telegram_service.test_connection()
        print(f"   Estado: {result.get('status')}")
        if result.get('status') == 'success':
            print(f"   ✅ Conexión exitosa")
            print(f"   Bot: @{result.get('bot_username')}")
            print(f"   Chat IDs: {result.get('chat_ids')}")
        else:
            print(f"   ❌ Error: {result.get('message')}")
            if result.get('error_type'):
                print(f"   Tipo de error: {result.get('error_type')}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    print()
    
    # 5. Enviar mensaje de prueba
    print("5. Enviando mensaje de prueba...")
    try:
        from datetime import datetime as dt
        test_message = f"""
✅ *TEST DE TELEGRAM BOT* ✅

🤖 El bot está funcionando correctamente.

📝 Este es un mensaje de prueba desde el script de diagnóstico.

⏰ Fecha: {dt.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """
        
        success = await telegram_service.send_message(
            text=test_message,
            parse_mode="Markdown",
            priority="normal"
        )
        
        if success:
            print("   ✅ Mensaje enviado exitosamente")
            print("   Revisa tu Telegram para confirmar")
        else:
            print("   ❌ Error al enviar mensaje")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    print("=" * 60)
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_telegram())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

