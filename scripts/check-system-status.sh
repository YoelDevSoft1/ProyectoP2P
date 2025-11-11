#!/bin/bash
# Script para verificar el estado del sistema

echo "🔍 Verificando estado del sistema..."
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar servicio
check_service() {
    local service_name=$1
    local url=$2
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} $service_name: OK"
        return 0
    else
        echo -e "${RED}❌${NC} $service_name: ERROR"
        return 1
    fi
}

# Verificar servicios Docker
echo "📦 Verificando servicios Docker..."
docker-compose ps --format "table {{.Name}}\t{{.Status}}"
echo ""

# Verificar Backend
echo "🔧 Verificando Backend..."
if check_service "Backend Health" "http://localhost:8000/api/v1/health"; then
    echo "   Health check exitoso"
else
    echo "   ⚠️  Backend no responde"
fi
echo ""

# Verificar Base de Datos
echo "🗄️  Verificando Base de Datos..."
if docker exec p2p_postgres pg_isready -U p2p_user -d p2p_db > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} PostgreSQL: OK"
else
    echo -e "${RED}❌${NC} PostgreSQL: ERROR"
fi
echo ""

# Verificar Redis
echo "💾 Verificando Redis..."
if docker exec p2p_redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Redis: OK"
else
    echo -e "${RED}❌${NC} Redis: ERROR"
fi
echo ""

# Verificar RabbitMQ
echo "🐰 Verificando RabbitMQ..."
if check_service "RabbitMQ Management" "http://localhost:15672"; then
    echo "   Management UI disponible"
else
    echo "   ⚠️  RabbitMQ Management UI no responde"
fi
echo ""

# Verificar Frontend
echo "🌐 Verificando Frontend..."
if check_service "Frontend" "http://localhost:3000"; then
    echo "   Frontend disponible"
else
    echo "   ⚠️  Frontend no responde"
fi
echo ""

# Verificar Endpoints Críticos
echo "🔌 Verificando Endpoints Críticos..."
check_service "Precios P2P" "http://localhost:8000/api/v1/prices/current"
check_service "Métricas" "http://localhost:8000/api/v1/metrics"
check_service "Configuración" "http://localhost:8000/api/v1/config"
echo ""

# Verificar Variables de Entorno
echo "🔐 Verificando Variables de Entorno..."
if [ -f .env ]; then
    echo -e "${GREEN}✅${NC} Archivo .env existe"
    
    # Verificar variables críticas
    required_vars=("DATABASE_URL" "REDIS_URL" "RABBITMQ_URL" "SECRET_KEY" "BINANCE_API_KEY" "BINANCE_API_SECRET")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env && ! grep -q "^${var}=$" .env && ! grep -q "^${var}=\s*$" .env; then
            echo -e "${GREEN}✅${NC} $var: Configurado"
        else
            echo -e "${RED}❌${NC} $var: NO configurado"
        fi
    done
else
    echo -e "${RED}❌${NC} Archivo .env no existe"
fi
echo ""

# Verificar Tablas de Base de Datos
echo "📊 Verificando Tablas de Base de Datos..."
tables=("users" "trades" "price_history" "alerts" "app_config")
for table in "${tables[@]}"; do
    if docker exec p2p_postgres psql -U p2p_user -d p2p_db -c "\d $table" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} Tabla $table: Existe"
    else
        echo -e "${RED}❌${NC} Tabla $table: NO existe"
    fi
done
echo ""

# Verificar Iconos PNG
echo "🖼️  Verificando Iconos PNG..."
if [ -f "frontend/public/icon-192.png" ] && [ -f "frontend/public/icon-512.png" ]; then
    echo -e "${GREEN}✅${NC} Iconos PNG: Existen"
else
    echo -e "${YELLOW}⚠️${NC}  Iconos PNG: Faltan (ejecutar generate-png-from-svg.html)"
fi
echo ""

echo "=========================================="
echo "✅ Verificación completada"
echo ""
echo "📝 Para más detalles, revisa:"
echo "   - docs/CHECKLIST_FUNCIONAMIENTO_COMPLETO.md"
echo "   - Logs: docker-compose logs -f [service]"

