from flask import Flask, render_template, request, url_for, redirect, jsonify
import pymysql

from peewee import *
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Import authentication utilities
from auth_utils import hash_password, verify_password, generate_jwt, decode_jwt, require_auth
from email_validator import validate_email, EmailNotValidError
def get_html_base (body):

     return """<!DOCTYPE html>
        <html lang="es">
        <head>
        <meta charset="UTF-8">
        <title>Inversor trifásico</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-4Q6Gf2aSP4eDXB8Miphtr37CMZZQ5oXLH2yaXMJ2w8e2ZtHTl7GptT4jmndRuHDT" crossorigin="anonymous">
        <link rel="stylesheet" href="style.css">
        </head>
        <body 
              """ + body + """
        </body>
        </html>
        """

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('ALLOWED_ORIGINS', '*'),
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configuracion de la DB con Peewee usando variables de entorno
db = MySQLDatabase(
    os.getenv('DB_NAME', 'list_products'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 3306)),
    ssl={'ssl_disabled': True}  # Usar por error 2026 (HY000): TLS/SSL
)

# Configuración MySQL usando variables de entorno
def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        passwd=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'list_products'),
        cursorclass=pymysql.cursors.DictCursor
    )


# Modelo base
class BaseModel(Model):
    class Meta: 
        database = db


# MODELOS PEEWEE (conversion de mysql a peewee)

# Modelo usuario
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

    def to_dict(self):
        # convierte el objeto a diccionario para JSON
        return {
            'id_user': self.id_user,
            'user_name': self.user_name,
            'email': self.email,
            'is_guest': self.is_guest,
            'guest_id': self.guest_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    

#Model producto
class Product(BaseModel):
    id_product = IntegerField(primary_key=True)
    product = CharField(max_length=100, null=False)
    price = DecimalField(decimal_places=2, null=False)

    class Meta:
        table_name = 'products'

    def to_dict(self):
        return {
            'id_product': self.id_product,
            'product': self.product,
            'price': float(self.price)
        }


# Modelo carrito
class Cart(BaseModel):
    id_cart = AutoField(primary_key=True)
    id_user = ForeignKeyField(User, column_name='id_user', backref='cart_items')
    id_product = ForeignKeyField(Product, column_name='id_product', backref='in_carts')
    quantity = IntegerField(default=1)
    added_date = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'cart'


def to_dict(self):
    return {
        'id_cart': self.id_cart,
        'id_user': self.id_user.id_user,
        'id_product': self.id_product.id_product,
        'quantity': self.quantity,
        'added_date': self.added_date.isoformat() if self.added_date else None,
        'product_name': self.id_product.product,
        'product_price': float(self.id_product.price),
        'subtotal': float(self.id_product.price * self.quantity)
    } 


# Conexion automatica a la BD
@app.before_request
def before_request():
    if db.is_closed():
        db.connect()

@app.teardown_request
def teardown_request(exception):
    if not db.is_closed():
        db.close()


# ===============
# ERROR HANDLERS
# ===============

@app.errorhandler(401)
def unauthorized_error(error):
    """Manejo personalizado de errores 401 Unathorized"""
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Invalid or expired token. Please login again',
        'code': 401
    }), 401


@app.errorhandler(403)
def forbidden_error(error):
    """Manejo personalizado de errores 403 Forbidden"""
    return jsonify({
        'success': False,
        'error': 'Forbidden',
        'message': 'You do not have permission to access this resource',
        'code': 403
    }), 403


@app.errorhandler(404)
def not_found_error(error):
    """Manejo personalizado de errores 404 Not Found"""
    return jsonify({
        'success': False,
        'error': 'Not Found',
        'message': 'The requested resource was not found.',
        'code': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Manejo personalizado de errores 500 Internal Server Error"""
    return jsonify({
        'success': False,
        'error': 'Internal Server Error',
        'message': 'An internal server error ocurred. Please try again later',
        'code': 500
    }), 500


# ====================
# GUEST USER FUNCTIONS
# ====================

def merge_cart(guest_user_id, real_user_id):
    """
    Fusiona el carrito de un usuario guest con un usuario real

    Args:
        guest_user_id (int): ID del usuario invitado
        real_user_id (int): ID del usuario real registrado

    Returns:
        dict: {'merged_count': int, 'updated_count': int, 'total_items': int}
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

        app.logger.info(f"Cart merged: {merged_count} moved, {updated_count} updated, guest user {guest_user_id} deleted")

        return {
            'merged_count': merged_count,
            'updated_count': updated_count,
            'deleted_count': deleted_count,
            'total_items': merged_count + updated_count
        }

    except Exception as e:
        app.logger.error(f"Error merging cart: {str(e)}")
        raise



# =============
# HEALTH CHECK
# =============

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check para verificar que el API esta funcionando

    Response:
        {
            "status": "ok",
            "timestamp": "2025-11-01T12:00:00",
            "version": "1.0.0",
            "database": "connected"
        }
    """

    try:
        db_connected = not db.is_closed()

        # Intentar query simple para verificar conexion real
        if db_connected:
            try:
                User.select().limit(1).count()
                db_status = 'connected'
                except Exception:
                    db_status = 'error'
        else:
            db_status = 'disconnected'

        status = 'ok' if db_status == 'connected' else 'degraded'

        return jsonify({
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'datebase': db_status
        }), 200 if status == 'ok' else 503

    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

# ====================
# GUEST USER ENDPOINTS
# ====================

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


@app.route('/api/guest/cleanup', methods=['DELETE'])
def cleanup_old_guests():
    """
    Eliminar usuarios guest antiguos (inactivos por mÃ¡s de X dias)
    
    NO requiere autenticaciÃ³n - puede ejecutarse desde cron jobs
    
    Query Parameters:
        - days: Dias de antigÃ¼edad (default: 30)
        - dry_run: Si es 'true', solo muestra cuantos se eliminaran
    """
    try:
        # Obtener parÃ¡metros
        days = int(request.args.get('days', 30))
        dry_run = request.args.get('dry_run', 'false').lower() == 'true'
        
        # ValidaciÃ³n
        if days < 1:
            return jsonify({
                'success': False,
                'error': 'El parametro days debe ser mayor a 0'
            }), 400
        
        # Calcular fecha lÃ­mite
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Buscar guests antiguos
        old_guests = User.select().where(
            (User.is_guest == True) &
            (User.created_at < cutoff_date)
        )
        
        count = old_guests.count()
        
        # Modo dry_run: solo mostrar informaciÃ³n
        if dry_run:
            guest_info = []
            for guest in old_guests:
                cart_count = Cart.select().where(Cart.id_user == guest.id_user).count()
                days_old = (datetime.now() - guest.created_at).days if guest.created_at else 0
                
                guest_info.append({
                    'id_user': guest.id_user,
                    'guest_id': guest.guest_id,
                    'created_at': guest.created_at.isoformat() if guest.created_at else None,
                    'days_old': days_old,
                    'cart_items': cart_count
                })
            
            return jsonify({
                'success': True,
                'message': f'Se eliminaran {count} usuarios guest',
                'count': count,
                'dry_run': True,
                'cutoff_date': cutoff_date.isoformat(),
                'days_threshold': days,
                'guests': guest_info
            }), 200
        
        # Modo real: eliminar guests y carritos
        deleted_carts = 0
        deleted_users = 0
        deleted_guests_info = []
        
        for guest in old_guests:
            # Eliminar carrito
            cart_count = Cart.delete().where(Cart.id_user == guest.id_user).execute()
            deleted_carts += cart_count
            
            deleted_guests_info.append({
                'id_user': guest.id_user,
                'guest_id': guest.guest_id,
                'cart_items_deleted': cart_count
            })
            
            # Eliminar usuario
            guest.delete_instance()
            deleted_users += 1
            
            app.logger.info(f'Deleted old guest {guest.id_user} ({cart_count} items)')
        
        return jsonify({
            'success': True,
            'message': f'Limpieza completada: {deleted_users} guests eliminados',
            'deleted_users': deleted_users,
            'deleted_cart_items': deleted_carts,
            'days_threshold': days,
            'cutoff_date': cutoff_date.isoformat(),
            'guests_deleted': deleted_guests_info
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Parametro invalido: {str(e)}'
        }), 400
    except Exception as e:
        app.logger.error(f'Error in cleanup: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Error al limpiar guests: {str(e)}'
        }), 500


# ====================
# AUTHENTICATION ENDPOINTS
# ====================

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

        # Validar email (sin verificación DNS para desarrollo)
        try:
            validate_email(email, check_deliverability=False)
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

        hashed_password = hash_password(password)

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


@app.route('/api/auth/validate', methods=['GET'])
@require_auth
def validate_token():
    """
    Validar si el token JWT es valido

    Headers:
        Authorization: Bearer <token>

    Reponse:
        {
            "success": true,
            "valid": true,
            "user_id": 123,
            "user_name": "John Doe",
            "email": "user@example.com",
            "is_guest": false,
            "message": "Token is valid"
        }
    """
    try: 
        user_id = request.user_id

        user = User.get_or_none(User.id_user == user_id)

        if not user: 
            return jsonify({
                'success': False,
                'valid': False,
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'valid': True,
            'user_id': user.id_user,
            'user_name': user.user_name,
            'email': user.email,
            'is_guest': user.is_guest,
            'message': 'Token is valid'
        }), 200

    except Exception as e:
        app.logger.error(f"Error validating token: {str(e)}")
        return jsonify({
            'success': False,
            'valid': False,
            'message': f'Error validating token {str(e)}'
        }), 500


@app.route('/api/auth/profile', methods=['GET', 'PUT'])
@require_auth
def user_profile():
    """
    GET: Obtener perfil de usuario autenticado
    PUT: Actualizar perfil del usuario autenticado

    Headers: 
        Authorization: Bearer <token>

    PUT Request JSON:
        {
            "user_name": "New Name"
        }
    """

    try:
        user_id = request.user_id
        user = User.get_or_none(User.id_user == user_id)

        if not user: 
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        if request.method == 'GET':
            return jsonify({
                'success': True,
                'user': {
                    'id_user': user.id_user,
                    'user_name': user.user_name,
                    'email': user.email,
                    'is_guest': user.is_guest,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
            }), 200

        elif request.method == 'PUT':
            data = request.get_json()

            if not data: 
                return jsonify({
                    'success': False,
                    'message': 'No data provided'
                }), 400

            updated = False

            if not updated: 
                return jsonify({
                    'success': False,
                    'message': 'No valid data to update'
                }), 400

            user.save()

            return jsonify({
                'success': True, 
                'message': 'Profile updated successfully',
                'user': {
                    'id_user': user.id_user,
                    'user_name': user.user_name,
                    'email': user.email,
                    'is_guest': user.is_guest
                }
            }), 200

    except Exception as e:
        app.logger.error(f'Error in profile endpoint: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500



# ===================================
# ENDPOINTS PROTEGIDOS DEL CARRITO
# ===================================

@app.route('/api/cart', methods=['GET'])
@require_auth
def get_cart():
    """
    Obtener carrito del usuario autenticado
    Requiere JWT token en header: Authorization: Bearer TOKEN
    """
    try:
        user_id = request.user_id  # Del decorator @require_auth
        
        # Obtener items del carrito con informaciÃ³n del producto
        cart_items = (Cart
            .select(Cart, Product)
            .join(Product)
            .where(Cart.id_user == user_id)
            .order_by(Cart.added_date.desc()))
        
        items = []
        total = 0
        
        for item in cart_items:
            subtotal = item.quantity * float(item.id_product.price)
            total += subtotal
            
            items.append({
                'id_cart': item.id_cart,
                'id_product': item.id_product.id_product,
                'name': item.id_product.product,
                'price': float(item.id_product.price),
                'quantity': item.quantity,
                'subtotal': subtotal,
                'added_date': item.added_date.isoformat() if item.added_date else None
            })
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'items': items,
            'total': total,
            'items_count': len(items)
        }), 200
        
    except Exception as e:
        app.logger.error(f'Error getting cart: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Error al obtener carrito: {str(e)}'
        }), 500



@app.route('/api/cart/items', methods=['GET'])
@require_auth
def get_cart_items():
    """
    Obtener items del carrito del usuario autenticado (version detallada)
    Usa el user_id del token JWT

    Headers:
        Authorization: Bearer <token>

    Response: 
        {
            "success": true,
            "items": [
                {
                    "id_cart": 1,
                    "product": {
                        "id_product": 5, 
                        "product": "Product Name",
                        "price": 99.99
                    },
                    "quantity": 2,
                    "subtotal": 199.98,
                    "added_date": "2025-11-01T12:00:00"
                }
            ],
            "total": 199.98,
            "items_count": 1
        }
    """
    try:
        user_id = request.user_id

        cart_items = (Cart
            .select(Cart, Product)
            .join(Product)
            .where(Cart.id_user == user_id)
            .order_by(Cart.added_date.desc())    
        )

        items = []
        total = 0

        for item in cart_items:
            subtotal = item.quantity * float(item.id_product.price)
            total += subtotal

            items.append({
                'id_cart': item.id_cart,
                'product': {
                    'id_product': item.id_product.id_product,
                    'product': item.id_product.product,
                    'price': float(item.id_product.price)
                },
                'quantity': item.quantity,
                'subtotal': subtotal,
                'added_date': item.added_date.isoformat() if item.added_date else None
            })

        return jsonify({
            'success': True,
            'items': itemns,
            'total': total,
            'items_count': len(items)
        }), 200

    except Exception as e:
        app.logger.error(f'Error getting cart items: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Error al obtener items: {str(e)}'
        }), 500


@app.route('/api/cart/count', methods=['GET'])
@require_auth
def get_cart_count():
    """
    Obtener solo el conteo de items en el carrito (más rápido)

    Headers: 
        Authorization: Bearer <token>

    Response: 
        {
            "success": true,
            "count": 5,
            "unique_products": 3
        }
    """

    try: 
        user_id = request.user_id

        total_items = Cart.select(fn.SUM(Cart.quantity)).where(
            Cart.id_user == user_id
        ).scalar() or 0

        unique_products = Cart.select().where(Cart.id_user == user_id).count()

        return jsonify({
            'success': True,
            'count': int(total_items),
            'unique_products': unique_products
        }), 200

    except Exception as e:
        app.logger.error(f'Error getting cart count: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500


@app.route('/api/cart/check/<int: product_id>', methods=['GET'])
@require_auth
def check_product_in_cart(product_id):
    """
    Verificar si un producto esta en el carrito del usuario autenticado

    Headers:
        Authorization: Bearer <token>

    Response:
        {
            "success": true,
            "exists": true,
            "cart_item": {
                "id_cart": 5,
                "id_product": 10,
                "quantity": 2
            }
        }
    """
    try:
        user_id = request.user_id

        cart_item = Cart.get_or_none(
            (Cart.id_user == user_id) &
            (Cart.id_product == product_id)
        )

        if cart_item:
            return jsonify({
                'success': True,
                'exists': True,
                'cart_item': {
                    'id_cart': cart_item.id_cart,
                    'id_product': product_id,
                    'quantity': cart_item.quantity
                }
            }), 200
        else:
            return jsonify({
                'success': True,
                'exists': False,
                'cart_item': None
            }), 200

    except Exception as e:
        app.logger.error(f'Error checking cart: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Error checking cart: {str(e)}'
        }), 500


@app.route('/api/cart/add', methods=['POST'])
@require_auth
def add_to_cart_protected():
    """
    Agregar producto al carrito (version protegida)
    Usa el user_id del token JWT, no del body
    
    Request JSON:
    {
        "id_product": 1,
        "quantity": 2
    }
    """
    try:
        user_id = request.user_id  # Del token, no del body (mÃ¡s seguro)
        data = request.get_json()
        
        if not data or 'id_product' not in data:
            return jsonify({
                'success': False,
                'error': 'id_product es requerido'
            }), 400
        
        id_product = int(data['id_product'])
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1:
            return jsonify({
                'success': False,
                'error': 'Cantidad debe ser mayor a 0'
            }), 400
        
        # Verificar que el producto existe
        product = Product.get_or_none(Product.id_product == id_product)
        if not product:
            return jsonify({
                'success': False,
                'error': 'Producto no encontrado'
            }), 404
        
        # Verificar si ya esta en el carrito
        existing = Cart.get_or_none(
            (Cart.id_user == user_id) &
            (Cart.id_product == id_product)
        )
        
        if existing:
            # Actualizar cantidad
            existing.quantity += quantity
            existing.save()
            
            return jsonify({
                'success': True,
                'message': 'Cantidad actualizada',
                'cart_item': {
                    'id_cart': existing.id_cart,
                    'id_product': id_product,
                    'quantity': existing.quantity
                }
            }), 200
        else:
            # Crear nuevo item
            new_item = Cart.create(
                id_user=user_id,
                id_product=id_product,
                quantity=quantity
            )
            
            return jsonify({
                'success': True,
                'message': 'Producto agregado al carrito',
                'cart_item': {
                    'id_cart': new_item.id_cart,
                    'id_product': id_product,
                    'quantity': quantity
                }
            }), 201
            
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'id_product y quantity deben ser numeros'
        }), 400
    except Exception as e:
        app.logger.error(f'Error adding to cart: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Error al agregar al carrito: {str(e)}'
        }), 500


@app.route('/api/cart/update', methods=['PUT'])
@require_auth
def update_cart_quantity_protected():
    """
    Actualizar cantidad de un producto en el carrito
    
    Request JSON:
    {
        "id_product": 1,
        "quantity": 5
    }
    """
    try:
        user_id = request.user_id
        data = request.get_json()
        
        if not data or 'id_product' not in data or 'quantity' not in data:
            return jsonify({
                'success': False,
                'error': 'id_product y quantity son requeridos'
            }), 400
        
        id_product = int(data['id_product'])
        quantity = int(data['quantity'])
        
        if quantity < 1:
            return jsonify({
                'success': False,
                'error': 'Cantidad debe ser mayor a 0'
            }), 400
        
        # Buscar item
        cart_item = Cart.get_or_none(
            (Cart.id_user == user_id) &
            (Cart.id_product == id_product)
        )
        
        if not cart_item:
            return jsonify({
                'success': False,
                'error': 'Producto no esta en el carrito'
            }), 404
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return jsonify({
            'success': True,
            'message': 'Cantidad actualizada',
            'cart_item': {
                'id_cart': cart_item.id_cart,
                'id_product': id_product,
                'quantity': quantity
            }
        }), 200
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'id_product y quantity deben ser numeros'
        }), 400
    except Exception as e:
        app.logger.error(f'Error updating cart: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Error al actualizar carrito: {str(e)}'
        }), 500


@app.route('/api/cart/remove', methods=['DELETE'])
@require_auth
def remove_from_cart_protected():
    """
    Eliminar producto del carrito
    
    Request JSON:
    {
        "id_product": 1
    }
    """
    try:
        user_id = request.user_id
        data = request.get_json()
        
        if not data or 'id_product' not in data:
            return jsonify({
                'success': False,
                'error': 'id_product es requerido'
            }), 400
        
        id_product = int(data['id_product'])
        
        # Buscar item en el carrito
        cart_item = Cart.get_or_none(
            (Cart.id_user == user_id) &
            (Cart.id_product == id_product)
        )
        
        if not cart_item:
            return jsonify({
                'success': False,
                'error': 'Producto no esta en el carrito'
            }), 404
        
        cart_item.delete_instance()
        
        return jsonify({
            'success': True,
            'message': 'Producto eliminado del carrito'
        }), 200
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'id_product debe ser un numero'
        }), 400
    except Exception as e:
        app.logger.error(f'Error removing from cart: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Error al eliminar del carrito: {str(e)}'
        }), 500



@app.route('/api/cart/clear', methods=['DELETE'])
@require_auth
def clear_cart():
    """
    Vaciar completamente el carrito del usuario autenticado
    """
    try:
        user_id = request.user_id
        
        deleted_count = Cart.delete().where(Cart.id_user == user_id).execute()
        
        return jsonify({
            'success': True,
            'message': f'Carrito vaciado: {deleted_count} items eliminados',
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        app.logger.error(f'Error clearing cart: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Error al vaciar carrito: {str(e)}'
        }), 500



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


# ====================
# LEGACY CART ENDPOINT (DEPRECATED)
# ====================

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart_legacy():
    """
    DEPRECADO: Usar /api/cart/add con autenticación JWT
    
    Este endpoint se mantiene SOLO para compatibilidad con vistas web HTML
    NO debe usarse desde Android (usar /api/cart/add)
    """
    try:
        # Detectar tipo de request
        data = request.get_json(silent=True)
        
        if data is not None:
            # Request JSON desde Android - RECHAZAR
            return jsonify({
                'success': False,
                'error': 'Este endpoint está deprecado. Use /api/cart/add con JWT token',
                'deprecated': True,
                'new_endpoint': '/api/cart/add',
                'documentation': 'https://docs.example.com/api/cart'
            }), 410  # 410 Gone - recurso deprecado
        
        # Si es formulario HTML, permitir (para vistas web)
        user_id = request.form.get('user_id')
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity', 1))
        
        if not user_id or user_id == 'None' or not product_id or product_id == 'None':
            return redirect(f'/cart-view?error=Debe seleccionar usuario y producto')
        
        user_id = int(user_id)
        product_id = int(product_id)
        
        # Validar usuario existe
        user_exists = User.get_or_none(User.id_user == user_id)
        if not user_exists:
            return redirect(url_for('cart_view', user_id=user_id, error='Usuario no encontrado'))
        
        # Validar producto existe
        product_exists = Product.get_or_none(Product.id_product == product_id)
        if not product_exists:
            return redirect(url_for('cart_view', user_id=user_id, error='Producto no encontrado'))
        
        # Buscar item existente
        carrito = Cart.get_or_none((Cart.id_user == user_id) & (Cart.id_product == product_id))
        
        if carrito:
            carrito.quantity += quantity
            carrito.save()
        else:
            carrito = Cart.create(id_user=user_id, id_product=product_id, quantity=quantity)
        
        return redirect(f'/cart-view?user_id={user_id}&success=true')
    
    except Exception as e:
        return redirect(f'/cart-view?error={str(e)}')


# ====================
# LEGACY CART ENDPOINTS (KEPT FOR WEB VIEWS)
# ====================

@app.route('/cart/user/<int:user_id>', methods=['GET'])
def get_cart_items_by_user(user_id):
    """
    LEGACY: Obtener items del carrito por user_id
    
    NOTA: Este endpoint NO está protegido y se mantiene solo para vistas web.
    Android debe usar /api/cart/items con JWT.
    """
    try:
        cart_items = Cart.select().where(Cart.id_user == user_id)

        if not cart_items.exists():
            return jsonify([]), 200
        
        result = []
        for cart_item in cart_items:
            product = Product.get_by_id(cart_item.id_product)
        
            result.append({
                'product': {
                    'id_product': product.id_product,
                    'product': product.product,
                    'price': float(product.price)
                },
                'quantity': cart_item.quantity,
                'addedDate': cart_item.added_date.strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/cart/<int:user_id>/<int:product_id>', methods=['GET'])
def get_cart_item(user_id, product_id):
    """
    LEGACY: Verificar si producto está en carrito
    
    Android debe usar /api/cart/check/<product_id> con JWT
    """
    try:
        carrito = Cart.get_or_none((Cart.id_user == user_id) & (Cart.id_product == product_id))

        if carrito:
            return jsonify({
                'id_cart': carrito.id_cart,
                'id_user': carrito.id_user.id_user,
                'id_product': carrito.id_product.id_product,
                'quantity': carrito.quantity
            }), 200
        else: 
            return jsonify(None), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/cart/<int:cart_id>', methods=['PUT'])
def update_cart_quantity(cart_id):
    """
    LEGACY: Actualizar cantidad por cart_id
    
    Android debe usar /api/cart/update con JWT
    """
    try:
        data = request.get_json()
        
        if not data or 'quantity' not in data:
            return jsonify({'success': False, 'error': 'Quantity requerida'}), 400
        
        quantity = int(data['quantity'])

        if quantity < 0:
            return jsonify({'success': False, 'error': 'Cantidad no puede ser negativa'}), 400
        
        cart_item = Cart.get_or_none(Cart.id_cart == cart_id)

        if not cart_item:
            return jsonify({'success': False, 'error': 'Item no encontrado'}), 404
        
        if quantity == 0:
            cart_item.delete_instance()
            return jsonify({
                'success': True,
                'message': 'Item eliminado del carrito'
            }), 200
        else: 
            cart_item.quantity = quantity
            cart_item.save()

            return jsonify({
                'success': True,
                'message': 'Cantidad actualizada',
                'data': {
                    'id_cart': cart_item.id_cart,
                    'id_user': cart_item.id_user.id_user,
                    'id_product': cart_item.id_product.id_product,
                    'quantity': cart_item.quantity
                }
            }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/cart/<int:cart_id>', methods=['DELETE'])
def delete_cart_item(cart_id):
    """
    LEGACY: Eliminar item por cart_id
    
    Android debe usar /api/cart/remove con JWT
    """
    try:
        cart_item = Cart.get_or_none(Cart.id_cart == cart_id)

        if not cart_item:
            return jsonify({'success': False, 'error': 'Item no encontrado'}), 404
        
        cart_item.delete_instance()

        return jsonify({
            'success': True,
            'message': 'Item eliminado del carrito'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    """
    LEGACY: Remover producto del carrito (para vistas web)
    """
    try:
        cart_id = request.form.get('cart_id')
        user_id = request.form.get('user_id')

        if not cart_id: 
            return redirect(f'/cart?user_id={user_id or ""}')
        
        remove_product = Cart.get_or_none(cart_id == Cart.id_cart)

        if remove_product:
            remove_product.delete_instance()

        return redirect(f'/cart?user_id={user_id}')
    
    except Exception as e:
        return redirect(f'/cart?user_id={user_id or ""}')


# CRUD para usuario (peewee)
# GET /users - Obtener todos los usuarios
@app.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.select()
        users_list = [{'id_user': user.id_user, 'user_name': user.user_name} for user in users]
        return jsonify(users_list), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# GET /users/<id> - Obtener un usuario por ID
@app.route('/users/<int:id_user>', methods=['GET'])
def get_user(id_user):
    try: 
        user = User.get_or_none(User.id_user == id_user)

        if user:
            return jsonify({'id_user': user.id_user, 'user_name': user.user_name}), 200
        else:
            return jsonify({'error': 'Usuario no encontrado'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# POST /users - crear un nuevo usuario
@app.route('/users', methods=['POST'])
def create_user():
    try: 
        data = request.get_json()

        if not data or 'user_name' not in data or not data['user_name'].strip():
            return jsonify({'error': 'Campo requerido: user_name no puede estar vacío'}), 400
        
        # Obtener el siguiente ID disponible (ya que no tienes AUTO_INCREMENT)
        max_id = User.select(fn.COALESCE(fn.MAX(User.id_user), 0).alias('max_id')).scalar()
        new_id = max_id + 1

        # Crear usuario con Peewee
        user = User.create(id_user=new_id, user_name=data['user_name'].strip())

        return jsonify({
            'message': 'Usuario creadp exitosamente',
            'id': user.id_user,
            'user_name': user.user_name 
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# PUT /users/<id> - actualizar usuario
@app.route('/users/<int:id_user>', methods=['PUT'])
def update_user(id_user):
    try: 
        data = request.get_json()

        if not data: 
            return jsonify({'error': 'No se enviaron datos'}), 400
        
        # Verificar si el usuario existe
        user = User.get_or_none(User.id_user == id_user)
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Validar y actualizar campos
        updated = False

        if 'user_name' in data and data['user_name'].strip():
            user.user_name = data['user_name'].strip()
            updated = True

        if not updated:
            return jsonify({'error': 'No se enviaron datos válidos para actualizar'}), 400
        
        user.save()
        return jsonify({'message': 'Usuario actualizado exitosamente'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

 
# DELETE /users/<id> - Eliminar usuario
@app.route('/users/<int:id_user>', methods=['DELETE'])
def delete_user(id_user):
    try:
        user = User.get_or_none(User.id_user == id_user)

        if not user:
            return jsonify({'error': 'El usuario no existe'}), 404
        
        user.delete_instance()
        return jsonify({'message': 'Usuario eliminado exitosamente'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# EndPoint (mantener compatibilidad)
@app.route('/usuarios')
def obtener_usuarios():
    try: 
        users = User.select()
        usuarios = [{'id': user.id_user, 'nombre': user.user_name} for user in users]
        return jsonify(usuarios)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# CRUD REST Endpoints para productos (peewee)
# GET /products - Obtener todos los productos
@app.route('/products', methods=['GET'])
def get_products():
    try:
        productos = Product.select()
        products_list = [{'id_product': products.id_product, 'product': products.product, 'price': products.price} for products in productos]
        return jsonify(products_list), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET /products/<id> - Obtener un producto por ID
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.get_or_none(Product.id_product == product_id)
        
        if product:
            return jsonify({'id_product': product.id_product, 'product': product.product, 'price': product.price}), 200
        else:
            return jsonify({'error': 'Producto no encontrado'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST /products - Crear un nuevo producto
@app.route('/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        print("Datos recibidos:", data)
        
        # Validacion de datos basicos
        if not data:
            return jsonify({'error': 'No se enviaron datos'}), 400
        
        if 'product' not in data or 'price' not in data:
            return jsonify({'error': 'Faltan campos requeridos: product, price'}), 400
        
        # Validación del producto
        if not data['product'] or not data['product'].strip():
            return jsonify({'error': 'El nombre del producto no puede estar vacío'}), 400
        
        # Validación del precio
        if data['price'] is None: 
            return jsonify({'error': 'El precio es requerido'}), 400
        
        print("Tipo de price:", type(data.get('price')))

        try:
            price = float(data['price'])
            if price <= 0:
                return jsonify({'error': 'El precio debe ser mayor a 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'El precio debe ser un número válido'}), 400
         
        # Obtener el siguiente ID
        max_id = Product.select(fn.COALESCE(fn.MAX(Product.id_product), 0).alias('max_id')).scalar()
        new_id = max_id + 1

        # Crear nuevo producto con precio incluido peewee
        producto = Product.create(
            id_product=new_id, 
            product=data['product'].strip(),
            price=price
            )
        
        return jsonify({
            'message': 'Producto creado exitosamente',
            'id': producto.id_product, 
            'product': producto.product,
            'price': producto.price
        }), 201

    except Exception as e:
        print(f"Error en create_product: {str(e)}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

# PUT /products/<id> - Actualizar un producto
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se enviaron datos'}), 400

        # Verificar si el producto existe
        product = Product.get_or_none(Product.id_product == product_id)
        if not product:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        # Validar y borrar campos
        updated = False

        if 'product' in data and data['product'].strip():
            product.product = data['product'].strip()
            updated = True
        
        if 'price' in data and isinstance(data['price'], (int, float)) and data['price']:
            product.price = data['price']
            updated = True

        if not updated:
            return jsonify({'error': 'No se enviaron datos validos para actualizar'}), 400
        
        product.save()
        return jsonify({'message': 'Producto actualizado exitosamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# DELETE /products/<id> - Eliminar un producto
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.get_or_none(Product.id_product == product_id)

        if not product:
                return jsonify({'error': 'Producto no encontrado'}), 404

        # Se elimina primero los registros relacionados en el carrito
        Cart.delete().where(Cart.id_product == product_id).execute()

        # Eliminar el producto
        product.delete_instance()
        return jsonify({'message': 'Producto eliminado exitosamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint original (mantener compatibilidad)
@app.route('/productos')
def obtener_productos():
    try:
        products = Product.select()

        # Convertir a formato compatible
        productos = []
        for row in products:
            productos.append({
                'id': row.id_product,
                'nombre': row.product,
                'precio': float(row.price)
            })

        return jsonify(productos)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/home') 
def home():
    try: 
        products = Product.select().order_by(Product.id_product.desc())

        result = ""
        for x in products:
            result += f"<li class='list-group-item list-group-item-action'>ID: {x.id_product} - Producto: {x.product} - Precio: {x.price}</li>"

        html_content = f"""
        <div class="row">
            <div class="col-md-6 offset-md-3">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h2>Lista de productos</h2>
                    <div>
                        <a href="/add-product" class="btn btn-success">+ Agregar Producto</a>
                        <a href="/add-user" class="btn btn-success">+ Agregar usuario</a>
                        <a href="/cart-view" class="btn btn-primary">🛒 Carrito</a>
                    </div>
                </div>
                <ul class="list-group">
                    {result}
                </ul>
            </div>
        </div>
        """
        return get_html_base(html_content)
    
    except Exception as ex:
        return get_html_base(f"<div class='alert alert-danger'>Error al consultar productos: {str(ex)}</div>")

@app.route('/prueba')
def prueba():
    return render_template('carrito.html')

# vista web de usuario (peewee)
@app.route('/add-user', methods=['GET','POST'])
def add_user():
    if request.method == 'GET':
        return render_template('add_user.html')
    
    elif request.method == 'POST':
        try: 
            user_name = request.form.get('user_name', '').strip() 

            if not user_name:
                return render_template('add_user.html',
                                       message='Rellenar todos los campos',
                                       success=False)
            
            # Obtener el sigueinte ID disponible (sin usar AUTO_INCREMENT)
            max_id = User.select(fn.COALESCE(fn.MAX(User.id_user), 0).alias('max_id')).scalar()
            new_id = max_id + 1

            # Crear usuario con Peewee
            user = User.create(id_user=new_id, user_name=user_name)

            return render_template('add_user.html',
                                   message=f'Usuario "{user_name}" agregado exitosamente',
                                   success=True)
        
        except Exception as e:
            return render_template('add_user.html',
                                   message= f'Error al agregar usuario: {str(e)}',
                                   success= False)



# Vista web para agregar productos
@app.route('/add-product', methods=['GET', 'POST'])
def add_product_web():
    if request.method == 'GET':
        return render_template('add_product.html')
    
    elif request.method == 'POST':
        try:
            # Obtener datos del formulario
            product = request.form.get('product', '').strip()
            price = request.form.get('price', '').strip()
            
            # Validar campos requeridos
            if not product or not price:
                return render_template('add_product.html', 
                                     message='Todos los campos son requeridos', 
                                     success=False)
            
            # Obtener el ID disponible
            max_id = Product.select(fn.COALESCE(fn.MAX(Product.id_product), 0).alias('max_id')).scalar()
            new_id = max_id + 1

            product = Product.create(
                id_product = new_id, 
                product = product, 
                price = price
                )

            return render_template('add_product.html', 
                                 message=f'Producto "{product.product}" agregado exitosamente', 
                                 success=True)
            
        except Exception as e:
            return render_template('add_product.html', 
                                 message=f'Error al agregar producto: {str(e)}', #aqui condicionar
                                 success=False)


# Vista del carrito de compras
@app.route('/cart-view')
def cart_view():
    try:
        user_id = request.args.get('user_id') #user_id solo coincide en /users
        
        users = User.select().order_by(User.user_name)

        products = Product.select().order_by(Product.product)

        cart_items = []
        cart_total = 0
        selected_user_name = None

        if user_id:
            # Obtener el nombre del usuario seleccionado
            user = (User.
                   select()
                   .where(User.id_user == user_id)
                   .first())
           
            if user:
                selected_user_name = user.user_name 

            # Obtener items del carrito para el usuario seleccionado
            cart_items = (Cart
                          .select(Cart.id_cart,
                                  Cart.quantity,
                                  Product.product,
                                  Product.price)
                            .join(Product, on=(Cart.id_product == Product.id_product))
                            .where(Cart.id_user == user_id)
                            .order_by(Cart.added_date.desc())
                            )
            
            cart_items = list(cart_items.dicts())
            # Calcular total
            cart_total = sum(item['price'] * item['quantity'] for item in cart_items)

            # CORREGIR QUE AL SELECCIONAR USUARIO EL CARRITO CORRESPONDA CORRECTAMENTE
        
        return render_template('cart_view.html', 
                             users=users, 
                             products=products,
                             cart_items=cart_items,
                             cart_total=cart_total,
                             selected_user=int(user_id) if user_id else None,
                             selected_user_name=selected_user_name)
    
    except Exception as e:
        return render_template('cart_view.html', 
                             users=[], 
                             products=[],
                             cart_items=[],
                             cart_total=0,
                             message=f'Error: {str(e)}',
                             success=False)


@app.route('/cart/user/<int:user_id>', methods=['GET'])
def get_cart_items_by_user(user_id):
    try:
        # Obtener todos los items del carrito para el usuario
        cart_items = Cart.select().where(Cart.id_user == user_id)

        if not cart_items.exists():
            return jsonify([]), 200 #carrito vacio
        
        # Respuesta con información del producto
        result = []
        for cart_item in cart_items:
            product = Product.get_by_id(cart_item.id_product)
        
            result.append({
                'product': {
                    'id_product': product.id_product,
                    'product': product.product,
                    'price': float(product.price)
                },
                'quantity': cart_item.quantity,
                'addedDate': cart_item.added_date.strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/cart/<int:user_id>/<int:product_id>', methods=['GET'])
def get_cart_item(user_id, product_id):
    try:
        carrito = Cart.get_or_none((Cart.id_user == user_id) & (Cart.id_product == product_id))

        if carrito:
            return jsonify({
                'id_cart': carrito.id_cart,
                'id_user': carrito.id_user.id_user,
                'id_product': carrito.id_product.id_product,
                'quantity': carrito.quantity
            }), 200
        else: 
            return jsonify(None), 404 # No existe en el carrito
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    try:
        # DETECCIÓN MEJORADA DEL TIPO DE REQUEST
        data = request.get_json(silent=True)  # No genera error si no es JSON
        
        if data is not None:
            # Es una petición JSON (Android)
            user_id = data.get('id_user')
            product_id = data.get('id_product') 
            quantity = int(data.get('quantity', 1))
            is_json_request = True
        else:
            # Es una petición de formulario HTML
            user_id = request.form.get('user_id')
            product_id = request.form.get('product_id')
            quantity = int(request.form.get('quantity', 1))
            is_json_request = False

        # Validación específica por tipo
        if is_json_request:
            if user_id is None or product_id is None:
                return jsonify({'success': False, 
                                'error': 'user_id y product_id requeridos'
                                }), 400
        else:
            if not user_id or user_id == 'None' or not product_id or product_id == 'None':
                return redirect(f'/cart-view?error=Debe seleccionar usuario y producto')

        # Convertir y procesar
        user_id = int(user_id)
        product_id = int(product_id)

        # VALIDAR QUE EL USUARIO EXISTA
        user_exists = User.get_or_none(User.id_user == user_id)
        if not user_exists:
            if is_json_request:
                return jsonify({
                    'success': False,
                    'error': 'User does not exist. Please create a guest user first.'
                }), 404
            else:
                return redirect(url_for('cart_view', user_id=user_id, error='Usuario no encontrado'))

        # VALIDAR QUE EL PRODUCTO EXISTA
        product_exists = Product.get_or_none(Product.id_product == product_id)
        if not product_exists:
            if is_json_request:
                return jsonify({
                    'success': False,
                    'error': 'Product does not exist'
                }), 404
            else:
                return redirect(url_for('cart_view', user_id=user_id, error='Producto no encontrado'))

        # Buscar si el producto ya existe en el carrito del usuario
        carrito = Cart.get_or_none((Cart.id_user == user_id) & (Cart.id_product == product_id))
        
        if carrito:
            # Actualizar cantidad si ya existe
            carrito.quantity += quantity
            carrito.save()
        else:
            # Agregar nuevo item
            carrito = Cart.create(id_user=user_id, id_product=product_id, quantity=quantity)

        if is_json_request:
            return jsonify({'success': True, 
                            'message': 'Agregado al carrito', 
                            'cartItemId': carrito.id
                            })
        else:
            return redirect(f'/cart-view?user_id={user_id}&success=true')

    except Exception as e:
        if 'is_json_request' in locals() and is_json_request:
            return jsonify({'success': False, 'error': str(e)}), 500
        else:
            return redirect(f'/cart-view?error={str(e)}')


@app.route('/cart/<int:cart_id>', methods=['PUT'])
def update_cart_quantity(cart_id):
    try:
        data = request.get_json()
        
        if not data or 'quantity' not in data:
            return jsonify({'success': False, 'error': 'Quantity requerida'}), 400
        
        quantity = int(data['quantity'])

        if quantity < 0:
            return jsonify({'success': False, 'error': 'Cantidad no puede ser negativa'}), 400
        
        cart_item = Cart.get_or_none(Cart.id_cart == cart_id)

        if not cart_item:
            return jsonify({'success': False, 'error': 'Item no encontrado'}), 404
        
        if quantity == 0:
            # Eliminar si cantidad es 0
            cart_item.delete_instance()
            return jsonify({
                'success': True,
                'message': 'Item eliminado del carrito'
            }), 200
        else: 
            # Actualizar cantidad
            cart_item.quantity = quantity
            cart_item.save()

            return jsonify({
                'success': True,
                'message': 'Cantidad actualizada',
                'data': {
                    'id_cart': cart_item.id_cart,
                    'id_user': cart_item.id_user.id_user,
                    'id_product': cart_item.id_product.id_product,
                    'quantity': cart_item.quantity
                }
            }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    


@app.route('/cart/<int:cart_id>', methods=['DELETE'])
def delete_cart_item(cart_id):
    try:
        cart_item = Cart.get_or_none(Cart.id_cart == cart_id)

        if not cart_item:
            return jsonify({'success': False, 'error': 'Item no encontrado'}), 404
        
        cart_item.delete_instance()

        return jsonify({
            'success': True,
            'message': 'Item eliminado del carrito'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



# Remover producto del carrito
@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    try:
        cart_id = request.form.get('cart_id')
        user_id = request.form.get('user_id')

        # Validación de parámetros requeridos
        if not cart_id: 
            return redirect(f'/cart?user_id={user_id or ""}')
        
        # Buscar el producto en el carrito
        remove_product = Cart.get_or_none(cart_id == Cart.id_cart)

        # Verificar que existe antes de eliminar
        if remove_product:
            remove_product.delete_instance()

        return redirect(f'/cart?user_id={user_id}')
    
    except Exception as e:
        return redirect(f'/cart?user_id={user_id or ""}')


if __name__=='__main__': #se comprueba la aplicacion
    app.run(debug=True, host='0.0.0.0' ,port=5002)  #aqui se corre el programa

