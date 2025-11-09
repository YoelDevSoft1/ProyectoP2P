# Guía de Inicio Rápido - Casa de Cambio P2P

Esta guía te ayudará a poner en marcha el sistema completo en tu máquina local.

## Pre-requisitos

Asegúrate de tener instalado:

- **Docker Desktop** (https://www.docker.com/products/docker-desktop)
- **Node.js 18+** (https://nodejs.org/)
- **Python 3.11+** (https://www.python.org/)
- **Git** (https://git-scm.com/)

## Paso 1: Configurar Variables de Entorno

1. Copia el archivo de ejemplo:
```bash
cp .env.example .env
```

2. Edita el archivo `.env` y configura las siguientes variables **CRÍTICAS**:

```env
# Binance API - ¡IMPORTANTE!
BINANCE_API_KEY=tu_api_key_de_binance
BINANCE_API_SECRET=tu_api_secret_de_binance

# Seguridad
SECRET_KEY=genera_una_clave_secreta_segura_aqui

# Notificaciones (opcional)
TELEGRAM_BOT_TOKEN=tu_bot_token
TELEGRAM_CHAT_ID=tu_chat_id
```

### Cómo obtener las API Keys de Binance:

1. Inicia sesión en Binance
2. Ve a **Perfil > API Management**
3. Crea una nueva API Key
4. **IMPORTANTE**:
   - Habilita solo permisos de **lectura** para P2P
   - **NO** habilites permisos de retiro
   - Guarda las keys en un lugar seguro
   - **NUNCA** las compartas ni las subas a GitHub

## Paso 2: Iniciar Servicios con Docker

```bash
# Iniciar todos los servicios
docker-compose up -d

# Verificar que estén corriendo
docker-compose ps
```

Deberías ver los siguientes servicios:
- ✅ postgres (PostgreSQL + TimescaleDB)
- ✅ redis (Cache)
- ✅ rabbitmq (Cola de mensajes)
- ✅ backend (FastAPI)
- ✅ celery_worker (Worker asíncrono)
- ✅ celery_beat (Tareas programadas)
- ✅ frontend (Next.js)
- ✅ grafana (Monitoreo - opcional)

## Paso 3: Verificar el Backend

Abre tu navegador y ve a:
- **API Docs**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/api/v1/health

Deberías ver:
```json
{
  "status": "healthy",
  "services": {
    "postgresql": "connected",
    "redis": "connected"
  }
}
```

## Paso 4: Iniciar el Frontend (Desarrollo)

Si quieres ejecutar el frontend en modo desarrollo (con hot reload):

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar en modo desarrollo
npm run dev
```

El frontend estará disponible en: http://localhost:3000

## Paso 5: Acceder a las Interfaces

### Landing Page
- **URL**: http://localhost:3000
- **Descripción**: Página principal con tasas en tiempo real

### Dashboard
- **URL**: http://localhost:3000/dashboard
- **Descripción**: Panel de control con estadísticas y monitoreo

### API Backend
- **URL**: http://localhost:8000/api/v1/docs
- **Descripción**: Documentación interactiva de la API (Swagger)

### RabbitMQ Management
- **URL**: http://localhost:15672
- **Usuario**: p2p_user
- **Password**: p2p_password_change_me
- **Descripción**: Monitoreo de colas de mensajes

### Grafana (Opcional)
- **URL**: http://localhost:3001
- **Usuario**: admin
- **Password**: admin_change_me
- **Descripción**: Dashboards de monitoreo avanzado

## Paso 6: Verificar Funcionalidad

### 1. Ver Precios en Tiempo Real

```bash
curl http://localhost:8000/api/v1/prices/current
```

### 2. Ver TRM de Colombia

```bash
curl http://localhost:8000/api/v1/prices/trm
```

### 3. Ver Estadísticas de Trading

```bash
curl http://localhost:8000/api/v1/trades/stats/summary?days=7
```

## Configuración del Bot de Trading

El bot tiene 3 modos de operación configurables en `.env`:

```env
# Modo manual: Solo análisis y alertas, sin operaciones automáticas
TRADING_MODE=manual

# Modo auto: Ejecuta operaciones automáticamente
TRADING_MODE=auto

# Modo híbrido: Auto para pequeñas, manual para grandes
TRADING_MODE=hybrid
```

### Configurar Límites de Trading

```env
# Margen de ganancia por operación
PROFIT_MARGIN_COP=2.5
PROFIT_MARGIN_VES=3.0

# Límites de operación
MIN_TRADE_AMOUNT=50
MAX_TRADE_AMOUNT=1000
MAX_DAILY_TRADES=50

# Stop loss
STOP_LOSS_PERCENTAGE=1.5
```

## Monitoreo de Logs

### Ver logs del backend:
```bash
docker-compose logs -f backend
```

### Ver logs del celery worker:
```bash
docker-compose logs -f celery_worker
```

### Ver logs del celery beat (tareas programadas):
```bash
docker-compose logs -f celery_beat
```

## Tareas Automáticas

El sistema ejecuta las siguientes tareas automáticamente:

| Tarea | Frecuencia | Descripción |
|-------|-----------|-------------|
| Actualizar precios | 10 seg | Obtiene precios de Binance P2P |
| Actualizar TRM | 5 min | Obtiene TRM del gobierno de Colombia |
| Analizar spread | 30 seg | Detecta oportunidades de arbitraje |
| Bot de trading | 1 min | Ejecuta el ciclo de trading (si está habilitado) |
| Re-entrenar ML | 24 hrs | Re-entrena modelos de Machine Learning |
| Limpiar datos | 1 semana | Elimina datos antiguos |

## Detener el Sistema

```bash
# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (¡CUIDADO! Borra la base de datos)
docker-compose down -v
```

## Problemas Comunes

### Error: "Cannot connect to database"
- Verifica que PostgreSQL esté corriendo: `docker-compose ps`
- Espera 30 segundos para que la DB termine de inicializar
- Reinicia el backend: `docker-compose restart backend`

### Error: "Binance API error"
- Verifica que tus API keys sean correctas
- Asegúrate de tener permisos habilitados en Binance
- Revisa los logs: `docker-compose logs backend`

### Frontend no se conecta al backend
- Verifica la variable `NEXT_PUBLIC_API_URL` en `.env`
- Asegúrate de que el backend esté corriendo en puerto 8000
- Revisa CORS en el backend (configurado en `backend/app/main.py`)

### Celery worker no procesa tareas
- Verifica RabbitMQ: `docker-compose logs rabbitmq`
- Reinicia el worker: `docker-compose restart celery_worker`
- Revisa logs: `docker-compose logs -f celery_worker`

## Desarrollo

### Ejecutar tests del backend:
```bash
cd backend
python -m pytest
```

### Lint del código:
```bash
# Backend
cd backend
black app/
flake8 app/

# Frontend
cd frontend
npm run lint
```

## Siguientes Pasos

1. **Configurar notificaciones**: Configura Telegram o Email para recibir alertas
2. **Ajustar parámetros**: Experimenta con diferentes márgenes y límites
3. **Monitorear rendimiento**: Usa Grafana para crear dashboards personalizados
4. **Entrenar modelos ML**: Espera acumular datos suficientes (mínimo 1000 registros)
5. **Modo automático**: Cuando te sientas cómodo, activa `TRADING_MODE=auto`

## Seguridad

⚠️ **IMPORTANTE**:

- **NUNCA** commitees el archivo `.env`
- Cambia todas las contraseñas por defecto
- Usa claves API con permisos mínimos
- En producción, usa HTTPS
- Implementa autenticación para el dashboard
- Habilita rate limiting
- Haz backups regulares de la base de datos

## Soporte

Si encuentras problemas:

1. Revisa los logs: `docker-compose logs -f`
2. Verifica la health del sistema: http://localhost:8000/api/v1/health
3. Consulta la documentación de la API: http://localhost:8000/api/v1/docs

## ¡Listo para Operar! 🚀

El sistema está configurado y listo para usar. Recuerda:
- Empieza en modo `manual` para familiarizarte
- Monitorea las operaciones constantemente
- Ajusta los parámetros según tu experiencia
- ¡Nunca operes más de lo que puedes permitirte perder!
