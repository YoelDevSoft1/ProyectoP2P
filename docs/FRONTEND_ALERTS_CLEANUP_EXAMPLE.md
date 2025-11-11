# 📝 Ejemplo de Código: Botón de Limpieza de Alertas

## 🎯 Implementación Rápida

### 1. Agregar Import del Icono

En `frontend/src/app/alerts/page.tsx`, línea ~24, agregar `Trash2`:

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
  Trash2  // ← AGREGAR ESTA LÍNEA
} from 'lucide-react'
```

### 2. Agregar Estados

Después de la línea ~55, agregar:

```typescript
const [cleanupStatus, setCleanupStatus] = useState<'idle' | 'cleaning' | 'success' | 'error'>('idle')
const [cleanupMessage, setCleanupMessage] = useState<string>('')
```

### 3. Agregar Mutation

Después de la línea ~132 (después de `markMultipleAsRead`), agregar:

```typescript
// Limpiar alertas antiguas
const cleanupAlertsMutation = useMutation({
  mutationFn: (maxAlerts: number = 40) => api.cleanupAlerts(maxAlerts),
  onSuccess: (data) => {
    setCleanupStatus('success')
    setCleanupMessage(
      data.message || 
      `✅ Se eliminaron ${data.deleted_alerts} alertas. Se mantuvieron ${data.alerts_kept} alertas más recientes.`
    )
    
    // Refrescar datos
    queryClient.invalidateQueries({ queryKey: ['alerts'] })
    queryClient.invalidateQueries({ queryKey: ['alerts-stats'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    
    // Limpiar mensaje después de 5 segundos
    setTimeout(() => {
      setCleanupStatus('idle')
      setCleanupMessage('')
    }, 5000)
  },
  onError: (error: any) => {
    setCleanupStatus('error')
    setCleanupMessage(
      error.response?.data?.detail || 
      '❌ Error al limpiar alertas. Por favor, intenta nuevamente.'
    )
    setTimeout(() => {
      setCleanupStatus('idle')
      setCleanupMessage('')
    }, 5000)
  },
})

// Función para manejar la limpieza
const handleCleanupAlerts = () => {
  if (
    confirm(
      '⚠️ ¿Estás seguro de que deseas limpiar las alertas antiguas?\n\n' +
      'Se mantendrán solo las 40 alertas más recientes y se eliminarán todas las demás.\n\n' +
      'Esta acción no se puede deshacer.'
    )
  ) {
    setCleanupStatus('cleaning')
    cleanupAlertsMutation.mutate(40)
  }
}
```

### 4. Agregar Botón en el Header

Reemplazar el código en las líneas ~333-344 con:

```typescript
<div className="flex items-center gap-2 sm:gap-4">
  <p className="text-white font-medium text-xs sm:text-sm lg:text-base hidden sm:block">
    {currentTime || '--:--:--'}
  </p>
  
  {/* Botón de Limpieza de Alertas */}
  <button
    onClick={handleCleanupAlerts}
    disabled={cleanupAlertsMutation.isPending || cleanupStatus === 'cleaning'}
    className="flex items-center gap-2 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-xs sm:text-sm"
    title="Limpiar alertas antiguas (mantener solo 40 más recientes)"
  >
    <Trash2 className="h-4 w-4" />
    <span className="hidden sm:inline">
      {cleanupAlertsMutation.isPending || cleanupStatus === 'cleaning' ? 'Limpiando...' : 'Limpiar'}
    </span>
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

### 5. Agregar Mensaje de Estado

Después de las Stats Cards (después de la línea ~388), agregar:

```typescript
{/* Mensaje de Estado de Limpieza */}
{cleanupStatus !== 'idle' && cleanupMessage && (
  <div className="px-4 sm:px-6 lg:px-8 py-4">
    <div
      className={`
        flex items-center gap-3 p-4 rounded-lg border animate-pulse
        ${cleanupStatus === 'success' 
          ? 'bg-green-900/30 border-green-500/50 text-green-400' 
          : cleanupStatus === 'error'
          ? 'bg-red-900/30 border-red-500/50 text-red-400'
          : 'bg-blue-900/30 border-blue-500/50 text-blue-400'
        }
      `}
    >
      {cleanupStatus === 'success' ? (
        <CheckCircle className="h-5 w-5 flex-shrink-0" />
      ) : cleanupStatus === 'error' ? (
        <XCircle className="h-5 w-5 flex-shrink-0" />
      ) : (
        <RefreshCw className="h-5 w-5 flex-shrink-0 animate-spin" />
      )}
      <span className="text-sm">{cleanupMessage}</span>
    </div>
  </div>
)}
```

## 🎨 Versión Alternativa: Botón en Stats Cards

Si prefieres el botón debajo de las estadísticas, agregar después de la línea ~386:

```typescript
{/* Botón de Limpieza */}
<div className="px-4 sm:px-6 lg:px-8 py-4">
  <div className="flex justify-between items-center bg-gray-800/50 rounded-lg p-4 border border-gray-700">
    <div>
      <p className="text-sm text-gray-400">
        Limpieza automática cada 10 minutos (mantiene 40 alertas más recientes)
      </p>
      <p className="text-xs text-gray-500 mt-1">
        Puedes limpiar manualmente las alertas antiguas en cualquier momento
      </p>
    </div>
    <button
      onClick={handleCleanupAlerts}
      disabled={cleanupAlertsMutation.isPending || cleanupStatus === 'cleaning'}
      className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <Trash2 className="h-4 w-4" />
      {cleanupAlertsMutation.isPending || cleanupStatus === 'cleaning' ? 'Limpiando...' : 'Limpiar Alertas'}
    </button>
  </div>
</div>
```

## ✅ Resumen de Cambios

1. ✅ Importar `Trash2` de `lucide-react`
2. ✅ Agregar estados `cleanupStatus` y `cleanupMessage`
3. ✅ Crear mutation `cleanupAlertsMutation`
4. ✅ Crear función `handleCleanupAlerts`
5. ✅ Agregar botón en el header (o en stats cards)
6. ✅ Agregar mensaje de estado

## 🧪 Pruebas

1. Abrir la página de alertas
2. Verificar que el botón aparezca
3. Hacer clic en "Limpiar Alertas"
4. Confirmar la acción
5. Verificar que se muestre el mensaje de éxito
6. Verificar que las alertas se refresquen automáticamente
7. Verificar que las estadísticas se actualicen

## 📊 Comportamiento Esperado

- **Antes de limpiar**: Mostrar total de alertas (ej: 9000)
- **Después de limpiar**: Mostrar solo 40 alertas
- **Mensaje de éxito**: "Se eliminaron 8960 alertas. Se mantuvieron 40 alertas más recientes."
- **Refresh automático**: Las estadísticas y la lista se actualizan automáticamente

## 🔍 Debugging

Si el botón no funciona:

1. Verificar que `api.cleanupAlerts` esté importado correctamente
2. Verificar la consola del navegador para errores
3. Verificar que el endpoint del backend esté funcionando: `POST /api/v1/analytics/alerts/cleanup`
4. Verificar que la respuesta del backend tenga el formato correcto

