/**
 * Utilidades para parsear y trabajar con métricas de Prometheus
 */

export interface PrometheusMetric {
  name: string
  labels?: Record<string, string>
  value: number
  timestamp?: number
}

export interface ParsedMetrics {
  [metricName: string]: PrometheusMetric[]
}

/**
 * Parsea el texto de métricas de Prometheus en un formato estructurado
 * Maneja el formato estándar de Prometheus text-based exposition format
 */
export function parsePrometheusMetrics(metricsText: string): Map<string, PrometheusMetric[]> {
  const metrics = new Map<string, PrometheusMetric[]>()
  
  if (!metricsText || typeof metricsText !== 'string') {
    return metrics
  }
  
  const lines = metricsText.split('\n')
  let currentTimestamp = Date.now() / 1000 // Timestamp por defecto en segundos

  for (const line of lines) {
    const trimmed = line.trim()

    // Ignorar líneas vacías
    if (!trimmed) {
      continue
    }

    // Ignorar comentarios
    if (trimmed.startsWith('#')) {
      // Puede contener información de timestamp en comentarios
      continue
    }

    // Parsear línea de métrica
    // Formatos posibles:
    // metric_name value
    // metric_name{label="value"} value
    // metric_name{label="value",label2="value2"} value timestamp
    // metric_name value timestamp
    
    // Regex mejorado para manejar diferentes formatos
    // 1. Nombre de métrica (puede incluir _ y :)
    // 2. Labels opcionales en {}
    // 3. Valor numérico (puede ser científico)
    // 4. Timestamp opcional (entero)
    const metricMatch = trimmed.match(/^([a-zA-Z_:][a-zA-Z0-9_:]*)\s*(?:\{([^}]*)\})?\s+([0-9.+-eE]+|NaN|Inf|\+Inf|-Inf)(?:\s+(\d+))?$/)

    if (metricMatch) {
      const [, name, labelsStr, valueStr, timestampStr] = metricMatch

      // Parsear labels
      const labels: Record<string, string> = {}
      if (labelsStr) {
        // Parsear labels: label1="value1",label2="value2"
        // Manejar comillas simples y dobles
        const labelPattern = /([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*["']([^"']*)["']/g
        let labelMatch
        while ((labelMatch = labelPattern.exec(labelsStr)) !== null) {
          labels[labelMatch[1]] = labelMatch[2]
        }
      }

      // Parsear valor
      let value: number
      if (valueStr === 'NaN') {
        value = NaN
      } else if (valueStr === '+Inf' || valueStr === 'Inf') {
        value = Infinity
      } else if (valueStr === '-Inf') {
        value = -Infinity
      } else {
        const parsed = parseFloat(valueStr)
        // Validar que el parseo fue exitoso
        if (isNaN(parsed)) {
          continue // Saltar esta línea si no se puede parsear
        }
        value = parsed
      }

      // Parsear timestamp (opcional, en segundos desde epoch Unix)
      // Los timestamps de Prometheus están en milisegundos si se proporcionan
      const timestamp = timestampStr 
        ? parseInt(timestampStr, 10) 
        : Math.floor(Date.now() / 1000) // Timestamp actual en segundos

      // Agregar métrica (incluyendo NaN e Infinity para que el componente pueda decidir qué hacer)
      const metric: PrometheusMetric = {
        name,
        labels: Object.keys(labels).length > 0 ? labels : undefined,
        value,
        timestamp,
      }

      if (!metrics.has(name)) {
        metrics.set(name, [])
      }
      metrics.get(name)!.push(metric)
    }
  }

  return metrics
}

/**
 * Obtiene el valor de una métrica específica
 * Si hay múltiples series con diferentes labels, devuelve el primero con valor válido
 */
export function getMetricValue(
  metrics: Map<string, PrometheusMetric[]>,
  metricName: string
): number | null {
  const metricSeries = metrics.get(metricName)
  if (!metricSeries || metricSeries.length === 0) {
    return null
  }

  // Buscar el último valor válido (no NaN, no Infinity)
  for (let i = metricSeries.length - 1; i >= 0; i--) {
    const value = metricSeries[i].value
    if (isFinite(value) && !isNaN(value)) {
      return value
    }
  }

  // Si no hay valores válidos, devolver el último (puede ser NaN o Infinity)
  return metricSeries[metricSeries.length - 1].value
}

/**
 * Obtiene todos los valores de una métrica como un array de puntos de datos
 * Útil para gráficos de series temporales
 * Filtra valores inválidos por defecto
 */
export function getMetricValues(
  metrics: Map<string, PrometheusMetric[]>,
  metricName: string,
  filterInvalid: boolean = true
): Array<{ time: string; value: number; [key: string]: any }> {
  const metricSeries = metrics.get(metricName)
  if (!metricSeries || metricSeries.length === 0) {
    return []
  }

  return metricSeries
    .filter((metric) => {
      // Filtrar valores inválidos si se solicita
      if (filterInvalid) {
        const value = metric.value
        return isFinite(value) && !isNaN(value)
      }
      return true
    })
    .map((metric) => {
      // Los timestamps de Prometheus están en segundos, convertir a milisegundos para Date
      const time = metric.timestamp
        ? new Date(metric.timestamp * 1000).toLocaleTimeString()
        : new Date().toLocaleTimeString()

      const dataPoint: { time: string; value: number; [key: string]: any } = {
        time,
        value: metric.value,
      }

      // Agregar labels como propiedades adicionales
      if (metric.labels) {
        Object.entries(metric.labels).forEach(([key, value]) => {
          dataPoint[key] = value
        })
      }

      return dataPoint
    })
}

/**
 * Suma todos los valores de una métrica
 * Útil para contadores que pueden tener múltiples series con diferentes labels
 * Ignora valores NaN e Infinity
 */
export function sumMetricValues(
  metrics: Map<string, PrometheusMetric[]>,
  metricName: string
): number {
  const metricSeries = metrics.get(metricName)
  if (!metricSeries || metricSeries.length === 0) {
    return 0
  }

  return metricSeries.reduce((sum, metric) => {
    const value = metric.value
    // Solo sumar valores válidos (finitos y no NaN)
    if (isFinite(value) && !isNaN(value)) {
      return sum + value
    }
    return sum
  }, 0)
}

/**
 * Obtiene el promedio de una métrica
 */
export function getMetricAverage(
  metrics: Map<string, PrometheusMetric[]>,
  metricName: string
): number | null {
  const metricSeries = metrics.get(metricName)
  if (!metricSeries || metricSeries.length === 0) {
    return null
  }

  const sum = metricSeries.reduce((sum, metric) => sum + metric.value, 0)
  return sum / metricSeries.length
}

/**
 * Filtra métricas por labels
 */
export function filterMetricsByLabels(
  metrics: Map<string, PrometheusMetric[]>,
  metricName: string,
  labels: Record<string, string>
): PrometheusMetric[] {
  const metricSeries = metrics.get(metricName)
  if (!metricSeries) {
    return []
  }

  return metricSeries.filter((metric) => {
    if (!metric.labels) {
      return Object.keys(labels).length === 0
    }

    return Object.entries(labels).every(([key, value]) => {
      return metric.labels?.[key] === value
    })
  })
}

/**
 * Obtiene el valor máximo de una métrica
 */
export function getMetricMax(
  metrics: Map<string, PrometheusMetric[]>,
  metricName: string
): number | null {
  const metricSeries = metrics.get(metricName)
  if (!metricSeries || metricSeries.length === 0) {
    return null
  }

  return Math.max(...metricSeries.map((metric) => metric.value))
}

/**
 * Obtiene el valor mínimo de una métrica
 */
export function getMetricMin(
  metrics: Map<string, PrometheusMetric[]>,
  metricName: string
): number | null {
  const metricSeries = metrics.get(metricName)
  if (!metricSeries || metricSeries.length === 0) {
    return null
  }

  return Math.min(...metricSeries.map((metric) => metric.value))
}
