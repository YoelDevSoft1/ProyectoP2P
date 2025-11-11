# 🗄️ Configuración de Adminer - Gestión Web de Base de Datos

## ✅ Estado

**Adminer ya está agregado a `docker-compose.yml`** 🎉

## 🚀 Iniciar Adminer

### Opción 1: Iniciar solo Adminer
```bash
docker-compose up -d adminer
```

### Opción 2: Iniciar todos los servicios (incluye Adminer)
```bash
docker-compose up -d
```

## 🌐 Acceder a Adminer

1. **Abrir navegador**: http://localhost:8080

2. **Configurar conexión**:
   - **Sistema**: `PostgreSQL`
   - **Servidor**: `postgres` (nombre del servicio en Docker)
   - **Usuario**: `p2p_user`
   - **Contraseña**: `p2p_password_change_me`
   - **Base de datos**: `p2p_db`

3. **Click "Entrar"**

## 📊 Funcionalidades

### Ver Tablas
- Click en la base de datos `p2p_db`
- Verás todas las tablas:
  - `alerts` - Alertas del sistema
  - `trades` - Operaciones de trading
  - `price_history` - Historial de precios
  - `users` - Usuarios
  - `app_config` - Configuración persistente

### Ejecutar Queries SQL
1. Click en "SQL command"
2. Escribe tu query:
   ```sql
   SELECT * FROM trades ORDER BY created_at DESC LIMIT 10;
   ```
3. Click "Execute"

### Ver Datos de una Tabla
1. Click en el nombre de la tabla (ej: `trades`)
2. Verás todos los datos
3. Puedes:
   - Filtrar datos
   - Ordenar por columnas
   - Editar registros
   - Eliminar registros
   - Agregar nuevos registros

### Exportar Datos
1. Selecciona la tabla
2. Click en "Export"
3. Elige formato:
   - SQL
   - CSV
   - JSON
   - XML
   - etc.
4. Click "Export"

### Importar Datos
1. Click en "Import"
2. Selecciona archivo
3. Click "Execute"

### Crear/Editar Tablas
1. Click en "Create table"
2. Define columnas
3. Click "Save"

### Ver Estructura de Tablas
1. Click en el nombre de la tabla
2. Click en "Structure"
3. Verás todas las columnas, tipos, índices, etc.

## 🔍 Queries Útiles

### Ver últimos trades
```sql
SELECT * FROM trades ORDER BY created_at DESC LIMIT 10;
```

### Ver últimas alertas
```sql
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;
```

### Ver precio history reciente
```sql
SELECT * FROM price_history ORDER BY timestamp DESC LIMIT 100;
```

### Ver configuración
```sql
SELECT * FROM app_config;
```

### Contar registros por tabla
```sql
SELECT 
    'trades' as tabla, COUNT(*) as total FROM trades
UNION ALL
SELECT 'alerts', COUNT(*) FROM alerts
UNION ALL
SELECT 'price_history', COUNT(*) FROM price_history
UNION ALL
SELECT 'app_config', COUNT(*) FROM app_config;
```

### Ver alertas no leídas
```sql
SELECT * FROM alerts WHERE is_read = false ORDER BY created_at DESC;
```

### Ver trades por estado
```sql
SELECT status, COUNT(*) as total 
FROM trades 
GROUP BY status;
```

## 🔒 Seguridad

### Desarrollo Local
- ✅ Está bien usar Adminer sin autenticación adicional
- ✅ Solo accesible desde `localhost`
- ✅ Requiere credenciales de base de datos

### Producción
- ⚠️ **NO** exponer Adminer públicamente sin protección adicional
- ⚠️ Usar autenticación adicional (reverse proxy con auth)
- ⚠️ Restringir acceso por IP
- ⚠️ Usar HTTPS

## 🛠️ Troubleshooting

### Problema: No puedo conectarme
**Solución**:
1. Verificar que el contenedor esté corriendo: `docker ps | grep adminer`
2. Verificar que PostgreSQL esté corriendo: `docker ps | grep postgres`
3. Verificar que el servidor sea `postgres` (no `localhost`)

### Problema: Error de conexión
**Solución**:
1. Verificar credenciales:
   - Usuario: `p2p_user`
   - Contraseña: `p2p_password_change_me`
   - Base de datos: `p2p_db`
2. Verificar que los servicios estén en la misma red Docker

### Problema: Puerto 8080 ocupado
**Solución**:
1. Cambiar el puerto en `docker-compose.yml`:
   ```yaml
   ports:
     - "8081:8080"  # Cambiar 8080 a 8081
   ```
2. Reiniciar: `docker-compose up -d adminer`

## 📝 Notas

- Adminer es una herramienta ligera (solo ~15MB)
- No requiere configuración adicional
- Funciona con múltiples bases de datos (PostgreSQL, MySQL, SQLite, etc.)
- Interfaz en múltiples idiomas (incluye español)

## 🎯 Próximos Pasos

1. **Iniciar Adminer**: `docker-compose up -d adminer`
2. **Acceder**: http://localhost:8080
3. **Conectar** a la base de datos
4. **Explorar** las tablas y datos
5. **Ejecutar** queries útiles

¡Listo! Ya puedes gestionar tu base de datos desde el navegador 🎉

