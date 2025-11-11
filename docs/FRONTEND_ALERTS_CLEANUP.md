# 🧹 Instrucciones: Botón de Limpieza de Alertas en Frontend

## 📋 Resumen

Esta guía explica cómo agregar un botón en el frontend para limpiar alertas antiguas, manteniendo solo las 40 más recientes.

## ✅ Backend Listo

El backend ya tiene el endpoint implementado:
- **Endpoint**: `POST /api/v1/analytics/alerts/cleanup`
- **Parámetro**: `max_alerts` (opcional, por defecto 40)
- **Respuesta**: Estadísticas de la limpieza

## 🔧 Paso 1: Función API (Ya Implementada)

La función ya está agregada en `frontend/src/lib/api.ts`:

```typescript
cleanupAlerts: async (maxAlerts: number = 40) => {
  try {
    const { data } = await requestWithRetry(() =>
      axiosInstance.post(`/analytics/alerts/cleanup`, null, {
        params: { max_alerts: maxAlerts }
      })
    )
    return data
  } catch (error: any) {
    console.error('Error cleaning up alerts:', error)
    throw error
  }
}
```

## 🎨 Paso 2: Agregar Botón en la Página de Alertas

### Ubicación del Archivo
`frontend/src/app/alerts/page.tsx`

### 2.1. Agregar Import del Icono

Agregar `Trash2` a los imports de `lucide-react`:

```typescript
import { 
  Bell, 
  Home, 
  Filter, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  TrendingUp, 
  Zap,
  Activity,
  Brain,
  DollarSign,
  Menu,
  X,
  CheckCheck,
  RefreshCw,
  BarChart3,
  Settings,
  Trash2  // ← Agregar este
} from 'lucide-react'
```

### 2.2. Agregar Estado para el Botón

Agregar estados para manejar la limpieza:

```typescript
const [cleanupStatus, setCleanupStatus] = useState<'idle' | 'cleaning' | 'success' | 'error'>('idle')
const [cleanupMessage, setCleanupMessage] = useState<string>('')
```

### 2.3. Agregar Mutation para Limpiar Alertas

Agregar la mutation después de las otras mutations:

```typescript
// Mutation para limpiar alertas
const cleanupAlertsMutation = useMutation({
  mutationFn: (maxAlerts: number = 40) => api.cleanupAlerts(maxAlerts),
  onSuccess: (data) => {
    setCleanupStatus('success')
    setCleanupMessage(data.message || `Se eliminaron ${data.deleted_alerts} alertas. Se mantuvieron ${data.alerts_kept} alertas más recientes.`)
    
    // Invalidar queries para refrescar los datos
    queryClient.invalidateQueries({ queryKey: ['alerts'] })
    queryClient.invalidateQueries({ queryKey: ['alerts-stats'] })
    
    // Limpiar mensaje después de 5 segundos
    setTimeout(() => {
      setCleanupStatus('idle')
      setCleanupMessage('')
    }, 5000)
  },
  onError: (error: any) => {
    setCleanupStatus('error')
    setCleanupMessage(error.response?.data?.detail || 'Error al limpiar alertas')
    setTimeout(() => {
      setCleanupStatus('idle')
      setCleanupMessage('')
    }, 5000)
  },
})
```

### 2.4. Agregar Función de Limpieza

Agregar función para manejar el click del botón:

```typescript
const handleCleanupAlerts = () => {
  if (confirm('¿Estás seguro de que deseas limpiar las alertas antiguas? Se mantendrán solo las 40 más recientes.')) {
    cleanupAlertsMutation.mutate(40)
  }
}
```

### 2.5. Agregar Botón en la UI

Agregar el botón en el header, junto al botón de "Actualizar":

```typescript
<div className="flex items-center gap-4">
  <p className="text-white font-medium text-xs sm:text-sm lg:text-base hidden sm:block">
    {currentTime || '--:--:--'}
  </p>
  
  {/* Botón de Limpieza de Alertas */}
  <button
    onClick={handleCleanupAlerts}
    disabled={cleanupAlertsMutation.isPending}
    className="flex items-center gap-2 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
    title="Limpiar alertas antiguas (mantener solo 40 más recientes)"
  >
    <Trash2 className="h-4 w-4" />
    <span className="hidden sm:inline">Limpiar Alertas</span>
  </button>
  
  <button
    onClick={() => refetch()}
    className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
    title="Actualizar"
  >
    <RefreshCw className="h-5 w-5" />
  </button>
</div>
```

### 2.6. Agregar Mensaje de Estado

Agregar un mensaje de éxito/error después de las Stats Cards:

```typescript
{/* Mensaje de Limpieza */}
{cleanupStatus !== 'idle' && (
  <div className="px-4 sm:px-6 lg:px-8 py-4">
    <div
      className={`
        flex items-center gap-3 p-4 rounded-lg border
        ${cleanupStatus === 'success' 
          ? 'bg-green-900/30 border-green-500/50 text-green-400' 
          : 'bg-red-900/30 border-red-500/50 text-red-400'
        }
      `}
    >
      {cleanupStatus === 'success' ? (
        <CheckCircle className="h-5 w-5" />
      ) : (
        <XCircle className="h-5 w-5" />
      )}
      <span className="text-sm">{cleanupMessage}</span>
    </div>
  </div>
)}
```

## 🎯 Ubicación Exacta del Botón

### Opción 1: En el Header (Recomendado)
Agregar el botón en el header junto al botón de actualizar, como se muestra arriba.

### Opción 2: En las Stats Cards
Agregar el botón debajo de las estadísticas, antes de los filtros:

```typescript
{/* Stats Cards */}
{allAlertsStats && (
  <div className="px-4 sm:px-6 lg:px-8 py-6">
    {/* ... Stats Cards existentes ... */}
    
    {/* Botón de Limpieza */}
    <div className="mt-4 flex justify-end">
      <button
        onClick={handleCleanupAlerts}
        disabled={cleanupAlertsMutation.isPending}
        className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Trash2 className="h-4 w-4" />
        {cleanupAlertsMutation.isPending ? 'Limpiando...' : 'Limpiar Alertas Antiguas'}
      </button>
    </div>
  </div>
)}
```

## 📊 Respuesta del Backend

El endpoint retorna:

```typescript
{
  status: "success",
  message: "Se eliminaron 8960 alertas. Se mantuvieron 40 alertas más recientes.",
  total_alerts_before: 9000,
  total_alerts_after: 40,
  deleted_alerts: 8960,
  alerts_kept: 40,
  max_alerts: 40
}
```

## 🎨 Estilos Sugeridos

- **Color del botón**: Rojo (`bg-red-600`) para indicar acción destructiva
- **Icono**: `Trash2` de lucide-react
- **Estado de carga**: Mostrar "Limpiando..." cuando `isPending` es true
- **Confirmación**: Usar `confirm()` antes de ejecutar la limpieza
- **Feedback visual**: Mostrar mensaje de éxito/error después de la operación

## ✅ Checklist de Implementación

- [x] Función `cleanupAlerts` agregada en `api.ts`
- [ ] Import de `Trash2` agregado
- [ ] Estados `cleanupStatus` y `cleanupMessage` agregados
- [ ] Mutation `cleanupAlertsMutation` creada
- [ ] Función `handleCleanupAlerts` implementada
- [ ] Botón agregado en la UI
- [ ] Mensaje de estado agregado
- [ ] Confirmación antes de limpiar
- [ ] Invalidación de queries después de limpiar
- [ ] Pruebas realizadas

## 🔍 Ejemplo Completo de Código

Ver el archivo `frontend/src/app/alerts/page.tsx` después de la implementación para ver el código completo.

## 📝 Notas Adicionales

1. **Confirmación**: Siempre pedir confirmación antes de limpiar, ya que es una acción destructiva.
2. **Refresh automático**: Después de limpiar, invalidar las queries para refrescar los datos automáticamente.
3. **Feedback visual**: Mostrar mensajes claros de éxito/error para que el usuario sepa qué pasó.
4. **Estado de carga**: Deshabilitar el botón mientras se ejecuta la limpieza.
5. **Manejo de errores**: Mostrar mensajes de error claros si algo falla.

## 🚀 Próximos Pasos

1. Implementar el botón siguiendo las instrucciones
2. Probar la funcionalidad con alertas reales
3. Ajustar estilos si es necesario
4. Agregar más opciones (por ejemplo, permitir cambiar el número de alertas a mantener)

