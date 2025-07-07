from flask import Flask, render_template, request, url_for, redirect, jsonify #flasks es una clase
from flask_mysqldb import MySQL
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

# Conexión MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Relic11&'
app.config['MYSQL_DB'] = 'list_products'

conexion = MySQL(app)

@app.route('/home') 
def home():
    try: 
        cursor = conexion.connection.cursor()
        sql="SELECT id, product, price FROM products ORDER BY id DESC"
        cursor.execute(sql)
        products = cursor.fetchall()

        result = ""
        for x in products:
            result += f"<li class='list-group-item list-group-item-action'>ID: {x[0]} - Producto: {x[1]} - Precio: {x[2]}</li>"

        html_content = f"""
        <div class="row">
            <h2 class="col-mb-6 offset-md-3"> Lista de productos</h2>
                <ul class="col-mb-6 offset-md-3 list-group">
                    {result}
                </ul>
        </div>
        """
        return get_html_base(html_content)
    
    except Exception as ex:
        return get_html_base(f"<div class='alert alert-danger'>Error al consultar productos: {str(ex)}</div>")


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
    app.run(debug=True, port=5000)  #aqui se corre el programa

#observar el estado de Debug mode: ctrl + c detengo el servidor
#activar el modo depuracion, dentro de run(debug=true), aquí puedo determinar el puerto para la ejecucion
#plantilla: documento html que tiene contenido que es devuelto a traves del servidor 

