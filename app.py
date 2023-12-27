#--------------------------------------------------------------------
# Instalar con pip install Flask
from flask import Flask, request, jsonify, render_template
#from flask import request

# Instalar con pip install flask-cors
from flask_cors import CORS

# Instalar con pip install mysql-connector-python
import mysql.connector

# Si es necesario, pip install Werkzeug
from werkzeug.utils import secure_filename

# No es necesario instalar, es parte del sistema standard de Python
import os
import time
#--------------------------------------------------------------------



app = Flask(__name__)
CORS(app)  # Esto habilitará CORS para todas las rutas

#--------------------------------------------------------------------
class Catalogo:
    #----------------------------------------------------------------
    # Constructor de la clase
    def __init__(self, host, user, password, database):
        # Primero, establecemos una conexión sin especificar la base de datos
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        self.cursor = self.conn.cursor()

        # Intentamos seleccionar la base de datos
        try:
            self.cursor.execute(f"USE {database}")
        except mysql.connector.Error as err:
            # Si la base de datos no existe, la creamos
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.cursor.execute(f"CREATE DATABASE {database}")
                self.conn.database = database
            else:
                raise err

        # Una vez que la base de datos está establecida, creamos la tabla si no existe
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
            num_excursion INT,
            nombre_excursion VARCHAR(255) NOT NULL,
            cantidad_personas INT NOT NULL,
            precio DECIMAL(10, 2) NOT NULL,
            imagen_url VARCHAR(255),
            num_agencia INT(4))''')
        self.conn.commit()

        # Cerrar el cursor inicial y abrir uno nuevo con el parámetro dictionary=True
        self.cursor.close()
        self.cursor = self.conn.cursor(dictionary=True)
        
    #----------------------------------------------------------------
    def agregar_producto(self, num_excursion, nombre_excursion, cantidad_personas, precio, imagen, num_agencia):
        # Verificamos si ya existe un producto con el mismo código
        self.cursor.execute(f"SELECT * FROM productos WHERE num_excursion = {num_excursion}")
        producto_existe = self.cursor.fetchone()
        if producto_existe:
            return False

        
        sql = "INSERT INTO productos (num_excursion, nombre_excursion, cantidad_personas, precio, imagen_url, num_agencia) VALUES (%s, %s, %s, %s, %s, %s)"
        valores = (num_excursion, nombre_excursion, cantidad_personas, precio, imagen, num_agencia)

        self.cursor.execute(sql, valores)        
        self.conn.commit()
        return True

    #----------------------------------------------------------------
    def consultar_producto(self, num_excursion):
        # Consultamos un producto a partir de su código
        self.cursor.execute(f"SELECT * FROM productos WHERE num_excursion = {num_excursion}")
        return self.cursor.fetchone()

    #----------------------------------------------------------------
    def modificar_producto(self, num_excursion, nueva_nombre_excursion, nueva_cantidad_personas, nuevo_precio, nueva_imagen, nuevo_num_agencia):
        sql = "UPDATE productos SET nombre_excursion = %s, cantidad_personas = %s, precio = %s, imagen_url = %s, num_agencia = %s WHERE num_excursion = %s"
        valores = (nueva_nombre_excursion, nueva_cantidad_personas, nuevo_precio, nueva_imagen, nuevo_num_agencia, num_excursion)
        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.rowcount > 0

    #----------------------------------------------------------------
    def listar_productos(self):
        self.cursor.execute("SELECT * FROM productos")
        productos = self.cursor.fetchall()
        return productos

    #----------------------------------------------------------------
    def eliminar_producto(self, num_excursion):
        # Eliminamos un producto de la tabla a partir de su código
        self.cursor.execute(f"DELETE FROM productos WHERE num_excursion = {num_excursion}")
        self.conn.commit()
        return self.cursor.rowcount > 0

    #----------------------------------------------------------------
    def mostrar_producto(self, num_excursion):
        # Mostramos los datos de un producto a partir de su código
        producto = self.consultar_producto(num_excursion)
        if producto:
            print("-" * 40)
            print(f"Código.....: {producto['num_excursion']}")
            print(f"Descripción: {producto['nombre_excursion']}")
            print(f"cantidad_personas...: {producto['cantidad_personas']}")
            print(f"Precio.....: {producto['precio']}")
            print(f"Imagen.....: {producto['imagen_url']}")
            print(f"num_agencia..: {producto['num_agencia']}")
            print("-" * 40)
        else:
            print("Producto no encontrado.")


#--------------------------------------------------------------------
# Cuerpo del programa
#--------------------------------------------------------------------
# Crear una instancia de la clase Catalogo
# catalogo = Catalogo(host='localhost', user='root', password='', database='miapp')
catalogo = Catalogo(host='pablominardi.mysql.pythonanywhere-services.com', user='pablominardi', password='Codeando!2874', database='pablominardi$miapp')

# catalogo.agregar_producto(1, "Televisor 25",11, 340000, "tele.jpg",1)
# catalogo.agregar_producto(2, "Notebook",11, 740000, "compu.jpg",1)
# catalogo.agregar_producto(3, "Mouse tres botones",11, 3400, "mouse.jpg",1)


# Carpeta para guardar las imagenes.
# RUTA_DESTINO = './static/imagenes/'

#Al subir al servidor, deberá utilizarse la siguiente ruta. USUARIO debe ser reemplazado por el nombre de usuario de Pythonanywhere
RUTA_DESTINO = '/home/pablominardi/mysite/static/imagenes'


#--------------------------------------------------------------------
# Listar todos los productos
#--------------------------------------------------------------------
#La ruta Flask /productos con el método HTTP GET está diseñada para proporcionar los detalles de todos los productos almacenados en la base de datos.
#El método devuelve una lista con todos los productos en formato JSON.
@app.route("/productos", methods=["GET"])
def listar_productos():
    productos = catalogo.listar_productos()
    return jsonify(productos)


#--------------------------------------------------------------------
# Mostrar un sólo producto según su código
#--------------------------------------------------------------------
#La ruta Flask /productos/<int:num_excursion> con el método HTTP GET está diseñada para proporcionar los detalles de un producto específico basado en su código.
#El método busca en la base de datos el producto con el código especificado y devuelve un JSON con los detalles del producto si lo encuentra, o None si no lo encuentra.
@app.route("/productos/<int:num_excursion>", methods=["GET"])
def mostrar_producto(num_excursion):
    producto = catalogo.consultar_producto(num_excursion)
    if producto:
        return jsonify(producto), 201
    else:
        return "Producto no encontrado", 404


#--------------------------------------------------------------------
# Agregar un producto
#--------------------------------------------------------------------
@app.route("/productos", methods=["POST"])
#La ruta Flask `/productos` con el método HTTP POST está diseñada para permitir la adición de un nuevo producto a la base de datos.
#La función agregar_producto se asocia con esta URL y es llamada cuando se hace una solicitud POST a /productos.
def agregar_producto():
    #Recojo los datos del form
    num_excursion = request.form['num_excursion']
    nombre_excursion = request.form['nombre_excursion']
    cantidad_personas = request.form['cantidad_personas']
    precio = request.form['precio']
    imagen = request.files['imagen']
    num_agencia = request.form['num_agencia']  
    nombre_imagen=""

    # Me aseguro que el producto exista
    producto = catalogo.consultar_producto(num_excursion)
    if not producto: # Si no existe el producto...
        # Genero el nombre de la imagen
        nombre_imagen = secure_filename(imagen.filename) #Chequea el nombre del archivo de la imagen, asegurándose de que sea seguro para guardar en el sistema de archivos
        nombre_base, extension = os.path.splitext(nombre_imagen) #Separa el nombre del archivo de su extensión.
        nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}" #Genera un nuevo nombre para la imagen usando un timestamp, para evitar sobreescrituras y conflictos de nombres.
        
        #Se agrega el producto a la base de datos
        if  catalogo.agregar_producto(num_excursion, nombre_excursion, cantidad_personas, precio, nombre_imagen, num_agencia):
            imagen.save(os.path.join(RUTA_DESTINO, nombre_imagen))

            #Si el producto se agrega con éxito, se devuelve una respuesta JSON con un mensaje de éxito y un código de estado HTTP 201 (Creado).
            return jsonify({"mensaje": "Producto agregado correctamente.", "imagen": nombre_imagen}), 201
        else:
            #Si el producto no se puede agregar, se devuelve una respuesta JSON con un mensaje de error y un código de estado HTTP 500 (Internal Server Error).
            return jsonify({"mensaje": "Error al agregar el producto."}), 500

    else:
        #Si el producto ya existe (basado en el código), se devuelve una respuesta JSON con un mensaje de error y un código de estado HTTP 400 (Solicitud Incorrecta).
        return jsonify({"mensaje": "Producto ya existe."}), 400
    

#--------------------------------------------------------------------
# Modificar un producto según su código
#--------------------------------------------------------------------
@app.route("/productos/<int:num_excursion>", methods=["PUT"])
#La ruta Flask /productos/<int:num_excursion> con el método HTTP PUT está diseñada para actualizar la información de un producto existente en la base de datos, identificado por su código.
#La función modificar_producto se asocia con esta URL y es invocada cuando se realiza una solicitud PUT a /productos/ seguido de un número (el código del producto).
def modificar_producto(num_excursion):
    #Se recuperan los nuevos datos del formulario
    nueva_nombre_excursion = request.form.get("nombre_excursion")
    nueva_cantidad_personas = request.form.get("cantidad_personas")
    nuevo_precio = request.form.get("precio")
    nuevo_num_agencia = request.form.get("num_agencia")
    imagen = request.files['imagen']

    # Procesamiento de la imagen
    nombre_imagen = secure_filename(imagen.filename) #Chequea el nombre del archivo de la imagen, asegurándose de que sea seguro para guardar en el sistema de archivos
    nombre_base, extension = os.path.splitext(nombre_imagen) #Separa el nombre del archivo de su extensión.
    nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}" #Genera un nuevo nombre para la imagen usando un timestamp, para evitar sobreescrituras y conflictos de nombres.

    # Busco el producto guardado
    producto = producto = catalogo.consultar_producto(num_excursion)
    if producto: # Si existe el producto...
        imagen_vieja = producto["imagen_url"]
        # Armo la ruta a la imagen
        ruta_imagen = os.path.join(RUTA_DESTINO, imagen_vieja)

        # Y si existe la borro.
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)
    
    # Se llama al método modificar_producto pasando el num_excursion del producto y los nuevos datos.
    if catalogo.modificar_producto(num_excursion, nueva_nombre_excursion, nueva_cantidad_personas, nuevo_precio, nombre_imagen, nuevo_num_agencia):
        #La imagen se guarda en el servidor.
        imagen.save(os.path.join(RUTA_DESTINO, nombre_imagen))

        #Si la actualización es exitosa, se devuelve una respuesta JSON con un mensaje de éxito y un código de estado HTTP 200 (OK).
        return jsonify({"mensaje": "Producto modificado"}), 200
    else:
        #Si el producto no se encuentra (por ejemplo, si no hay ningún producto con el código dado), se devuelve un mensaje de error con un código de estado HTTP 404 (No Encontrado).
        return jsonify({"mensaje": "Producto no encontrado"}), 403



#--------------------------------------------------------------------
# Eliminar un producto según su código
#--------------------------------------------------------------------
@app.route("/productos/<int:num_excursion>", methods=["DELETE"])
#La ruta Flask /productos/<int:num_excursion> con el método HTTP DELETE está diseñada para eliminar un producto específico de la base de datos, utilizando su código como identificador.
#La función eliminar_producto se asocia con esta URL y es llamada cuando se realiza una solicitud DELETE a /productos/ seguido de un número (el código del producto).
def eliminar_producto(num_excursion):
    # Busco el producto en la base de datos
    producto = catalogo.consultar_producto(num_excursion)
    if producto: # Si el producto existe, verifica si hay una imagen asociada en el servidor.
        imagen_vieja = producto["imagen_url"]
        # Armo la ruta a la imagen
        ruta_imagen = os.path.join(RUTA_DESTINO, imagen_vieja)

        # Y si existe, la elimina del sistema de archivos.
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)

        # Luego, elimina el producto del catálogo
        if catalogo.eliminar_producto(num_excursion):
            #Si el producto se elimina correctamente, se devuelve una respuesta JSON con un mensaje de éxito y un código de estado HTTP 200 (OK).
            return jsonify({"mensaje": "Producto eliminado"}), 200
        else:
            #Si ocurre un error durante la eliminación (por ejemplo, si el producto no se puede eliminar de la base de datos por alguna razón), se devuelve un mensaje de error con un código de estado HTTP 500 (Error Interno del Servidor).
            return jsonify({"mensaje": "Error al eliminar el producto"}), 500
    else:
        #Si el producto no se encuentra (por ejemplo, si no existe un producto con el num_excursion proporcionado), se devuelve un mensaje de error con un código de estado HTTP 404 (No Encontrado). 
        return jsonify({"mensaje": "Producto no encontrado"}), 404

#--------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)