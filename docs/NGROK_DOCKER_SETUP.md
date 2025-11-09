# Configuración de ngrok en Docker

Esta guía explica cómo configurar ngrok para exponer el backend públicamente usando Docker.

## Prerequisitos

1. **Cuenta de ngrok**: Crea una cuenta gratuita en [ngrok](https://dashboard.ngrok.com/signup)
2. **Authtoken**: Obtén tu authtoken desde [dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)

## Configuración

### 1. Agregar Authtoken al archivo .env

Agrega tu authtoken de ngrok al archivo `.env` en la raíz del proyecto:

```env
NGROK_AUTHTOKEN=tu_authtoken_aqui_2abc123def456ghi789
```

**⚠️ IMPORTANTE**: Nunca commits el archivo `.env` al repositorio. El authtoken es sensible.

### 2. Verificar que el archivo de configuración existe

El archivo `docker/ngrok/ngrok.yml` debe existir con la siguiente estructura:

```yaml
version: "2"
authtoken: ${NGROK_AUTHTOKEN}

tunnels:
  backend:
    addr: backend:8000
    proto: http
    schemes:
      - https
      - http
    inspect: true
    bind_tls: true
    request_header:
      add:
        - "ngrok-skip-browser-warning:true"

web_addr: 0.0.0.0:4040
log_level: info
log_format: logfmt
log: stdout
```

### 3. Iniciar el contenedor de ngrok

```bash
docker-compose up -d ngrok
```

O iniciar todos los servicios:

```bash
docker-compose up -d
```

## Verificar que funciona

### 1. Ver logs de ngrok

```bash
docker-compose logs -f ngrok
```

Deberías ver algo como:

```
Configurando authtoken de ngrok...
Authtoken configurado correctamente
Iniciando ngrok...
ngrok

Session Status                online
Account                       Tu Cuenta (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Forwarding                    https://xxxx-xxxx-xxxx.ngrok-free.app -> http://backend:8000
```

### 2. Interfaz web de ngrok

Abre tu navegador y ve a: **http://localhost:4040**

Aquí puedes ver:
- Todas las requests que llegan
- Response status codes
- Request/response bodies
- Tiempos de respuesta
- URL pública del túnel

### 3. Obtener la URL pública

Puedes obtener la URL pública del túnel de dos formas:

#### Opción 1: Interfaz web
Ve a http://localhost:4040 y verás la URL pública en la página principal.

#### Opción 2: API de ngrok
```bash
curl http://localhost:4040/api/tunnels
```

Esto retornará un JSON con la información del túnel:

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
      }
    }
  ]
}
```

### 4. Probar el backend públicamente

Una vez que tengas la URL pública (por ejemplo: `https://xxxx-xxxx-xxxx.ngrok-free.app`), puedes probar el backend:

```bash
curl https://xxxx-xxxx-xxxx.ngrok-free.app/api/v1/health
```

Deberías obtener una respuesta JSON con el estado del backend.

## Configuración del Frontend

Si quieres que tu frontend use la URL de ngrok, actualiza la variable de entorno:

```env
NEXT_PUBLIC_API_URL=https://xxxx-xxxx-xxxx.ngrok-free.app
```

**Nota**: En ngrok free tier, la URL cambia cada vez que reinicias ngrok. Para una URL fija, necesitas ngrok Pro ($8/mes).

## Troubleshooting

### Error: "NGROK_AUTHTOKEN no está configurado"

**Solución**: 
1. Verifica que el archivo `.env` existe en la raíz del proyecto
2. Verifica que `NGROK_AUTHTOKEN` está configurado en el archivo `.env`
3. Verifica que el authtoken es válido

### Error: "Error reading configuration file '/etc/ngrok/ngrok.yml': is a directory"

**Solución**:
1. Elimina el directorio si existe: `rm -rf docker/ngrok/ngrok.yml`
2. Crea el archivo de configuración correctamente
3. Reinicia el contenedor: `docker-compose restart ngrok`

### Error: "Cannot connect to backend:8000"

**Solución**:
1. Verifica que el servicio `backend` está corriendo: `docker-compose ps backend`
2. Verifica que el backend está en la misma red Docker (`p2p_network`)
3. Verifica que el backend está escuchando en el puerto 8000
4. Revisa los logs del backend: `docker-compose logs backend`

### ngrok no expone el servicio

**Solución**:
1. Verifica los logs: `docker-compose logs ngrok`
2. Verifica la interfaz web: http://localhost:4040
3. Verifica que el authtoken es válido
4. Verifica que el archivo de configuración es válido YAML

### La URL de ngrok cambia cada vez

**Causa**: Esto es normal en ngrok free tier.

**Solución**: 
- Para desarrollo: Actualiza la variable `NEXT_PUBLIC_API_URL` cada vez que reinicies ngrok
- Para producción: Considera usar ngrok Pro ($8/mes) para una URL fija, o usar otro servicio como Cloudflare Tunnel

## Características de ngrok Free Tier

- ✅ **HTTPS incluido**: Automáticamente
- ✅ **40 requests/minuto**: Límite de rate
- ⚠️ **URL cambia**: Cada vez que reinicias ngrok
- ⚠️ **Sesión máxima**: 2 horas (después reconecta automáticamente)
- ⚠️ **Página de advertencia**: ngrok free tier muestra una página de advertencia (se puede saltar con el header `ngrok-skip-browser-warning:true`)

## Mejores Prácticas

1. **Seguridad**: Nunca commits el authtoken al repositorio
2. **Monitoreo**: Usa la interfaz web de ngrok (http://localhost:4040) para monitorear requests
3. **Logs**: Revisa los logs regularmente para detectar problemas
4. **Backup**: Guarda tu authtoken en un gestor de contraseñas seguro
5. **Producción**: Para producción, considera usar ngrok Pro o otro servicio de tunneling más estable

## Alternativas a ngrok

Si ngrok no es adecuado para tus necesidades, considera:

- **Cloudflare Tunnel**: Gratuito, URL fija, sin límites de rate
- **Tailscale**: VPN privada, ideal para desarrollo
- **LocalTunnel**: Alternativa gratuita a ngrok
- **Serveo**: Túnel SSH gratuito
- **Bore**: Túnel simple y gratuito

## Referencias

- [Documentación de ngrok](https://ngrok.com/docs)
- [Dashboard de ngrok](https://dashboard.ngrok.com)
- [Configuración de ngrok](https://ngrok.com/docs/ngrok-agent/config)

