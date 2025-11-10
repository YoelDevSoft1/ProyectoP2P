# 🔧 Correcciones Aplicadas

## Problemas Resueltos

### 1. Error de Grafana: "Dashboard title cannot be empty"

**Problema:**
- Grafana no podía cargar el dashboard `p2p-exchange-overview.json`
- Error: "Dashboard title cannot be empty"

**Solución:**
- ✅ Actualizado el dashboard con el formato completo y válido
- ✅ Agregados campos requeridos: `time`, `timepicker`, `templating`, `annotations`, `links`
- ✅ Agregadas configuraciones de `xaxis` y `yaxes` para cada panel
- ✅ Agregado campo `datasource` en cada target
- ✅ Agregadas opciones de configuración para paneles tipo `stat`

**Archivo modificado:**
- `docker/grafana/dashboards/p2p-exchange-overview.json`

### 2. Error de Celery: "error parsing value for field BACKEND_CORS_ORIGINS"

**Problema:**
- Celery Worker y Celery Beat no podían iniciar
- Error: `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`
- Pydantic Settings intentaba parsear valores vacíos de `BACKEND_CORS_ORIGINS` como JSON

**Solución:**
- ✅ Cambiado `BACKEND_CORS_ORIGINS` de `List[str]` a `str` para evitar parsing automático de JSON
- ✅ Implementado validator que normaliza el valor a string ANTES de cualquier parsing
- ✅ Creada propiedad `cors_origins_list` que procesa el string y retorna una lista cuando se necesita
- ✅ Manejo robusto de valores vacíos, None, strings, listas y JSON
- ✅ Actualizado `main.py` para usar `settings.cors_origins_list` en lugar de `settings.BACKEND_CORS_ORIGINS`

**Archivos modificados:**
- `backend/app/core/config.py`
- `backend/app/main.py`

## Cambios Detallados

### Config.py

**Antes:**
```python
BACKEND_CORS_ORIGINS: List[str] = Field(
    default=["http://localhost:3000", "https://proyecto-p2p.vercel.app"]
)
```

**Después:**
```python
BACKEND_CORS_ORIGINS: str = Field(
    default="http://localhost:3000,https://proyecto-p2p.vercel.app"
)

@property
def cors_origins_list(self) -> List[str]:
    """Procesa BACKEND_CORS_ORIGINS y retorna lista"""
    # ... lógica de procesamiento
```

### Main.py

**Antes:**
```python
cors_origins = settings.BACKEND_CORS_ORIGINS
```

**Después:**
```python
cors_origins = settings.cors_origins_list
```

## Cómo Verificar

### 1. Verificar Grafana
```bash
# Reiniciar servicios
docker-compose restart grafana

# Ver logs
docker-compose logs grafana

# Debe mostrar:
# "Dashboard loaded successfully" o similar
# Sin errores de "Dashboard title cannot be empty"
```

### 2. Verificar Celery
```bash
# Reiniciar servicios
docker-compose restart celery_worker celery_beat

# Ver logs
docker-compose logs celery_worker
docker-compose logs celery_beat

# Debe mostrar:
# "celery@... ready" o similar
# Sin errores de "error parsing value for field BACKEND_CORS_ORIGINS"
```

## Configuración de .env

### Opciones válidas para BACKEND_CORS_ORIGINS:

1. **String separada por comas (recomendado):**
```env
BACKEND_CORS_ORIGINS=http://localhost:3000,https://proyecto-p2p.vercel.app
```

2. **JSON array:**
```env
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://proyecto-p2p.vercel.app"]
```

3. **Valor vacío (usa defaults):**
```env
BACKEND_CORS_ORIGINS=
```

4. **Wildcard (permite todos):**
```env
BACKEND_CORS_ORIGINS=*
```

## Notas Adicionales

- El validator ahora maneja correctamente valores vacíos, None, strings, listas y JSON
- Si el valor está vacío o es None, se usan los valores por defecto
- Si se detecta "*" o "ngrok" en los orígenes, se permite todos los orígenes ("*")
- El dashboard de Grafana ahora incluye todas las configuraciones necesarias para funcionar correctamente

## Próximos Pasos

1. ✅ Reiniciar los servicios afectados
2. ✅ Verificar que los logs no muestren errores
3. ✅ Verificar que Grafana cargue el dashboard correctamente
4. ✅ Verificar que Celery Worker y Beat inicien correctamente
5. ✅ Probar que CORS funcione correctamente en el frontend

## Si Persisten Problemas

### Grafana:
- Verificar que el archivo `p2p-exchange-overview.json` tenga formato JSON válido
- Verificar permisos del archivo en el contenedor
- Verificar que el datasource de Prometheus esté configurado correctamente

### Celery:
- Verificar que el archivo `.env` no tenga valores inválidos para `BACKEND_CORS_ORIGINS`
- Verificar que todas las variables de entorno requeridas estén configuradas
- Verificar que la conexión a RabbitMQ esté funcionando

