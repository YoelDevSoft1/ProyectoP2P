# 🗄️ DBeaver - Gestión de Base de Datos

## ✅ Estado

**DBeaver NO requiere migración** - Es solo una herramienta de administración.

**PostgreSQL está listo**:
- ✅ Contenedor corriendo
- ✅ Puerto 5432 abierto
- ✅ Base de datos `p2p_db` disponible
- ✅ Tablas creadas

---

## 🚀 Instalación Rápida

### Paso 1: Descargar DBeaver

1. **Visitar**: https://dbeaver.io/download/
2. **Descargar**: Windows 64 bit (installer)
3. **Ejecutar**: Archivo `.exe` descargado

### Paso 2: Instalar

1. **Seguir wizard** de instalación
2. **Click "Next"** → **"Install"** → **"Finish"**

### Paso 3: Configurar Conexión

1. **Abrir DBeaver**
2. **Click "Nueva Conexión"** (icono de enchufe)
3. **Seleccionar "PostgreSQL"**
4. **Configurar**:
   - Host: `localhost`
   - Port: `5432`
   - Database: `p2p_db`
   - Username: `p2p_user`
   - Password: `p2p_password_change_me`
5. **Click "Test Connection"**
6. **Click "Finish"**

### Paso 4: ¡Listo!

Ya puedes usar DBeaver para gestionar tu base de datos.

---

## 📋 Configuración

### Credenciales

- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `p2p_db`
- **Username**: `p2p_user`
- **Password**: `p2p_password_change_me`

### Tablas Disponibles

- `alerts` - Alertas del sistema
- `trades` - Operaciones de trading
- `price_history` - Historial de precios
- `users` - Usuarios
- `app_config` - Configuración persistente

---

## 🎨 Funcionalidades

### Ver Datos
- Explorar tablas
- Ver registros
- Filtrar y ordenar

### Ejecutar Queries
- Editor SQL avanzado
- Autocompletado
- Sintaxis highlighting

### ER Diagrams
- Ver diagramas de relaciones
- Entender estructura de BD

### Exportar/Importar
- Exportar a CSV, JSON, SQL, Excel
- Importar desde archivos

### Editar Datos
- Editar datos directamente
- Guardar cambios

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

### Contar registros
```sql
SELECT 
    'trades' as tabla, COUNT(*) as total FROM trades
UNION ALL
SELECT 'alerts', COUNT(*) FROM alerts
UNION ALL
SELECT 'price_history', COUNT(*) FROM price_history;
```

---

## 📚 Documentación

- **Guía completa**: `docs/GUIA_DBEAVER_PASO_A_PASO.md`
- **Instalación rápida**: `docs/DBEAVER_INSTALACION_RAPIDA.md`
- **Configuración completa**: `docs/DBEAVER_CONFIGURACION_COMPLETA.md`

---

## ✅ Verificación

### Verificar PostgreSQL

```powershell
.\scripts\verificar-postgres.ps1
```

### Verificar Instalación de DBeaver

```powershell
.\scripts\instalar-dbeaver.ps1
```

---

## 🎯 Ventajas

- ✅ **100% local**: Datos no salen de tu máquina
- ✅ **Muy completo**: Todas las funciones necesarias
- ✅ **Gratis**: Completamente gratuito
- ✅ **Fácil de usar**: Interfaz intuitiva
- ✅ **Sin migración**: Solo herramienta de administración

---

## 🆘 Troubleshooting

### No puedo conectarme
1. Verificar que PostgreSQL esté corriendo
2. Verificar que el puerto 5432 esté abierto
3. Verificar credenciales

### Error al descargar driver
1. Verificar conexión a internet
2. Intentar descargar manualmente

### No veo las tablas
1. Refrescar conexión
2. Expandir: `Schemas` → `public` → `Tables`

---

## ✅ Conclusión

**DBeaver es la herramienta perfecta** para gestionar tu base de datos:
- ✅ Muy fácil de configurar
- ✅ Muy completo
- ✅ 100% privacidad
- ✅ Gratis

¡Disfruta gestionando tu base de datos! 🎉

