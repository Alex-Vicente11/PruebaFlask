# ✅ CHECKLIST DE INICIO - USUARIOS ANÓNIMOS

**¡Usa esta guía mañana para empezar rápidamente!**

---

## 🚀 INICIO RÁPIDO (15 minutos)

### 1. Preparar el entorno

```bash
# Navegar al proyecto
cd /Users/alancruzmendez/projects/PruebaFlask

# Activar entorno virtual
source .venv/bin/activate

# Instalar nuevas dependencias
pip install -r requirements.txt

# Verificar que todo se instaló
pip list | grep -E "PyJWT|bcrypt|email-validator|python-dotenv|Flask-CORS"
```

**✅ Checkpoint:** Deberías ver las 5 librerías listadas.

---

### 2. Configurar variables de entorno

```bash
# Copiar el template
cp .env.example .env

# Editar .env (usa tu editor favorito)
nano .env  # o code .env si usas VS Code
```

**Actualizar en .env:**
```
DB_PASSWORD=Relic11&
JWT_SECRET_KEY=mi-clave-super-secreta-123456789
```

**✅ Checkpoint:** El archivo `.env` existe y tiene tus credenciales.

---

### 3. Hacer backup de la base de datos

```bash
# Crear backup
mysqldump -u root -p list_products > backup_antes_migracion_$(date +%Y%m%d_%H%M%S).sql

# Verificar que se creó
ls -lh backup_antes_migracion_*.sql
```

**✅ Checkpoint:** Deberías ver un archivo .sql con tamaño > 0 bytes.

---

### 4. Ejecutar migración de base de datos

```bash
# Opción 1: Desde MySQL CLI
mysql -u root -p list_products < migrations/001_add_guest_support.sql

# Opción 2: Desde MySQL Workbench
# - Abrir el archivo migrations/001_add_guest_support.sql
# - Ejecutar todo el script
```

**Verificar que funcionó:**
```sql
USE list_products;
DESCRIBE user;
```

**✅ Checkpoint:** Deberías ver las nuevas columnas: email, password_hash, is_guest, guest_id, created_at

---

## 📝 ORDEN DE IMPLEMENTACIÓN RECOMENDADO

### SESIÓN 1: Base (2-3 horas)

- [ ] **Tarea 4:** Actualizar modelo User en `app.py`
  ```python
  class User(BaseModel):
      id_user = IntegerField(primary_key=True)
      user_name = CharField(max_length=100, null=False)
      email = CharField(max_length=255, null=True, unique=True)
      password_hash = CharField(max_length=255, null=True)
      is_guest = BooleanField(default=False)
      guest_id = CharField(max_length=100, null=True, unique=True)
      created_at = DateTimeField(default=datetime.now)
  ```

- [ ] **Tarea 6:** Crear archivo `auth_utils.py` (copiar del plan completo)

- [ ] **Tarea 17:** Actualizar `app.py` para usar `.env`
  ```python
  from dotenv import load_dotenv
  import os

  load_dotenv()

  db = MySQLDatabase(
      os.getenv('DB_NAME'),
      user=os.getenv('DB_USER'),
      password=os.getenv('DB_PASSWORD'),
      host=os.getenv('DB_HOST'),
      port=int(os.getenv('DB_PORT'))
  )
  ```

**Probar:** Ejecutar `python app.py` y verificar que corre sin errores.

---

### SESIÓN 2: Endpoints básicos (2-3 horas)

- [ ] **Tarea 7:** Implementar `POST /api/guest/create` (código en el plan)

- [ ] **Tarea 16:** Agregar CORS
  ```python
  from flask_cors import CORS
  CORS(app)
  ```

**Probar con curl:**
```bash
curl -X POST http://localhost:5002/api/guest/create \
  -H "Content-Type: application/json" \
  -d '{"guest_id": "guest_test_123"}'
```

**✅ Checkpoint:** Deberías recibir `{"success": true, "user_id": X, "is_guest": true}`

---

### SESIÓN 3: Fusión de carrito (2 horas)

- [ ] **Tarea 8:** Crear función `merge_cart()` en `app.py` (código en el plan)

**Probar manualmente:**
1. Crear un guest con POST /api/guest/create
2. Agregar productos al carrito del guest con POST /add-to-cart
3. Ejecutar la fusión desde Python shell:
   ```python
   from app import *
   merge_cart(guest_user_id=X, real_user_id=Y)
   ```

**✅ Checkpoint:** Los items se transfieren correctamente.

---

### SESIÓN 4: Autenticación (3-4 horas)

- [ ] **Tarea 9:** Implementar `POST /api/auth/register` (código en el plan)

- [ ] **Tarea 10:** Implementar `POST /api/auth/login` (código en el plan)

**Probar registro:**
```bash
# 1. Crear guest
curl -X POST http://localhost:5002/api/guest/create \
  -H "Content-Type: application/json" \
  -d '{"guest_id": "guest_abc123"}'

# 2. Agregar producto al carrito del guest
curl -X POST http://localhost:5002/add-to-cart \
  -H "Content-Type: application/json" \
  -d '{"id_user": 123, "id_product": 1, "quantity": 2}'

# 3. Registrar usuario
curl -X POST http://localhost:5002/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "user_name": "Test User",
    "guest_id": "guest_abc123"
  }'
```

**✅ Checkpoint:** Deberías recibir `cart_migrated: true` y un token JWT.

---

### SESIÓN 5: Seguridad y endpoints adicionales (2-3 horas)

- [ ] **Tarea 11:** Crear decorator `@require_auth` (en `auth_utils.py`)

- [ ] **Tarea 12:** Proteger endpoints sensibles

- [ ] **Tarea 13:** Implementar `POST /api/cart/merge`

- [ ] **Tarea 14:** Implementar `DELETE /api/guest/cleanup`

---

### SESIÓN 6: Testing (2-3 horas)

- [ ] **Tarea 18-21:** Crear tests (archivo `test_guest_auth.py`)

```bash
# Ejecutar tests
pytest test_guest_auth.py -v
```

---

### SESIÓN 7: Documentación y pruebas finales (2 horas)

- [ ] **Tarea 23:** Documentar API
- [ ] **Tarea 24:** Crear ejemplo de Android
- [ ] **Tarea 22:** Probar todos los endpoints con Postman
- [ ] **Tarea 26:** Probar edge cases

---

## 🎯 HITOS CLAVE

Después de cada sesión, deberías poder hacer esto:

### Después de Sesión 1:
- ✅ El servidor corre sin errores
- ✅ La BD tiene las nuevas columnas
- ✅ Las variables de entorno funcionan

### Después de Sesión 2:
- ✅ Puedes crear un usuario guest desde Postman/curl
- ✅ El guest_id se guarda correctamente

### Después de Sesión 3:
- ✅ Puedes fusionar carritos manualmente

### Después de Sesión 4:
- ✅ Registro funciona
- ✅ Login funciona
- ✅ La fusión automática funciona
- ✅ Recibes un token JWT válido

### Después de Sesión 5:
- ✅ Los endpoints están protegidos
- ✅ La limpieza de guests funciona

### Después de Sesión 6:
- ✅ Todos los tests pasan

### Después de Sesión 7:
- ✅ Documentación completa
- ✅ Ready para integrar con Android

---

## 🚨 SI ALGO SALE MAL

### Error: "Module not found"
```bash
pip install -r requirements.txt
```

### Error: "Can't connect to MySQL"
```bash
# Verificar que MySQL está corriendo
mysql -u root -p

# Verificar credenciales en .env
cat .env
```

### Error: "Column doesn't exist"
```bash
# Re-ejecutar migración
mysql -u root -p list_products < migrations/001_add_guest_support.sql
```

### Error: "Invalid JWT"
```python
# Verificar que JWT_SECRET_KEY es el mismo en .env y auth_utils.py
```

---

## 📚 ARCHIVOS DE REFERENCIA

Durante la implementación, consulta:

1. **`PLAN_USUARIOS_ANONIMOS.md`** - Código completo de cada función
2. **`README_CONTINUACION.md`** - Resumen ejecutivo
3. **`migrations/001_add_guest_support.sql`** - Script de migración
4. **`.env.example`** - Template de variables

---

## 💡 TIPS PARA MAÑANA

1. **No intentes hacer todo en un día** - Avanza paso a paso
2. **Haz commits frecuentes** - Después de cada tarea importante
3. **Prueba cada endpoint antes de continuar** - No acumules código sin probar
4. **Usa Postman** - Crea una colección con todos los requests
5. **Revisa los logs** - Agrega `app.logger.info()` en puntos críticos

---

## 🔄 FLUJO DE TRABAJO RECOMENDADO

```
1. Lee la tarea en el plan
2. Implementa el código
3. Prueba manualmente con curl/Postman
4. Si funciona → Commit
5. Si no funciona → Debug con logs
6. Repite
```

---

## ✅ CRITERIO DE "TERMINADO"

Una tarea está completa cuando:

- [ ] El código está implementado
- [ ] Funciona manualmente (probado con Postman)
- [ ] No hay errores en la consola
- [ ] Hiciste commit con mensaje descriptivo
- [ ] Actualizaste la todo list (si estás usando una)

---

**¡Buena suerte mañana! 🚀**

Recuerda: El objetivo es que funcione, no que sea perfecto. Refactoriza después.
