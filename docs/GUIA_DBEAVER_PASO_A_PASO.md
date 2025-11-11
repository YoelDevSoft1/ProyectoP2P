# 🚀 Guía Paso a Paso: Instalar y Configurar DBeaver

## 📋 Resumen

Esta guía te lleva paso a paso para instalar y configurar DBeaver en **5-10 minutos**.

**NO requiere migración** - Solo es una herramienta de administración.

---

## ✅ Paso 1: Verificar PostgreSQL

Antes de instalar DBeaver, verifica que PostgreSQL esté accesible:

```powershell
# Ejecutar script de verificación
.\scripts\verificar-postgres.ps1
```

O manualmente:
```powershell
# Verificar contenedor
docker ps | Select-String "postgres"

# Verificar puerto
Test-NetConnection -ComputerName localhost -Port 5432
```

**Debe mostrar**:
- ✅ Contenedor corriendo
- ✅ Puerto 5432 abierto

---

## 📥 Paso 2: Descargar DBeaver

1. **Abrir navegador**
2. **Visitar**: https://dbeaver.io/download/
3. **Click**: "Windows 64 bit (installer)"
4. **Descargar**: Archivo `.exe`

**Tiempo**: 1-2 minutos

---

## 🔧 Paso 3: Instalar DBeaver

1. **Ejecutar** el archivo `.exe` descargado
2. **Seguir wizard de instalación**:
   - Click "Next"
   - Aceptar licencia (GPL)
   - Seleccionar carpeta de instalación (por defecto: `C:\Program Files\DBeaver`)
   - Click "Install"
   - Esperar instalación
   - Click "Finish"

**Tiempo**: 2-3 minutos

**Nota**: Puede pedir permisos de administrador - aceptar.

---

## 🔌 Paso 4: Abrir DBeaver

1. **Buscar DBeaver** en el menú de inicio
2. **Abrir DBeaver**
3. **Ver interfaz principal**

**Primera vez**: DBeaver puede pedir crear un workspace - aceptar.

**Tiempo**: 10 segundos

---

## ⚙️ Paso 5: Crear Nueva Conexión

1. **Click en "Nueva Conexión"**:
   - Icono de enchufe en la barra superior
   - O: `Database` → `New Database Connection`
   - O: `Ctrl+Shift+N`

2. **Seleccionar PostgreSQL**:
   - Buscar "PostgreSQL" en la lista
   - Seleccionar "PostgreSQL"
   - Click "Next"

**Tiempo**: 10 segundos

---

## 🔐 Paso 6: Configurar Conexión

### Pestaña "Principal"

**Configuración**:
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `p2p_db`
- **Username**: `p2p_user`
- **Password**: `p2p_password_change_me`

**⚠️ IMPORTANTE**: 
- Marcar "Save password" si quieres que guarde la contraseña
- O dejar sin marcar para mayor seguridad

### Probar Conexión

1. **Click "Test Connection"** (botón abajo)
2. **Si pide descargar driver**:
   - Aparecerá ventana "Download driver"
   - Click "Download" (automático)
   - Esperar descarga (puede tardar 1-2 minutos)
   - Click "OK"

3. **Verificar resultado**:
   - Debe aparecer: "Connected"
   - Si hay error, verificar credenciales

**Tiempo**: 1-2 minutos (si descarga driver)

---

## 💾 Paso 7: Guardar Conexión

1. **Click "Finish"**
2. **Ver tu base de datos** en el panel izquierdo:
   - `Databases` → `p2p_db`
   - Expandir para ver tablas

**Tiempo**: 10 segundos

---

## 🎨 Paso 8: Explorar Base de Datos

### Ver Tablas

1. **Expandir**: `Databases` → `p2p_db` → `Schemas` → `public` → `Tables`
2. **Ver tablas**:
   - `alerts`
   - `trades`
   - `price_history`
   - `users`
   - `app_config`

### Ver Datos de una Tabla

1. **Click derecho** en tabla (ej: `trades`)
2. **Seleccionar**: "View Data" o "Open Data"
3. **Ver datos** en formato tabla

### Ejecutar Query SQL

1. **Click en "SQL Editor"**:
   - Icono de lápiz en la barra superior
   - O: `SQL Editor` → `New SQL Script`
   - O: `Ctrl+\`

2. **Escribir query**:
   ```sql
   SELECT * FROM trades ORDER BY created_at DESC LIMIT 10;
   ```

3. **Ejecutar**:
   - Click "Execute SQL" (icono de play)
   - O: `Ctrl+Enter`

4. **Ver resultados** en la parte inferior

---

## 🎯 Funcionalidades Útiles

### 1. Ver Estructura de Tabla

1. **Click derecho** en tabla
2. **Seleccionar**: "Properties" o "View DDL"
3. **Ver estructura**: Columnas, tipos, índices, etc.

### 2. Crear ER Diagram

1. **Click derecho** en base de datos `p2p_db`
2. **Seleccionar**: "View Diagram"
3. **Ver diagrama** de relaciones entre tablas

### 3. Exportar Datos

1. **Click derecho** en tabla
2. **Seleccionar**: "Export Data"
3. **Elegir formato**: CSV, JSON, SQL, Excel, etc.
4. **Configurar** opciones
5. **Exportar**

### 4. Importar Datos

1. **Click derecho** en tabla
2. **Seleccionar**: "Import Data"
3. **Seleccionar archivo**
4. **Configurar** opciones
5. **Importar**

### 5. Editar Datos

1. **Ver datos** de una tabla
2. **Click en celda** para editar
3. **Modificar valor**
4. **Guardar**: Click en icono de guardar o `Ctrl+S`

---

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

### Ver configuración persistente
```sql
SELECT * FROM app_config;
```

---

## 🎨 Atajos de Teclado Útiles

- `Ctrl+Shift+N`: Nueva conexión
- `Ctrl+\`: Nuevo SQL Editor
- `Ctrl+Enter`: Ejecutar query
- `Ctrl+S`: Guardar
- `F5`: Refrescar
- `Ctrl+F`: Buscar
- `Ctrl+H`: Reemplazar

---

## 🔒 Seguridad

### Ventajas de DBeaver

- ✅ **100% local**: Datos no salen de tu máquina
- ✅ **Sin servicios externos**: No depende de internet
- ✅ **Privacidad total**: Solo tú ves tus datos
- ✅ **Sin límites**: Sin límites de uso
- ✅ **Gratis**: Completamente gratuito

### Recomendaciones

1. **No guardar contraseñas** si trabajas en equipo
2. **Usar contraseñas fuertes** en producción
3. **Backup regular** de datos importantes
4. **No compartir conexiones** con contraseñas guardadas

---

## 🛠️ Troubleshooting

### Problema: No puedo conectarme

**Solución**:
1. Verificar que PostgreSQL esté corriendo: `docker ps | Select-String "postgres"`
2. Verificar que el puerto 5432 esté abierto: `Test-NetConnection -ComputerName localhost -Port 5432`
3. Verificar credenciales:
   - Host: `localhost`
   - Port: `5432`
   - Database: `p2p_db`
   - Username: `p2p_user`
   - Password: `p2p_password_change_me`

### Problema: Error al descargar driver

**Solución**:
1. Verificar conexión a internet
2. Intentar descargar manualmente desde: https://jdbc.postgresql.org/download/
3. Agregar driver manualmente en DBeaver: `Database` → `Driver Manager` → `New Driver`

### Problema: No veo las tablas

**Solución**:
1. Expandir: `Databases` → `p2p_db` → `Schemas` → `public` → `Tables`
2. Refrescar: Click derecho en `p2p_db` → "Refresh"
3. Verificar que las tablas existan: `docker exec p2p_postgres psql -U p2p_user -d p2p_db -c "\dt"`

---

## ✅ Verificación Final

### Checklist

- [ ] DBeaver instalado
- [ ] Conexión configurada
- [ ] Conexión probada exitosamente
- [ ] Tablas visibles
- [ ] Puedo ver datos
- [ ] Puedo ejecutar queries
- [ ] Puedo ver estructura de tablas

---

## 🎯 Próximos Pasos

1. **Explorar datos**: Ver tablas y datos
2. **Ejecutar queries**: Probar queries útiles
3. **Crear ER diagram**: Ver relaciones entre tablas
4. **Exportar datos**: Exportar datos a CSV/JSON
5. **Personalizar**: Configurar DBeaver según tus preferencias

---

## 📚 Recursos Adicionales

- **Documentación oficial**: https://dbeaver.com/docs/
- **Foros**: https://github.com/dbeaver/dbeaver/discussions
- **Tutoriales**: https://dbeaver.com/learn/

---

## ✅ Conclusión

**DBeaver está listo para usar**:
- ✅ Instalado y configurado
- ✅ Conectado a PostgreSQL
- ✅ Listo para administrar tu base de datos

**Tiempo total**: 5-10 minutos
**Dificultad**: ⭐ Muy fácil
**Riesgo**: ✅ Cero

¡Disfruta gestionando tu base de datos con DBeaver! 🎉

