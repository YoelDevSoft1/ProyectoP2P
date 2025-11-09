# Guía de Implementación Frontend - Métricas y Monitoreo

## 📋 Resumen

Esta guía explica cómo se han implementado las métricas y el monitoreo en el frontend de la aplicación P2P Exchange.

## 🎯 Componentes Implementados

### 1. **SystemHealth** (`src/components/SystemHealth.tsx`)
Componente que muestra el estado de salud de todos los servicios del sistema.

**Características:**
- Health checks de PostgreSQL, Redis, RabbitMQ y Celery
- Actualización automática cada 30 segundos
- Indicadores visuales de estado (healthy, degraded, unhealthy)
- Información detallada de cada servicio (latencia, workers, tareas activas)

**Uso:**
```tsx
import { SystemHealth } from '@/components/SystemHealth'

<SystemHealth />
```

### 2. **MetricsDashboard** (`src/components/MetricsDashboard.tsx`)
Dashboard completo con todas las métricas del sistema.

**Características:**
- Parsing de métricas Prometheus
- Gráficos de HTTP requests, DB queries, Redis operations, Celery tasks, Trades
- Tarjetas de estadísticas en tiempo real
- Actualización automática cada 15 segundos

**Uso:**
```tsx
import { MetricsDashboard } from '@/components/MetricsDashboard'

<MetricsDashboard />
```

### 3. **RealTimeMetrics** (`src/components/RealTimeMetrics.tsx`)
Métricas en tiempo real con gráficos actualizados cada 5 segundos.

**Características:**
- Gráficos en tiempo real
- Historial de hasta 50 puntos
- Métricas de HTTP, DB, Redis, Celery y Trades

**Uso:**
```tsx
import { RealTimeMetrics } from '@/components/RealTimeMetrics'

<RealTimeMetrics />
```

### 4. **ServiceStatusCard** (`src/components/ServiceStatusCard.tsx`)
Tarjeta reutilizable para mostrar el estado de un servicio individual.

**Características:**
- Indicadores visuales de estado
- Información de latencia y detalles
- Timestamp de última verificación

**Uso:**
```tsx
import { ServiceStatusCard } from '@/components/ServiceStatusCard'

<ServiceStatusCard
  name="PostgreSQL"
  status="healthy"
  latency={12}
  details={{ pool_size: 10 }}
/>
```

## 📚 Utilidades

### 1. **Prometheus Parser** (`src/lib/prometheus.ts`)
Utilidades para parsear y trabajar con métricas de Prometheus.

**Funciones principales:**
- `parsePrometheusMetrics(metricsText: string)`: Parsea texto de métricas a objetos
- `getMetricValue(metrics, metricName, labels?)`: Obtiene el valor de una métrica
- `getMetricValues(metrics, metricName)`: Obtiene todos los valores de una métrica
- `sumMetricValues(metrics, metricName, labels?)`: Suma los valores de una métrica

**Uso:**
```typescript
import { parsePrometheusMetrics, getMetricValue } from '@/lib/prometheus'

const metricsText = await api.getPrometheusMetrics()
const metrics = parsePrometheusMetrics(metricsText)
const httpRequests = getMetricValue(metrics, 'http_requests_total')
```

### 2. **API Client** (`src/lib/api.ts`)
Cliente de API actualizado con endpoints de health checks y métricas.

**Endpoints agregados:**
- `healthCheck()`: Health check completo del sistema
- `getDatabaseHealth()`: Health check de PostgreSQL
- `getRedisHealth()`: Health check de Redis
- `getRabbitMQHealth()`: Health check de RabbitMQ
- `getCeleryHealth()`: Health check de Celery
- `getPrometheusMetrics()`: Obtiene métricas en formato Prometheus

**Uso:**
```typescript
import api from '@/lib/api'

const health = await api.healthCheck()
const metrics = await api.getPrometheusMetrics()
```

## 🎨 Páginas

### 1. **Monitoring Page** (`src/app/monitoring/page.tsx`)
Página principal de monitoreo que combina todos los componentes.

**Características:**
- Sistema de health checks
- Dashboard de métricas
- Diseño responsive

**Ruta:** `/monitoring`

## 🚀 Cómo Usar

### 1. Agregar a la Navegación

Agrega un enlace a la página de monitoreo en tu navegación:

```tsx
<Link href="/monitoring">
  Monitoreo
</Link>
```

### 2. Integrar en el Dashboard

Puedes agregar componentes individuales a tu dashboard existente:

```tsx
import { SystemHealth } from '@/components/SystemHealth'
import { RealTimeMetrics } from '@/components/RealTimeMetrics'

export default function DashboardPage() {
  return (
    <div>
      <SystemHealth />
      <RealTimeMetrics />
    </div>
  )
}
```

### 3. Crear una Página Dedicada

Crea una página completa de monitoreo:

```tsx
'use client'

import { SystemHealth } from '@/components/SystemHealth'
import { MetricsDashboard } from '@/components/MetricsDashboard'
import { RealTimeMetrics } from '@/components/RealTimeMetrics'

export default function MonitoringPage() {
  return (
    <div className="space-y-6">
      <SystemHealth />
      <RealTimeMetrics />
      <MetricsDashboard />
    </div>
  )
}
```

## 📊 Métricas Disponibles

### Métricas de Negocio
- `trades_executed_total`: Total de trades ejecutados
- `trade_profit_usd`: Profit de trades
- `active_arbitrage_opportunities`: Oportunidades de arbitraje activas
- `price_updates_total`: Actualizaciones de precios

### Métricas Técnicas
- `http_requests_total`: Total de requests HTTP
- `http_request_duration_seconds`: Duración de requests HTTP
- `db_queries_total`: Total de queries a la base de datos
- `db_query_duration_seconds`: Duración de queries
- `redis_operations_total`: Total de operaciones Redis
- `redis_operation_duration_seconds`: Duración de operaciones
- `celery_tasks_total`: Total de tareas Celery
- `celery_task_duration_seconds`: Duración de tareas

## 🎨 Personalización

### Colores de Estado
Los colores se pueden personalizar en los componentes:
- `healthy`: Verde (#10b981)
- `degraded`: Amarillo (#f59e0b)
- `unhealthy`: Rojo (#ef4444)

### Intervalos de Actualización
Puedes ajustar los intervalos de actualización:
- Health checks: 30 segundos (por defecto)
- Métricas: 15 segundos (por defecto)
- Métricas en tiempo real: 5 segundos (por defecto)

### Gráficos
Los gráficos usan Recharts y se pueden personalizar:
- Colores
- Tipos de gráfico (Line, Area, Bar)
- Ejes y escalas
- Tooltips y leyendas

## 🔧 Troubleshooting

### Métricas no se muestran
1. Verifica que el endpoint `/api/v1/metrics` esté funcionando
2. Verifica la conexión con el backend
3. Revisa la consola del navegador para errores

### Health checks fallan
1. Verifica que los servicios estén corriendo
2. Verifica las URLs de los servicios en el backend
3. Revisa los logs del backend

### Gráficos vacíos
1. Verifica que haya datos en las métricas
2. Verifica el formato de los datos parseados
3. Revisa la configuración de los gráficos

## 📝 Próximos Pasos

1. **Alertas**: Agregar notificaciones cuando los servicios estén down
2. **Historial**: Guardar histórico de métricas
3. **Exportación**: Permitir exportar métricas a CSV/JSON
4. **Filtros**: Agregar filtros por fecha y servicio
5. **Comparaciones**: Comparar métricas entre períodos

## 🎯 Mejoras Futuras

1. **WebSockets**: Usar WebSockets para actualizaciones en tiempo real
2. **Cache**: Implementar cache de métricas
3. **Optimización**: Optimizar el rendimiento de los gráficos
4. **Accesibilidad**: Mejorar la accesibilidad de los componentes
5. **Internacionalización**: Agregar soporte multi-idioma

## 📚 Recursos

- [Recharts Documentation](https://recharts.org/)
- [Prometheus Metrics](https://prometheus.io/docs/concepts/metric_types/)
- [Next.js Documentation](https://nextjs.org/docs)
- [React Query](https://tanstack.com/query/latest)

## ✅ Checklist de Implementación

- [x] Componente SystemHealth
- [x] Componente MetricsDashboard
- [x] Componente RealTimeMetrics
- [x] Componente ServiceStatusCard
- [x] Parser de métricas Prometheus
- [x] API client actualizado
- [x] Página de monitoreo
- [x] Documentación

## 🎉 Conclusión

El sistema de monitoreo está completamente implementado y listo para usar. Todos los componentes son reutilizables y personalizables, y el sistema está diseñado para ser escalable y mantenible.

