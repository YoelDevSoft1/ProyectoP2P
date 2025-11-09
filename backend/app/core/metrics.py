"""
Métricas Prometheus para monitoreo del sistema.
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from typing import Optional
import time

# ===== MÉTRICAS DE NEGOCIO =====

# Trades
trades_executed_total = Counter(
    'trades_executed_total',
    'Total trades executed',
    ['asset', 'fiat', 'status']
)

trade_profit_usd = Histogram(
    'trade_profit_usd',
    'Trade profit in USD',
    ['asset', 'fiat'],
    buckets=[0, 10, 50, 100, 500, 1000, 5000, float('inf')]
)

trade_volume_usd = Histogram(
    'trade_volume_usd',
    'Trade volume in USD',
    ['asset', 'fiat'],
    buckets=[0, 100, 500, 1000, 5000, 10000, 50000, float('inf')]
)

# Oportunidades de arbitraje
active_arbitrage_opportunities = Gauge(
    'active_arbitrage_opportunities',
    'Number of active arbitrage opportunities',
    ['strategy']
)

arbitrage_opportunities_detected_total = Counter(
    'arbitrage_opportunities_detected_total',
    'Total arbitrage opportunities detected',
    ['strategy', 'asset', 'fiat']
)

arbitrage_profit_percent = Histogram(
    'arbitrage_profit_percent',
    'Arbitrage profit percentage',
    ['strategy'],
    buckets=[0, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, float('inf')]
)

# Precios
price_updates_total = Counter(
    'price_updates_total',
    'Total price updates',
    ['asset', 'fiat', 'source']
)

price_spread_percent = Histogram(
    'price_spread_percent',
    'Price spread percentage',
    ['asset', 'fiat'],
    buckets=[0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float('inf')]
)

# ===== MÉTRICAS TÉCNICAS =====

# HTTP Requests
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# Database
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['query_type', 'table', 'status']
)

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size',
    ['state']  # active, idle, overflow
)

db_connection_errors_total = Counter(
    'db_connection_errors_total',
    'Total database connection errors',
    ['error_type']
)

# Redis
redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status']  # operation: get, set, delete, etc.
)

redis_operation_duration_seconds = Histogram(
    'redis_operation_duration_seconds',
    'Redis operation duration in seconds',
    ['operation'],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

redis_cache_hits_total = Counter(
    'redis_cache_hits_total',
    'Total Redis cache hits',
    ['key_pattern']
)

redis_cache_misses_total = Counter(
    'redis_cache_misses_total',
    'Total Redis cache misses',
    ['key_pattern']
)

redis_connection_errors_total = Counter(
    'redis_connection_errors_total',
    'Total Redis connection errors'
)

# Celery
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']  # status: started, succeeded, failed
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0, 3600.0]
)

celery_tasks_active = Gauge(
    'celery_tasks_active',
    'Number of active Celery tasks',
    ['task_name']
)

celery_tasks_queued = Gauge(
    'celery_tasks_queued',
    'Number of queued Celery tasks',
    ['queue_name']
)

celery_task_retries_total = Counter(
    'celery_task_retries_total',
    'Total Celery task retries',
    ['task_name']
)

# RabbitMQ
rabbitmq_connection_status = Gauge(
    'rabbitmq_connection_status',
    'RabbitMQ connection status (1=connected, 0=disconnected)'
)

rabbitmq_messages_published_total = Counter(
    'rabbitmq_messages_published_total',
    'Total messages published to RabbitMQ',
    ['exchange', 'routing_key']
)

rabbitmq_messages_consumed_total = Counter(
    'rabbitmq_messages_consumed_total',
    'Total messages consumed from RabbitMQ',
    ['queue']
)

# External APIs
external_api_requests_total = Counter(
    'external_api_requests_total',
    'Total external API requests',
    ['api_name', 'endpoint', 'status_code']
)

external_api_request_duration_seconds = Histogram(
    'external_api_request_duration_seconds',
    'External API request duration in seconds',
    ['api_name', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

external_api_errors_total = Counter(
    'external_api_errors_total',
    'Total external API errors',
    ['api_name', 'error_type']
)

# Circuit Breakers
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=half-open, 2=open)',
    ['circuit_name']
)

circuit_breaker_failures_total = Counter(
    'circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['circuit_name']
)

circuit_breaker_opens_total = Counter(
    'circuit_breaker_opens_total',
    'Total circuit breaker opens',
    ['circuit_name']
)

# ===== INFORMACIÓN DEL SISTEMA =====
app_info = Info(
    'app_info',
    'Application information'
)

app_info.info({
    'version': '1.0.0',
    'name': 'Casa de Cambio P2P'
})


# ===== HELPERS =====

class MetricsMiddleware:
    """Middleware para capturar métricas automáticamente"""
    
    @staticmethod
    def track_request(method: str, endpoint: str, status_code: int, duration: float):
        """Registrar métricas de request HTTP"""
        # Normalizar endpoint para evitar demasiadas métricas únicas
        # Ej: /api/v1/prices/USDT/COP -> /api/v1/prices/{asset}/{fiat}
        normalized_endpoint = endpoint
        if "/prices/" in endpoint and endpoint.count("/") >= 4:
            parts = endpoint.split("/")
            if len(parts) >= 5:
                normalized_endpoint = f"{parts[0]}/{parts[1]}/{parts[2]}/{parts[3]}/{{asset}}/{{fiat}}"
        
        http_requests_total.labels(
            method=method,
            endpoint=normalized_endpoint,
            status_code=status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=normalized_endpoint,
            status_code=status_code
        ).observe(duration)
    
    @staticmethod
    def track_db_query(query_type: str, table: str, duration: float, status: str = "success"):
        """Registrar métricas de query de base de datos"""
        db_queries_total.labels(
            query_type=query_type,
            table=table,
            status=status
        ).inc()
        
        db_query_duration_seconds.labels(
            query_type=query_type,
            table=table
        ).observe(duration)
    
    @staticmethod
    def track_redis_operation(operation: str, duration: float, status: str = "success"):
        """Registrar métricas de operación Redis"""
        redis_operations_total.labels(
            operation=operation,
            status=status
        ).inc()
        
        redis_operation_duration_seconds.labels(
            operation=operation
        ).observe(duration)
    
    @staticmethod
    def track_cache_hit(key_pattern: str):
        """Registrar cache hit"""
        redis_cache_hits_total.labels(key_pattern=key_pattern).inc()
    
    @staticmethod
    def track_cache_miss(key_pattern: str):
        """Registrar cache miss"""
        redis_cache_misses_total.labels(key_pattern=key_pattern).inc()
    
    @staticmethod
    def track_celery_task(task_name: str, duration: Optional[float] = None, status: str = "succeeded"):
        """Registrar métricas de tarea Celery"""
        celery_tasks_total.labels(task_name=task_name, status=status).inc()
        
        if duration is not None:
            celery_task_duration_seconds.labels(task_name=task_name).observe(duration)
    
    @staticmethod
    def track_external_api(api_name: str, endpoint: str, duration: float, status_code: int):
        """Registrar métricas de API externa"""
        external_api_requests_total.labels(
            api_name=api_name,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        external_api_request_duration_seconds.labels(
            api_name=api_name,
            endpoint=endpoint
        ).observe(duration)
    
    @staticmethod
    def update_circuit_breaker_state(circuit_name: str, state: int):
        """Actualizar estado del circuit breaker (0=closed, 1=half-open, 2=open)"""
        circuit_breaker_state.labels(circuit_name=circuit_name).set(state)
    
    @staticmethod
    def track_circuit_breaker_failure(circuit_name: str):
        """Registrar fallo en circuit breaker"""
        circuit_breaker_failures_total.labels(circuit_name=circuit_name).inc()
    
    @staticmethod
    def track_circuit_breaker_open(circuit_name: str):
        """Registrar apertura de circuit breaker"""
        circuit_breaker_opens_total.labels(circuit_name=circuit_name).inc()


# Instancia global
metrics = MetricsMiddleware()

