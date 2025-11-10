# Solución de Problemas con ngrok

## Error ERR_NGROK_334: Endpoint ya está en línea

### Problema
```
ERROR: failed to start tunnel: The endpoint 'https://denver-unbrooded-miley.ngrok-free.dev' is already online.
ERR_NGROK_334
```

### Causa
Hay otra instancia de ngrok corriendo (desde terminal local, otro contenedor, sesión previa, o el dominio está reservado y en uso) que está usando el mismo dominio.

**Nota**: Si tienes un dominio reservado en ngrok (como `denver-unbrooded-miley.ngrok-free.dev`), solo puede estar activo en una instancia a la vez.

### Soluciones

#### Solución 1: Detener todas las instancias de ngrok (Recomendado)

**Usando el script proporcionado:**
```powershell
# Detener todas las instancias de ngrok
.\scripts\stop-all-ngrok.ps1

# Limpiar y reiniciar ngrok
.\scripts\ngrok-clean-restart.ps1
```

**Manual - Windows:**
```powershell
# Ver procesos de ngrok
Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"}

# Detener todos los procesos de ngrok
Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"} | Stop-Process -Force

# Detener contenedor Docker
docker-compose stop ngrok
```

**Linux/Mac:**
```bash
# Ver procesos de ngrok
ps aux | grep ngrok

# Detener todos los procesos de ngrok
pkill ngrok
```

**Desde Docker:**
```bash
# Ver contenedores de ngrok
docker ps | grep ngrok

# Detener contenedores de ngrok
docker stop $(docker ps -q --filter "name=ngrok")
```

#### Solución 2: Usar un dominio diferente

Si necesitas múltiples instancias, puedes usar dominios diferentes. Sin embargo, en ngrok free tier, solo puedes usar un dominio a la vez.

#### Solución 3: Habilitar Pooling (Solo para ngrok Pro/Enterprise)

Si tienes ngrok Pro, puedes habilitar pooling para que múltiples instancias compartan el mismo dominio:

```yaml
tunnels:
  backend:
    addr: backend:8000
    proto: http
    inspect: true
    # Solo disponible en ngrok Pro
    # pooling_enabled: true
```

#### Solución 4: Usar un dominio único cada vez

Para desarrollo, ngrok free tier genera un dominio único cada vez que inicias una nueva sesión. Si necesitas que cambie cada vez:

1. Detén todas las instancias de ngrok
2. Reinicia el contenedor:
   ```bash
   docker-compose restart ngrok
   ```

### Verificar instancias activas

**Verificar desde ngrok dashboard:**
1. Ve a https://dashboard.ngrok.com/cloud-edge/tunnels
2. Verifica si hay túneles activos
3. Detén los túneles que no necesites
4. Si tienes un dominio reservado, verifica que no esté en uso en otra sesión

**Verificar desde la línea de comandos:**
```powershell
# Ver contenedores de ngrok
docker ps | grep ngrok

# Ver procesos de ngrok
Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"}

# Ver túneles activos (si ngrok está corriendo)
curl http://localhost:4040/api/tunnels
```

**Verificar desde la API local:**
```bash
# Si tienes ngrok corriendo localmente
curl http://localhost:4040/api/tunnels
```

### Prevención

Para evitar este problema en el futuro:

1. **Detén ngrok correctamente**: Usa `Ctrl+C` o `docker-compose stop ngrok`
2. **Verifica antes de iniciar**: Asegúrate de que no hay otras instancias corriendo
3. **Usa scripts**: Usa los scripts proporcionados (`scripts/start-ngrok.ps1`) que verifican el estado

## Otros Errores Comunes

### Error: NGROK_AUTHTOKEN no configurado

**Solución:**
1. Verifica que el archivo `.env` existe
2. Verifica que `NGROK_AUTHTOKEN` está en el archivo `.env`
3. Reinicia el contenedor: `docker-compose restart ngrok`

### Error: Cannot connect to backend:8000

**Solución:**
1. Verifica que el backend está corriendo: `docker-compose ps backend`
2. Verifica que el backend está en la misma red: `docker network inspect p2p_network`
3. Verifica que el backend está escuchando en el puerto 8000

### Error: YAML parsing error

**Solución:**
1. Verifica que el archivo `docker/ngrok/ngrok.yml` tiene el formato correcto
2. Verifica que no hay caracteres especiales
3. Usa un validador YAML online para verificar la sintaxis

## Comandos Útiles

### Ver logs de ngrok
```bash
docker-compose logs -f ngrok
```

### Reiniciar ngrok
```bash
docker-compose restart ngrok
```

### Detener ngrok
```bash
docker-compose stop ngrok
```

### Ver estado de ngrok
```bash
docker-compose ps ngrok
```

### Obtener URL pública
```bash
curl http://localhost:4040/api/tunnels | jq
```

### Limpiar contenedores de ngrok
```bash
docker-compose down ngrok
docker-compose up -d ngrok
```

## Referencias

- [ngrok Error 334](https://ngrok.com/docs/errors/err_ngrok_334)
- [ngrok Documentation](https://ngrok.com/docs)
- [ngrok Dashboard](https://dashboard.ngrok.com)

