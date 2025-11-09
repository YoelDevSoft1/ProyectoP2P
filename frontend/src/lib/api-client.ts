/**
 * Cliente de API mejorado con retry logic, circuit breaker y manejo robusto de errores.
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_V1 = `${API_URL}/api/v1`

class CircuitBreaker {
  private failures: number = 0
  private lastFailureTime: number = 0
  private state: 'closed' | 'open' | 'half-open' = 'closed'
  private readonly failureThreshold: number = 5
  private readonly timeout: number = 30000 // 30 segundos
  private readonly resetTimeout: number = 60000 // 1 minuto

  canAttempt(): boolean {
    const now = Date.now()

    // Si está cerrado, permitir requests
    if (this.state === 'closed') {
      return true
    }

    // Si está abierto, verificar si ha pasado el timeout
    if (this.state === 'open') {
      if (now - this.lastFailureTime > this.resetTimeout) {
        this.state = 'half-open'
        this.failures = 0
        return true
      }
      return false
    }

    // Si está half-open, permitir un intento
    if (this.state === 'half-open') {
      return true
    }

    return false
  }

  recordSuccess(): void {
    this.failures = 0
    this.state = 'closed'
  }

  recordFailure(): void {
    this.failures++
    this.lastFailureTime = Date.now()

    if (this.failures >= this.failureThreshold) {
      this.state = 'open'
    }
  }

  getState(): string {
    return this.state
  }
}

// Instancia global del circuit breaker
const circuitBreaker = new CircuitBreaker()

// Retry configuration
interface RetryConfig {
  retries: number
  retryDelay: number
  retryCondition?: (error: AxiosError) => boolean
}

const defaultRetryConfig: RetryConfig = {
  retries: 3,
  retryDelay: 1000,
  retryCondition: (error: AxiosError) => {
    // Solo reintentar para errores de red o timeout
    if (!error.response) {
      return true // Error de red
    }
    // Reintentar para errores 5xx (server errors)
    if (error.response.status >= 500) {
      return true
    }
    // Reintentar para timeout
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      return true
    }
    return false
  },
}

// Función para retry con exponential backoff
async function retryRequest<T>(
  fn: () => Promise<T>,
  config: RetryConfig = defaultRetryConfig
): Promise<T> {
  let lastError: AxiosError

  for (let attempt = 0; attempt <= config.retries; attempt++) {
    try {
      // Verificar circuit breaker antes de hacer la request
      if (!circuitBreaker.canAttempt()) {
        throw new Error('Circuit breaker is open. API is unavailable.')
      }

      const result = await fn()
      circuitBreaker.recordSuccess()
      return result
    } catch (error) {
      lastError = error as AxiosError

      // Si es el último intento, no reintentar
      if (attempt === config.retries) {
        circuitBreaker.recordFailure()
        throw error
      }

      // Verificar si se debe reintentar
      if (config.retryCondition && !config.retryCondition(lastError)) {
        throw error
      }

      // Calcular delay con exponential backoff
      const delay = config.retryDelay * Math.pow(2, attempt)
      await new Promise((resolve) => setTimeout(resolve, delay))
    }
  }

  circuitBreaker.recordFailure()
  throw lastError!
}

// Crear instancia de axios con configuración mejorada
const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_V1,
  timeout: 30000, // 30 segundos (aumentado de 10s)
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true',
  },
})

// Interceptor de request
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Agregar timestamp para evitar caché
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now(),
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor de response mejorado
axiosInstance.interceptors.response.use(
  (response) => {
    circuitBreaker.recordSuccess()
    return response
  },
  async (error: AxiosError) => {
    // Solo loguear errores que no sean timeouts normales
    if (error.code !== 'ECONNABORTED') {
      console.error('API Error:', {
        message: error.message,
        code: error.code,
        status: error.response?.status,
        url: error.config?.url,
        circuitBreakerState: circuitBreaker.getState(),
      })
    }

    // Si el circuit breaker está abierto, retornar error inmediatamente
    if (!circuitBreaker.canAttempt()) {
      return Promise.reject(
        new Error('API is temporarily unavailable. Please try again later.')
      )
    }

    return Promise.reject(error)
  }
)

// Función helper para hacer requests con retry
async function requestWithRetry<T>(
  requestFn: () => Promise<T>,
  retryConfig?: Partial<RetryConfig>
): Promise<T> {
  const config = { ...defaultRetryConfig, ...retryConfig }
  return retryRequest(requestFn, config)
}

// Local Storage Cache para datos críticos
class LocalCache {
  private readonly prefix = 'p2p_cache_'
  private readonly defaultTTL = 5 * 60 * 1000 // 5 minutos

  set(key: string, value: any, ttl: number = this.defaultTTL): void {
    try {
      const item = {
        value,
        timestamp: Date.now(),
        ttl,
      }
      localStorage.setItem(`${this.prefix}${key}`, JSON.stringify(item))
    } catch (error) {
      // Si localStorage no está disponible, ignorar
      console.warn('LocalStorage not available:', error)
    }
  }

  get<T>(key: string): T | null {
    try {
      const itemStr = localStorage.getItem(`${this.prefix}${key}`)
      if (!itemStr) return null

      const item = JSON.parse(itemStr)
      const now = Date.now()

      // Verificar si el item expiró
      if (now - item.timestamp > item.ttl) {
        localStorage.removeItem(`${this.prefix}${key}`)
        return null
      }

      return item.value as T
    } catch (error) {
      return null
    }
  }

  clear(key: string): void {
    try {
      localStorage.removeItem(`${this.prefix}${key}`)
    } catch (error) {
      // Ignorar
    }
  }

  clearAll(): void {
    try {
      const keys = Object.keys(localStorage)
      keys.forEach((key) => {
        if (key.startsWith(this.prefix)) {
          localStorage.removeItem(key)
        }
      })
    } catch (error) {
      // Ignorar
    }
  }
}

const localCache = new LocalCache()

// Función helper para requests con caché y fallback
async function requestWithCache<T>(
  cacheKey: string,
  requestFn: () => Promise<T>,
  options: {
    cacheTTL?: number
    useCache?: boolean
    fallbackToCache?: boolean
  } = {}
): Promise<T> {
  const { cacheTTL = 5 * 60 * 1000, useCache = true, fallbackToCache = true } = options

  // Intentar obtener de caché primero
  if (useCache) {
    const cached = localCache.get<T>(cacheKey)
    if (cached) {
      return cached
    }
  }

  try {
    // Hacer request con retry
    const data = await requestWithRetry(requestFn)
    
    // Guardar en caché
    if (useCache) {
      localCache.set(cacheKey, data, cacheTTL)
    }
    
    return data
  } catch (error) {
    // Si falla y tenemos fallback, usar caché
    if (fallbackToCache) {
      const cached = localCache.get<T>(cacheKey)
      if (cached) {
        console.warn(`Using cached data for ${cacheKey} due to API error`)
        return cached
      }
    }
    throw error
  }
}

export { axiosInstance, requestWithRetry, requestWithCache, localCache, circuitBreaker }

