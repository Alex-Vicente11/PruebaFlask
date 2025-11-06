# API Documentation - Anonymous Users System

## Tabla de Contenidos
1. [Introducción](#introducción)
2. [Autenticación](#autenticación)
3. [Endpoints de Guest Users](#endpoints-de-guest-users)
4. [Endpoints de Autenticación](#endpoints-de-autenticación)
5. [Endpoints de Carrito](#endpoints-de-carrito)
6. [Endpoints de Administración](#endpoints-de-administración)
7. [Modelos de Datos](#modelos-de-datos)
8. [Códigos de Error](#códigos-de-error)
9. [Ejemplos de Flujos](#ejemplos-de-flujos)

---

## Introducción

Este sistema permite a los usuarios utilizar la aplicación sin necesidad de registro previo mediante "usuarios invitados" (guests). Cuando el usuario decide registrarse o hacer login, su carrito de compras se fusiona automáticamente con su cuenta real.

### Características principales:
- ✅ Uso de la app sin fricción inicial
- ✅ Fusión automática de carrito al registrarse/login
- ✅ Autenticación mediante JWT tokens
- ✅ Limpieza automática de guests antiguos
- ✅ Compatible con endpoints existentes

### Base URL
```
http://localhost:5002
```

Para producción, reemplazar con la URL del servidor.

---

## Autenticación

### Tipos de Autenticación

#### 1. Sin autenticación
Los endpoints públicos no requieren token:
- `POST /api/guest/create`
- `POST /api/auth/register`
- `POST /api/auth/login`

#### 2. Con JWT Token
Los endpoints protegidos requieren el header de autorización:
```http
Authorization: Bearer <token>
```

### Obtener un Token

Los tokens JWT se obtienen al:
1. Registrarse (`POST /api/auth/register`)
2. Hacer login (`POST /api/auth/login`)

### Estructura del Token

El token contiene:
```json
{
  "user_id": 123,
  "is_guest": false,
  "exp": 1763836464,
  "iat": 1761244464
}
```

- **user_id**: ID del usuario
- **is_guest**: Si es usuario invitado (siempre `false` para usuarios autenticados)
- **exp**: Timestamp de expiración (30 días)
- **iat**: Timestamp de emisión

---

## Endpoints de Guest Users

### POST /api/guest/create

Crea o recupera un usuario invitado.

#### Request

```http
POST /api/guest/create
Content-Type: application/json
```

```json
{
  "guest_id": "guest_uuid4_timestamp"
}
```

**Parámetros:**
- `guest_id` (string, requerido): Identificador único generado en el cliente
  - Formato recomendado: `guest_<UUID>_<timestamp>`
  - Ejemplo: `guest_a1b2c3d4-e5f6-7890-abcd-ef1234567890_1729707600`

#### Response Success (201 - Created)

```json
{
  "success": true,
  "user_id": 14,
  "is_guest": true,
  "message": "Guest user created successfully"
}
```

#### Response Success (200 - Already Exists)

Si el `guest_id` ya existe, retorna el usuario existente:

```json
{
  "success": true,
  "user_id": 14,
  "is_guest": true,
  "message": "Guest user already exists"
}
```

#### Response Error (400 - Bad Request)

```json
{
  "success": false,
  "message": "guest_id is required"
}
```

#### Response Error (500 - Internal Server Error)

```json
{
  "success": false,
  "message": "Error creating guest user: <error details>"
}
```

#### Ejemplo de Uso

**cURL:**
```bash
curl -X POST http://localhost:5002/api/guest/create \
  -H "Content-Type: application/json" \
  -d '{
    "guest_id": "guest_a1b2c3d4-e5f6-7890-abcd-ef1234567890_1729707600"
  }'
```

**JavaScript/Fetch:**
```javascript
const response = await fetch('http://localhost:5002/api/guest/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    guest_id: `guest_${crypto.randomUUID()}_${Date.now()}`
  })
});

const data = await response.json();
console.log('Guest User ID:', data.user_id);
```

**Kotlin (Android):**
```kotlin
data class GuestRequest(val guest_id: String)
data class GuestResponse(
    val success: Boolean,
    val user_id: Int,
    val is_guest: Boolean,
    val message: String
)

suspend fun createGuestUser(guestId: String): GuestResponse {
    return apiService.createGuest(GuestRequest(guestId))
}
```

---

## Endpoints de Autenticación

### POST /api/auth/register

Registra un nuevo usuario. Si se proporciona `guest_id`, el carrito del guest se fusiona automáticamente con el nuevo usuario.

#### Request

```http
POST /api/auth/register
Content-Type: application/json
```

```json
{
  "email": "usuario@example.com",
  "password": "securePassword123",
  "user_name": "John Doe",
  "guest_id": "guest_a1b2c3d4-e5f6-7890-abcd-ef1234567890_1729707600"
}
```

**Parámetros:**
- `email` (string, requerido): Email válido del usuario
- `password` (string, requerido): Contraseña (mínimo recomendado: 8 caracteres)
- `user_name` (string, opcional): Nombre del usuario (default: "User")
- `guest_id` (string, opcional): ID del guest para fusionar carrito

#### Response Success (201 - Created)

```json
{
  "success": true,
  "user_id": 15,
  "is_guest": false,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "cart_migrated": true,
  "cart_items_count": 3,
  "message": "User registered successfully"
}
```

**Campos de respuesta:**
- `success`: Indica si la operación fue exitosa
- `user_id`: ID del nuevo usuario creado
- `is_guest`: Siempre `false` para usuarios registrados
- `token`: JWT token para autenticación futura
- `cart_migrated`: `true` si se fusionó un carrito de guest
- `cart_items_count`: Número de items fusionados del carrito
- `message`: Mensaje descriptivo

#### Response Error (400 - Bad Request)

```json
{
  "success": false,
  "message": "email and password are required"
}
```

```json
{
  "success": false,
  "message": "Invalid email format"
}
```

#### Response Error (409 - Conflict)

```json
{
  "success": false,
  "message": "Email already registered"
}
```

#### Response Error (500 - Internal Server Error)

```json
{
  "success": false,
  "message": "Error registering user: <error details>"
}
```

#### Ejemplo de Uso

**cURL:**
```bash
curl -X POST http://localhost:5002/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "password": "miPassword123",
    "user_name": "Juan Pérez",
    "guest_id": "guest_a1b2c3d4-e5f6-7890-abcd-ef1234567890_1729707600"
  }'
```

**JavaScript/Fetch:**
```javascript
const response = await fetch('http://localhost:5002/api/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'usuario@example.com',
    password: 'miPassword123',
    user_name: 'Juan Pérez',
    guest_id: localStorage.getItem('guest_id') // Del guest previo
  })
});

const data = await response.json();
if (data.success) {
  localStorage.setItem('auth_token', data.token);
  localStorage.setItem('user_id', data.user_id);
  localStorage.removeItem('guest_id'); // Ya no es necesario
  
  console.log(`Carrito fusionado: ${data.cart_items_count} items`);
}
```

**Kotlin (Android):**
```kotlin
data class RegisterRequest(
    val email: String,
    val password: String,
    val user_name: String,
    val guest_id: String?
)

data class AuthResponse(
    val success: Boolean,
    val user_id: Int?,
    val is_guest: Boolean,
    val token: String?,
    val cart_migrated: Boolean,
    val cart_items_count: Int,
    val message: String
)

suspend fun registerUser(
    email: String,
    password: String,
    userName: String,
    guestId: String?
): AuthResponse {
    val request = RegisterRequest(email, password, userName, guestId)
    val response = apiService.register(request)
    
    if (response.success && response.token != null) {
        // Guardar token en SharedPreferences
        sharedPrefs.edit()
            .putString("auth_token", response.token)
            .putInt("user_id", response.user_id ?: 0)
            .remove("guest_id") // Eliminar guest_id
            .apply()
    }
    
    return response
}
```

---

### POST /api/auth/login

Inicia sesión de un usuario existente. Si se proporciona `guest_id`, el carrito del guest se fusiona con el usuario autenticado.

#### Request

```http
POST /api/auth/login
Content-Type: application/json
```

```json
{
  "email": "usuario@example.com",
  "password": "securePassword123",
  "guest_id": "guest_a1b2c3d4-e5f6-7890-abcd-ef1234567890_1729707600"
}
```

**Parámetros:**
- `email` (string, requerido): Email del usuario registrado
- `password` (string, requerido): Contraseña del usuario
- `guest_id` (string, opcional): ID del guest para fusionar carrito

#### Response Success (200 - OK)

```json
{
  "success": true,
  "user_id": 15,
  "user_name": "John Doe",
  "email": "usuario@example.com",
  "is_guest": false,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "cart_migrated": true,
  "cart_items_count": 2,
  "message": "Login successful"
}
```

#### Response Error (400 - Bad Request)

```json
{
  "success": false,
  "message": "email and password are required"
}
```

#### Response Error (401 - Unauthorized)

```json
{
  "success": false,
  "message": "Invalid credentials"
}
```

#### Response Error (500 - Internal Server Error)

```json
{
  "success": false,
  "message": "Error during login: <error details>"
}
```

#### Ejemplo de Uso

**cURL:**
```bash
curl -X POST http://localhost:5002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "password": "miPassword123",
    "guest_id": "guest_a1b2c3d4-e5f6-7890-abcd-ef1234567890_1729707600"
  }'
```

**JavaScript/Fetch:**
```javascript
const response = await fetch('http://localhost:5002/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'usuario@example.com',
    password: 'miPassword123',
    guest_id: localStorage.getItem('guest_id')
  })
});

const data = await response.json();
if (data.success) {
  localStorage.setItem('auth_token', data.token);
  localStorage.setItem('user_id', data.user_id);
  localStorage.removeItem('guest_id');
  
  console.log(`Bienvenido ${data.user_name}!`);
  console.log(`Items fusionados: ${data.cart_items_count}`);
}
```

**Kotlin (Android):**
```kotlin
data class LoginRequest(
    val email: String,
    val password: String,
    val guest_id: String?
)

suspend fun loginUser(
    email: String,
    password: String,
    guestId: String?
): AuthResponse {
    val request = LoginRequest(email, password, guestId)
    val response = apiService.login(request)
    
    if (response.success && response.token != null) {
        sharedPrefs.edit()
            .putString("auth_token", response.token)
            .putInt("user_id", response.user_id ?: 0)
            .putString("user_name", response.user_name)
            .remove("guest_id")
            .apply()
    }
    
    return response
}
```

---

## Endpoints de Carrito

### POST /api/cart/merge

🔒 **Requiere Autenticación**

Fusiona manualmente el carrito de un guest con el usuario autenticado actual. Este endpoint es un backup en caso de que la fusión automática falle.

#### Request

```http
POST /api/cart/merge
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "guest_id": "guest_a1b2c3d4-e5f6-7890-abcd-ef1234567890_1729707600"
}
```

**Parámetros:**
- `guest_id` (string, requerido): ID del guest cuyo carrito se desea fusionar

**Headers requeridos:**
- `Authorization`: Bearer token obtenido del login/registro

#### Response Success (200 - OK)

```json
{
  "success": true,
  "merged_items": 3,
  "message": "Cart successfully merged"
}
```

#### Response Error (400 - Bad Request)

```json
{
  "success": false,
  "message": "guest_id is required"
}
```

#### Response Error (401 - Unauthorized)

```json
{
  "success": false,
  "message": "Token missing"
}
```

```json
{
  "success": false,
  "message": "Invalid or expired token"
}
```

#### Response Error (404 - Not Found)

```json
{
  "success": false,
  "message": "Guest user not found"
}
```

#### Response Error (500 - Internal Server Error)

```json
{
  "success": false,
  "message": "Error merging cart: <error details>"
}
```

#### Ejemplo de Uso

**cURL:**
```bash
curl -X POST http://localhost:5002/api/cart/merge \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "guest_id": "guest_a1b2c3d4-e5f6-7890-abcd-ef1234567890_1729707600"
  }'
```

**JavaScript/Fetch:**
```javascript
const token = localStorage.getItem('auth_token');

const response = await fetch('http://localhost:5002/api/cart/merge', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    guest_id: 'guest_a1b2c3d4-e5f6-7890-abcd-ef1234567890_1729707600'
  })
});

const data = await response.json();
console.log(`Fusionados ${data.merged_items} items`);
```

**Kotlin (Android):**
```kotlin
data class MergeRequest(val guest_id: String)

data class MergeResponse(
    val success: Boolean,
    val merged_items: Int,
    val message: String
)

suspend fun mergeGuestCart(guestId: String): MergeResponse {
    val token = sharedPrefs.getString("auth_token", "") ?: ""
    
    return apiService.mergeCart(
        authorization = "Bearer $token",
        request = MergeRequest(guestId)
    )
}
```

---

## Endpoints de Administración

### DELETE /api/guest/cleanup

🔒 **Requiere Autenticación**

Elimina usuarios guest inactivos que tengan más de 30 días de antigüedad (configurable mediante variable de entorno `GUEST_CLEANUP_DAYS`).

Este endpoint debería ser ejecutado periódicamente mediante un cron job o tarea programada.

#### Request

```http
DELETE /api/guest/cleanup
Authorization: Bearer <token>
```

**Headers requeridos:**
- `Authorization`: Bearer token de un usuario autenticado

#### Response Success (200 - OK)

```json
{
  "success": true,
  "deleted_guests": 15,
  "deleted_cart_items": 42,
  "message": "Cleanup completed: 15 guests deleted"
}
```

**Campos de respuesta:**
- `deleted_guests`: Número de usuarios guest eliminados
- `deleted_cart_items`: Número de items de carrito eliminados
- `message`: Mensaje descriptivo del resultado

#### Response Error (401 - Unauthorized)

```json
{
  "success": false,
  "message": "Token missing"
}
```

```json
{
  "success": false,
  "message": "Invalid or expired token"
}
```

#### Response Error (500 - Internal Server Error)

```json
{
  "success": false,
  "message": "Error during cleanup: <error details>"
}
```

#### Ejemplo de Uso

**cURL:**
```bash
curl -X DELETE http://localhost:5002/api/guest/cleanup \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**JavaScript/Fetch:**
```javascript
const token = localStorage.getItem('auth_token');

const response = await fetch('http://localhost:5002/api/guest/cleanup', {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const data = await response.json();
console.log(`Limpieza completada: ${data.deleted_guests} guests eliminados`);
```

**Cron Job (Linux):**
```bash
# Ejecutar limpieza todos los domingos a las 3:00 AM
0 3 * * 0 curl -X DELETE http://localhost:5002/api/guest/cleanup -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

---

## Modelos de Datos

### User Model

```javascript
{
  "id_user": 15,              // int, primary key
  "user_name": "John Doe",    // string, max 100 chars
  "email": "user@example.com",// string, max 255 chars, unique, nullable
  "password_hash": "...",     // string, max 255 chars, nullable
  "is_guest": false,          // boolean, default false
  "guest_id": null,           // string, max 100 chars, unique, nullable
  "created_at": "2025-10-23T12:00:00" // datetime
}
```

**Tipos de usuarios:**

1. **Usuario Guest:**
```javascript
{
  "id_user": 14,
  "user_name": "Guest User",
  "email": null,
  "password_hash": null,
  "is_guest": true,
  "guest_id": "guest_a1b2c3d4-e5f6-7890-abcd-ef1234567890_1729707600",
  "created_at": "2025-10-23T12:00:00"
}
```

2. **Usuario Registrado:**
```javascript
{
  "id_user": 15,
  "user_name": "John Doe",
  "email": "john@example.com",
  "password_hash": "$2b$12$...",
  "is_guest": false,
  "guest_id": null,
  "created_at": "2025-10-23T12:30:00"
}
```

### Cart Item Model

```javascript
{
  "id_cart": 1,
  "id_user": 15,
  "id_product": 5,
  "quantity": 2,
  "added_date": "2025-10-23T12:00:00"
}
```

---

## Códigos de Error

### HTTP Status Codes

| Código | Nombre | Descripción |
|--------|--------|-------------|
| 200 | OK | La solicitud fue exitosa |
| 201 | Created | El recurso fue creado exitosamente |
| 400 | Bad Request | Datos de entrada inválidos o faltantes |
| 401 | Unauthorized | Token de autenticación faltante o inválido |
| 403 | Forbidden | Sin permisos para acceder al recurso |
| 404 | Not Found | Recurso no encontrado |
| 409 | Conflict | Conflicto con el estado actual (ej: email duplicado) |
| 500 | Internal Server Error | Error del servidor |

### Mensajes de Error Comunes

#### Autenticación

| Mensaje | Causa | Solución |
|---------|-------|----------|
| `Token missing` | No se envió el header Authorization | Agregar header `Authorization: Bearer <token>` |
| `Invalid or expired token` | Token inválido o expirado | Obtener nuevo token haciendo login |

#### Validación

| Mensaje | Causa | Solución |
|---------|-------|----------|
| `guest_id is required` | Falta el parámetro guest_id | Incluir guest_id en el body |
| `email and password are required` | Faltan credenciales | Incluir email y password |
| `Invalid email format` | Email con formato incorrecto | Verificar formato del email |

#### Conflictos

| Mensaje | Causa | Solución |
|---------|-------|----------|
| `Email already registered` | El email ya existe | Usar login en lugar de registro |
| `Invalid credentials` | Email o contraseña incorrectos | Verificar credenciales |

---

## Ejemplos de Flujos

### Flujo 1: Usuario Nuevo (Guest → Registro)

```mermaid
sequenceDiagram
    participant App
    participant API
    participant DB

    Note over App: Usuario instala la app
    
    App->>App: Generar guest_id único
    App->>API: POST /api/guest/create
    API->>DB: Crear usuario guest
    DB-->>API: user_id: 14
    API-->>App: user_id: 14, is_guest: true
    
    Note over App: Usuario agrega productos
    
    App->>API: POST /add-to-cart (user_id: 14)
    API->>DB: Guardar item en carrito
    DB-->>API: OK
    API-->>App: success: true
    
    Note over App: Usuario decide registrarse
    
    App->>API: POST /api/auth/register (con guest_id)
    API->>DB: Crear usuario real
    API->>DB: Fusionar carrito (guest → real)
    API->>DB: Eliminar guest
    DB-->>API: OK
    API-->>App: token, cart_migrated: true, cart_items_count: 3
    
    Note over App: Usuario autenticado con carrito intacto
```

**Código de ejemplo (Kotlin):**

```kotlin
// 1. Al instalar la app
val guestId = "guest_${UUID.randomUUID()}_${System.currentTimeMillis()}"
sharedPrefs.edit().putString("guest_id", guestId).apply()

val guestResponse = apiService.createGuest(GuestRequest(guestId))
sharedPrefs.edit().putInt("user_id", guestResponse.user_id).apply()

// 2. Usuario agrega productos al carrito
apiService.addToCart(AddToCartRequest(
    id_user = sharedPrefs.getInt("user_id", 0),
    id_product = productId,
    quantity = 1
))

// 3. Usuario se registra
val registerResponse = apiService.register(RegisterRequest(
    email = email,
    password = password,
    user_name = userName,
    guest_id = sharedPrefs.getString("guest_id", null)
))

// Guardar token y limpiar guest_id
sharedPrefs.edit()
    .putString("auth_token", registerResponse.token)
    .putInt("user_id", registerResponse.user_id ?: 0)
    .remove("guest_id")
    .apply()

println("Carrito fusionado: ${registerResponse.cart_items_count} items")
```

---

### Flujo 2: Usuario Existente (Guest → Login)

```mermaid
sequenceDiagram
    participant App
    participant API
    participant DB

    Note over App: Usuario en nuevo dispositivo
    
    App->>App: Generar guest_id único
    App->>API: POST /api/guest/create
    API->>DB: Crear usuario guest
    DB-->>API: user_id: 16
    API-->>App: user_id: 16, is_guest: true
    
    Note over App: Usuario agrega productos
    
    App->>API: POST /add-to-cart (user_id: 16)
    API->>DB: Guardar item en carrito
    DB-->>API: OK
    API-->>App: success: true
    
    Note over App: Usuario hace login con cuenta existente
    
    App->>API: POST /api/auth/login (con guest_id)
    API->>DB: Validar credenciales
    API->>DB: Fusionar carrito (guest → usuario real)
    API->>DB: Eliminar guest
    DB-->>API: OK
    API-->>App: token, cart_migrated: true, cart_items_count: 2
    
    Note over App: Carrito del dispositivo fusionado con cuenta
```

**Código de ejemplo (Kotlin):**

```kotlin
// 1. Usuario en nuevo dispositivo
val guestId = "guest_${UUID.randomUUID()}_${System.currentTimeMillis()}"
sharedPrefs.edit().putString("guest_id", guestId).apply()

val guestResponse = apiService.createGuest(GuestRequest(guestId))
sharedPrefs.edit().putInt("user_id", guestResponse.user_id).apply()

// 2. Agregar productos
apiService.addToCart(AddToCartRequest(
    id_user = sharedPrefs.getInt("user_id", 0),
    id_product = productId,
    quantity = 2
))

// 3. Login con cuenta existente
val loginResponse = apiService.login(LoginRequest(
    email = email,
    password = password,
    guest_id = sharedPrefs.getString("guest_id", null)
))

// Guardar datos de usuario
sharedPrefs.edit()
    .putString("auth_token", loginResponse.token)
    .putInt("user_id", loginResponse.user_id ?: 0)
    .putString("user_name", loginResponse.user_name)
    .remove("guest_id")
    .apply()

println("Bienvenido de vuelta ${loginResponse.user_name}!")
println("Items del nuevo dispositivo fusionados: ${loginResponse.cart_items_count}")
```

---

### Flujo 3: Fusión Manual de Carrito

```mermaid
sequenceDiagram
    participant App
    participant API
    participant DB

    Note over App: Usuario ya autenticado, pero tiene guest_id guardado
    
    App->>API: POST /api/cart/merge (con token y guest_id)
    API->>API: Validar token
    API->>DB: Buscar guest por guest_id
    API->>DB: Fusionar carrito
    API->>DB: Eliminar guest
    DB-->>API: OK
    API-->>App: merged_items: 5
    
    Note over App: Carrito fusionado manualmente
```

**Cuándo usar:**
- Cuando la fusión automática falló
- Cuando el usuario tiene un guest_id antiguo
- Para recuperación de carritos

**Código de ejemplo (Kotlin):**

```kotlin
// Si detectas que hay un guest_id pero el usuario está logueado
val guestId = sharedPrefs.getString("guest_id", null)
val token = sharedPrefs.getString("auth_token", null)

if (guestId != null && token != null) {
    try {
        val mergeResponse = apiService.mergeCart(
            authorization = "Bearer $token",
            request = MergeRequest(guestId)
        )
        
        if (mergeResponse.success) {
            // Limpiar guest_id después de fusión exitosa
            sharedPrefs.edit().remove("guest_id").apply()
            
            showMessage("${mergeResponse.merged_items} items recuperados!")
        }
    } catch (e: Exception) {
        Log.e("CartMerge", "Error fusionando carrito: ${e.message}")
    }
}
```

---

## Notas Importantes

### Seguridad

1. **Tokens JWT:**
   - Los tokens expiran en 30 días
   - Guardar en almacenamiento seguro (SharedPreferences encriptado en Android)
   - Nunca compartir tokens entre usuarios

2. **Contraseñas:**
   - Se hashean con bcrypt antes de guardarse
   - Nunca se retornan en las respuestas de API
   - Mínimo recomendado: 8 caracteres

3. **Guest IDs:**
   - Deben ser únicos por dispositivo
   - Se recomienda formato: `guest_<UUID>_<timestamp>`
   - No reutilizar después de fusión

### Mejores Prácticas

1. **Manejo de Errores:**
```kotlin
try {
    val response = apiService.register(request)
    if (response.success) {
        // Manejar éxito
    } else {
        // Mostrar mensaje de error al usuario
        showError(response.message)
    }
} catch (e: HttpException) {
    // Error HTTP (400, 401, 500, etc.)
    when (e.code()) {
        401 -> showError("Credenciales inválidas")
        409 -> showError("Email ya registrado")
        else -> showError("Error del servidor")
    }
} catch (e: IOException) {
    // Error de red
    showError("Error de conexión. Verifica tu internet")
}
```

2. **Reintentos:**
```kotlin
// Usar Retrofit con interceptor para reintentos
class RetryInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        var attempt = 0
        var response = chain.proceed(chain.request())
        
        while (!response.isSuccessful && attempt < 3) {
            attempt++
            Thread.sleep(1000L * attempt) // Backoff exponencial
            response = chain.proceed(chain.request())
        }
        
        return response
    }
}
```

3. **Caché:**
```kotlin
// Guardar datos del usuario localmente
data class UserCache(
    val userId: Int,
    val userName: String,
    val email: String,
    val token: String,
    val expiresAt: Long
)

fun cacheUser(user: UserCache) {
    val json = Gson().toJson(user)
    sharedPrefs.edit().putString("user_cache", json).apply()
}
```

### Performance

1. **Limpieza de Guests:**
   - Configurar cron job semanal
   - Ajustar `GUEST_CLEANUP_DAYS` según necesidad
   - Monitorear crecimiento de la tabla `user`

2. **Índices de Base de Datos:**
   - Verificar que los índices existan:
     - `idx_guest_id` en `user(guest_id)`
     - `idx_is_guest` en `user(is_guest)`
     - `idx_email` en `user(email)`

3. **Rate Limiting:**
   - Implementar límites de requests por IP
   - Prevenir ataques de fuerza bruta en login

---

## Recursos Adicionales

### Variables de Entorno

Configurar en el archivo `.env`:

```env
# Base de Datos
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=list_products

# JWT
JWT_SECRET_KEY=tu-clave-secreta-super-segura

# Flask
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_APP=app.py

# Servidor
SERVER_HOST=0.0.0.0
SERVER_PORT=5002

# CORS
ALLOWED_ORIGINS=*

# Guest Cleanup
GUEST_CLEANUP_DAYS=30
```

### Logging

El sistema registra automáticamente:
- Creación de usuarios guest
- Fusiones de carrito exitosas
- Limpiezas de guests
- Errores de autenticación

Los logs se pueden ver en la consola del servidor Flask.

### Contacto y Soporte

Para reportar bugs o solicitar features, contactar al equipo de desarrollo.

---

**Versión de la API:** 1.0  
**Última actualización:** 2025-10-23
