# 🚀 Configuración de Outerbase - Guía Completa

## 📋 Resumen

Outerbase es una plataforma web con IA para gestionar y visualizar bases de datos. Se conecta a tu PostgreSQL existente (no migras la BD, solo cambias la herramienta).

**URL**: https://www.outerbase.com/

---

## 🎯 Características Principales

### 1. IA Integrada (EZQL™)
- Pregunta en lenguaje natural sobre tus datos
- Genera queries automáticamente
- Ayuda a escribir y corregir queries

### 2. Editor con IA
- Autocompletado inteligente
- Sugerencias de queries
- Corrección de errores

### 3. Auto-generación de Gráficos
- Crea visualizaciones automáticamente
- Dashboards interactivos
- Gráficos embedibles

### 4. Tablas tipo Spreadsheet
- Navegación intuitiva
- Edición directa de datos
- Filtros y ordenamiento

### 5. Data Catalog
- Catálogo de datos
- Términos de negocio
- Diagramas relacionales

### 6. Dashboards
- Dashboards interactivos
- Gráficos con IA
- Embedibles en tu aplicación

---

## 🚀 Configuración Paso a Paso

### Paso 1: Crear Cuenta en Outerbase

1. **Visitar**: https://www.outerbase.com/
2. **Registrarse**: Crear cuenta gratuita
3. **Verificar Email**: Verificar tu email

### Paso 2: Exponer PostgreSQL (Importante)

**⚠️ PROBLEMA**: Outerbase está en la nube, pero tu PostgreSQL está en localhost.

**Soluciones**:

#### Opción A: Usar ngrok (Recomendado para desarrollo)

1. **Ya tienes ngrok configurado** en tu proyecto
2. **Exponer PostgreSQL**:
   ```bash
   # Agregar túnel para PostgreSQL en ngrok.yml
   # O usar ngrok CLI:
   ngrok tcp 5432
   ```
3. **Obtener URL pública**: ngrok te dará una URL pública
4. **Usar en Outerbase**: Usar la URL de ngrok como host

#### Opción B: SSH Tunneling (Más seguro)

Outerbase soporta SSH tunneling:

1. **Configurar SSH en tu servidor**
2. **En Outerbase**: Usar opción "SSH Tunnel"
3. **Configurar**:
   - SSH Host: Tu servidor
   - SSH Port: 22
   - SSH User: Tu usuario
   - SSH Key: Tu clave SSH
   - Database Host: localhost (desde el servidor)
   - Database Port: 5432

#### Opción C: Exponer PostgreSQL Públicamente (No recomendado)

1. **Configurar firewall** para permitir conexión externa
2. **Actualizar PostgreSQL** para escuchar en 0.0.0.0
3. **⚠️ RIESGO**: Exponer BD públicamente es inseguro

### Paso 3: Conectar Base de Datos en Outerbase

1. **Nueva Conexión**:
   - Click en "Connections" o "New Connection"
   - Seleccionar "PostgreSQL"

2. **Configuración**:
   - **Connection Name**: `P2P Database`
   - **Host**: `[tu-host]` (localhost si usas SSH, ngrok URL si usas ngrok)
   - **Port**: `5432` (o puerto de ngrok si usas ngrok)
   - **Database**: `p2p_db`
   - **Username**: `p2p_user`
   - **Password**: `p2p_password_change_me`
   - **SSL Mode**: `disable` (o `require` si usas SSL)

3. **SSH Tunnel** (si usas Opción B):
   - Habilitar "Use SSH Tunnel"
   - Configurar SSH credentials

4. **Test Connection**:
   - Click "Test Connection"
   - Verificar que la conexión funcione

5. **Save**:
   - Click "Save" o "Connect"

### Paso 4: Explorar Datos

1. **Ver Tablas**:
   - Ver todas las tablas: `alerts`, `trades`, `price_history`, `users`, `app_config`
   - Click en una tabla para ver datos

2. **Navegar Datos**:
   - Navegar como spreadsheet
   - Filtrar y ordenar
   - Editar datos directamente

3. **Usar EZQL™ (IA)**:
   - Pregunta en lenguaje natural: "¿Cuántos trades hay en la última semana?"
   - Outerbase genera la query automáticamente
   - Ver resultados

### Paso 5: Crear Dashboards

1. **Nuevo Dashboard**:
   - Click en "Dashboards" → "New Dashboard"
   - Nombre: "P2P Trading Dashboard"

2. **Agregar Gráficos**:
   - Usar EZQL™ para generar gráficos
   - Ejemplo: "Muestra los trades por día"
   - Outerbase genera el gráfico automáticamente

3. **Personalizar**:
   - Agregar más gráficos
   - Personalizar colores
   - Configurar filtros

4. **Embed**:
   - Obtener código para embedir
   - Agregar a tu aplicación frontend

---

## 🔧 Configurar ngrok para PostgreSQL

### Opción 1: Agregar a ngrok.yml

Agregar túnel para PostgreSQL en `docker/ngrok/ngrok.yml`:

```yaml
tunnels:
  backend:
    addr: backend:8000
    proto: http
    hostname: denver-unbrooded-miley.ngrok-free.dev
  
  postgres:
    addr: postgres:5432
    proto: tcp
```

**⚠️ NOTA**: ngrok free tier tiene límites en conexiones TCP.

### Opción 2: Usar ngrok CLI

```bash
# En una terminal separada
ngrok tcp 5432
```

Esto te dará una URL pública tipo: `tcp://0.tcp.ngrok.io:12345`

**Usar en Outerbase**:
- Host: `0.tcp.ngrok.io`
- Port: `12345` (el puerto que ngrok asigne)

---

## 🎨 Usar Funcionalidades de Outerbase

### 1. EZQL™ (IA para Queries)

**Ejemplos de preguntas**:
- "¿Cuántos trades hay en la última semana?"
- "Muestra los trades más rentables"
- "¿Cuál es el spread promedio por par?"
- "Muestra las alertas no leídas"

**Outerbase genera la query automáticamente** y muestra los resultados.

### 2. Editor con IA

1. **Escribir Query**:
   ```sql
   SELECT * FROM trades WHERE status = 'COMPLETED'
   ```

2. **IA ayuda**:
   - Autocompletado inteligente
   - Sugerencias de mejora
   - Corrección de errores

3. **Ejecutar**:
   - Click "Run"
   - Ver resultados

### 3. Auto-generación de Gráficos

1. **Preguntar a EZQL™**:
   - "Muestra los trades por día en un gráfico"
   - "Muestra el profit por mes"

2. **Outerbase genera**:
   - Query SQL
   - Gráfico automáticamente
   - Dashboard interactivo

### 4. Tablas tipo Spreadsheet

1. **Navegar Datos**:
   - Click en tabla `trades`
   - Ver datos como spreadsheet
   - Filtrar y ordenar

2. **Editar Datos**:
   - Click en celda
   - Editar directamente
   - Guardar cambios

### 5. Dashboards

1. **Crear Dashboard**:
   - Click "Dashboards" → "New Dashboard"
   - Nombre: "P2P Trading Analytics"

2. **Agregar Gráficos**:
   - Usar EZQL™ para generar gráficos
   - Agregar múltiples gráficos
   - Personalizar

3. **Embed**:
   - Obtener código de embed
   - Agregar a tu frontend:
     ```html
     <iframe src="https://outerbase.com/dashboard/xxx" width="100%" height="600"></iframe>
     ```

### 6. Data Catalog

1. **Definir Términos**:
   - Click "Data Catalog"
   - Agregar términos de negocio
   - Ejemplo: "Trade" = "Operación de compra/venta de criptomonedas"

2. **Diagramas Relacionales**:
   - Ver relaciones entre tablas
   - Entender estructura de BD

3. **Documentación**:
   - Documentar tu base de datos
   - Agregar descripciones a columnas

---

## 🔒 Seguridad

### Consideraciones

1. **Datos en Tránsito**:
   - Outerbase usa encriptación TLS
   - Datos encriptados en tránsito

2. **Datos en Reposo**:
   - Outerbase NO almacena tus datos
   - Solo se conecta a tu BD
   - Tus datos quedan en tu servidor

3. **Autenticación**:
   - Usar contraseñas fuertes
   - Habilitar 2FA si está disponible
   - Restringir acceso por IP si es posible

4. **SSH Tunneling**:
   - Más seguro que exponer PostgreSQL públicamente
   - Recomendado para producción

---

## 📊 Comparación con Otras Herramientas

| Característica | Outerbase | DBeaver | Adminer |
|---------------|-----------|---------|---------|
| **IA Integrada** | ✅ Sí | ❌ No | ❌ No |
| **Dashboards** | ✅ Sí | ❌ No | ❌ No |
| **Auto-gráficos** | ✅ Sí | ❌ No | ❌ No |
| **Web-based** | ✅ Sí | ❌ No | ✅ Sí |
| **Privacidad** | ⚠️ Datos pasan por sus servidores | ✅ 100% local | ✅ 100% local |
| **Costo** | 💰 Gratis (planes pagos) | ✅ Gratis | ✅ Gratis |
| **Instalación** | ✅ No | ❌ Sí | ✅ No (Docker) |

---

## 🎯 Recomendación

### Usar Outerbase para:
- ✅ Dashboards y visualizaciones
- ✅ IA para ayudar con queries
- ✅ Análisis rápido de datos
- ✅ Crear gráficos automáticamente

### Usar DBeaver para:
- ✅ Administración seria
- ✅ Desarrollo y debugging
- ✅ Queries complejas
- ✅ ER diagrams

### Usar Adminer para:
- ✅ Acceso rápido desde navegador
- ✅ Tareas simples
- ✅ Alternativa ligera

---

## ✅ Próximos Pasos

1. **Crear cuenta** en Outerbase
2. **Configurar conexión** a PostgreSQL (usar ngrok o SSH)
3. **Explorar funcionalidades** (EZQL™, dashboards, etc.)
4. **Crear dashboards** para tu aplicación
5. **Embed dashboards** en tu frontend

¿Quieres que te ayude a configurar la conexión de Outerbase a tu PostgreSQL?

