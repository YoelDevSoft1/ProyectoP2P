# 💾 Configuración Persistente - Trading Mode

## 📋 Problema Resuelto

Anteriormente, cuando se cambiaba el modo de trading (manual, auto, hybrid) desde la página de configuración, el cambio solo se guardaba en memoria. Al reiniciar el servidor, el modo volvía a su valor por defecto.

## ✅ Solución Implementada

Se implementó un sistema de configuración persistente que guarda los valores en la base de datos y los carga automáticamente al iniciar el servidor.

## 🏗️ Arquitectura

### 1. Modelo de Base de Datos
- **Archivo**: `backend/app/models/app_config.py`
- **Tabla**: `app_config`
- **Campos**:
  - `key`: Clave de configuración (ej: "trading.mode")
  - `value`: Valor (guardado como texto, parseado según tipo)
  - `value_type`: Tipo de dato (str, int, float, bool, dict, list)
  - `description`: Descripción de la configuración
  - `is_sensitive`: Si es sensible (no se muestra en logs)

### 2. Servicio de Configuración
- **Archivo**: `backend/app/services/config_service.py`
- **Clase**: `ConfigService`
- **Métodos**:
  - `get_config(key, default)`: Obtener valor de configuración
  - `set_config(key, value, description, is_sensitive)`: Guardar configuración
  - `delete_config(key)`: Eliminar configuración
  - `load_trading_config_to_settings()`: Cargar configuración de trading desde DB a settings
  - `save_trading_config_from_settings()`: Guardar configuración de trading desde settings a DB

### 3. Endpoint de Configuración
- **Archivo**: `backend/app/api/endpoints/config.py`
- **Endpoint**: `PUT /api/v1/config`
- **Cambios**:
  - Ahora persiste los cambios en la base de datos
  - Los cambios se aplican inmediatamente en memoria
  - Los cambios persisten después de reiniciar

### 4. Inicialización
- **Archivo**: `backend/app/main.py`
- **Función**: `lifespan()`
- **Comportamiento**:
  - Al iniciar el servidor, carga la configuración desde la base de datos
  - Actualiza `settings.TRADING_MODE` y otros valores de trading
  - Si no existe configuración en la DB, usa los valores por defecto

## 🔄 Flujo de Datos

### Al Guardar Configuración:
1. Usuario cambia modo de trading en frontend
2. Frontend llama a `PUT /api/v1/config`
3. Backend actualiza `settings.TRADING_MODE` en memoria
4. Backend guarda en base de datos usando `ConfigService.set_config()`
5. Cambio se aplica inmediatamente

### Al Iniciar Servidor:
1. Se inicializa la base de datos
2. Se carga configuración desde DB usando `ConfigService.load_trading_config_to_settings()`
3. Se actualizan los valores en `settings`
4. El bot de trading y otras partes del sistema leen desde `settings`

## 📊 Configuraciones Persistidas

Actualmente se persisten las siguientes configuraciones de trading:
- `trading.mode`: Modo de trading (manual, auto, hybrid)
- `trading.profit_margin_cop`: Margen de ganancia para COP (%)
- `trading.profit_margin_ves`: Margen de ganancia para VES (%)
- `trading.min_trade_amount`: Monto mínimo de trade (USD)
- `trading.max_trade_amount`: Monto máximo de trade (USD)
- `trading.max_daily_trades`: Máximo de trades por día
- `trading.stop_loss_percentage`: Stop loss (%)

## 🔍 Verificación

### Verificar que la configuración se guardó:
```sql
SELECT * FROM app_config WHERE key = 'trading.mode';
```

### Verificar logs al iniciar:
Buscar en los logs:
```
Loaded trading mode from DB: auto
Persistent configuration loaded from database
```

## 🚀 Migración

### Primera Ejecución:
1. Al iniciar el servidor por primera vez, se crea la tabla `app_config` automáticamente
2. Si no hay configuración guardada, se usan los valores por defecto de `settings`
3. Al cambiar la configuración desde la API, se guarda en la base de datos

### Migración de Datos Existentes:
Si ya tienes configuración en `.env` y quieres migrarla a la base de datos:
1. Inicia el servidor (cargará valores de `.env`)
2. Llama a `PUT /api/v1/config` con la configuración actual
3. La configuración se guardará en la base de datos

## 🔒 Seguridad

- Las configuraciones sensibles (tokens, contraseñas) NO se pueden modificar via API
- Solo las configuraciones de trading se persisten
- Las configuraciones sensibles deben cambiarse en `.env` y reiniciar el servidor

## 🐛 Troubleshooting

### Problema: La configuración no persiste
**Solución**:
1. Verificar que la tabla `app_config` existe: `\d app_config` (PostgreSQL)
2. Verificar logs al iniciar: buscar "Persistent configuration loaded from database"
3. Verificar que no hay errores en los logs

### Problema: El modo de trading no cambia
**Solución**:
1. Verificar que el endpoint `PUT /api/v1/config` se ejecuta correctamente
2. Verificar que la respuesta del endpoint indica éxito
3. Verificar que `settings.TRADING_MODE` se actualiza en memoria
4. Verificar que el bot de trading lee `settings.TRADING_MODE` correctamente

### Problema: Error al cargar configuración
**Solución**:
1. Verificar que la base de datos está accesible
2. Verificar que la tabla `app_config` existe
3. Verificar logs para ver el error específico
4. Si la tabla no existe, reiniciar el servidor para crearla

## 📝 Notas

- La configuración se carga **una vez** al iniciar el servidor
- Si cambias la configuración mientras el servidor está corriendo, el cambio se aplica inmediatamente
- Si reinicias el servidor, la configuración se carga desde la base de datos
- Los valores por defecto en `settings` se usan solo si no hay configuración en la DB

## 🔄 Extensión Futura

Para agregar más configuraciones persistentes:
1. Agregar la clave en `ConfigService.load_trading_config_to_settings()`
2. Agregar el guardado en el endpoint `PUT /api/v1/config`
3. La configuración se cargará automáticamente al iniciar

Ejemplo:
```python
# En config_service.py
def load_trading_config_to_settings(self):
    # ... código existente ...
    
    # Nueva configuración
    new_setting = self.get_config("trading.new_setting", settings.NEW_SETTING)
    if new_setting is not None:
        settings.NEW_SETTING = new_setting
```

## ✅ Checklist de Implementación

- [x] Modelo `AppConfig` creado
- [x] Servicio `ConfigService` implementado
- [x] Endpoint actualizado para persistir en DB
- [x] Carga de configuración al iniciar implementada
- [x] Tabla creada automáticamente en `init_db()`
- [x] Logs agregados para debugging
- [x] Manejo de errores implementado
- [x] Documentación creada

