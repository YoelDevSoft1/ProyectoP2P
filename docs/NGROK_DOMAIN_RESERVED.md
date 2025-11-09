# Solución para Dominio Reservado de ngrok

## Problema

Tienes un dominio reservado `denver-unbrooded-miley.ngrok-free.dev` que está actualmente activo en otra instancia de ngrok, causando el error `ERR_NGROK_334`.

## Soluciones

### Solución 1: Detener el túnel activo desde el Dashboard (Recomendado)

1. **Ve al Dashboard de ngrok:**
   - https://dashboard.ngrok.com/cloud-edge/tunnels

2. **Busca el túnel activo:**
   - Busca el túnel que está usando `denver-unbrooded-miley.ngrok-free.dev`
   - Verás que tiene "1 punto final" activo

3. **Detén el túnel:**
   - Haz clic en el túnel
   - Haz clic en "Stop" o "Detener"
   - O simplemente cierra la instancia de ngrok que lo está usando

4. **Reinicia el contenedor:**
   ```powershell
   docker-compose restart ngrok
   ```

### Solución 2: Usar el Script Automático

Ejecuta el script que detiene todas las instancias y reinicia ngrok:

```powershell
.\scripts\fix-ngrok-domain-conflict.ps1
```

Este script:
- Detiene todas las instancias de ngrok
- Espera a que los túneles se cierren
- Te permite verificar el dashboard
- Reinicia ngrok limpio

### Solución 3: Usar un Dominio Nuevo (Temporal)

Si no puedes detener el túnel activo, puedes configurar ngrok para que use un dominio nuevo cada vez:

1. **No especifiques el dominio** en la configuración (ya está así)
2. **Ngrok generará un dominio nuevo** automáticamente cada vez que inicies

Esto es útil para desarrollo, pero la URL cambiará cada vez que reinicies ngrok.

### Solución 4: Configurar el Dominio Reservado (Si lo necesitas)

Si quieres usar específicamente el dominio `denver-unbrooded-miley.ngrok-free.dev`:

1. **Detén el túnel activo** desde el dashboard
2. **Descomenta la línea** en `docker/ngrok/ngrok.yml`:
   ```yaml
   tunnels:
     backend:
       addr: backend:8000
       proto: http
       inspect: true
       domain: "denver-unbrooded-miley.ngrok-free.dev"
   ```
3. **Reinicia ngrok:**
   ```powershell
   docker-compose restart ngrok
   ```

**Nota**: En ngrok free tier, solo puedes usar un dominio reservado a la vez, y solo puede estar activo en una instancia.

## Verificar que Funciona

Después de aplicar la solución:

1. **Ver logs:**
   ```powershell
   docker-compose logs -f ngrok
   ```

2. **Verificar estado:**
   ```powershell
   curl http://localhost:4040/api/tunnels
   ```

3. **Ver interfaz web:**
   - http://localhost:4040

Deberías ver:
```
Session Status                online
Forwarding                    https://xxxx.ngrok-free.app -> http://backend:8000
```

## Prevención

Para evitar este problema:

1. **Siempre detén ngrok correctamente:**
   ```powershell
   docker-compose stop ngrok
   ```

2. **Verifica antes de iniciar:**
   - Revisa el dashboard: https://dashboard.ngrok.com/cloud-edge/tunnels
   - Detén cualquier túnel activo antes de iniciar uno nuevo

3. **Usa los scripts proporcionados:**
   - `scripts/stop-all-ngrok.ps1` - Detiene todas las instancias
   - `scripts/ngrok-clean-restart.ps1` - Limpia y reinicia
   - `scripts/fix-ngrok-domain-conflict.ps1` - Soluciona conflictos

## Referencias

- [ngrok Dashboard](https://dashboard.ngrok.com/cloud-edge/tunnels)
- [ngrok Error 334](https://ngrok.com/docs/errors/err_ngrok_334)
- [ngrok Domains](https://ngrok.com/docs/cloud-edge/modules/domains/)

