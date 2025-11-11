# 🗄️ Herramientas Web para Gestionar la Base de Datos

## 📋 Opciones Disponibles

Para PostgreSQL, las mejores herramientas web son:

### 1. **pgAdmin** (Más Popular) ⭐ RECOMENDADO
- **Descripción**: Interfaz web completa para PostgreSQL
- **Características**:
  - Interfaz gráfica completa
  - Editor SQL avanzado
  - Gestión de usuarios y permisos
  - Visualización de datos
  - Exportar/Importar datos
  - Monitoreo de performance
- **Puerto**: 5050
- **Ventajas**: Muy completo, estándar de la industria
- **Desventajas**: Puede ser pesado para algunas tareas simples

### 2. **Adminer** (Más Ligero) ⚡ RECOMENDADO PARA SIMPLICIDAD
- **Descripción**: Cliente web ligero y fácil de usar
- **Características**:
  - Interfaz simple y rápida
  - Soporte para múltiples bases de datos (PostgreSQL, MySQL, SQLite, etc.)
  - Editor SQL
  - Gestión de tablas
  - Exportar/Importar datos
- **Puerto**: 8080
- **Ventajas**: Muy ligero, fácil de usar, una sola página PHP
- **Desventajas**: Menos funciones avanzadas que pgAdmin

### 3. **pgweb** (Minimalista)
- **Descripción**: Cliente web minimalista para PostgreSQL
- **Características**:
  - Interfaz simple
  - Ejecutar queries SQL
  - Visualizar tablas
- **Puerto**: 8081
- **Ventajas**: Muy ligero, rápido
- **Desventajas**: Funcionalidad limitada

### 4. **Hasura** (GraphQL + Admin)
- **Descripción**: Engine GraphQL con interfaz de administración
- **Características**:
  - API GraphQL automática
  - Interfaz de administración
  - Gestión de permisos
  - Visualización de datos
- **Puerto**: 8080
- **Ventajas**: Potente, incluye API GraphQL
- **Desventajas**: Más complejo, requiere más configuración

---

## 🚀 Configuración Rápida

### Opción 1: pgAdmin (Recomendado para uso completo)

Agregar al `docker-compose.yml`:

```yaml
  # pgAdmin para gestión de base de datos
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: p2p_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@p2p.com
      PGADMIN_DEFAULT_PASSWORD: admin_change_me
      PGADMIN_CONFIG_SERVER_MODE: 'False'
      PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: 'False'
    ports:
      - "5050:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    networks:
      - p2p_network
    restart: unless-stopped
    depends_on:
      - postgres
```

**Acceso**:
- URL: http://localhost:5050
- Email: `admin@p2p.com`
- Password: `admin_change_me`

**Configuración del servidor en pgAdmin**:
1. Login en pgAdmin
2. Click derecho en "Servers" → "Register" → "Server"
3. **General Tab**:
   - Name: `P2P Database`
4. **Connection Tab**:
   - Host: `postgres` (nombre del servicio en Docker)
   - Port: `5432`
   - Database: `p2p_db`
   - Username: `p2p_user`
   - Password: `p2p_password_change_me`
5. Click "Save"

---

### Opción 2: Adminer (Recomendado para simplicidad) ⚡

Agregar al `docker-compose.yml`:

```yaml
  # Adminer para gestión de base de datos (ligero)
  adminer:
    image: adminer:latest
    container_name: p2p_adminer
    ports:
      - "8080:8080"
    networks:
      - p2p_network
    restart: unless-stopped
    depends_on:
      - postgres
```

**Acceso**:
- URL: http://localhost:8080
- Sistema: `PostgreSQL`
- Servidor: `postgres` (nombre del servicio en Docker)
- Usuario: `p2p_user`
- Contraseña: `p2p_password_change_me`
- Base de datos: `p2p_db`

---

### Opción 3: pgweb (Minimalista)

Agregar al `docker-compose.yml`:

```yaml
  # pgweb para gestión de base de datos (minimalista)
  pgweb:
    image: sosedoff/pgweb:latest
    container_name: p2p_pgweb
    environment:
      PGWEB_DATABASE_URL: postgres://p2p_user:p2p_password_change_me@postgres:5432/p2p_db?sslmode=disable
    ports:
      - "8081:8081"
    networks:
      - p2p_network
    restart: unless-stopped
    depends_on:
      - postgres
```

**Acceso**:
- URL: http://localhost:8081
- Se conecta automáticamente a la base de datos

---

## 📊 Comparación Rápida

| Herramienta | Complejidad | Funciones | Recursos | Mejor Para |
|------------|-------------|-----------|----------|------------|
| **pgAdmin** | Media | ⭐⭐⭐⭐⭐ | Alto | Uso completo, administración avanzada |
| **Adminer** | Baja | ⭐⭐⭐⭐ | Bajo | Uso rápido, simplicidad |
| **pgweb** | Baja | ⭐⭐⭐ | Muy bajo | Consultas simples, visualización |
| **Hasura** | Alta | ⭐⭐⭐⭐⭐ | Medio | API GraphQL + administración |

---

## 🎯 Recomendación

### Para empezar rápido: **Adminer**
- Muy fácil de configurar
- Interfaz simple
- Hace todo lo necesario

### Para uso completo: **pgAdmin**
- Interfaz completa
- Más funciones
- Estándar de la industria

---

## 🔧 Agregar al Proyecto

Te recomiendo agregar **Adminer** por su simplicidad. Aquí está la configuración completa:

### Paso 1: Agregar al docker-compose.yml

```yaml
  # Adminer para gestión de base de datos
  adminer:
    image: adminer:latest
    container_name: p2p_adminer
    ports:
      - "8080:8080"
    networks:
      - p2p_network
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
```

### Paso 2: Agregar volumen (opcional)

```yaml
volumes:
  # ... otros volúmenes existentes
  pgadmin_data:  # Solo si usas pgAdmin
```

### Paso 3: Iniciar el servicio

```bash
docker-compose up -d adminer
```

### Paso 4: Acceder

1. Abrir http://localhost:8080
2. Configurar conexión:
   - **Sistema**: `PostgreSQL`
   - **Servidor**: `postgres`
   - **Usuario**: `p2p_user`
   - **Contraseña**: `p2p_password_change_me`
   - **Base de datos**: `p2p_db`
3. Click "Entrar"

---

## 📝 Uso de Adminer

### Ver Tablas
1. Click en la base de datos `p2p_db`
2. Verás todas las tablas: `alerts`, `trades`, `price_history`, `users`, `app_config`

### Ejecutar Queries
1. Click en "SQL command"
2. Escribe tu query:
   ```sql
   SELECT * FROM trades ORDER BY created_at DESC LIMIT 10;
   ```
3. Click "Execute"

### Ver Datos de una Tabla
1. Click en el nombre de la tabla (ej: `trades`)
2. Verás todos los datos
3. Puedes filtrar, ordenar, editar, eliminar

### Exportar Datos
1. Selecciona la tabla
2. Click en "Export"
3. Elige formato (SQL, CSV, JSON, etc.)
4. Click "Export"

### Importar Datos
1. Click en "Import"
2. Selecciona archivo
3. Click "Execute"

---

## 🔒 Seguridad

### Recomendaciones
1. **No exponer en producción** sin autenticación adicional
2. **Usar contraseñas fuertes** en producción
3. **Restringir acceso** por IP si es posible
4. **Usar HTTPS** en producción

### Para Desarrollo Local
- Está bien usar Adminer sin autenticación adicional
- Solo accesible desde `localhost`

---

## 🎨 Screenshots de Referencia

### Adminer
- Interfaz simple y limpia
- Fácil de navegar
- Editor SQL integrado

### pgAdmin
- Interfaz más completa
- Más opciones de configuración
- Mejor para administración avanzada

---

## ✅ Conclusión

**Recomendación**: Agregar **Adminer** por su simplicidad y facilidad de uso.

**Pasos**:
1. Agregar servicio Adminer al `docker-compose.yml`
2. Iniciar: `docker-compose up -d adminer`
3. Acceder: http://localhost:8080
4. Conectar a la base de datos

¿Quieres que agregue Adminer o pgAdmin a tu `docker-compose.yml`?

