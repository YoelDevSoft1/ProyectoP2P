# Casa de Cambio P2P - Sistema Automatizado

Sistema completo de casa de cambio con trading automatizado en Binance P2P para operaciones USDT/COP y USDT/VES.

## Características Principales

- **Landing Page**: Tasas en tiempo real con TRM + margen de ganancia
- **Trading Automatizado**: Bot inteligente para operar en Binance P2P
- **Análisis de Spread**: Detección de oportunidades de arbitraje
- **Machine Learning**: Predicción de mejores momentos para operar
- **Dashboard**: Monitoreo en tiempo real de operaciones
- **Modo Manual/Automático**: Control total sobre las operaciones

## Stack Tecnológico

### Frontend
- Next.js 14+ (TypeScript)
- TailwindCSS + shadcn/ui
- Recharts para visualización
- WebSockets para datos en tiempo real

### Backend
- FastAPI (Python 3.11+)
- PostgreSQL + TimescaleDB
- Redis para cache
- RabbitMQ + Celery para tareas asíncronas
- Binance Connector Python

### ML/Análisis
- pandas, numpy
- scikit-learn
- TA-Lib

## Estructura del Proyecto

```
ProyectoP2P/
├── backend/              # API FastAPI
│   ├── app/
│   │   ├── api/         # Endpoints REST
│   │   ├── core/        # Configuración
│   │   ├── models/      # Modelos DB
│   │   ├── services/    # Lógica de negocio
│   │   ├── trading/     # Bot de trading
│   │   └── ml/          # Modelos ML
│   ├── celery_app/      # Workers asíncronos
│   └── tests/
├── frontend/            # Next.js app
│   ├── src/
│   │   ├── app/        # App router
│   │   ├── components/ # Componentes React
│   │   └── lib/        # Utilidades
│   └── public/
├── docker/              # Dockerfiles
└── docker-compose.yml
```

## Requisitos del Sistema

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- 16GB RAM mínimo
- Conexión a internet estable

## Inicio Rápido

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Edita .env y agrega tus API keys de Binance

# 2. Instalar dependencias
make install

# 3. Iniciar todos los servicios
make start

# 4. Verificar que todo funciona
make health
```

Luego accede a:
- **Landing Page**: http://localhost:3000
- **Dashboard**: http://localhost:3000/dashboard
- **API Docs**: http://localhost:8000/api/v1/docs

📖 **[Ver Guía Completa de Inicio](docs/QUICKSTART.md)**

## Configuración

### Variables de Entorno Críticas

```env
# API Keys de Binance (REQUERIDO)
BINANCE_API_KEY=tu_api_key
BINANCE_API_SECRET=tu_api_secret

# Modo de Trading
TRADING_MODE=manual  # manual, auto, hybrid

# Márgenes de Ganancia
PROFIT_MARGIN_COP=2.5
PROFIT_MARGIN_VES=3.0
```

Ver [.env.example](.env.example) para todas las configuraciones disponibles.

## Comandos Útiles

```bash
make start          # Iniciar servicios
make stop           # Detener servicios
make logs           # Ver logs
make restart        # Reiniciar servicios
make clean          # Limpiar todo (¡cuidado!)
make backend-logs   # Ver logs del backend
make worker-logs    # Ver logs del worker
```

## Seguridad

- ⚠️ **NUNCA** commitear las API keys de Binance
- Usar variables de entorno para credenciales
- Implementar rate limiting
- Validar todos los inputs

## Licencia

Privado - Todos los derechos reservados
