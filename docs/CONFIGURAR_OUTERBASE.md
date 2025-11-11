# 🚀 Configurar Outerbase - Guía Rápida

## 📋 Resumen

Outerbase es una plataforma web con IA para gestionar y visualizar bases de datos. Se conecta a tu PostgreSQL existente.

**URL**: https://www.outerbase.com/

---

## 🎯 Características Principales

### 1. IA Integrada (EZQL™)
- Pregunta en lenguaje natural: "¿Cuántos trades hay en la última semana?"
- Genera queries automáticamente
- Ayuda a escribir y corregir queries

### 2. Dashboards
- Crea dashboards interactivos
- Auto-genera gráficos con IA
- Embed dashboards en tu aplicación

### 3. Tablas tipo Spreadsheet
- Navega datos como spreadsheet
- Edita datos directamente
- Filtra y ordena fácilmente

### 4. Data Catalog
- Catálogo de datos
- Diagramas relacionales
- Documentación de BD

---

## 🚀 Configuración Paso a Paso

### Paso 1: Crear Cuenta en Outerbase

1. Visitar: https://www.outerbase.com/
2. Crear cuenta gratuita
3. Verificar email

### Paso 2: Configurar ngrok para PostgreSQL

**⚠️ IMPORTANTE**: Outerbase está en la nube, pero tu PostgreSQL está en localhost. Necesitas exponer PostgreSQL.

#### Opción A: Agregar a ngrok.yml (Ya configurado)

Ya agregué el túnel de PostgreSQL a `docker/ngrok/ngrok.yml`:

```yaml
tunnels:
  backend:
    addr: backend:8000
    proto: http
  postgres:
    addr: postgres:5432
    proto: tcp
```

#### Reiniciar ngrok

```bash
docker-compose restart ngrok
```

#### Obtener URL de PostgreSQL

1. Visitar: http://localhost:4040
2. Ver túneles activos
3. Buscar el túnel `postgres`
4. Copiar la URL TCP (ejemplo: `tcp://0.tcp.ngrok.io:12345`)

### Paso 3: Conectar en Outerbase

1. **Nueva Conexión**:
   - Click en "Connections" o "New Connection"
   - Seleccionar "PostgreSQL"

2. **Configuración**:
   - **Connection Name**: `P2P Database`
   - **Host**: `0.tcp.ngrok.io` (el host de ngrok, sin `tcp://`)
   - **Port**: `12345` (el puerto que ngrok asigne)
   - **Database**: `p2p_db`
   - **Username**: `p2p_user`
   - **Password**: `p2p_password_change_me`
   - **SSL Mode**: `disable`

3. **Test Connection**:
   - Click "Test Connection"
   - Verificar que funcione

4. **Save**:
   - Click "Save" o "Connect"

### Paso 4: Usar Outerbase

#### Usar EZQL™ (IA)

1. **Preguntar en lenguaje natural**:
   - "¿Cuántos trades hay en la última semana?"
   - "Muestra los trades más rentables"
   - "¿Cuál es el spread promedio por par?"

2. **Outerbase genera la query automáticamente**

3. **Ver resultados**

#### Crear Dashboards

1. **Nuevo Dashboard**:
   - Click "Dashboards" → "New Dashboard"
   - Nombre: "P2P Trading Dashboard"

2. **Agregar Gráficos**:
   - Usar EZQL™: "Muestra los trades por día"
   - Outerbase genera el gráfico automáticamente

3. **Embed**:
   - Obtener código para embedir
   - Agregar a tu aplicación frontend

#### Navegar Datos

1. **Ver Tablas**:
   - Ver todas las tablas
   - Click en una tabla para ver datos

2. **Editar Datos**:
   - Navegar como spreadsheet
   - Editar directamente
   - Guardar cambios

---

## 🔒 Seguridad

### Consideraciones

1. **ngrok TCP**:
   - ⚠️ Público (cualquiera con la URL puede conectarse)
   - ✅ Rápido y fácil
   - ⚠️ Solo para desarrollo

2. **SSH Tunneling** (Más seguro):
   - ✅ Conexión encriptada
   - ✅ Autenticación por clave SSH
   - ✅ Recomendado para producción

### Recomendación

- **Desarrollo**: Usar ngrok TCP
- **Producción**: Usar SSH Tunneling

---

## 📊 Comparación Rápida

| Característica | Outerbase | DBeaver | Adminer |
|---------------|-----------|---------|---------|
| **IA Integrada** | ✅ Sí | ❌ No | ❌ No |
| **Dashboards** | ✅ Sí | ❌ No | ❌ No |
| **Web-based** | ✅ Sí | ❌ No | ✅ Sí |
| **Privacidad** | ⚠️ Datos pasan por sus servidores | ✅ 100% local | ✅ 100% local |
| **Editor SQL** | ✅ Básico con IA | ✅ Avanzado | ✅ Básico |

---

## 🎯 Recomendación

### Usar los 3 Herramientas

1. **DBeaver**: Para administración y desarrollo
2. **Outerbase**: Para dashboards y visualizaciones
3. **Adminer**: Como alternativa ligera

**Ventajas**:
- ✅ Lo mejor de todos los mundos
- ✅ DBeaver para trabajo técnico
- ✅ Outerbase para visualización y dashboards
- ✅ Adminer para acceso rápido

---

## ✅ Próximos Pasos

1. ✅ **DBeaver**: Instalar y configurar (para administración)
2. ✅ **Outerbase**: Crear cuenta y conectar (para dashboards)
3. ✅ **Adminer**: Ya está configurado (como backup)

¿Quieres que te ayude a configurar Outerbase o DBeaver?

