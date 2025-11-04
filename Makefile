# Makefile para Casa de Cambio P2P

.PHONY: help install start stop restart logs clean test

help:
	@echo "Comandos disponibles:"
	@echo "  make install   - Instalar dependencias"
	@echo "  make start     - Iniciar todos los servicios"
	@echo "  make stop      - Detener todos los servicios"
	@echo "  make restart   - Reiniciar todos los servicios"
	@echo "  make logs      - Ver logs de todos los servicios"
	@echo "  make clean     - Limpiar contenedores y volúmenes"
	@echo "  make test      - Ejecutar tests"
	@echo "  make backend-logs - Ver logs del backend"
	@echo "  make worker-logs  - Ver logs del celery worker"

install:
	@echo "Instalando dependencias del frontend..."
	cd frontend && npm install
	@echo "Creando archivo .env desde .env.example..."
	@if not exist .env copy .env.example .env
	@echo "¡Listo! Ahora configura tu archivo .env"

start:
	@echo "Iniciando servicios con Docker..."
	docker-compose up -d
	@echo "Servicios iniciados. Verifica el estado con: make logs"

stop:
	@echo "Deteniendo servicios..."
	docker-compose down

restart:
	@echo "Reiniciando servicios..."
	docker-compose restart

logs:
	docker-compose logs -f

backend-logs:
	docker-compose logs -f backend

worker-logs:
	docker-compose logs -f celery_worker

clean:
	@echo "ADVERTENCIA: Esto eliminará todos los contenedores y volúmenes"
	@echo "Presiona Ctrl+C para cancelar o Enter para continuar..."
	@pause
	docker-compose down -v
	@echo "Limpieza completada"

test:
	@echo "Ejecutando tests del backend..."
	cd backend && python -m pytest

dev-frontend:
	@echo "Iniciando frontend en modo desarrollo..."
	cd frontend && npm run dev

build:
	@echo "Construyendo imágenes de Docker..."
	docker-compose build

status:
	@echo "Estado de los servicios:"
	docker-compose ps

health:
	@echo "Verificando health del backend..."
	curl http://localhost:8000/api/v1/health

setup: install
	@echo "Configuración inicial completada"
	@echo "Siguiente paso: Edita el archivo .env con tus credenciales"
	@echo "Luego ejecuta: make start"
