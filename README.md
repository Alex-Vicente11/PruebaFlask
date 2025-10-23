# 🛒 PruebaFlask - E-commerce Backend API

Backend Flask para aplicación de e-commerce con sistema de usuarios anónimos y fusión automática de carritos.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Tabla de Contenidos

- [Características](#características)
- [Inicio Rápido](#inicio-rápido)
- [Documentación](#documentación)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Desarrollo](#desarrollo)
- [Arquitectura](#arquitectura)
- [Seguridad](#seguridad)
- [Contribuir](#contribuir)

---

## ✨ Características

### Sistema de Usuarios Anónimos
- ✅ **Uso sin registro**: Los usuarios pueden usar la app inmediatamente
- ✅ **Carritos persistentes**: Los items del carrito se mantienen al registrarse
- ✅ **Fusión automática**: El carrito se fusiona automáticamente al hacer login/registro
- ✅ **Conversión sin fricción**: Experiencia fluida de guest a usuario registrado

### Funcionalidades
- 🔐 Autenticación JWT
- 🛒 Gestión de carritos de compra
- 📦 CRUD completo de productos
- 👤 Gestión de usuarios
- 🧹 Limpieza automática de usuarios antiguos
- 🔒 Seguridad con bcrypt y validaciones

---

## 🚀 Inicio Rápido

### Prerequisitos

- Python 3.9+
- MySQL 5.7+
- pip y virtualenv

### Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd PruebaFlask
```

2. **Crear entorno virtual**
```bash
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

5. **Ejecutar migraciones**

**Opción A - Script Python (Recomendado para Windows):**
```bash
python3 run_migration.py
```

**Opción B - MySQL CLI (Linux/macOS):**
```bash
mysql -u root list_products < migrations/001_add_guest_support.sql
```

**Opción C - Windows CMD:**
```cmd
mysql -u root list_products < migrations\001_add_guest_support.sql
```

**Opción D - MySQL Workbench:**
- Abrir MySQL Workbench
- Conectar al servidor
- Abrir el archivo `migrations/001_add_guest_support.sql`
- Ejecutar con el botón "Execute" (⚡) o `Ctrl + Shift + Enter`

6. **Poblar base de datos (opcional)**
```bash
python3 seed_database.py --clean
```

7. **Iniciar servidor**
```bash
python3 app.py
```

El servidor estará disponible en `http://localhost:5002`

---

## 📚 Documentación

### 📖 Guías Principales

| Documento | Descripción | Tamaño |
|-----------|-------------|--------|
| **[API Documentation](API_DOCUMENTATION.md)** | Documentación completa de todos los endpoints | 26 KB |
| **[Android Integration](ANDROID_INTEGRATION.md)** | Guía paso a paso para integración Android | 31 KB |
| **[Development Guide](DEVELOPMENT_GUIDE.md)** | Guía de desarrollo y seeding de datos | 16 KB |
| **[Final Summary](RESUMEN_FINAL.md)** | Resumen ejecutivo del proyecto | 15 KB |

### 📋 Documentos de Planificación

- [Plan de Usuarios Anónimos](PLAN_USUARIOS_ANONIMOS.md) - Plan técnico detallado (26 KB)
- [README de Continuación](README_CONTINUACION.md) - Resumen del sistema (8 KB)
- [Checklist de Inicio](CHECKLIST_INICIO.md) - Guía de inicio rápido (8 KB)

---

## 🔌 API Endpoints

### Usuarios Guest

```http
POST /api/guest/create
```
Crea un usuario invitado para usar la app sin registro.

**[Ver documentación completa →](API_DOCUMENTATION.md#post-apiguestcreate)**

### Autenticación

```http
POST /api/auth/register   # Registrar usuario con fusión de carrito
POST /api/auth/login      # Login con fusión de carrito
```

**[Ver documentación completa →](API_DOCUMENTATION.md#endpoints-de-autenticación)**

### Carrito

```http
POST /add-to-cart         # Agregar item al carrito
POST /api/cart/merge      # Fusión manual de carrito (requiere auth)
GET  /cart/user/:id       # Obtener items del carrito
```

**[Ver documentación completa →](API_DOCUMENTATION.md#endpoints-de-carrito)**

### Administración

```http
DELETE /api/guest/cleanup  # Limpiar guests antiguos (requiere auth)
```

**[Ver documentación completa →](API_DOCUMENTATION.md#endpoints-de-administración)**

---

## 🧪 Testing

### Ejecutar Tests Unitarios

```bash
# Todos los tests
pytest test_guest_auth.py -v

# Tests específicos
pytest test_guest_auth.py::TestGuestAuthSystem::test_create_guest_user -v

# Con cobertura
pytest --cov=app --cov-report=html test_guest_auth.py
```

### Tests Manuales con Datos de Prueba

```bash
# Poblar base de datos con datos de prueba
python3 seed_database.py --clean

# Credenciales de prueba
# Email: test1@example.com | Password: password123
# Email: admin@test.com    | Password: admin123
```

**[Ver guía completa de testing →](DEVELOPMENT_GUIDE.md#testing)**

---

## 🛠️ Desarrollo

### Estructura del Proyecto

```
PruebaFlask/
├── app.py                      # Aplicación principal Flask
├── auth_utils.py              # Utilidades de autenticación JWT
├── seed_database.py           # Script de poblado de datos
├── test_guest_auth.py         # Tests unitarios
│
├── migrations/                # Migraciones de base de datos
│   └── 001_add_guest_support.sql
│
├── templates/                 # Templates HTML
├── static/                    # Archivos estáticos
│
├── .env                       # Variables de entorno (no comiteado)
├── .env.example              # Template de variables
├── .gitignore                # Archivos a ignorar
├── requirements.txt          # Dependencias Python
│
└── docs/                     # Documentación
    ├── API_DOCUMENTATION.md
    ├── ANDROID_INTEGRATION.md
    ├── DEVELOPMENT_GUIDE.md
    └── RESUMEN_FINAL.md
```

### Workflow de Desarrollo

1. **Crear rama de feature**
```bash
git checkout -b feature/mi-feature
```

2. **Poblar base de datos**
```bash
python3 seed_database.py --clean
```

3. **Desarrollar y probar**
```bash
# Iniciar servidor
python3 app.py

# En otra terminal, ejecutar tests
pytest test_guest_auth.py -v
```

4. **Limpiar datos de prueba**
```bash
python3 seed_database.py --only-clean
```

**[Ver guía completa de desarrollo →](DEVELOPMENT_GUIDE.md)**

---

## 🏗️ Arquitectura

### Stack Tecnológico

**Backend:**
- Flask 3.0.0 - Framework web
- Peewee - ORM para MySQL
- PyJWT - Autenticación con tokens
- bcrypt - Hash de contraseñas
- Flask-CORS - Manejo de CORS

**Base de Datos:**
- MySQL 5.7+
- 3 tablas principales: `user`, `products`, `cart`

**Testing:**
- pytest - Framework de testing
- pytest-flask - Testing de Flask

### Flujo de Usuario Anónimo

```
1. Usuario instala app
   ↓
2. App genera UUID único (guest_id)
   ↓
3. POST /api/guest/create → Obtiene user_id
   ↓
4. Usuario agrega productos al carrito
   ↓
5. Usuario decide registrarse/login
   ↓
6. POST /api/auth/register (con guest_id)
   ↓
7. Backend fusiona carrito automáticamente
   ↓
8. Usuario registrado con carrito intacto ✅
```

**[Ver arquitectura detallada →](API_DOCUMENTATION.md#introducción)**

---

## 🔒 Seguridad

### Medidas Implementadas

- ✅ **JWT Tokens**: Autenticación stateless con expiración de 30 días
- ✅ **Password Hashing**: bcrypt con salt único por password
- ✅ **Email Validation**: Validación de formato de email
- ✅ **Input Sanitization**: Validación de todos los inputs
- ✅ **CORS**: Configurado para permitir requests desde app móvil
- ✅ **Environment Variables**: Credenciales en .env (no comiteado)

### Mejores Prácticas

```python
# ❌ NO HACER
password = "password123"  # Plain text
db_password = "Relic11&"  # Hardcoded

# ✅ HACER
password_hash = hash_password(password)  # Hashed
db_password = os.getenv('DB_PASSWORD')   # Environment variable
```

**[Ver guía de seguridad →](API_DOCUMENTATION.md#seguridad)**

---

## 📊 Base de Datos

### Modelo de Datos

#### Tabla: `user`
```sql
CREATE TABLE user (
  id_user INT PRIMARY KEY,
  user_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) UNIQUE,
  password_hash VARCHAR(255),
  is_guest BOOLEAN DEFAULT FALSE,
  guest_id VARCHAR(100) UNIQUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Tabla: `products`
```sql
CREATE TABLE products (
  id_product INT PRIMARY KEY,
  product VARCHAR(100) NOT NULL,
  price DECIMAL(10,2) NOT NULL
);
```

#### Tabla: `cart`
```sql
CREATE TABLE cart (
  id_cart INT AUTO_INCREMENT PRIMARY KEY,
  id_user INT,
  id_product INT,
  quantity INT DEFAULT 1,
  added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_user) REFERENCES user(id_user),
  FOREIGN KEY (id_product) REFERENCES products(id_product)
);
```

**[Ver modelos completos →](API_DOCUMENTATION.md#modelos-de-datos)**

---

## 🤝 Contribuir

### Para el Equipo Backend

1. Fork el repositorio
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

### Para el Equipo Android

Seguir la guía completa de integración:

**[Android Integration Guide →](ANDROID_INTEGRATION.md)**

Incluye:
- ✅ Setup completo de Retrofit
- ✅ Arquitectura MVVM
- ✅ 15+ clases de ejemplo
- ✅ Manejo de errores
- ✅ Tests unitarios

---

## 📞 Recursos Adicionales

### Enlaces Útiles

- [Documentación de Flask](https://flask.palletsprojects.com/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [Peewee ORM](http://docs.peewee-orm.com/)
- [Retrofit (Android)](https://square.github.io/retrofit/)

### Comandos Útiles

```bash
# Iniciar servidor de desarrollo
python3 app.py

# Ejecutar tests
pytest test_guest_auth.py -v

# Poblar base de datos con datos de prueba
python3 seed_database.py --clean

# Limpiar datos de prueba
python3 seed_database.py --only-clean

# Ver logs en tiempo real
tail -f app.log

# Conectar a MySQL
mysql -u root list_products
```

---

## 📈 Estado del Proyecto

| Aspecto | Estado |
|---------|--------|
| **Backend API** | ✅ Completo |
| **Autenticación** | ✅ Implementada |
| **Tests Unitarios** | ✅ 25+ tests |
| **Documentación** | ✅ Completa |
| **Integración Android** | 📱 Lista para integrar |

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

---

## 👥 Equipo

**Backend:** Sistema de usuarios anónimos implementado  
**Frontend:** Listo para integración Android  

---

## 🎉 Agradecimientos

- Flask community
- PyJWT library
- bcrypt library
- Todos los contributors

---

**📍 Versión:** 1.0.0  
**📅 Última actualización:** 2025-10-23  
**🚀 Estado:** Listo para producción

---

<div align="center">
  
**[⬆ Volver arriba](#-pruebaflask---e-commerce-backend-api)**

Desarrollado con ❤️ y ☕

</div>
