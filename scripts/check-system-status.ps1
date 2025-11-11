# Script PowerShell para verificar el estado del sistema

Write-Host "🔍 Verificando estado del sistema..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Función para verificar servicio
function Test-Service {
    param (
        [string]$ServiceName,
        [string]$Url
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "✅ $ServiceName`: OK" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ $ServiceName`: ERROR" -ForegroundColor Red
        return $false
    }
}

# Verificar servicios Docker
Write-Host "📦 Verificando servicios Docker..." -ForegroundColor Yellow
docker-compose ps
Write-Host ""

# Verificar Backend
Write-Host "🔧 Verificando Backend..." -ForegroundColor Yellow
if (Test-Service "Backend Health" "http://localhost:8000/api/v1/health") {
    Write-Host "   Health check exitoso" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Backend no responde" -ForegroundColor Yellow
}
Write-Host ""

# Verificar Base de Datos
Write-Host "🗄️  Verificando Base de Datos..." -ForegroundColor Yellow
try {
    $dbCheck = docker exec p2p_postgres pg_isready -U p2p_user -d p2p_db 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PostgreSQL: OK" -ForegroundColor Green
    } else {
        Write-Host "❌ PostgreSQL: ERROR" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ PostgreSQL: ERROR" -ForegroundColor Red
}
Write-Host ""

# Verificar Redis
Write-Host "💾 Verificando Redis..." -ForegroundColor Yellow
try {
    $redisCheck = docker exec p2p_redis redis-cli ping 2>&1
    if ($redisCheck -match "PONG") {
        Write-Host "✅ Redis: OK" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis: ERROR" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Redis: ERROR" -ForegroundColor Red
}
Write-Host ""

# Verificar RabbitMQ
Write-Host "🐰 Verificando RabbitMQ..." -ForegroundColor Yellow
if (Test-Service "RabbitMQ Management" "http://localhost:15672") {
    Write-Host "   Management UI disponible" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  RabbitMQ Management UI no responde" -ForegroundColor Yellow
}
Write-Host ""

# Verificar Frontend
Write-Host "🌐 Verificando Frontend..." -ForegroundColor Yellow
if (Test-Service "Frontend" "http://localhost:3000") {
    Write-Host "   Frontend disponible" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Frontend no responde" -ForegroundColor Yellow
}
Write-Host ""

# Verificar Endpoints Críticos
Write-Host "🔌 Verificando Endpoints Críticos..." -ForegroundColor Yellow
Test-Service "Precios P2P" "http://localhost:8000/api/v1/prices/current"
Test-Service "Métricas" "http://localhost:8000/api/v1/metrics"
Test-Service "Configuración" "http://localhost:8000/api/v1/config"
Write-Host ""

# Verificar Variables de Entorno
Write-Host "🔐 Verificando Variables de Entorno..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ Archivo .env existe" -ForegroundColor Green
    
    # Verificar variables críticas
    $requiredVars = @("DATABASE_URL", "REDIS_URL", "RABBITMQ_URL", "SECRET_KEY", "BINANCE_API_KEY", "BINANCE_API_SECRET")
    foreach ($var in $requiredVars) {
        $line = Get-Content .env | Select-String "^${var}="
        if ($line -and $line -notmatch "^\s*$" -and $line -notmatch "^\s*#") {
            $value = $line -replace "^${var}=", ""
            if ($value -and $value.Trim() -ne "") {
                Write-Host "✅ $var`: Configurado" -ForegroundColor Green
            } else {
                Write-Host "❌ $var`: NO configurado" -ForegroundColor Red
            }
        } else {
            Write-Host "❌ $var`: NO configurado" -ForegroundColor Red
        }
    }
} else {
    Write-Host "❌ Archivo .env no existe" -ForegroundColor Red
}
Write-Host ""

# Verificar Iconos PNG
Write-Host "🖼️  Verificando Iconos PNG..." -ForegroundColor Yellow
if ((Test-Path "frontend/public/icon-192.png") -and (Test-Path "frontend/public/icon-512.png")) {
    Write-Host "✅ Iconos PNG: Existen" -ForegroundColor Green
} else {
    Write-Host "⚠️  Iconos PNG: Faltan (ejecutar generate-png-from-svg.html)" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Verificación completada" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Para más detalles, revisa:" -ForegroundColor Cyan
Write-Host "   - docs/CHECKLIST_FUNCIONAMIENTO_COMPLETO.md" -ForegroundColor Cyan
Write-Host "   - Logs: docker-compose logs -f [service]" -ForegroundColor Cyan

