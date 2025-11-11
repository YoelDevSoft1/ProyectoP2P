# 📋 Resumen: API de Configuración para Frontend

## 🎯 Objetivo

Crear una página de configuración en el frontend que permita a los usuarios visualizar y modificar la configuración de la aplicación de forma segura.

---

## 🔌 Endpoints Disponibles

### 1. GET `/api/v1/config`
**Descripción**: Obtiene toda la configuración actual de la aplicación.

**Respuesta**:
```json
{
  "trading": { ... },
  "p2p": { ... },
  "arbitrage": { ... },
  "notifications": { ... },
  "ml": { ... },
  "alpha_vantage": { ... },
  "fx": { ... },
  "rate_limiting": { ... },
  "browser": { ... },
  "environment": "development",
  "version": "1.0.0",
  "debug": true
}
```

### 2. PUT `/api/v1/config`
**Descripción**: Actualiza la configuración (solo secciones enviadas).

**Request Body**:
```json
{
  "trading": { ... },  // Opcional
  "p2p": { ... },      // Opcional
  // ... otras secciones opcionales
}
```

**⚠️ Nota**: Los cambios solo se aplican en memoria. Para cambios permanentes, modificar `.env` y reiniciar.

### 3. GET `/api/v1/config/sections`
**Descripción**: Obtiene la lista de secciones disponibles con metadatos (útil para UI dinámica).

**Respuesta**:
```json
{
  "sections": [
    {
      "id": "trading",
      "name": "Trading",
      "description": "Configuración de trading y márgenes de ganancia",
      "icon": "💰",
      "fields": [ ... ]
    },
    // ... más secciones
  ]
}
```

---

## 📁 Archivos Creados

### Backend
- `backend/app/api/endpoints/config.py` - Endpoints de configuración
- `backend/app/main.py` - Router de configuración agregado

### Frontend
- `frontend/src/types/config.ts` - Tipos TypeScript
- `frontend/src/lib/api.ts` - Funciones API agregadas (ya actualizado)

### Documentación
- `docs/FRONTEND_CONFIG_API.md` - Documentación completa
- `docs/FRONTEND_CONFIG_QUICKSTART.md` - Guía rápida
- `docs/CONFIG_API_SUMMARY.md` - Este archivo

---

## 🎨 Estructura de Datos

### Secciones de Configuración

1. **Trading** (`trading`)
   - Modo de trading (manual/auto/hybrid)
   - Márgenes de ganancia (COP, VES)
   - Límites de trade (min/max)
   - Stop loss

2. **P2P** (`p2p`)
   - Assets monitoreados
   - Fiats monitoreados
   - Configuración de análisis
   - Caché de precios

3. **Arbitraje** (`arbitrage`)
   - Assets y fiats para arbitraje
   - Top oportunidades
   - Límites de liquidez y ganancia

4. **Notificaciones** (`notifications`)
   - Habilitar/deshabilitar
   - Telegram (token oculto, chat ID)
   - Email (SMTP)

5. **Machine Learning** (`ml`)
   - Intervalo de re-entrenamiento
   - Umbrales de confianza
   - Puntos de datos mínimos

6. **Alpha Vantage** (`alpha_vantage`)
   - API Key (oculto)
   - Habilitar/deshabilitar
   - Tiempo de caché

7. **FX y Tasas** (`fx`)
   - Tiempos de caché
   - Intervalos de actualización
   - Tasas de cambio por defecto

8. **Rate Limiting** (`rate_limiting`)
   - Límites por minuto
   - Límites de API de Binance

9. **Browser Automation** (`browser`)
   - Modo headless
   - Timeout
   - Tamaño del pool

---

## 🔒 Seguridad

1. **Tokens Sensibles**: Se muestran parcialmente ocultos (solo primeros 8 caracteres)
2. **No Actualizables via API**: Tokens y contraseñas no se pueden actualizar via API
3. **Cambios Temporales**: Los cambios solo se aplican en memoria
4. **Validación**: Todos los datos se validan antes de aplicarse

---

## 💻 Ejemplo de Uso en Frontend

```typescript
import api from '@/lib/api'
import type { AppConfigResponse, ConfigUpdateRequest } from '@/types/config'

// Obtener configuración
const config: AppConfigResponse = await api.getConfiguration()

// Actualizar configuración
await api.updateConfiguration({
  trading: {
    trading_mode: 'auto',
    profit_margin_cop: 3.0,
    // ... más campos
  }
})

// Obtener secciones
const sections = await api.getConfigSections()
```

---

## ✅ Validaciones

Todas las validaciones se realizan en el backend usando Pydantic:

- **Trading**: `trading_mode` debe ser "manual", "auto" o "hybrid"
- **Números**: Rangos válidos según cada campo
- **Arrays**: No vacíos cuando son requeridos
- **Strings**: Validación de formato (emails, etc.)

---

## 🚀 Próximos Pasos para el Frontend

1. **Crear Componente Principal**
   - `frontend/src/components/ConfigurationPage.tsx`

2. **Crear Componentes por Sección**
   - `TradingConfigSection.tsx`
   - `P2PConfigSection.tsx`
   - `ArbitrageConfigSection.tsx`
   - `NotificationsConfigSection.tsx`
   - `MLConfigSection.tsx`
   - `AlphaVantageConfigSection.tsx`
   - `FXConfigSection.tsx`
   - `RateLimitingConfigSection.tsx`
   - `BrowserConfigSection.tsx`

3. **Implementar Validación en Frontend**
   - Validar antes de enviar al backend
   - Mostrar errores de validación

4. **Agregar UI/UX**
   - Formularios por sección
   - Botones de guardar/cancelar
   - Indicadores de cambios sin guardar
   - Confirmación para cambios importantes

5. **Integrar con React Query**
   - Usar `useQuery` para obtener configuración
   - Usar `useMutation` para actualizar
   - Invalidar cache después de actualizar

---

## 📚 Documentación Completa

- **Documentación Completa**: `docs/FRONTEND_CONFIG_API.md`
- **Guía Rápida**: `docs/FRONTEND_CONFIG_QUICKSTART.md`
- **Tipos TypeScript**: `frontend/src/types/config.ts`

---

## 🔍 Testing

### Probar Endpoints

```bash
# Obtener configuración
curl http://localhost:8000/api/v1/config

# Actualizar configuración
curl -X PUT http://localhost:8000/api/v1/config \
  -H "Content-Type: application/json" \
  -d '{
    "trading": {
      "trading_mode": "auto",
      "profit_margin_cop": 3.0,
      "profit_margin_ves": 3.5,
      "min_trade_amount": 100.0,
      "max_trade_amount": 2000.0,
      "max_daily_trades": 100,
      "stop_loss_percentage": 2.0
    }
  }'

# Obtener secciones
curl http://localhost:8000/api/v1/config/sections
```

---

## ⚠️ Limitaciones Actuales

1. **Cambios Temporales**: Los cambios solo se aplican en memoria
2. **No Persistencia**: No se guardan en base de datos (futuro)
3. **Sin Historial**: No hay historial de cambios (futuro)
4. **Sin Permisos**: No hay sistema de permisos (futuro)
5. **Tokens Sensibles**: No se pueden actualizar via API (por diseño de seguridad)

---

## 🎯 Características Futuras

1. Persistencia en base de datos
2. Sistema de permisos
3. Historial de cambios
4. Rollback de configuraciones
5. Exportar/importar configuración
6. Validación avanzada
7. Notificaciones de cambios

---

## 📞 Soporte

Para preguntas o problemas:
1. Revisar documentación en `docs/FRONTEND_CONFIG_API.md`
2. Revisar tipos en `frontend/src/types/config.ts`
3. Probar endpoints en `/api/v1/docs` (Swagger UI)
4. Contactar al equipo de backend

---

## ✅ Checklist para Frontend

- [ ] Crear componente principal `ConfigurationPage`
- [ ] Crear componentes por sección
- [ ] Integrar con React Query
- [ ] Implementar validación en frontend
- [ ] Agregar UI/UX (formularios, botones, etc.)
- [ ] Agregar manejo de errores
- [ ] Agregar loading states
- [ ] Agregar confirmación para cambios importantes
- [ ] Agregar indicadores de cambios sin guardar
- [ ] Testing de componentes
- [ ] Testing de integración con API

---

## 🎨 Recomendaciones de UI

1. **Tabs o Acordeones**: Organizar secciones en tabs o acordeones
2. **Formularios por Sección**: Cada sección tiene su propio formulario
3. **Validación en Tiempo Real**: Validar campos mientras el usuario escribe
4. **Guardar por Sección**: Permitir guardar cambios por sección
5. **Reset por Sección**: Permitir resetear cambios por sección
6. **Indicadores Visuales**: Mostrar qué secciones tienen cambios sin guardar
7. **Confirmación**: Solicitar confirmación para cambios importantes
8. **Ayuda Contextual**: Mostrar ayuda para cada campo
9. **Valores por Defecto**: Mostrar valores por defecto cuando sea relevante
10. **Responsive**: Asegurar que la UI sea responsive

---

¡Listo para empezar a desarrollar la página de configuración! 🚀

