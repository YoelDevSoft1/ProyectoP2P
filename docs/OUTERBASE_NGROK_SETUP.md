# 🔧 Configurar ngrok para Outerbase - PostgreSQL

## 📋 Problema

Outerbase está en la nube, pero tu PostgreSQL está en `localhost`. Necesitas exponer PostgreSQL para que Outerbase pueda conectarse.

## 🚀 Solución: Usar ngrok

### Opción 1: Agregar PostgreSQL a ngrok.yml (Recomendado)

#### Paso 1: Verificar ngrok.yml

```bash
cat docker/ngrok/ngrok.yml
```

#### Paso 2: Agregar Túnel para PostgreSQL

Agregar a `docker/ngrok/ngrok.yml`:

```yaml
version: "3"
tunnels:
  backend:
    addr: backend:8000
    proto: http
    # hostname: denver-unbrooded-miley.ngrok-free.dev  # Opcional: dominio reservado
  
  postgres:
    addr: postgres:5432
    proto: tcp
```

**⚠️ NOTA**: ngrok free tier tiene límites en conexiones TCP. Para producción, considera usar SSH tunneling.

#### Paso 3: Reiniciar ngrok

```bash
docker-compose restart ngrok
```

#### Paso 4: Obtener URL de PostgreSQL

```bash
# Ver logs de ngrok
docker-compose logs ngrok

# O visitar: http://localhost:4040
# Ver la URL TCP asignada
```

**Ejemplo de URL**: `tcp://0.tcp.ngrok.io:12345`

#### Paso 5: Configurar en Outerbase

1. **Nueva Conexión** en Outerbase
2. **Configuración**:
   - **Host**: `0.tcp.ngrok.io` (sin el prefijo `tcp://`)
   - **Port**: `12345` (el puerto que ngrok asigne)
   - **Database**: `p2p_db`
   - **Username**: `p2p_user`
   - **Password**: `p2p_password_change_me`

3. **Test Connection**
4. **Save**

### Opción 2: Usar ngrok CLI (Alternativa)

#### Paso 1: Instalar ngrok CLI

```bash
# Windows: Descargar de https://ngrok.com/download
# O usar chocolatey: choco install ngrok
```

#### Paso 2: Autenticar

```bash
ngrok config add-authtoken TU_AUTHTOKEN
```

#### Paso 3: Exponer PostgreSQL

```bash
ngrok tcp 5432
```

#### Paso 4: Obtener URL

ngrok mostrará algo como:
```
Forwarding  tcp://0.tcp.ngrok.io:12345 -> localhost:5432
```

#### Paso 5: Configurar en Outerbase

Usar la URL de ngrok como host y port en Outerbase.

---

## 🔒 Opción Más Segura: SSH Tunneling

### Configurar SSH Tunneling en Outerbase

1. **Tener servidor SSH** (puede ser tu máquina local con SSH)
2. **En Outerbase**:
   - Habilitar "Use SSH Tunnel"
   - **SSH Host**: Tu servidor SSH
   - **SSH Port**: 22
   - **SSH User**: Tu usuario
   - **SSH Key**: Tu clave SSH privada
   - **Database Host**: `localhost` (desde el servidor SSH)
   - **Database Port**: `5432`

---

## ⚠️ Consideraciones de Seguridad

### ngrok TCP (Opción 1)

- ⚠️ **Público**: Cualquiera con la URL puede conectarse
- ⚠️ **Sin autenticación**: Solo protección por URL aleatoria
- ✅ **Rápido**: Fácil de configurar
- ⚠️ **Límites**: ngrok free tier tiene límites

### SSH Tunneling (Opción 2)

- ✅ **Seguro**: Conexión encriptada
- ✅ **Autenticación**: Requiere clave SSH
- ✅ **Privado**: Solo tú puedes conectarte
- ⚠️ **Configuración**: Más complejo de configurar

### Recomendación

- **Desarrollo**: Usar ngrok TCP (rápido y fácil)
- **Producción**: Usar SSH Tunneling (más seguro)

---

## 🔧 Configuración Completa

### docker/ngrok/ngrok.yml

```yaml
version: "3"
tunnels:
  backend:
    addr: backend:8000
    proto: http
    # hostname: denver-unbrooded-miley.ngrok-free.dev
  
  postgres:
    addr: postgres:5432
    proto: tcp
```

### Reiniciar ngrok

```bash
docker-compose restart ngrok
```

### Ver URL de PostgreSQL

```bash
# Ver logs
docker-compose logs ngrok

# O visitar: http://localhost:4040
# Ver túneles activos
```

### Configurar en Outerbase

1. **Nueva Conexión** → PostgreSQL
2. **Host**: `[host-de-ngrok]`
3. **Port**: `[puerto-de-ngrok]`
4. **Database**: `p2p_db`
5. **Username**: `p2p_user`
6. **Password**: `p2p_password_change_me`
7. **Test Connection**
8. **Save**

---

## ✅ Verificación

### Probar Conexión

1. **En Outerbase**: Test Connection
2. **Ver tablas**: Deberías ver `alerts`, `trades`, `price_history`, etc.
3. **Ejecutar query**: Probar una query simple
4. **Usar EZQL™**: Probar IA con una pregunta

### Si hay Errores

1. **Verificar ngrok**: Que esté corriendo
2. **Verificar PostgreSQL**: Que esté accesible
3. **Verificar firewall**: Que permita conexiones
4. **Verificar credenciales**: Usuario y contraseña correctos

---

## 🎯 Próximos Pasos

1. ✅ Configurar ngrok para PostgreSQL
2. ✅ Conectar Outerbase a PostgreSQL
3. ✅ Explorar funcionalidades de Outerbase
4. ✅ Crear dashboards
5. ✅ Embed dashboards en tu aplicación

¿Quieres que te ayude a configurar ngrok para PostgreSQL?

