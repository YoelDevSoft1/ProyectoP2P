# ✅ DBeaver - Configuración Completa

## 🎯 Resumen

**DBeaver NO requiere migración** - Es solo una herramienta de administración.

**Estado actual**:
- ✅ PostgreSQL está corriendo y accesible
- ✅ Puerto 5432 abierto
- ✅ Base de datos `p2p_db` disponible
- ⚠️ DBeaver NO está instalado aún

---

## 📥 Paso 1: Descargar DBeaver

### Opción A: Desde el Navegador (Ya abierto)

1. **En el navegador** (ya se abrió automáticamente)
2. **Click**: "Windows 64 bit (installer)"
3. **Descargar**: Archivo `dbeaver-ce-XX.X.X-win32.win32.x86_64.exe`

### Opción B: Descarga Directa

**URL**: https://dbeaver.io/download/

**Archivo**: `dbeaver-ce-XX.X.X-win32.win32.x86_64.exe` (última versión)

---

## 🔧 Paso 2: Instalar DBeaver

1. **Ejecutar** el archivo `.exe` descargado
2. **Seguir wizard**:
   - **Welcome**: Click "Next"
   - **License**: Aceptar licencia (GPL) → Click "Next"
   - **Choose Install Location**: Dejar por defecto (`C:\Program Files\DBeaver`) → Click "Next"
   - **Choose Start Menu Folder**: Dejar por defecto → Click "Next"
   - **Additional Tasks**: 
     - ✅ Create desktop shortcut (recomendado)
     - ✅ Associate SQL files with DBeaver (opcional)
     - Click "Next"
   - **Ready to Install**: Click "Install"
   - **Installing**: Esperar instalación (1-2 minutos)
   - **Completed**: Click "Finish"

**Tiempo**: 2-3 minutos

---

## 🚀 Paso 3: Abrir DBeaver

1. **Buscar DBeaver** en el menú de inicio
2. **Abrir DBeaver**
3. **Primera vez**: DBeaver puede pedir crear un workspace
   - Dejar por defecto: `C:\Users\Yoel\AppData\Roaming\DBeaverData\workspace6`
   - Click "Launch"

**Tiempo**: 10 segundos

---

## 🔌 Paso 4: Crear Nueva Conexión

### Método 1: Desde el Menú

1. **Click en "Database"** (menú superior)
2. **Seleccionar "New Database Connection"**
3. **O usar atajo**: `Ctrl+Shift+N`

### Método 2: Desde el Icono

1. **Click en el icono de enchufe** en la barra superior
2. **Ver ventana "Connect to a database"**

**Tiempo**: 10 segundos

---

## ⚙️ Paso 5: Seleccionar PostgreSQL

1. **Buscar "PostgreSQL"** en la lista
2. **Seleccionar "PostgreSQL"**
3. **Click "Next"**

**Tiempo**: 10 segundos

---

## 🔐 Paso 6: Configurar Conexión

### Pestaña "Principal" (Main)

**Configuración**:
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `p2p_db`
- **Username**: `p2p_user`
- **Password**: `p2p_password_change_me`

**Opciones**:
- ✅ **Save password**: Marcar si quieres que guarde la contraseña
- ⚠️ **Show all databases**: Desmarcar (solo ver p2p_db)

### Probar Conexión

1. **Click "Test Connection"** (botón abajo)
2. **Si pide descargar driver**:
   - Aparecerá ventana "Download driver"
   - Click "Download" (automático)
   - Esperar descarga (puede tardar 1-2 minutos)
   - Ver mensaje: "Driver downloaded successfully"
   - Click "OK"

3. **Verificar resultado**:
   - Debe aparecer: "Connected"
   - Si hay error, verificar credenciales

**Tiempo**: 1-2 minutos (si descarga driver)

---

## 💾 Paso 7: Guardar Conexión

1. **Click "Finish"**
2. **Ver tu base de datos** en el panel izquierdo:
   - `Database Navigator` → `p2p_db`
   - Expandir para ver: `Schemas` → `public` → `Tables`

**Tiempo**: 10 segundos

---

## 🎨 Paso 8: Explorar Base de Datos

### Ver Tablas

1. **Expandir**: `Database Navigator` → `p2p_db` → `Schemas` → `public` → `Tables`
2. **Ver tablas**:
   - `alerts` - Alertas del sistema
   - `trades` - Operaciones de trading
   - `price_history` - Historial de precios
   - `users` - Usuarios
   - `app_config` - Configuración persistente

### Ver Datos de una Tabla

1. **Click derecho** en tabla (ej: `trades`)
2. **Seleccionar**: "View Data" o "Open Data"
3. **Ver datos** en formato tabla
4. **Navegar**: Usar scroll para ver más datos
5. **Filtrar**: Usar barra de búsqueda para filtrar

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
   - Click "Execute SQL Statement" (icono de play)
   - O: `Ctrl+Enter`
   - O: `F5`

4. **Ver resultados** en la parte inferior

---

## 🎯 Funcionalidades Avanzadas

### 1. Ver Estructura de Tabla

1. **Click derecho** en tabla
2. **Seleccionar**: "Properties" o "View DDL"
3. **Ver estructura**:
   - Columnas y tipos
   - Índices
   - Constraints
   - Triggers

### 2. Crear ER Diagram

1. **Click derecho** en base de datos `p2p_db`
2. **Seleccionar**: "View Diagram"
3. **Ver diagrama** de relaciones entre tablas
4. **Personalizar**: Arrastrar tablas, cambiar colores, etc.

### 3. Exportar Datos

1. **Click derecho** en tabla
2. **Seleccionar**: "Export Data"
3. **Elegir formato**:
   - CSV
   - JSON
   - SQL
   - Excel
   - XML
   - etc.
4. **Configurar** opciones (columnas, filtros, etc.)
5. **Exportar**

### 4. Importar Datos

1. **Click derecho** en tabla
2. **Seleccionar**: "Import Data"
3. **Seleccionar archivo** (CSV, JSON, SQL, etc.)
4. **Configurar** opciones (mapeo de columnas, etc.)
5. **Importar**

### 5. Editar Datos

1. **Ver datos** de una tabla
2. **Click en celda** para editar
3. **Modificar valor**
4. **Guardar**: Click en icono de guardar o `Ctrl+S`
5. **Confirmar**: Click "Yes" para guardar cambios

### 6. Buscar en Datos

1. **Abrir tabla** en modo "View Data"
2. **Click en icono de lupa** (buscar)
3. **Escribir** término de búsqueda
4. **Ver resultados** filtrados

### 7. Ordenar Datos

1. **Abrir tabla** en modo "View Data"
2. **Click en encabezado de columna** para ordenar
3. **Click nuevamente** para cambiar orden (ascendente/descendente)

---

## 🔍 Queries Útiles para Probar

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

### Ver trades más rentables
```sql
SELECT * FROM trades 
WHERE status = 'COMPLETED' 
ORDER BY actual_profit DESC 
LIMIT 10;
```

### Ver spreads más altos
```sql
SELECT asset, fiat, AVG(spread) as avg_spread
FROM price_history
GROUP BY asset, fiat
ORDER BY avg_spread DESC
LIMIT 10;
```

---

## 🎨 Personalizar DBeaver

### Cambiar Tema

1. **Window** → **Preferences** → **Appearance** → **Theme**
2. **Seleccionar tema**: Dark, Light, etc.
3. **Click "Apply and Close"**

### Configurar Editor SQL

1. **Window** → **Preferences** → **SQL Editor**
2. **Configurar**:
   - Autocompletado
   - Formato de código
   - Colores de sintaxis
   - etc.

### Configurar Fuentes

1. **Window** → **Preferences** → **Appearance** → **Colors and Fonts**
2. **Seleccionar** elemento (SQL Editor, etc.)
3. **Cambiar fuente** y tamaño

---

## 🔒 Seguridad

### Ventajas de DBeaver

- ✅ **100% local**: Datos no salen de tu máquina
- ✅ **Sin servicios externos**: No depende de internet
- ✅ **Privacidad total**: Solo tú ves tus datos
- ✅ **Sin límites**: Sin límites de uso
- ✅ **Gratis**: Completamente gratuito

### Recomendaciones

1. **No guardar contraseñas** si trabajas en equipo compartido
2. **Usar contraseñas fuertes** en producción
3. **Backup regular** de datos importantes
4. **No compartir conexiones** con contraseñas guardadas

---

## 🛠️ Troubleshooting

### Problema: No puedo conectarme

**Solución**:
1. Verificar que PostgreSQL esté corriendo:
   ```powershell
   docker ps | Select-String "postgres"
   ```
2. Verificar que el puerto 5432 esté abierto:
   ```powershell
   Test-NetConnection -ComputerName localhost -Port 5432
   ```
3. Verificar credenciales:
   - Host: `localhost` (no `127.0.0.1`)
   - Port: `5432`
   - Database: `p2p_db`
   - Username: `p2p_user`
   - Password: `p2p_password_change_me`

### Problema: Error al descargar driver

**Solución**:
1. Verificar conexión a internet
2. Intentar descargar manualmente desde: https://jdbc.postgresql.org/download/
3. Agregar driver manualmente en DBeaver:
   - `Database` → `Driver Manager` → `New Driver`
   - Seleccionar "PostgreSQL"
   - Agregar archivo JAR del driver

### Problema: No veo las tablas

**Solución**:
1. Expandir: `Database Navigator` → `p2p_db` → `Schemas` → `public` → `Tables`
2. Refrescar: Click derecho en `p2p_db` → "Refresh"
3. Verificar que las tablas existan:
   ```powershell
   docker exec p2p_postgres psql -U p2p_user -d p2p_db -c "\dt"
   ```

### Problema: Error "Connection refused"

**Solución**:
1. Verificar que PostgreSQL esté corriendo
2. Verificar que el puerto 5432 esté expuesto en Docker
3. Verificar que no haya firewall bloqueando el puerto

### Problema: Error "Authentication failed"

**Solución**:
1. Verificar username: `p2p_user`
2. Verificar password: `p2p_password_change_me`
3. Verificar que el usuario tenga permisos en la base de datos

---

## ✅ Checklist de Verificación

### Instalación
- [ ] DBeaver descargado
- [ ] DBeaver instalado
- [ ] DBeaver abierto

### Configuración
- [ ] Conexión creada
- [ ] Credenciales configuradas
- [ ] Conexión probada exitosamente
- [ ] Driver descargado (si fue necesario)

### Uso
- [ ] Base de datos visible
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
- **Video tutoriales**: YouTube - "DBeaver tutorial"

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

---

## 🆘 Si Necesitas Ayuda

1. **Revisar documentación**: `docs/GUIA_DBEAVER_PASO_A_PASO.md`
2. **Revisar troubleshooting**: Sección de troubleshooting arriba
3. **Verificar PostgreSQL**: `.\scripts\verificar-postgres.ps1`
4. **Consultar foros**: https://github.com/dbeaver/dbeaver/discussions

