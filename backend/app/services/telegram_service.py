"""
Servicio mejorado de Telegram con manejo robusto de errores, rate limiting y retries.
"""
import asyncio
import time
from typing import Dict, Optional, List, Union
from datetime import datetime, timedelta
from enum import Enum
import structlog
from functools import wraps

from app.core.config import settings
from app.core.metrics import (
    metrics,
    telegram_messages_sent_total,
    telegram_message_send_duration_seconds,
    telegram_errors_total
)

logger = structlog.get_logger()


class TelegramErrorType(Enum):
    """Tipos de errores de Telegram"""
    NETWORK_ERROR = "network_error"
    RATE_LIMIT = "rate_limit"
    CHAT_NOT_FOUND = "chat_not_found"
    BOT_BLOCKED = "bot_blocked"
    INVALID_TOKEN = "invalid_token"
    MESSAGE_TOO_LONG = "message_too_long"
    INVALID_MARKDOWN = "invalid_markdown"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class TelegramRateLimiter:
    """Rate limiter para Telegram API"""
    
    def __init__(self, max_messages_per_second: float = 20.0, burst: int = 5):
        """
        Args:
            max_messages_per_second: Máximo de mensajes por segundo
            burst: Número de mensajes que se pueden enviar en ráfaga
        """
        self.max_messages_per_second = max_messages_per_second
        self.burst = burst
        self.min_interval = 1.0 / max_messages_per_second
        self._last_send_time = 0.0
        self._token_bucket = burst
        self._last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Esperar hasta que se pueda enviar un mensaje"""
        async with self._lock:
            now = time.time()
            
            # Refill token bucket
            elapsed = now - self._last_refill
            tokens_to_add = elapsed * self.max_messages_per_second
            self._token_bucket = min(self.burst, self._token_bucket + tokens_to_add)
            self._last_refill = now
            
            # Si hay tokens disponibles, usar uno
            if self._token_bucket >= 1:
                self._token_bucket -= 1
                return
            
            # Calcular tiempo de espera
            wait_time = self.min_interval - (now - self._last_send_time)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            self._last_send_time = time.time()


class TelegramService:
    """
    Servicio mejorado de Telegram con:
    - Retry con exponential backoff
    - Rate limiting
    - Validación de configuración
    - Manejo de mensajes largos
    - Soporte para botones inline
    - Manejo robusto de errores
    - Timeouts
    - Métricas
    """
    
    # Límites de Telegram
    MAX_MESSAGE_LENGTH = 4096
    MAX_CAPTION_LENGTH = 1024
    
    def __init__(self):
        self.enabled = False
        self.bot = None
        self.chat_ids: List[str] = []
        self.rate_limiter = TelegramRateLimiter(max_messages_per_second=20.0, burst=5)
        self._last_health_check: Optional[datetime] = None
        self._health_check_interval = timedelta(minutes=5)
        self._is_healthy = False
        
        self._initialize()
    
    def _initialize(self) -> None:
        """Inicializar servicio de Telegram"""
        if not settings.ENABLE_NOTIFICATIONS:
            logger.debug("Telegram disabled: ENABLE_NOTIFICATIONS is False")
            return
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram disabled: TELEGRAM_BOT_TOKEN not configured")
            return
        
        try:
            from telegram import Bot
            from telegram.error import TelegramError
            
            # Crear instancia del bot con timeout explícito
            self.bot = Bot(
                token=settings.TELEGRAM_BOT_TOKEN,
                request=None,  # Usar request por defecto
            )
            
            # Parsear chat_ids (puede ser uno o múltiples separados por comas)
            chat_id_str = settings.TELEGRAM_CHAT_ID or ""
            if chat_id_str:
                # Convertir chat_ids a string para asegurar compatibilidad
                self.chat_ids = [str(cid.strip()) for cid in chat_id_str.split(",") if cid.strip()]
            else:
                logger.warning("Telegram disabled: TELEGRAM_CHAT_ID not configured")
                return
            
            if not self.chat_ids:
                logger.warning("Telegram disabled: No valid chat IDs found")
                return
            
            self.enabled = True
            logger.info(
                "Telegram service initialized",
                chat_ids_count=len(self.chat_ids),
                chat_ids=self.chat_ids
            )
            
        except ImportError as e:
            logger.warning(
                "python-telegram-bot not installed, Telegram notifications disabled",
                error=str(e)
            )
            self.enabled = False
        except Exception as e:
            logger.error(
                "Error initializing Telegram service",
                error=str(e),
                error_type=type(e).__name__
            )
            self.enabled = False
    
    async def health_check(self) -> bool:
        """Verificar salud del servicio de Telegram"""
        if not self.enabled:
            return False
        
        # Verificar salud periódicamente
        now = datetime.utcnow()
        if (
            self._last_health_check
            and (now - self._last_health_check) < self._health_check_interval
        ):
            return self._is_healthy
        
        try:
            # Intentar obtener información del bot
            bot_info = await asyncio.wait_for(
                self.bot.get_me(),
                timeout=5.0
            )
            
            self._is_healthy = True
            self._last_health_check = now
            logger.debug("Telegram health check passed", bot_username=bot_info.username)
            return True
            
        except asyncio.TimeoutError:
            logger.warning("Telegram health check timeout")
            self._is_healthy = False
            return False
        except Exception as e:
            logger.warning("Telegram health check failed", error=str(e))
            self._is_healthy = False
            return False
    
    def _classify_error(self, error: Exception) -> TelegramErrorType:
        """Clasificar error de Telegram"""
        error_str = str(error).lower()
        
        if "timeout" in error_str or "timed out" in error_str:
            return TelegramErrorType.TIMEOUT
        elif "rate limit" in error_str or "too many requests" in error_str:
            return TelegramErrorType.RATE_LIMIT
        elif "chat not found" in error_str:
            return TelegramErrorType.CHAT_NOT_FOUND
        elif "bot was blocked" in error_str or "blocked by the user" in error_str:
            return TelegramErrorType.BOT_BLOCKED
        elif "unauthorized" in error_str or "invalid token" in error_str:
            return TelegramErrorType.INVALID_TOKEN
        elif "message is too long" in error_str or "message too long" in error_str:
            return TelegramErrorType.MESSAGE_TOO_LONG
        elif "can't parse" in error_str or "parse error" in error_str:
            return TelegramErrorType.INVALID_MARKDOWN
        elif "network" in error_str or "connection" in error_str:
            return TelegramErrorType.NETWORK_ERROR
        else:
            return TelegramErrorType.UNKNOWN
    
    def _should_retry(self, error_type: TelegramErrorType, attempt: int, max_retries: int) -> bool:
        """Determinar si se debe reintentar"""
        if attempt >= max_retries:
            return False
        
        # No reintentar para errores que no se resolverán con retry
        if error_type in [
            TelegramErrorType.CHAT_NOT_FOUND,
            TelegramErrorType.BOT_BLOCKED,
            TelegramErrorType.INVALID_TOKEN,
            TelegramErrorType.MESSAGE_TOO_LONG,
        ]:
            return False
        
        # Reintentar para errores temporales
        return error_type in [
            TelegramErrorType.NETWORK_ERROR,
            TelegramErrorType.RATE_LIMIT,
            TelegramErrorType.TIMEOUT,
            TelegramErrorType.UNKNOWN,
        ]
    
    async def _send_with_retry(
        self,
        chat_id: str,
        text: str,
        parse_mode: Optional[str] = "Markdown",
        reply_markup: Optional[Dict] = None,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> bool:
        """
        Enviar mensaje con retry y exponential backoff.
        
        Args:
            chat_id: ID del chat
            text: Texto del mensaje
            parse_mode: Modo de parseo (Markdown, HTML, None)
            reply_markup: Botones inline (opcional)
            max_retries: Número máximo de reintentos
            initial_delay: Delay inicial en segundos
        
        Returns:
            True si se envió exitosamente
        """
        if not self.enabled or not self.bot:
            return False
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
        last_error_type = None
        send_start_time = time.time()
        self._send_start_time = send_start_time
        
        for attempt in range(max_retries + 1):
            try:
                # Intentar enviar con timeout
                await asyncio.wait_for(
                    self.bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup,
                        disable_web_page_preview=False,
                    ),
                    timeout=10.0
                )
                
                # Éxito - calcular duración
                send_duration = time.time() - send_start_time
                telegram_messages_sent_total.labels(status="success", error_type="none").inc()
                if send_duration > 0:
                    telegram_message_send_duration_seconds.observe(send_duration)
                logger.debug("Telegram message sent", chat_id=chat_id, attempt=attempt + 1, duration=send_duration)
                return True
                
            except asyncio.TimeoutError:
                error_type = TelegramErrorType.TIMEOUT
                last_error_type = error_type
                logger.warning(
                    "Telegram send timeout",
                    chat_id=chat_id,
                    attempt=attempt + 1,
                    max_retries=max_retries
                )
                
            except Exception as e:
                error_type = self._classify_error(e)
                last_error_type = error_type
                
                logger.warning(
                    "Telegram send error",
                    chat_id=chat_id,
                    error_type=error_type.value,
                    error=str(e),
                    attempt=attempt + 1,
                    max_retries=max_retries
                )
                
                # Si es error de Markdown, intentar con HTML o sin formato
                if error_type == TelegramErrorType.INVALID_MARKDOWN:
                    if parse_mode == "Markdown":
                        logger.debug("Retrying with HTML format")
                        return await self._send_with_retry(
                            chat_id=chat_id,
                            text=text,
                            parse_mode="HTML",
                            reply_markup=reply_markup,
                            max_retries=0,  # No más reintentos
                        )
                    elif parse_mode == "HTML":
                        logger.debug("Retrying without format")
                        return await self._send_with_retry(
                            chat_id=chat_id,
                            text=self._strip_formatting(text),
                            parse_mode=None,
                            reply_markup=reply_markup,
                            max_retries=0,  # No más reintentos
                        )
                
                # Si no se debe reintentar, salir
                if not self._should_retry(error_type, attempt, max_retries):
                    telegram_errors_total.labels(error_type=error_type.value).inc()
                    telegram_messages_sent_total.labels(status="failed", error_type=error_type.value).inc()
                    return False
                
                # Calcular delay con exponential backoff
                delay = initial_delay * (2 ** attempt)
                
                # Para rate limiting, esperar más tiempo
                if error_type == TelegramErrorType.RATE_LIMIT:
                    delay = max(delay, 5.0)
                
                logger.debug(
                    "Retrying Telegram send",
                    chat_id=chat_id,
                    attempt=attempt + 1,
                    delay=delay
                )
                
                await asyncio.sleep(delay)
        
        # Todos los reintentos fallaron
        error_type_value = last_error_type.value if last_error_type else "unknown"
        telegram_errors_total.labels(error_type=error_type_value).inc()
        telegram_messages_sent_total.labels(status="failed", error_type=error_type_value).inc()
        logger.error(
            "Failed to send Telegram message after retries",
            chat_id=chat_id,
            max_retries=max_retries,
            last_error_type=error_type_value
        )
        return False
    
    def _strip_formatting(self, text: str) -> str:
        """Eliminar formato Markdown/HTML del texto"""
        import re
        # Eliminar Markdown
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # Italic
        text = re.sub(r'__(.*?)__', r'\1', text)  # Bold
        text = re.sub(r'_(.*?)_', r'\1', text)  # Italic
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Links
        text = re.sub(r'`(.*?)`', r'\1', text)  # Code
        # Eliminar HTML
        text = re.sub(r'<[^>]+>', '', text)  # HTML tags
        return text
    
    def _split_message(self, text: str, max_length: int = MAX_MESSAGE_LENGTH) -> List[str]:
        """Dividir mensaje largo en múltiples mensajes"""
        if len(text) <= max_length:
            return [text]
        
        messages = []
        lines = text.split('\n')
        current_message = ""
        
        for line in lines:
            # Si agregar esta línea excede el límite, guardar mensaje actual
            if len(current_message) + len(line) + 1 > max_length:
                if current_message:
                    messages.append(current_message.strip())
                    current_message = ""
                
                # Si la línea sola es muy larga, dividirla
                if len(line) > max_length:
                    # Dividir por palabras si es posible
                    words = line.split(' ')
                    for word in words:
                        if len(current_message) + len(word) + 1 > max_length:
                            if current_message:
                                messages.append(current_message.strip())
                            current_message = word + " "
                        else:
                            current_message += word + " "
                else:
                    current_message = line + "\n"
            else:
                current_message += line + "\n"
        
        # Agregar último mensaje
        if current_message:
            messages.append(current_message.strip())
        
        return messages
    
    async def send_message(
        self,
        text: str,
        parse_mode: Optional[str] = "Markdown",
        reply_markup: Optional[Dict] = None,
        priority: str = "normal",
        chat_ids: Optional[List[str]] = None,
    ) -> bool:
        """
        Enviar mensaje a Telegram.
        
        Args:
            text: Texto del mensaje
            parse_mode: Modo de parseo (Markdown, HTML, None)
            reply_markup: Botones inline (opcional)
            priority: Prioridad (normal, high, critical)
            chat_ids: Lista de chat IDs (si None, usa los configurados)
        
        Returns:
            True si se envió a al menos un chat
        """
        if not self.enabled:
            return False
        
        # Usar chat_ids proporcionados o los configurados
        target_chat_ids = chat_ids or self.chat_ids
        if not target_chat_ids:
            logger.warning("No chat IDs available for Telegram message")
            return False
        
        # Dividir mensaje si es muy largo
        messages = self._split_message(text)
        
        success_count = 0
        total_chats = len(target_chat_ids)
        
        for chat_id in target_chat_ids:
            chat_success = True
            
            for i, message_text in enumerate(messages):
                # Agregar indicador de mensaje múltiple si es necesario
                if len(messages) > 1:
                    message_text = f"📄 *Parte {i + 1}/{len(messages)}*\n\n{message_text}"
                
                sent = await self._send_with_retry(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup if i == len(messages) - 1 else None,  # Botones solo en último mensaje
                )
                
                if not sent:
                    chat_success = False
                    break
                
                # Pequeño delay entre mensajes múltiples
                if i < len(messages) - 1:
                    await asyncio.sleep(0.5)
            
            if chat_success:
                success_count += 1
        
        # Log resultado
        if success_count > 0:
            logger.info(
                "Telegram message sent",
                success_count=success_count,
                total_chats=total_chats,
                message_count=len(messages),
                priority=priority
            )
            return True
        else:
            logger.error(
                "Failed to send Telegram message to any chat",
                total_chats=total_chats
            )
            return False
    
    def create_inline_keyboard(self, buttons: List[List[Dict[str, str]]]) -> Optional[Dict]:
        """
        Crear teclado inline con botones.
        
        Args:
            buttons: Lista de listas de botones. Cada lista interna es una fila.
                     Cada botón es un dict con 'text' y 'url' o 'callback_data'.
        
        Returns:
            Dict con formato de reply_markup o None si hay error
        """
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = []
            for row in buttons:
                keyboard_row = []
                for button in row:
                    if 'url' in button:
                        keyboard_row.append(
                            InlineKeyboardButton(text=button['text'], url=button['url'])
                        )
                    elif 'callback_data' in button:
                        keyboard_row.append(
                            InlineKeyboardButton(text=button['text'], callback_data=button['callback_data'])
                        )
                if keyboard_row:
                    keyboard.append(keyboard_row)
            
            if keyboard:
                return InlineKeyboardMarkup(keyboard)
            return None
            
        except ImportError:
            logger.warning("Cannot create inline keyboard: telegram not installed")
            return None
        except Exception as e:
            logger.error("Error creating inline keyboard", error=str(e))
            return None
    
    async def test_connection(self) -> Dict[str, any]:
        """
        Probar conexión con Telegram.
        
        Returns:
            Dict con resultado de la prueba
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "Telegram service is disabled",
                "enabled": False
            }
        
        try:
            # Verificar bot
            bot_info = await asyncio.wait_for(self.bot.get_me(), timeout=5.0)
            
            # Verificar chat
            test_message = f"✅ *TEST DE CONEXIÓN*\n\n⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n🤖 Bot: @{bot_info.username}\n✅ Conexión exitosa"
            
            success = await self.send_message(
                text=test_message,
                parse_mode="Markdown",
                priority="normal"
            )
            
            if success:
                return {
                    "status": "success",
                    "message": "Telegram connection test successful",
                    "enabled": True,
                    "bot_username": bot_info.username,
                    "chat_ids": self.chat_ids,
                    "health": self._is_healthy
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to send test message",
                    "enabled": True,
                    "bot_username": bot_info.username,
                    "chat_ids": self.chat_ids
                }
                
        except asyncio.TimeoutError:
            return {
                "status": "error",
                "message": "Telegram API timeout",
                "enabled": True
            }
        except Exception as e:
            error_type = self._classify_error(e)
            return {
                "status": "error",
                "message": str(e),
                "error_type": error_type.value,
                "enabled": True
            }


# Instancia global del servicio
telegram_service = TelegramService()

