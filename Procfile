# Procfile para Railway/Heroku
# Define los diferentes procesos que se ejecutarán

# Proceso web (API FastAPI)
web: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT

# Worker de Celery (ejecutar tareas asíncronas)
worker: cd backend && celery -A celery_app.worker worker --loglevel=info --concurrency=2

# Beat de Celery (programador de tareas)
beat: cd backend && celery -A celery_app.worker beat --loglevel=info
