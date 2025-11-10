# Casa de Cambio P2P - Sistema Automatizado

> Plataforma integral de compraventa USDT/COP y USDT/VES con landing page pública, dashboard avanzado y un backend FastAPI con trading automatizado sobre Binance P2P.

## Tabla de Contenido
1. [Características clave](#características-clave)
2. [Arquitectura de alto nivel](#arquitectura-de-alto-nivel)
3. [Stack tecnológico](#stack-tecnológico)
4. [Requisitos del sistema](#requisitos-del-sistema)
5. [Variables de entorno esenciales](#variables-de-entorno-esenciales)
6. [Inicio rápido](#inicio-rápido)
7. [Desarrollo y comandos útiles](#desarrollo-y-comandos-útiles)
8. [Estructura del proyecto](#estructura-del-proyecto)
9. [Documentación complementaria](#documentación-complementaria)
10. [Roadmap y flujos pendientes](#roadmap-y-flujos-pendientes)
11. [Seguridad](#seguridad)
12. [Licencia](#licencia)

## Características clave

- **Landing Page en tiempo real** con tasas, calculadora y CTAs optimizadas para conversión.
- **Dashboard operativo** con métricas de trading, alertas, inventario y analítica avanzada.
- **Bot automatizado Binance P2P** con modos manual/auto/híbrido y límites de riesgo configurables.
- **Motor de precios y ML** para predicción de spreads, oportunidades y recomendación de tarifas.
- **Infraestructura dockerizada** (FastAPI, PostgreSQL + TimescaleDB, Redis, RabbitMQ, Celery, Workers) lista para despliegues locales o cloud.
- **Monitoreo y observabilidad**: health checks, métricas, logs centralizados y scripts de diagnóstico NGROK.

## Arquitectura de alto nivel

```
Usuarios ──> Frontend Next.js (Landing + Dashboard)
                   │
                   ▼
          FastAPI Backend (API, Bot, ML, Servicios)
        /            |            \
PostgreSQL+TS   Redis Cache   RabbitMQ + Celery
        \            |            /
         ↘── Integraciones Binance P2P / TRM ──↙
```

## Stack tecnológico

### Frontend
- Next.js 14+ (App Router, TypeScript)
- TailwindCSS + shadcn/ui + Recharts
- React Query, WebSockets y servicios de caching

### Backend
- FastAPI (Python 3.11+), Pydantic y SQLAlchemy
- PostgreSQL + TimescaleDB para series temporales
- Redis para cache y locking
- RabbitMQ + Celery (worker + beat) para tareas asíncronas
- Binance Connector & servicios TRM (Colombia)

### ML / Análisis
- pandas, numpy, scikit-learn, TA-Lib
- Pipelines de entrenamiento programado y métricas de desempeño

## Requisitos del sistema

- Python 3.11+
- Node.js 18+
- Docker y Docker Compose
- 16 GB de RAM mínima recomendada
- Acceso a internet estable (para Binance/NGROK)

## Variables de entorno esenciales

Define un `.env` a partir de `.env.example`:

```bash
cp .env.example .env
```

Valores mínimos a completar:

```env
BINANCE_API_KEY=tu_api_key
BINANCE_API_SECRET=tu_api_secret
TRADING_MODE=manual           # manual | auto | hybrid
PROFIT_MARGIN_COP=2.5
PROFIT_MARGIN_VES=3.0
```

Consulta `.env.example` para conocer las claves adicionales (NGROK, Redis, DB, etc.).

## Inicio rápido

```bash
# 1. Variables de entorno
cp .env.example .env
# 2. Dependencias del frontend
make install
# 3. Levantar todo el stack (Docker)
make start
# 4. Verificar health del backend
make health
```

URLs por defecto:
- Landing Page: http://localhost:3000
- Dashboard: http://localhost:3000/dashboard
- API Docs (Swagger): http://localhost:8000/api/v1/docs

Para un repaso detallado consulta `docs/QUICKSTART.md` y `docs/QUICK_DEPLOY.md`.

## Desarrollo y comandos útiles

```bash
make start          # Inicia todos los servicios en Docker
make stop           # Detiene y libera contenedores
make restart        # Reinicia los servicios
make logs           # Logs combinados
make backend-logs   # Logs del backend FastAPI
make worker-logs    # Logs del worker Celery
make dev-frontend   # Frontend en modo desarrollo (npm run dev)
make clean          # Elimina contenedores/volúmenes (acción destructiva)
make health         # Verifica health del backend
```

NGROK y otras utilidades cuentan con scripts dedicados en `scripts/` y guías en `docs/NGROK_*.md`.

## Estructura del proyecto

```
ProyectoP2P/
├── backend/              # API FastAPI + bot + Celery
│   ├── app/
│   │   ├── api/         # Endpoints REST
│   │   ├── core/        # Configuración y DB
│   │   ├── models/      # Modelos SQLAlchemy
│   │   ├── services/    # Integraciones y lógica
│   │   ├── trading/     # Motor de trading P2P
│   │   └── ml/          # Pipelines de ML
│   ├── celery_app/      # Worker y tareas
│   └── tests/
├── frontend/            # App Next.js
│   ├── src/app/        # App Router + páginas
│   ├── src/components/ # UI reutilizable
│   └── src/lib/        # Cliente API y utils
├── docker/              # Dockerfiles y configs
├── docs/                # Guías operativas
├── scripts/             # NGROK y helpers
└── docker-compose.yml   # Orquestación local
```

## Documentación complementaria

La documentación está organizada en carpetas temáticas dentro de `docs/`:

### 📚 Documentación Organizada

- **`docs/README.md`**: Índice completo de toda la documentación
- **`docs/QUICKSTART.md`**: Guía paso a paso para comenzar
- **`docs/ml/`**: Documentación de Machine Learning y modelos
- **`docs/intel/`**: Documentación de Intel GPU y Extensiones
- **`docs/installation/`**: Guías de instalación y configuración
- **`docs/deployment/`**: Documentación de despliegue
- **`docs/troubleshooting/`**: Solución de problemas
- **`docs/api/`**: Documentación de API
- **`docs/features/`**: Características avanzadas
- **`docs/guides/`**: Guías detalladas

### 📖 Documentos Principales

- **`docs/QUICKSTART.md`**: Guía rápida para comenzar
- **`docs/PROYECTO_COMPLETO.md`**: Visión general del proyecto
- **`docs/ESTADO_REAL_SISTEMA.md`**: Estado actual del sistema
- **`docs/PENDING_FLOWS.md`**: Flujos pendientes de implementación
- **`docs/api/ROADMAP_INTEGRACION_API.md`**: Lista completa de endpoints
- **`docs/guides/FRONTEND_IMPROVEMENTS.md`**: Plan de UX/UI
- **`docs/troubleshooting/NGROK_TROUBLESHOOTING.md`**: Diagnósticos de NGROK
- **`docs/deployment/DEPLOYMENT_CHECKLIST.md`**: Checklist de despliegue

## Roadmap y flujos pendientes

Los componentes que aún requieren integración con datos reales o creación completa se documentan en `docs/PENDING_FLOWS.md`, incluyendo un diagrama de flujo Mermaid y las dependencias exactas por endpoint:

- Sincronización de inventario y control de trading (`InventoryManager`, `TradingControl`).
- Paneles avanzados (Spot, Market Making, Order Execution, Arbitrage).
- Métricas ML/riesgo, análisis de liquidez y monitoreo de salud.

Consulta el documento para priorizar tareas y verificar bloqueadores antes de desarrollar cada flujo.

## Seguridad

- ⚠️ **Nunca** publiques ni subas las claves de Binance, tokens NGROK o secretos.
- Mantén las variables sensibles fuera del repo (`.env`, gestores de secretos).
- Aplica rate limiting y validación estricta en todos los endpoints expuestos.
- Revisa y monitorea órdenes automáticas antes de operar con capital real.

## Licencia

Privado – Todos los derechos reservados.
