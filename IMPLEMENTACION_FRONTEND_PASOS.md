# Pasos para Implementar Monitoreo en el Frontend

## 📋 Resumen Ejecutivo

Esta guía te ayudará a implementar paso a paso el sistema de monitoreo y métricas en el frontend de tu aplicación P2P Exchange.

## 🚀 Paso 1: Verificar Dependencias

Asegúrate de que tienes todas las dependencias necesarias en `package.json`:

```json
{
  "dependencies": {
    "recharts": "^2.10.4",
    "lucide-react": "^0.314.0",
    "@tanstack/react-query": "^5.17.19",
    "axios": "^1.6.5"
  }
}
```

Si no las tienes, instálalas:

```bash
cd frontend
npm install recharts lucide-react @tanstack/react-query axios
```

## 🚀 Paso 2: Archivos Creados

Los siguientes archivos ya han sido creados automáticamente:

### 1. Utilidades
- ✅ `frontend/src/lib/api.ts` - Cliente API actualizado con endpoints de health y métricas
- ✅ `frontend/src/lib/prometheus.ts` - Parser de métricas Prometheus

### 2. Componentes
- ✅ `frontend/src/components/SystemHealth.tsx` - Componente de health checks
- ✅ `frontend/src/components/MetricsDashboard.tsx` - Dashboard de métricas
- ✅ `frontend/src/components/RealTimeMetrics.tsx` - Métricas en tiempo real
- ✅ `frontend/src/components/ServiceStatusCard.tsx` - Tarjeta de estado de servicio

### 3. Páginas
- ✅ `frontend/src/app/monitoring/page.tsx` - Página de monitoreo

## 🚀 Paso 3: Agregar Enlace de Navegación

### Opción A: Agregar al Sidebar del Dashboard

Ya se ha agregado automáticamente en `frontend/src/app/dashboard/page.tsx`:

```tsx
<Link
  href="/monitoring"
  className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
>
  <Activity className="h-5 w-5 mr-3" />
  Monitoreo
</Link>
```

### Opción B: Agregar a tu Navegación Principal

Si tienes una navegación principal, agrega:

```tsx
import Link from 'next/link'
import { Activity } from 'lucide-react'

<Link href="/monitoring">
  <Activity className="w-5 h-5" />
  Monitoreo
</Link>
```

## 🚀 Paso 4: Integrar en el Dashboard Existente

Puedes agregar los componentes directamente a tu dashboard:

### Opción A: Agregar como Tab

En `frontend/src/app/dashboard/page.tsx`, agrega un nuevo tab:

```tsx
const tabs = [
  // ... tabs existentes
  { id: 'monitoring', label: 'Monitoreo', icon: Activity },
]

// En el renderizado:
{activeTab === 'monitoring' && (
  <div className="space-y-8">
    <SystemHealth />
    <RealTimeMetrics />
  </div>
)}
```

### Opción B: Agregar en Overview

Agrega los componentes en la vista overview:

```tsx
{activeTab === 'overview' && (
  <div className="space-y-8">
    <SystemHealth />
    <DashboardStats data={dashboardData} />
    {/* ... resto del contenido */}
  </div>
)}
```

## 🚀 Paso 5: Verificar la Configuración del Backend

Asegúrate de que el backend esté configurado correctamente:

1. **Health Checks**: Verifica que `/api/v1/health` funcione
2. **Métricas**: Verifica que `/api/v1/metrics` funcione
3. **CORS**: Asegúrate de que CORS esté configurado correctamente

### Probar Endpoints

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Métricas
curl http://localhost:8000/api/v1/metrics
```

## 🚀 Paso 6: Probar la Implementación

### 1. Iniciar el Backend

```bash
cd backend
# Asegúrate de que todos los servicios estén corriendo
docker-compose up -d
```

### 2. Iniciar el Frontend

```bash
cd frontend
npm run dev
```

### 3. Acceder a la Página de Monitoreo

Navega a: `http://localhost:3000/monitoring`

## 🚀 Paso 7: Personalización (Opcional)

### Cambiar Intervalos de Actualización

En `SystemHealth.tsx`:

```tsx
// Cambiar de 30 segundos a 10 segundos
const interval = setInterval(fetchHealth, 10000)
```

En `MetricsDashboard.tsx`:

```tsx
// Cambiar de 15 segundos a 5 segundos
const interval = setInterval(fetchMetrics, 5000)
```

En `RealTimeMetrics.tsx`:

```tsx
// Cambiar de 5 segundos a 2 segundos
const interval = setInterval(fetchMetrics, 2000)
```

### Cambiar Colores

En los componentes, puedes cambiar los colores:

```tsx
// En SystemHealth.tsx
const getStatusColor = (status: string) => {
  switch (status?.toLowerCase()) {
    case 'healthy':
      return 'bg-green-100 text-green-800 border-green-200' // Cambiar estos colores
    // ...
  }
}
```

### Agregar Más Métricas

En `MetricsDashboard.tsx`, puedes agregar más gráficos:

```tsx
// Agregar nueva métrica
const newMetricData = getMetricValues(metrics, 'nombre_de_la_metrica')

// Agregar nuevo gráfico
<div className="bg-white rounded-lg shadow p-6">
  <h3 className="text-lg font-semibold mb-4">Nueva Métrica</h3>
  <ResponsiveContainer width="100%" height={300}>
    <LineChart data={newMetricData}>
      {/* ... configuración del gráfico */}
    </LineChart>
  </ResponsiveContainer>
</div>
```

## 🚀 Paso 8: Solución de Problemas

### Problema: Métricas no se muestran

**Solución:**
1. Verifica que el endpoint `/api/v1/metrics` esté funcionando
2. Verifica la consola del navegador para errores
3. Verifica que el formato de las métricas sea correcto

### Problema: Health checks fallan

**Solución:**
1. Verifica que todos los servicios estén corriendo
2. Verifica las URLs en el backend
3. Verifica los logs del backend

### Problema: Gráficos vacíos

**Solución:**
1. Verifica que haya datos en las métricas
2. Verifica el formato de los datos parseados
3. Verifica la configuración de los gráficos

### Problema: Errores de CORS

**Solución:**
1. Verifica la configuración de CORS en el backend
2. Verifica que `NEXT_PUBLIC_API_URL` esté configurado correctamente
3. Verifica que el backend permita requests desde el frontend

## 🚀 Paso 9: Mejoras Futuras

### 1. Agregar WebSockets

Para actualizaciones en tiempo real más eficientes:

```tsx
// Crear hook para WebSockets
const useWebSocket = (url: string) => {
  const [data, setData] = useState(null)
  
  useEffect(() => {
    const ws = new WebSocket(url)
    ws.onmessage = (event) => {
      setData(JSON.parse(event.data))
    }
    return () => ws.close()
  }, [url])
  
  return data
}
```

### 2. Agregar Cache

Para mejorar el rendimiento:

```tsx
import { useQuery } from '@tanstack/react-query'

const { data } = useQuery({
  queryKey: ['health'],
  queryFn: () => api.healthCheck(),
  staleTime: 10000, // Cache por 10 segundos
  cacheTime: 30000, // Mantener en cache por 30 segundos
})
```

### 3. Agregar Filtros

Para filtrar métricas por fecha o servicio:

```tsx
const [selectedService, setSelectedService] = useState('all')
const [dateRange, setDateRange] = useState({ start: null, end: null })

// Filtrar datos
const filteredData = data.filter(item => {
  if (selectedService !== 'all' && item.service !== selectedService) return false
  // ... más filtros
  return true
})
```

## ✅ Checklist de Implementación

- [x] Dependencias instaladas
- [x] Archivos creados
- [x] Enlace de navegación agregado
- [x] Backend configurado
- [x] Frontend probado
- [x] Health checks funcionando
- [x] Métricas funcionando
- [x] Gráficos mostrando datos
- [x] Documentación leída

## 🎉 ¡Listo!

Una vez completados todos los pasos, tendrás un sistema de monitoreo completo y funcional en el frontend. Los componentes son reutilizables y personalizables, y el sistema está diseñado para ser escalable y mantenible.

## 📚 Recursos Adicionales

- [Documentación de Recharts](https://recharts.org/)
- [Documentación de React Query](https://tanstack.com/query/latest)
- [Documentación de Next.js](https://nextjs.org/docs)
- [GUIA_IMPLEMENTACION_FRONTEND.md](./GUIA_IMPLEMENTACION_FRONTEND.md) - Guía completa de implementación

## 🆘 Soporte

Si tienes problemas:
1. Revisa la consola del navegador
2. Revisa los logs del backend
3. Verifica la configuración de CORS
4. Verifica que todos los servicios estén corriendo
5. Revisa la documentación de los componentes

