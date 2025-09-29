from flask import Flask, render_template, request, url_for, redirect, jsonify
import pymysql

from peewee import *
from datetime import datetime
import os
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

# Configuracion de la DB con Peewee
db = MySQLDatabase(
    'list_products',
    user='root',
    password='Relic11&',
    host='localhost',
    port=3306
)

# Configuración MySQL
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        passwd='Relic11&',
        database='list_products',
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

    class Meta:
        table_name = 'user'

    def to_dict(self):
        # convierte el objeto a diccionario para JSON
        return {
            'id_user': self.id_user,
            'user_name': self.user_name
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

