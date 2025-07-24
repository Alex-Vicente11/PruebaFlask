from flask import Flask, render_template, request, url_for, redirect, jsonify
import pymysql
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

# Configuración MySQL
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='Relic11&',
        database='list_products',
        cursorclass=pymysql.cursors.DictCursor
    )


# CRUD para usuario
# GET /users - Obtener todos los usuarios
@app.route('/users', methods=['GET'])
def get_users():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_user, user_name FROM user")
            users = cursor.fetchall()

        connection.close()
        return jsonify(users), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

#GET /users/<id> - Obtener un usuario por ID
@app.route('/users/<int:id_user>', methods=['GET'])
def get_user(id_user):
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_user, user_name FROM user WHERE id_user = %s", (id_user,))
            user = cursor.fetchone()
        
        connection.close()

        if user:
            return jsonify(user), 200
        else: 
            return jsonify({'Error': 'usuario no encontrado'}),404
        
    except Exception as e:
        return jsonify({'error': str(e)}),500
    
# POST /users - crear un nuevo usuario
@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()

        if not data or 'id_user' not in data or 'user_name' not in data:
            return jsonify({'error': 'Faltan campos requeridos: id_user, user_name'}), 400
        
 #       id_user = data['id_user']

        connection = get_db_connection()
        with connection.cursor() as cursor:
 #           cursor.execute("SELECT id_user FROM user WHERE id_user = %s", (id_user))
 #           exist = cursor.fetchone()
  #          if exist:
   #             return jsonify({'error': 'El ID ya existen, prueba con otro'}), 400


            sql = "INSERT INTO user (id_user, user_name) VALUES (%s, %s)" 
            cursor.execute(sql, (data['id_user'], data['user_name']))
            connection.commit()
            new_id = cursor.lastrowid

        connection.close()

        return jsonify({
            'message': 'Usuario creado exitosamente',
            'id': new_id 
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# PUT /users/<id> - actualizar usuario
@app.route('/users/<int:id_user>', methods=['PUT'])
def update_user(id_user):
    try:
        data = request.get_json()

        if not data: 
            return jsonify({'error': 'No se enviaron datos' }), 400
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_user FROM user WHERE id_user = %s", (id_user,))
            if not cursor.fetchone():
                return jsonify({'error': 'Usuario no encontrado'}), 404
            
            fields = []
            values = []

            if 'id_user' in data:
                fields.append("id_user = %s")
                #values.append("id_user", data['id_user'])
                values.append(data['id_user'])
            if 'user_name' in data:
                fields.append("user_name = %s")
                #values.append("user_name", data['user_name'])
                values.append(data['user_name'])

            if not fields:
                return jsonify({'error': 'No se enviaron datos para actualizar'}), 400
            
            values.append(id_user)
            sql = f"UPDATE user SET {','.join(fields)} WHERE id_user = %s"
            cursor.execute(sql,values)
            connection.commit()

        connection.close()

        return jsonify({'message': 'Usuario actualizado exitosamente'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# DELETE /users/<id> - Eliminar usuario
@app.route('/users/<int:id_user>', methods=['DELETE'])
def delete_user(id_user):
    try: 
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT id_user FROM user WHERE id_user=%s", (id_user,))
            if not cursor.fetchone():
                return jsonify({'error': 'El usuario no existe'}), 404
            
            cursor.execute("DELETE FROM user WHERE id_user=%s", (id_user,))
            connection.commit()

        connection.close()

        return jsonify({'message': 'Usuario eliminado exitosamente'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

#EndPoint (mantener compatibilidad)
@app.route('/usuarios')
def obtener_usuarios():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_user AS id, user_name AS nombre FROM user")
            rows = cursor.fetchall()

        connection.close()

        usuarios = []
        for row in rows:
            usuarios.append({
                'id': row['id'],
                'nombre': row['nombre']
            })

        return jsonify(usuarios)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# CRUD REST Endpoints para productos
# GET /products - Obtener todos los productos
@app.route('/products', methods=['GET'])
def get_products():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_product, product, price FROM products")
            productos = cursor.fetchall()
            
        connection.close()
        return jsonify(productos), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET /products/<id> - Obtener un producto por ID
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_product, product, price FROM products WHERE id = %s", (product_id,))
            producto = cursor.fetchone()
            
        connection.close()
        
        if producto:
            return jsonify(producto), 200
        else:
            return jsonify({'error': 'Producto no encontrado'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST /products - Crear un nuevo producto
@app.route('/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        
        if not data or 'id_product' not in data or 'product' not in data or 'price' not in data:
            return jsonify({'error': 'Faltan campos requeridos: id_product, product, price'}), 400
        
        id_product = data['id_product']

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_product FROM products WHERE id_product=%s", (id_product,))
            exist = cursor.fetchone()
            if exist:
                return jsonify({'error': 'El ID ya existe, prueba con otro'}), 400
            
            
            sql = "INSERT INTO products (id_product, product, price) VALUES (%s, %s, %s)"
            cursor.execute(sql, (data['id_product'], data['product'], data['price']))
            connection.commit()
            new_id = cursor.lastrowid
            
        connection.close()
        
        return jsonify({
            'message': 'Producto creado exitosamente',
            'id': new_id
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# PUT /products/<id> - Actualizar un producto
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se enviaron datos'}), 400

        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Verificar si el producto existe
            cursor.execute("SELECT id_product FROM products WHERE id_product = %s", (product_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Producto no encontrado'}), 404

            # Construir query dinámicamente según campos enviados
            fields = []
            values = []
            
            if 'id_product' in data:
                fields.append("id_product = %s")
                values.append(data['id_product'])
            if 'product' in data:
                fields.append("product = %s")
                values.append(data['product'])
            if 'price' in data:
                fields.append("price = %s")
                values.append(data['price'])
            
            if not fields:
                return jsonify({'error': 'No se enviaron campos para actualizar'}), 400

            values.append(product_id)
            sql = f"UPDATE products SET {', '.join(fields)} WHERE id_product = %s"
            cursor.execute(sql, values)
            connection.commit()
            
        connection.close()
        
        return jsonify({'message': 'Producto actualizado exitosamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# DELETE /products/<id> - Eliminar un producto
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Verificar si el producto existe
            cursor.execute("SELECT id_product FROM products WHERE id_product = %s", (product_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Producto no encontrado'}), 404

            # Eliminar el producto
            cursor.execute("DELETE FROM products WHERE id_product = %s", (product_id,))
            connection.commit()
            
        connection.close()
        
        return jsonify({'message': 'Producto eliminado exitosamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint original (mantener compatibilidad)
@app.route('/productos')
def obtener_productos():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_product AS id, product AS nombre, price AS precio FROM products")
            rows = cursor.fetchall()
            
        connection.close()
        
        # Convertir a formato compatible
        productos = []
        for row in rows:
            productos.append({
                'id': row['id'],
                'nombre': row['nombre'],
                'precio': float(row['precio'])
            })

        return jsonify(productos)

    except Exception as e:
        return jsonify({'error': str(e)}), 500







@app.route('/home') 
def home():
    try: 
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql="SELECT id_product, product, price FROM products ORDER BY id_product DESC"
            cursor.execute(sql)
            products = cursor.fetchall()
        
        connection.close()

        result = ""
        for x in products:
            result += f"<li class='list-group-item list-group-item-action'>ID: {x['id_product']} - Producto: {x['product']} - Precio: {x['price']}</li>"

        html_content = f"""
        <div class="row">
            <div class="col-md-6 offset-md-3">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h2>Lista de productos</h2>
                    <a href="/add-product" class="btn btn-success">+ Agregar Producto</a>
                    <a href="/add-user" class="btn btn-success">+ Agregar usuario</a>
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

# vista web de usuario
@app.route('/add-user', methods=['GET','POST'])
def add_user():
    if request.method == 'GET':
        return render_template('add_user.html')
    
    elif request.method == 'POST':
        try: 
            id_user = request.form.get('id_user')
            user_name = request.form.get('user_name')

            if not id_user or not user_name:
                return render_template('add_user.html',
                                       message='Rellenar todos los campos',
                                       success=False)
            
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT id_user FROM user WHERE id_user = %s", (id_user,))
                exist = cursor.fetchone()
                if exist:
                    connection.close()
                    return render_template('add_user.html',
                                   message = f'El ID {id_user} ya existe, intenta con otro.',
                                   success=False)


            with connection.cursor() as cursor:
                sql = "INSERT INTO user (id_user, user_name) VALUES (%s,%s)"
                cursor.execute(sql, (int(id_user), user_name))
                connection.commit()

            connection.close()

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
            id_product = request.form.get('id_product')
            product = request.form.get('product')
            price = request.form.get('price')
            
            # Validar campos requeridos
            if not id_product or not product or not price:
                return render_template('add_product.html', 
                                     message='Todos los campos son requeridos', 
                                     success=False)
            
            # Verificar si ya existe el id-product
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT id_product FROM products WHERE id_product = %s", (id_product,))
                exist = cursor.fetchone()
                if exist:
                    connection.close()
                    return render_template('add_product.html',
                                           message = f'El ID {id_product} ya existe, intenta con otro.',
                                            success=False)
                    
                # Insertar en la base de datos 
                with connection.cursor() as cursor:
                    sql = "INSERT INTO products (id_product, product, price) VALUES (%s, %s, %s)"
                    cursor.execute(sql, (int(id_product), product, float(price)))
                    connection.commit()
                
            connection.close()
            
            return render_template('add_product.html', 
                                 message=f'Producto "{product}" agregado exitosamente', 
                                 success=True)
            
        except Exception as e:
            return render_template('add_product.html', 
                                 message=f'Error al agregar producto: {str(e)}', #aqui condicionar
                                 success=False)

#def index(): 
#    products = [
#        {"name": "Alice", "id": 30, "brand": "Nueva York"},
#        {"name": "Bob", "id": 25, "brand": "Los Ángeles"},
#        {"name": "Charlie", "id": 35, "brand": "Chicago"}
#    ]
#    result = ""
#    for x in products:
#        result += f"<li>{x['name']}</li>"
#    return get_html_base("""                    
#    <ul>
#        {result}
#    </ul>
#    """.format(result=result))
# return get_html_base(f'<button type="{btn_name}" class="btn btn-primary">Haz clic</button>')


@app.route('/product')
def product():
    return get_html_base("""
    <div class="container-md" style="background-color: cyan;"> 
        <div class="row">
            <div class="col-4 ">
                <img src="https://3.bp.blogspot.com/-MfvUawjHslc/U4tvUsR9hbI/AAAAAAACNoQ/ALk3_7AMSbk/s1600/imagenes-gratis-fondos-fotos-y-postales-para-computadoras-dise%C3%B1adores-publicistas-y-estudiantes-free-photos+(8).jpg" class="img-fluid" alt="inversor" >
            </div>
        </div>

        <div class="row">
            <div class="col-4 mt-4 p-5  border border-5 border-primary" style="background-color: orange">
                <h1>Inversor trifásico bidireccional para motores asíncronos</h1>
                <p>Cuenta con disipador  de calor, etapa de potencia, sensores de corriente y temperatura.</p>
            </div>
        </div>

        <div class="row">
            <div class="col-4 md-4" style="background-color: gray;">
                <h2>$ 1,300</h2>
                <p>Inversor modificado 3000W de onda sinusoidal DC 12v a AC 110V</p>
            </div>
        </div>
     </div>                  
    """)

#<div class="col-12 mt-4 p-5  border border-5 border-primary" style="background-color: orange">
#Dentro de estas funciones se puede implementar más código para tener una ejeción adecuada
#Para realizar acciones antes de una petición
@app.before_request
def before_request():
    print("Antes de la petición...")

#Para realizar acciones después de la petición
@app.after_request
def after_request(respose):  #se requiere para despues de la vista el parametro response
    print("Después de la petición")
    return respose

@app.route('/contacto/<nombre>/<int:edad>') #url dinamica (decorador)
def contacto(nombre, edad):
    data= {
        'titulo':'contacto',
        'nombre':nombre,
        'edad' :edad
    }
    return render_template('contacto.html', data=data)


#query_string significa pasarle a una url un serie de parametros que puede ser variable
def query_string():  #se considera una vista?
    print(request)   #es un objeto (sera lo que un cliente solicita a un servidor)
    print(request.args)
    print(request.args.get('param1')) #param1 es nombre de la llave y envía el parametro
    print(request.args.get('param2')) 
    return "OK"      #necesariamente se debe retornar algo
#en la pag web, ? indica que se pasan parametros (param1=jose)

#def pagina_no_encontrada(error): #control de paginas con error 404
    #return render_template('404.html'), 404  #404 es el codigo de error asociado a una pagina no encontrada
 #   return redirect(url_for('index'))  #aqui se redirije a la ventana (vista) de index en caso de error
#url_for indica a la url asociada a la vista(index)


if __name__=='__main__': #se comprueba la aplicacion
    app.add_url_rule('/query_string',view_func=query_string) #aqui se enlaza la funcion a la url
#   app.register_error_handler(404, pagina_no_encontrada)    #se registra el manejador de error que apunte a la funcion pag_no_encontrada
    app.run(debug=True, port=5001)  #aqui se corre el programa

#observar el estado de Debug mode: ctrl + c detengo el servidor
#activar el modo depuracion, dentro de run(debug=true), aquí puedo determinar el puerto para la ejecucion
#plantilla: documento html que tiene contenido que es devuelto a traves del servidor 

