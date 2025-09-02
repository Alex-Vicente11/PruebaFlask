# Guía de Desarrollo - Database Seeding

## 📚 Tabla de Contenidos
1. [Script de Seeding](#script-de-seeding)
2. [Uso del Script](#uso-del-script)
3. [Datos Generados](#datos-generados)
4. [Casos de Uso](#casos-de-uso)
5. [Comandos Útiles](#comandos-útiles)

---

## Script de Seeding

El archivo `seed_database.py` es un script de desarrollo que pobla la base de datos con datos de prueba para facilitar el testing y la integración con Android.

### Características

✅ **Productos de prueba**: 10 productos tech variados  
✅ **Usuarios registrados**: 5 usuarios con contraseñas conocidas  
✅ **Usuarios guest**: 6 guests con diferentes antigüedades  
✅ **Carritos poblados**: Items aleatorios en carritos  
✅ **Limpieza automática**: Opción para limpiar datos previos  

---

## Uso del Script

### Instalación

No requiere instalación adicional. Usa las mismas dependencias del proyecto.

### Comandos Disponibles

#### 1. Crear datos de prueba
```bash
python3 seed_database.py
```

#### 2. Limpiar y crear datos nuevos
```bash
python3 seed_database.py --clean
```

#### 3. Solo limpiar datos de prueba
```bash
python3 seed_database.py --only-clean
```

### Opciones

| Opción | Descripción |
|--------|-------------|
| `--clean` | Elimina datos de prueba existentes antes de crear nuevos |
| `--only-clean` | Solo limpia los datos sin crear nuevos |

---

## Datos Generados

### 📦 Productos (10 items)

Todos los productos tienen el prefijo `[TEST]` para identificarlos fácilmente:

- iPhone 15 Pro - $999.99
- Samsung Galaxy S24 - $899.99
- MacBook Air M3 - $1299.99
- iPad Pro 12.9 - $1099.99
- AirPods Pro - $249.99
- Apple Watch Series 9 - $399.99
- Magic Keyboard - $149.99
- USB-C Cable - $19.99
- Wireless Charger - $39.99
- Phone Case - $29.99

### 👤 Usuarios Registrados (5)

| Email | Password | Nombre |
|-------|----------|--------|
| test1@example.com | password123 | Test User 1 |
| test2@example.com | password123 | Test User 2 |
| test3@example.com | password123 | Test User 3 |
| admin@test.com | admin123 | Admin Test |
| demo@example.com | demo123 | Demo User |

### 👻 Usuarios Guest (6)

| Antigüedad | Tiene Carrito | Uso Sugerido |
|------------|---------------|--------------|
| 0 días | ✓ | Probar registro inmediato |
| 1 día | ✓ | Probar login reciente |
| 7 días | ✗ | Guest sin actividad |
| 15 días | ✓ | Guest moderadamente viejo |
| 31 días | ✗ | **Probar cleanup** |
| 35 días | ✓ | **Probar cleanup con carrito** |

### 🛒 Carritos

- **Usuarios registrados**: Primeros 3 usuarios tienen 1-4 items cada uno
- **Guests con carrito**: Tienen 1-3 items cada uno
- **Items totales**: ~19 items distribuidos

---

## Casos de Uso

### Caso 1: Probar Registro con Fusión de Carrito

1. Ejecutar seeding:
```bash
python3 seed_database.py --clean
```

2. Obtener un `guest_id` del output:
```
guest_id: seed_guest_21_1761245237
```

3. Desde Android o Postman, hacer POST a `/api/auth/register`:
```json
{
  "email": "nuevo@example.com",
  "password": "password123",
  "user_name": "Nuevo Usuario",
  "guest_id": "seed_guest_21_1761245237"
}
```

4. Verificar en la respuesta:
```json
{
  "success": true,
  "cart_migrated": true,
  "cart_items_count": 2  // Items fusionados
}
```

### Caso 2: Probar Login con Fusión de Carrito

1. Login con usuario existente:
```bash
curl -X POST http://localhost:5002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test1@example.com",
    "password": "password123",
    "guest_id": "seed_guest_22_1761245237"
  }'
```

2. Verificar fusión de carrito en la respuesta

### Caso 3: Probar Cleanup de Guests Antiguos

1. Ejecutar seeding (incluye guests de 31+ días)

2. Obtener token de autenticación:
```bash
curl -X POST http://localhost:5002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "admin123"}'
```

3. Ejecutar cleanup:
```bash
curl -X DELETE http://localhost:5002/api/guest/cleanup \
  -H "Authorization: Bearer YOUR_TOKEN"
```

4. Verificar respuesta:
```json
{
  "success": true,
  "deleted_guests": 2,
  "deleted_cart_items": 3,
  "message": "Cleanup completed: 2 guests deleted"
}
```

### Caso 4: Testing desde Android

1. Ejecutar seeding

2. En tu app Android, usar las credenciales de prueba:
```kotlin
// Login de prueba
loginViewModel.login("test1@example.com", "password123")

// Verificar que el carrito tiene items
cartViewModel.getCartItems()
```

3. Probar agregar productos (usar IDs del output del seeding)

### Caso 5: Testing Manual con Postman

1. Importar colección de Postman (crear una basada en API_DOCUMENTATION.md)

2. Crear environment variables:
```
base_url: http://localhost:5002
test_email: test1@example.com
test_password: password123
```

3. Probar endpoints uno por uno

---

## Comandos Útiles

### Ver datos creados en MySQL

```bash
# Conectar a MySQL
mysql -u root list_products

# Ver usuarios de prueba
SELECT id_user, user_name, email, is_guest, guest_id 
FROM user 
WHERE email LIKE '%test%' OR guest_id LIKE 'seed_guest%';

# Ver productos de prueba
SELECT id_product, product, price 
FROM products 
WHERE product LIKE '[TEST]%';

# Ver carritos de usuarios de prueba
SELECT c.id_cart, c.id_user, u.user_name, p.product, c.quantity
FROM cart c
JOIN user u ON c.id_user = u.id_user
JOIN products p ON c.id_product = p.id_product
WHERE u.email LIKE '%test%' OR u.guest_id LIKE 'seed_guest%';

# Contar guests por antigüedad
SELECT 
  CASE 
    WHEN DATEDIFF(NOW(), created_at) < 7 THEN '< 7 días'
    WHEN DATEDIFF(NOW(), created_at) < 30 THEN '7-30 días'
    ELSE '> 30 días'
  END AS antigüedad,
  COUNT(*) as cantidad
FROM user
WHERE is_guest = TRUE AND guest_id LIKE 'seed_guest%'
GROUP BY antigüedad;
```

### Verificar el seeding

```bash
# Contar registros creados
python3 -c "
from app import db, User, Product, Cart
db.connect()

users = User.select().where(
    (User.email.contains('test@')) | 
    (User.guest_id.contains('seed_guest'))
).count()

products = Product.select().where(
    Product.product.contains('[TEST]')
).count()

cart_items = Cart.select().join(User).where(
    (User.email.contains('test@')) | 
    (User.guest_id.contains('seed_guest'))
).count()

print(f'Usuarios: {users}')
print(f'Productos: {products}')
print(f'Items en carrito: {cart_items}')
"
```

### Limpiar todos los datos de prueba

```bash
# Opción 1: Usar el script
python3 seed_database.py --only-clean

# Opción 2: Directamente en MySQL
mysql -u root list_products << 'SQL'
DELETE FROM cart WHERE id_user IN (
  SELECT id_user FROM user 
  WHERE email LIKE '%test%' OR guest_id LIKE 'seed_guest%'
);

DELETE FROM user 
WHERE email LIKE '%test%' OR guest_id LIKE 'seed_guest%';

DELETE FROM products 
WHERE product LIKE '[TEST]%';
SQL
```

### Reset completo de la base de datos

⚠️ **ADVERTENCIA**: Esto eliminará TODOS los datos, no solo los de prueba

```bash
mysql -u root list_products << 'SQL'
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE cart;
TRUNCATE TABLE user;
TRUNCATE TABLE products;
SET FOREIGN_KEY_CHECKS = 1;
SQL

# Luego ejecutar seeding
python3 seed_database.py
```

---

## Integración con Workflow de Desarrollo

### Workflow Recomendado

1. **Inicio del día**:
```bash
# Actualizar código
git pull origin feature/anonymous-users

# Limpiar y crear datos frescos
python3 seed_database.py --clean

# Iniciar servidor
python3 app.py
```

2. **Durante desarrollo**:
```bash
# Si necesitas datos nuevos
python3 seed_database.py --clean

# Si solo quieres limpiar
python3 seed_database.py --only-clean
```

3. **Antes de hacer pruebas importantes**:
```bash
# Asegurar datos limpios
python3 seed_database.py --clean

# Verificar que se crearon correctamente
mysql -u root list_products -e "
SELECT 
  (SELECT COUNT(*) FROM user WHERE email LIKE '%test%') as test_users,
  (SELECT COUNT(*) FROM user WHERE guest_id LIKE 'seed_guest%') as test_guests,
  (SELECT COUNT(*) FROM products WHERE product LIKE '[TEST]%') as test_products;
"
```

---

## Troubleshooting

### Error: "Module not found"

```bash
# Asegúrate de estar en el entorno virtual
source .venv/bin/activate

# Reinstalar dependencias si es necesario
pip install -r requirements.txt
```

### Error: "Can't connect to MySQL"

```bash
# Verificar que MySQL está corriendo
ps aux | grep mysql

# Verificar credenciales en .env
cat .env | grep DB_
```

### Error: "Duplicate entry"

```bash
# Limpiar datos existentes primero
python3 seed_database.py --only-clean

# Luego crear nuevos
python3 seed_database.py
```

### Los carritos no tienen items

```bash
# Verificar que se crearon productos primero
mysql -u root list_products -e "SELECT COUNT(*) FROM products WHERE product LIKE '[TEST]%';"

# Si no hay productos, ejecutar de nuevo
python3 seed_database.py --clean
```

---

## Mejores Prácticas

### ✅ DO

- Ejecutar `--clean` antes de demos o testing importante
- Usar las credenciales de prueba documentadas
- Verificar los guest_ids en el output antes de usarlos
- Mantener los prefijos `[TEST]` para fácil identificación
- Documentar cualquier cambio al script de seeding

### ❌ DON'T

- No usar datos de seeding en producción
- No modificar manualmente los datos de prueba (usar el script)
- No commitear guest_ids específicos en el código
- No mezclar datos reales con datos de prueba

---

## Personalización

### Agregar más productos

Editar `seed_database.py`, sección `create_products()`:

```python
products_data = [
    {"name": "[TEST] Nuevo Producto", "price": 99.99},
    # ... más productos
]
```

### Agregar más usuarios

Editar `seed_database.py`, sección `create_users()`:

```python
users_data = [
    {
        "name": "Mi Usuario",
        "email": "miusuario@test.com",
        "password": "password123"
    },
    # ... más usuarios
]
```

### Cambiar cantidad de guests

Editar `seed_database.py`, sección `create_guest_users()`:

```python
guest_configs = [
    {"days_old": 0, "has_cart": True},
    # Agregar más configuraciones
]
```

---

## Referencias

- [API Documentation](API_DOCUMENTATION.md)
- [Android Integration Guide](ANDROID_INTEGRATION.md)
- [Test Suite](test_guest_auth.py)

---

**Última actualización:** 2025-10-23  
**Mantenedor:** Equipo de Backend
