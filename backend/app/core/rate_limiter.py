"""
Rate limiter global usando Redis para coordinar solicitudes entre múltiples workers.
"""
import asyncio
import time
from typing import Optional
import structlog
from app.core.redis_pool import redis_pool

logger = structlog.get_logger()


class GlobalRateLimiter:
    """
    Rate limiter global usando Redis para coordinar solicitudes
    entre múltiples workers de Celery.
    
    Usa un token bucket distribuido implementado con Redis.
    Los scripts Lua están cacheados para mejor rendimiento.
    """
    
    # Script Lua para token bucket (cacheado)
    LUA_SCRIPT = """
    local key = KEYS[1]
    local last_update_key = KEYS[2]
    local rate = tonumber(ARGV[1])
    local burst = tonumber(ARGV[2])
    local tokens_requested = tonumber(ARGV[3])
    local now = tonumber(ARGV[4])
    
    -- Obtener estado actual
    local current_tokens = tonumber(redis.call('GET', key) or burst)
    local last_update = tonumber(redis.call('GET', last_update_key) or now)
    
    -- Calcular tokens a agregar basado en el tiempo transcurrido
    local elapsed = now - last_update
    local tokens_to_add = elapsed * rate
    
    -- Actualizar tokens (no exceder burst)
    current_tokens = math.min(burst, current_tokens + tokens_to_add)
    
    -- Verificar si hay suficientes tokens
    if current_tokens >= tokens_requested then
        -- Consumir tokens
        current_tokens = current_tokens - tokens_requested
        redis.call('SET', key, current_tokens)
        redis.call('SET', last_update_key, now)
        redis.call('EXPIRE', key, 60)
        redis.call('EXPIRE', last_update_key, 60)
        return 1
    else
        -- No hay suficientes tokens, actualizar estado pero no consumir
        redis.call('SET', key, current_tokens)
        redis.call('SET', last_update_key, now)
        redis.call('EXPIRE', key, 60)
        redis.call('EXPIRE', last_update_key, 60)
        return 0
    end
    """
    
    def __init__(
        self,
        rate: float = 10.0,  # 10 requests por segundo
        burst: int = 20,  # Permitir hasta 20 requests en ráfaga
        key_prefix: str = "rate_limit:binance_p2p"
    ):
        self.rate = rate  # Tokens por segundo
        self.burst = burst  # Capacidad máxima del bucket
        self.key_prefix = key_prefix
        self.key = f"{key_prefix}:tokens"
        self.last_update_key = f"{key_prefix}:last_update"
        self._script_sha: Optional[str] = None  # SHA del script Lua cacheado
    
    async def _load_script(self, redis_client) -> str:
        """
        Cargar script Lua en Redis y cachear el SHA.
        Esto mejora el rendimiento al evitar enviar el script en cada operación.
        
        Args:
            redis_client: Cliente Redis
            
        Returns:
            SHA del script cacheado
        """
        if self._script_sha is None:
            try:
                # Cargar script en Redis y obtener SHA
                self._script_sha = await redis_client.script_load(self.LUA_SCRIPT)
                logger.debug("Rate limiter Lua script loaded and cached", sha=self._script_sha[:8])
            except Exception as e:
                logger.warning("Failed to load Lua script, using eval instead", error=str(e))
                # Si falla, usaremos eval directamente (menos eficiente pero funciona)
                self._script_sha = None
        
        return self._script_sha
    
    async def acquire(self, tokens: int = 1) -> bool:
        """
        Intentar adquirir tokens. Retorna True si se pueden adquirir, False en caso contrario.
        
        Args:
            tokens: Número de tokens a adquirir (default: 1)
            
        Returns:
            True si se pueden adquirir los tokens, False si se debe esperar
        """
        try:
            redis_client = await redis_pool.get_client()
            if not redis_client:
                # Si Redis no está disponible, permitir la solicitud pero loguear advertencia
                logger.warning("Redis not available for rate limiting, allowing request")
                return True
            
            now = time.time()
            
            # Intentar usar script cacheado (EVALSHA)
            script_sha = await self._load_script(redis_client)
            
            try:
                if script_sha:
                    # Usar EVALSHA con script cacheado (más eficiente)
                    result = await redis_client.evalsha(
                        script_sha,
                        2,
                        self.key,
                        self.last_update_key,
                        str(self.rate),
                        str(self.burst),
                        str(tokens),
                        str(now)
                    )
                else:
                    # Fallback a EVAL si no se pudo cachear el script
                    result = await redis_client.eval(
                        self.LUA_SCRIPT,
                        2,
                        self.key,
                        self.last_update_key,
                        str(self.rate),
                        str(self.burst),
                        str(tokens),
                        str(now)
                    )
            except Exception as e:
                # Si EVALSHA falla (script no encontrado), recargar y usar EVAL
                if "NOSCRIPT" in str(e) or "not found" in str(e).lower():
                    logger.debug("Script not found in cache, reloading")
                    self._script_sha = None
                    result = await redis_client.eval(
                        self.LUA_SCRIPT,
                        2,
                        self.key,
                        self.last_update_key,
                        str(self.rate),
                        str(self.burst),
                        str(tokens),
                        str(now)
                    )
                else:
                    raise
            
            return bool(result)
            
        except Exception as e:
            logger.error("Error in rate limiter", error=str(e))
            # En caso de error, permitir la solicitud para no bloquear el sistema
            return True
    
    async def wait_for_token(self, tokens: int = 1, max_wait: float = 5.0) -> bool:
        """
        Esperar hasta que haya tokens disponibles.
        
        Args:
            tokens: Número de tokens a adquirir
            max_wait: Tiempo máximo de espera en segundos
            
        Returns:
            True si se adquirieron los tokens, False si se agotó el tiempo de espera
        """
        start_time = time.time()
        wait_interval = 0.1  # Esperar 100ms entre intentos
        
        while (time.time() - start_time) < max_wait:
            if await self.acquire(tokens):
                return True
            await asyncio.sleep(wait_interval)
        
        return False


# Instancia global de rate limiter para Binance P2P API
# 8 requests por segundo (más conservador que 10)
# Burst de 15 para permitir algunas solicitudes rápidas
binance_p2p_rate_limiter = GlobalRateLimiter(
    rate=8.0,  # 8 requests por segundo
    burst=15,  # Permitir hasta 15 requests en ráfaga
    key_prefix="rate_limit:binance_p2p"
)

