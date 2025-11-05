#!/bin/bash

# ============================================
# Script de Deployment Rápido a Railway
# ============================================

set -e  # Exit on error

echo "🚀 Iniciando deployment a Railway..."
echo ""

# Colors
GREEN='\033[0.32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}⚠️  Railway CLI no encontrado. Instalando...${NC}"
    npm install -g @railway/cli
fi

# Login to Railway
echo -e "${GREEN}📝 Iniciando sesión en Railway...${NC}"
railway login

# Link project or create new
echo ""
echo -e "${GREEN}🔗 ¿Quieres linkear a un proyecto existente o crear uno nuevo?${NC}"
echo "1) Linkear a proyecto existente"
echo "2) Crear nuevo proyecto"
read -p "Selecciona opción (1 o 2): " option

if [ "$option" == "1" ]; then
    railway link
else
    railway init
fi

# Create services
echo ""
echo -e "${GREEN}🏗️  Creando servicios...${NC}"

# Backend API
echo -e "${YELLOW}Creando servicio: backend-api${NC}"
railway service create backend-api

# Celery Worker
echo -e "${YELLOW}Creando servicio: celery-worker${NC}"
railway service create celery-worker

# Celery Beat
echo -e "${YELLOW}Creando servicio: celery-beat${NC}"
railway service create celery-beat

# Add PostgreSQL
echo ""
echo -e "${GREEN}💾 ¿Quieres agregar PostgreSQL de Railway?${NC}"
read -p "(y/n): " add_postgres

if [ "$add_postgres" == "y" ]; then
    railway add --plugin postgresql
    echo -e "${GREEN}✅ PostgreSQL agregado${NC}"
fi

# Add Redis
echo ""
echo -e "${GREEN}🔴 ¿Quieres agregar Redis de Railway?${NC}"
read -p "(y/n): " add_redis

if [ "$add_redis" == "y" ]; then
    railway add --plugin redis
    echo -e "${GREEN}✅ Redis agregado${NC}"
fi

# Set environment variables
echo ""
echo -e "${GREEN}🔐 Configurando variables de entorno...${NC}"

# Generate SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)

# Set variables for backend-api
railway service select backend-api
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=INFO
railway variables set SECRET_KEY=$SECRET_KEY
railway variables set TRADING_MODE=manual
railway variables set BINANCE_TESTNET=false

echo -e "${GREEN}✅ Variables básicas configuradas${NC}"

# Deploy
echo ""
echo -e "${GREEN}🚀 ¿Desplegar ahora?${NC}"
read -p "(y/n): " deploy_now

if [ "$deploy_now" == "y" ]; then
    echo -e "${GREEN}📦 Desplegando backend-api...${NC}"
    railway service select backend-api
    railway up -d

    echo ""
    echo -e "${GREEN}📦 Desplegando celery-worker...${NC}"
    railway service select celery-worker
    railway up -d

    echo ""
    echo -e "${GREEN}📦 Desplegando celery-beat...${NC}"
    railway service select celery-beat
    railway up -d

    echo ""
    echo -e "${GREEN}✅ Deployment completado!${NC}"
    echo ""
    echo -e "${YELLOW}🔗 Obteniendo URL del backend...${NC}"
    railway service select backend-api
    railway domain
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Setup completado!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}📝 Próximos pasos:${NC}"
echo "1. Configura las variables de entorno faltantes en Railway Dashboard"
echo "2. Agrega tu Binance API key y secret"
echo "3. Configura las URLs de bases de datos externas (Neon, Upstash, CloudAMQP)"
echo "4. Actualiza BACKEND_CORS_ORIGINS con tu URL de Vercel"
echo "5. Ejecuta migraciones de base de datos"
echo ""
echo -e "${YELLOW}🌐 Railway Dashboard:${NC} https://railway.app/project"
echo -e "${YELLOW}📚 Documentación completa:${NC} docs/DEPLOYMENT_PRODUCTION.md"
echo ""
