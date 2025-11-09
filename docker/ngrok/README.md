# Configuración de ngrok

Este directorio contiene la configuración de ngrok para exponer el backend públicamente.

## Configuración Requerida

### 1. Obtener Authtoken de ngrok

1. Crear una cuenta en [ngrok](https://dashboard.ngrok.com/signup)
2. Obtener tu authtoken desde [dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)
3. Agregar el authtoken al archivo `.env`:

```env
NGROK_AUTHTOKEN=tu_authtoken_aqui
```

### 2. Verificar que el archivo de configuración existe

El archivo `ngrok.yml` debe existir en este directorio con el siguiente contenido:

```yaml
version: "2"
tunnels:
  backend:
    addr: backend:8000
    proto: http
    schemes:
      - https
      - http
    inspect: true
    bind_tls: true

web_addr: 0.0.0.0:4040
log_level: info
log_format: logfmt
log: stdout
```

## Uso

Una vez configurado, ngrok se iniciará automáticamente con Docker Compose:

```bash
docker-compose up -d ngrok
```

## Verificar que funciona

1. **Interfaz web de ngrok**: http://localhost:4040
2. **Ver túneles activos**: http://localhost:4040/api/tunnels
3. **URL pública**: Se mostrará en los logs de ngrok o en la interfaz web

## Ejemplo de respuesta de la API de ngrok

```json
{
  "tunnels": [
    {
      "name": "backend",
      "uri": "/api/tunnels/backend",
      "public_url": "https://xxxx-xxxx-xxxx.ngrok-free.app",
      "proto": "https",
      "config": {
        "addr": "backend:8000",
        "inspect": true
      },
      "metrics": {
        "conns": {
          "count": 0,
          "gauge": 0,
          "rate1": 0,
          "rate5": 0,
          "rate15": 0,
          "p50": 0,
          "p90": 0,
          "p95": 0,
          "p99": 0
        }
      }
    }
  ]
}
```

## Troubleshooting

### Error: "Error reading configuration file"
- Verifica que el archivo `ngrok.yml` existe y no es un directorio
- Verifica que el archivo tiene el formato YAML correcto
- Verifica los permisos del archivo

### Error: "authtoken not found"
- Verifica que `NGROK_AUTHTOKEN` está configurado en `.env`
- Verifica que el authtoken es válido en [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)

### Error: "Cannot connect to backend:8000"
- Verifica que el servicio `backend` está corriendo
- Verifica que el backend está en la misma red Docker (`p2p_network`)
- Verifica que el backend está escuchando en el puerto 8000

### ngrok no expone el servicio
- Verifica los logs: `docker-compose logs ngrok`
- Verifica la interfaz web: http://localhost:4040
- Verifica que el authtoken es válido

## Notas

- **Free Tier**: ngrok free tier tiene limitaciones (40 requests/minuto, URL cambia en cada reinicio)
- **Headers**: Se agrega el header `ngrok-skip-browser-warning:true` para saltar la página de advertencia
- **HTTPS**: ngrok proporciona HTTPS automáticamente
- **Inspect**: La inspección está habilitada para ver requests en la interfaz web

