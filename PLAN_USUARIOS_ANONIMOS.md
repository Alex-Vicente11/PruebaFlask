# PLAN DE IMPLEMENTACIÓN: SISTEMA DE USUARIOS ANÓNIMOS

**Fecha de creación:** 2025-10-20
**Proyecto:** PruebaFlask - Backend Flask
**App conectada:** /Users/alancruzmendez/projects/Comercio-app

---

## 📋 RESUMEN EJECUTIVO

Este plan implementa un sistema completo de usuarios anónimos (guests) que permite:
- ✅ Usar la app sin registro previo
- ✅ Agregar productos al carrito como usuario invitado
- ✅ Registrarse o hacer login y **fusionar automáticamente** el carrito
- ✅ Mantener todos los items del carrito al convertirse en usuario real

---

## 🎯 OBJETIVOS

1. Permitir que usuarios usen la app sin fricción inicial
2. Incrementar conversión de guests a usuarios registrados
3. Mejorar experiencia de usuario manteniendo su carrito
4. Mantener todos los endpoints compatibles con JSON para Android

---

## 🏗️ ARQUITECTURA TÉCNICA

### Cambios en Base de Datos
```sql
ALTER TABLE user ADD:
  - email VARCHAR(255) NULL UNIQUE
  - password_hash VARCHAR(255) NULL
  - is_guest BOOLEAN DEFAULT FALSE
  - guest_id VARCHAR(100) NULL UNIQUE
  - created_at DATETIME DEFAULT CURRENT_TIMESTAMP
```

### Nuevos Endpoints
- `POST /api/guest/create` - Crear usuario invitado
- `POST /api/auth/register` - Registrar usuario (con fusión de carrito)
- `POST /api/auth/login` - Login (con fusión de carrito)
- `POST /api/cart/merge` - Fusión manual de carrito
- `DELETE /api/guest/cleanup` - Limpieza de guests antiguos

### Nuevas Dependencias
- PyJWT - Autenticación con tokens
- bcrypt - Hash de contraseñas
- email-validator - Validación de emails
- python-dotenv - Variables de entorno

---

## 📊 PLAN DE TRABAJO DETALLADO

### **FASE 1: PREPARACIÓN Y MIGRACIONES** (Estimado: 2-3 horas)

#### Tarea 1: Crear backup de BD
```bash
mysqldump -u root -p list_products > backup_before_migration_$(date +%Y%m%d_%H%M%S).sql
```

#### Tarea 2-3: Ejecutar migraciones SQL
```sql
-- Archivo: migrations/001_add_guest_support.sql

-- Agregar columnas
ALTER TABLE user
ADD COLUMN email VARCHAR(255) NULL UNIQUE,
ADD COLUMN password_hash VARCHAR(255) NULL,
ADD COLUMN is_guest BOOLEAN DEFAULT FALSE,
ADD COLUMN guest_id VARCHAR(100) NULL UNIQUE,
ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Crear índices
CREATE INDEX idx_guest_id ON user(guest_id);
CREATE INDEX idx_is_guest ON user(is_guest);
CREATE INDEX idx_email ON user(email);

-- Actualizar usuarios existentes
UPDATE user SET is_guest = FALSE WHERE is_guest IS NULL;
```

#### Tarea 4: Actualizar modelo User
```python
class User(BaseModel):
    id_user = IntegerField(primary_key=True)
    user_name = CharField(max_length=100, null=False)
    email = CharField(max_length=255, null=True, unique=True)
    password_hash = CharField(max_length=255, null=True)
    is_guest = BooleanField(default=False)
    guest_id = CharField(max_length=100, null=True, unique=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'user'
```

#### Tarea 5: Instalar dependencias
```bash
pip install PyJWT bcrypt email-validator python-dotenv
pip freeze > requirements.txt
```

---

### **FASE 2: UTILIDADES Y FUNCIONES BASE** (Estimado: 3-4 horas)

#### Tarea 6: Crear módulo de autenticación
**Archivo nuevo:** `auth_utils.py`

```python
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import os

SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')

def hash_password(password):
    """Hash de contraseña con bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    """Verificar contraseña"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_jwt(user_id, is_guest=False):
    """Generar token JWT"""
    payload = {
        'user_id': user_id,
        'is_guest': is_guest,
        'exp': datetime.utcnow() + timedelta(days=30),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def decode_jwt(token):
    """Decodificar token JWT"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator para proteger endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'success': False, 'message': 'Token missing'}), 401

        if token.startswith('Bearer '):
            token = token[7:]

        payload = decode_jwt(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401

        request.user_id = payload['user_id']
        request.is_guest = payload.get('is_guest', False)

        return f(*args, **kwargs)

    return decorated_function
```

#### Tarea 8: Crear función merge_cart()
**Ubicación:** Agregar a `app.py`

```python
def merge_cart(guest_user_id, real_user_id):
    """
    Fusiona el carrito de un usuario guest con un usuario real

    Args:
        guest_user_id (int): ID del usuario invitado
        real_user_id (int): ID del usuario real registrado

    Returns:
        dict: {'merged_count': int, 'deleted_count': int}
    """
    try:
        # Obtener items del carrito del guest
        guest_cart_items = Cart.select().where(Cart.id_user == guest_user_id)

        merged_count = 0
        updated_count = 0

        for guest_item in guest_cart_items:
            # Verificar si el producto ya existe en el carrito del usuario real
            existing_item = Cart.get_or_none(
                (Cart.id_user == real_user_id) &
                (Cart.id_product == guest_item.id_product)
            )

            if existing_item:
                # Si existe, sumar cantidades
                existing_item.quantity += guest_item.quantity
                existing_item.save()
                updated_count += 1
            else:
                # Si no existe, cambiar el id_user
                guest_item.id_user = real_user_id
                guest_item.save()
                merged_count += 1

        # Eliminar items residuales del guest
        deleted_count = Cart.delete().where(Cart.id_user == guest_user_id).execute()

        # Eliminar usuario guest
        User.delete().where(User.id_user == guest_user_id).execute()

        app.logger.info(f"Cart merged: {merged_count} moved, {updated_count} updated, {deleted_count} deleted")

        return {
            'merged_count': merged_count,
            'updated_count': updated_count,
            'deleted_count': deleted_count,
            'total_items': merged_count + updated_count
        }

    except Exception as e:
        app.logger.error(f"Error merging cart: {str(e)}")
        raise
```

---

### **FASE 3: ENDPOINTS DE GUEST** (Estimado: 2 horas)

#### Tarea 7: Implementar POST /api/guest/create

```python
@app.route('/api/guest/create', methods=['POST'])
def create_guest():
    """
    Crear o recuperar usuario invitado

    Request JSON:
    {
        "guest_id": "guest_uuid4_timestamp"
    }

    Response JSON:
    {
        "success": true,
        "user_id": 123,
        "is_guest": true,
        "message": "Guest user created successfully"
    }
    """
    try:
        data = request.get_json()

        if not data or 'guest_id' not in data:
            return jsonify({
                'success': False,
                'message': 'guest_id is required'
            }), 400

        guest_id = data['guest_id']

        # Verificar si el guest ya existe
        existing_user = User.get_or_none(User.guest_id == guest_id)

        if existing_user:
            return jsonify({
                'success': True,
                'user_id': existing_user.id_user,
                'is_guest': True,
                'message': 'Guest user already exists'
            }), 200

        # Crear nuevo usuario guest
        max_id = User.select(fn.COALESCE(fn.MAX(User.id_user), 0).alias('max_id')).scalar()
        new_id = max_id + 1

        new_guest = User.create(
            id_user=new_id,
            user_name='Guest User',
            is_guest=True,
            guest_id=guest_id,
            email=None,
            password_hash=None
        )

        app.logger.info(f"New guest created: {new_id} with guest_id: {guest_id}")

        return jsonify({
            'success': True,
            'user_id': new_guest.id_user,
            'is_guest': True,
            'message': 'Guest user created successfully'
        }), 201

    except Exception as e:
        app.logger.error(f"Error creating guest: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error creating guest user: {str(e)}'
        }), 500
```

---

### **FASE 4: AUTENTICACIÓN** (Estimado: 4-5 horas)

#### Tarea 9: Implementar POST /api/auth/register

```python
from email_validator import validate_email, EmailNotValidError

@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    Registrar nuevo usuario (con fusión de carrito si viene de guest)

    Request JSON:
    {
        "email": "user@example.com",
        "password": "securePassword123",
        "user_name": "John Doe",
        "guest_id": "guest_uuid4_..." (OPCIONAL)
    }
    """
    try:
        data = request.get_json()

        # Validaciones
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'message': 'email and password are required'
            }), 400

        email = data['email']
        password = data['password']
        user_name = data.get('user_name', 'User')
        guest_id = data.get('guest_id')

        # Validar email
        try:
            validate_email(email)
        except EmailNotValidError:
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400

        # Verificar si el email ya existe
        existing_user = User.get_or_none(User.email == email)
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Email already registered'
            }), 409

        # Crear nuevo usuario
        max_id = User.select(fn.COALESCE(fn.MAX(User.id_user), 0).alias('max_id')).scalar()
        new_id = max_id + 1

        hashed_password = hash_password(password).decode('utf-8')

        new_user = User.create(
            id_user=new_id,
            user_name=user_name,
            email=email,
            password_hash=hashed_password,
            is_guest=False,
            guest_id=None
        )

        # Si viene de guest, fusionar carrito
        cart_migrated = False
        cart_items_count = 0

        if guest_id:
            guest_user = User.get_or_none(User.guest_id == guest_id)
            if guest_user:
                merge_result = merge_cart(guest_user.id_user, new_user.id_user)
                cart_migrated = True
                cart_items_count = merge_result['total_items']
                app.logger.info(f"Cart merged for new user {new_id}: {cart_items_count} items")

        # Generar token JWT
        token = generate_jwt(new_user.id_user, is_guest=False)

        return jsonify({
            'success': True,
            'user_id': new_user.id_user,
            'is_guest': False,
            'token': token,
            'cart_migrated': cart_migrated,
            'cart_items_count': cart_items_count,
            'message': 'User registered successfully'
        }), 201

    except Exception as e:
        app.logger.error(f"Error registering user: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error registering user: {str(e)}'
        }), 500
```

#### Tarea 10: Implementar POST /api/auth/login

```python
@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Login de usuario (con fusión de carrito si viene de guest)

    Request JSON:
    {
        "email": "user@example.com",
        "password": "securePassword123",
        "guest_id": "guest_uuid4_..." (OPCIONAL)
    }
    """
    try:
        data = request.get_json()

        # Validaciones
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'message': 'email and password are required'
            }), 400

        email = data['email']
        password = data['password']
        guest_id = data.get('guest_id')

        # Buscar usuario por email
        user = User.get_or_none((User.email == email) & (User.is_guest == False))

        if not user:
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401

        # Verificar contraseña
        if not verify_password(password, user.password_hash):
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401

        # Si viene de guest, fusionar carrito
        cart_migrated = False
        cart_items_count = 0

        if guest_id:
            guest_user = User.get_or_none(User.guest_id == guest_id)
            if guest_user:
                merge_result = merge_cart(guest_user.id_user, user.id_user)
                cart_migrated = True
                cart_items_count = merge_result['total_items']
                app.logger.info(f"Cart merged on login for user {user.id_user}: {cart_items_count} items")

        # Generar token JWT
        token = generate_jwt(user.id_user, is_guest=False)

        return jsonify({
            'success': True,
            'user_id': user.id_user,
            'user_name': user.user_name,
            'email': user.email,
            'is_guest': False,
            'token': token,
            'cart_migrated': cart_migrated,
            'cart_items_count': cart_items_count,
            'message': 'Login successful'
        }), 200

    except Exception as e:
        app.logger.error(f"Error during login: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error during login: {str(e)}'
        }), 500
```

---

### **FASE 5: PROTECCIÓN Y SEGURIDAD** (Estimado: 2-3 horas)

#### Tarea 11-12: Proteger endpoints

```python
# Ejemplo: Proteger DELETE /users/<id>
@app.route('/users/<int:id>', methods=['DELETE'])
@require_auth  # ← Agregar decorator
def delete_user(id):
    # Solo el mismo usuario o admin puede eliminar
    if request.user_id != id:
        return jsonify({
            'success': False,
            'message': 'Unauthorized'
        }), 403

    # ... resto del código
```

#### Tarea 16: Configurar CORS

```python
from flask_cors import CORS

# En la inicialización de Flask
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # En producción: especificar el dominio de la app
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

#### Tarea 17: Variables de entorno

**Archivo nuevo:** `.env`
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=Relic11&
DB_NAME=list_products
JWT_SECRET_KEY=tu-clave-secreta-super-segura-cambiar-en-produccion
```

**Actualizar app.py:**
```python
from dotenv import load_dotenv
import os

load_dotenv()

db = MySQLDatabase(
    os.getenv('DB_NAME', 'list_products'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 3306))
)
```

---

### **FASE 6: ENDPOINTS ADICIONALES** (Estimado: 2 horas)

#### Tarea 13: Implementar POST /api/cart/merge

```python
@app.route('/api/cart/merge', methods=['POST'])
@require_auth
def manual_cart_merge():
    """
    Fusión manual de carrito (backup por si falla automática)

    Request JSON:
    {
        "guest_id": "guest_uuid4_..."
    }
    """
    try:
        data = request.get_json()

        if not data or 'guest_id' not in data:
            return jsonify({
                'success': False,
                'message': 'guest_id is required'
            }), 400

        guest_id = data['guest_id']
        real_user_id = request.user_id

        # Buscar usuario guest
        guest_user = User.get_or_none(User.guest_id == guest_id)

        if not guest_user:
            return jsonify({
                'success': False,
                'message': 'Guest user not found'
            }), 404

        # Fusionar carrito
        merge_result = merge_cart(guest_user.id_user, real_user_id)

        return jsonify({
            'success': True,
            'merged_items': merge_result['total_items'],
            'message': 'Cart successfully merged'
        }), 200

    except Exception as e:
        app.logger.error(f"Error in manual cart merge: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error merging cart: {str(e)}'
        }), 500
```

#### Tarea 14: Implementar DELETE /api/guest/cleanup

```python
@app.route('/api/guest/cleanup', methods=['DELETE'])
@require_auth
def cleanup_old_guests():
    """
    Eliminar usuarios guest inactivos (más de 30 días)
    Requiere autenticación de admin (implementar validación)
    """
    try:
        # Solo admin puede ejecutar (agregar validación de rol)
        # Por ahora, cualquier usuario autenticado

        # Calcular fecha límite (30 días atrás)
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=30)

        # Buscar guests antiguos
        old_guests = User.select().where(
            (User.is_guest == True) &
            (User.created_at < cutoff_date)
        )

        deleted_guests = 0
        deleted_cart_items = 0

        for guest in old_guests:
            # Eliminar items del carrito
            cart_count = Cart.delete().where(Cart.id_user == guest.id_user).execute()
            deleted_cart_items += cart_count

            # Eliminar usuario
            guest.delete_instance()
            deleted_guests += 1

        app.logger.info(f"Cleanup: {deleted_guests} guests, {deleted_cart_items} cart items")

        return jsonify({
            'success': True,
            'deleted_guests': deleted_guests,
            'deleted_cart_items': deleted_cart_items,
            'message': f'Cleanup completed: {deleted_guests} guests deleted'
        }), 200

    except Exception as e:
        app.logger.error(f"Error in cleanup: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error during cleanup: {str(e)}'
        }), 500
```

---

### **FASE 7: VALIDACIONES Y MEJORAS** (Estimado: 1-2 horas)

#### Tarea 15: Validar existencia de user_id

```python
# Actualizar endpoint POST /add-to-cart
@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    # ... código existente para obtener datos ...

    # AGREGAR VALIDACIÓN
    user_exists = User.get_or_none(User.id_user == user_id)
    if not user_exists:
        if request.get_json(silent=True):
            return jsonify({
                'success': False,
                'message': 'User does not exist'
            }), 404
        else:
            return redirect(url_for('cart_view', user_id=user_id, error='User not found'))

    # ... resto del código ...
```

#### Tarea 25: Agregar logging

```python
import logging

# Configurar logging en app.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

---

### **FASE 8: TESTING** (Estimado: 4-5 horas)

#### Tarea 18-21: Crear tests

**Archivo nuevo:** `test_guest_auth.py`

```python
import unittest
from app import app, db, User, Cart, Product
from auth_utils import hash_password, verify_password, generate_jwt, decode_jwt

class TestGuestSystem(unittest.TestCase):

    def setUp(self):
        """Setup antes de cada test"""
        self.app = app.test_client()
        self.app.testing = True

        # Limpiar tablas de test
        # ... código de limpieza ...

    def test_create_guest(self):
        """Test: Crear usuario guest"""
        response = self.app.post('/api/guest/create', json={
            'guest_id': 'test_guest_123'
        })

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_guest'])
        self.assertIsNotNone(data['user_id'])

    def test_duplicate_guest(self):
        """Test: Intentar crear guest duplicado"""
        # Crear guest
        self.app.post('/api/guest/create', json={
            'guest_id': 'test_guest_123'
        })

        # Intentar crear de nuevo
        response = self.app.post('/api/guest/create', json={
            'guest_id': 'test_guest_123'
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('already exists', data['message'])

    def test_register_with_cart_merge(self):
        """Test: Registrar usuario y fusionar carrito"""
        # 1. Crear guest
        guest_response = self.app.post('/api/guest/create', json={
            'guest_id': 'test_guest_456'
        })
        guest_data = guest_response.get_json()
        guest_user_id = guest_data['user_id']

        # 2. Agregar productos al carrito como guest
        # (Crear producto primero)
        # ... código para crear producto y agregar al carrito ...

        # 3. Registrar usuario
        register_response = self.app.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'user_name': 'Test User',
            'guest_id': 'test_guest_456'
        })

        self.assertEqual(register_response.status_code, 201)
        register_data = register_response.get_json()

        # 4. Verificar fusión
        self.assertTrue(register_data['cart_migrated'])
        self.assertGreater(register_data['cart_items_count'], 0)

        # 5. Verificar que guest fue eliminado
        guest_user = User.get_or_none(User.id_user == guest_user_id)
        self.assertIsNone(guest_user)

    def test_login_with_cart_merge(self):
        """Test: Login y fusionar carrito de guest"""
        # Similar al test anterior pero con login
        pass

    def test_merge_cart_function(self):
        """Test: Función merge_cart directamente"""
        # ... test de la función merge_cart ...
        pass

if __name__ == '__main__':
    unittest.main()
```

#### Tarea 22: Pruebas manuales con Postman

**Crear colección Postman con:**
1. Create Guest
2. Add to Cart (as guest)
3. Register User (with guest_id)
4. Verify cart merged
5. Login User (with guest_id)
6. Manual Cart Merge
7. Guest Cleanup

---

### **FASE 9: DOCUMENTACIÓN** (Estimado: 2 horas)

#### Tarea 23: Documentación de API

**Archivo nuevo:** `API_DOCUMENTATION.md`

```markdown
# API Documentation - Guest Users System

## Authentication

All authenticated endpoints require a JWT token in the header:
```
Authorization: Bearer <token>
```

## Endpoints

### 1. POST /api/guest/create
Create or retrieve guest user...

[... documentación completa de cada endpoint ...]
```

#### Tarea 24: Script de ejemplo para Android

**Archivo nuevo:** `android_integration_example.kt`

```kotlin
// Ejemplo de integración con Android
object GuestUserManager {

    private const val PREFS_NAME = "user_prefs"
    private const val KEY_GUEST_ID = "guest_id"
    private const val KEY_USER_ID = "user_id"
    private const val KEY_AUTH_TOKEN = "auth_token"

    fun getOrCreateGuestId(context: Context): String {
        // ... código de ejemplo ...
    }

    suspend fun registerGuestUser(guestId: String): Result<UserResponse> {
        // ... código de ejemplo ...
    }
}
```

---

### **FASE 10: PRUEBAS FINALES** (Estimado: 2-3 horas)

#### Tarea 26: Escenarios de Edge Cases

1. **Escenario 1:** Guest con 5 items → Registra → Usuario real ya tenía 3 items (2 duplicados)
   - Resultado esperado: 6 items totales (cantidades sumadas en duplicados)

2. **Escenario 2:** Guest se registra sin items en carrito
   - Resultado esperado: Usuario creado, no hay fusión

3. **Escenario 3:** Usuario registrado usa app en nuevo dispositivo como guest → Login
   - Resultado esperado: Carritos se fusionan correctamente

4. **Escenario 4:** Guest_id inválido en registro
   - Resultado esperado: Usuario se crea sin fusión

5. **Escenario 5:** Dos requests simultáneos para crear mismo guest_id
   - Resultado esperado: Uno crea, otro retorna existente (gracias a UNIQUE constraint)

---

## 📝 NOTAS IMPORTANTES PARA LA IMPLEMENTACIÓN

### Seguridad
- ⚠️ NUNCA commitear el archivo `.env`
- ⚠️ Agregar `.env` al `.gitignore`
- ⚠️ Cambiar JWT_SECRET_KEY en producción
- ⚠️ Validar todas las entradas del usuario
- ⚠️ Sanitizar datos antes de queries

### Performance
- Crear índices en `guest_id`, `email`, `is_guest`
- Considerar batch deletes para cleanup
- Monitorear queries lentas
- Agregar paginación a endpoints GET si es necesario

### Mantenimiento
- Ejecutar cleanup de guests cada semana (cron job)
- Monitorear tasa de conversión guest → usuario real
- Logs para debugging de fusiones de carrito
- Alertas si fallan muchas fusiones

### Compatibilidad
- Mantener endpoints antiguos funcionando
- Todos los endpoints deben retornar JSON
- Agregar versionado de API si es necesario (/api/v1/)

---

## 🚀 ORDEN DE EJECUCIÓN RECOMENDADO

**DÍA 1: Base de datos y modelos**
- Tareas 1-5

**DÍA 2: Utilidades y guest endpoints**
- Tareas 6-8

**DÍA 3: Autenticación**
- Tareas 9-10

**DÍA 4: Seguridad y endpoints adicionales**
- Tareas 11-17

**DÍA 5: Testing y documentación**
- Tareas 18-24

**DÍA 6: Pruebas finales y deployment**
- Tareas 25-26

---

## ✅ CRITERIOS DE ÉXITO

- [ ] Usuario puede usar app sin registrarse
- [ ] Carrito se mantiene al registrarse
- [ ] Carrito se mantiene al hacer login
- [ ] No hay data leaks entre usuarios
- [ ] Guests antiguos se limpian automáticamente
- [ ] Todos los tests pasan
- [ ] API documentada completamente
- [ ] Android app puede integrarse sin problemas
- [ ] Performance aceptable (<500ms por request)
- [ ] Logs útiles para debugging

---

## 📞 REFERENCIAS

- Documentación Flask: https://flask.palletsprojects.com/
- PyJWT: https://pyjwt.readthedocs.io/
- bcrypt: https://github.com/pyca/bcrypt/
- Peewee ORM: http://docs.peewee-orm.com/

---

**Última actualización:** 2025-10-20
**Estado:** Plan creado, listo para implementación
