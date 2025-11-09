/**
 * Cliente de API para comunicación con el backend.
 */
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_V1 = `${API_URL}/api/v1`

// Crear instancia de axios
const axiosInstance = axios.create({
  baseURL: API_V1,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    // Header para evitar la página de interceptor de ngrok
    'ngrok-skip-browser-warning': 'true',
  },
})

// Interceptor para logging (opcional)
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

const api = {
  // Health Check
  healthCheck: async () => {
    const { data } = await axiosInstance.get('/health')
    return data
  },

  // Health Checks Individuales
  getDatabaseHealth: async () => {
    try {
      const { data } = await axiosInstance.get('/health/db')
      return data
    } catch (error: any) {
      console.error('Error fetching database health:', error)
      return { status: 'error', error: error.message }
    }
  },

  getRedisHealth: async () => {
    try {
      const { data } = await axiosInstance.get('/health/redis')
      return data
    } catch (error: any) {
      console.error('Error fetching Redis health:', error)
      return { status: 'error', error: error.message }
    }
  },

  getRabbitMQHealth: async () => {
    try {
      const { data } = await axiosInstance.get('/health/rabbitmq')
      return data
    } catch (error: any) {
      console.error('Error fetching RabbitMQ health:', error)
      return { status: 'error', error: error.message }
    }
  },

  getCeleryHealth: async () => {
    try {
      const { data } = await axiosInstance.get('/health/celery')
      return data
    } catch (error: any) {
      console.error('Error fetching Celery health:', error)
      return { status: 'error', error: error.message }
    }
  },

  // Métricas Prometheus (texto plano)
  getPrometheusMetrics: async () => {
    try {
      const { data } = await axiosInstance.get('/metrics', {
        responseType: 'text',
        headers: {
          'Accept': 'text/plain',
        },
      })
      return data
    } catch (error: any) {
      console.error('Error fetching Prometheus metrics:', error)
      return null
    }
  },

  // Prices
  getCurrentPrices: async (asset = 'USDT', fiat?: string) => {
    try {
      const params = new URLSearchParams({ asset })
      if (fiat) params.append('fiat', fiat)

      const { data } = await axiosInstance.get(`/prices/current?${params}`)
      return data
    } catch (error: any) {
      console.error('Error fetching current prices:', error)
      // Retornar un objeto vacío en lugar de lanzar error
      return {}
    }
  },

  getPriceHistory: async (asset = 'USDT', fiat = 'COP', hours = 24) => {
    const { data } = await axiosInstance.get('/prices/history', {
      params: { asset, fiat, hours },
    })
    return data
  },

  getTRM: async () => {
    try {
      const { data } = await axiosInstance.get('/prices/trm')
      return data
    } catch (error: any) {
      console.error('Error fetching TRM:', error)
      // Retornar null en lugar de lanzar error
      return null
    }
  },

  getSpreadAnalysis: async (asset = 'USDT') => {
    const { data } = await axiosInstance.get('/prices/spread-analysis', {
      params: { asset },
    })
    return data
  },

  // Trades
  getTrades: async (skip = 0, limit = 50, status?: string, fiat?: string) => {
    const params: any = { skip, limit }
    if (status) params.status = status
    if (fiat) params.fiat = fiat

    const { data } = await axiosInstance.get('/trades/', { params })
    return data
  },

  getTrade: async (tradeId: number) => {
    const { data } = await axiosInstance.get(`/trades/${tradeId}`)
    return data
  },

  getTradeStats: async (days = 7) => {
    try {
      const { data } = await axiosInstance.get('/trades/stats/summary', {
        params: { days },
      })
      return data
    } catch (error: any) {
      console.error('Error fetching trade stats:', error)
      // Retornar null en lugar de lanzar error
      return null
    }
  },

  // Analytics
  getDashboardData: async () => {
    const { data } = await axiosInstance.get('/analytics/dashboard')
    return data
  },

  getPerformanceMetrics: async (days = 30) => {
    const { data } = await axiosInstance.get('/analytics/performance', {
      params: { days },
    })
    return data
  },

  getAlerts: async (skip = 0, limit = 20, alertType?: string, isRead?: boolean) => {
    const params: any = { skip, limit }
    if (alertType) params.alert_type = alertType
    if (isRead !== undefined) params.is_read = isRead

    const { data } = await axiosInstance.get('/analytics/alerts', { params })
    return data
  },

  markAlertAsRead: async (alertId: number) => {
    const { data } = await axiosInstance.post(`/analytics/alerts/${alertId}/read`)
    return data
  },
}

export default api
