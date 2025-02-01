from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from factory import DatabaseFactory
from flask import jsonify
import base64
import imghdr
from PIL import Image
import io
from factory import UsuarioDTO, PublicacionDTO

app = Flask(__name__)

# Configuración de las bases de datos
SQL_SERVER_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': 'sqlserver,1433', 
    'database': 'Registros',
    'username': 'sa',
    'password': 'ProyectoGrupo5'
}

MONGO_DB_CONFIG = {
    'host': 'mongodb', 
    'port': 27017,
    'database': 'Proyecto_Grupo5',
    'collection': 'Fotos_Perfil',
    'username': 'admin',
    'password': 'proyectogrupo5AS'
}

# Configuración de la clave secreta para la sesión
app.secret_key = 'una_clave_secreta'

# Configurar la sesión
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

factory = DatabaseFactory() # Se crea la clase padre

@app.route('/') # Ruta por defecto
def inicio():
    return render_template('inicio_sesion.html')

@app.route('/login', methods=['GET', 'POST']) # Método de login
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Obtener DAO de usuarios
        usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)
        user_data = usuario_dao.verificar_usuario(username, password) # Se verifica que el usuario no exista en la base de datos
        
        if user_data:
            session['id_usuario'] = user_data['id']
            session['nombre_usuario'] = user_data['username']
            
            return redirect(url_for('publicaciones')) # Si el inicio es correcto se dirige a la feed de publicaciones
        
        return redirect(url_for('inicio')) # Si no es así se dirige al login nuevamente
    
    return redirect(url_for('inicio')) # Redirecciona a la página de login

@app.route('/crear_cuenta', methods=['GET', 'POST'])
def crear_cuenta():
    if request.method == 'POST':
        username = request.form['nombre_usuario']
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']
        
        # Llamar al método del DAO para registrar el usuario
        usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)
        resultado = usuario_dao.registrar_usuario(username, correo, contrasena, confirmar_contrasena) # Registra el usuario en la DB
        
        if resultado:  # Si el resultado es positivo, es decir, el registro fue exitoso
            return redirect(url_for('inicio'))  # Redirigir al inicio de sesión (inicio_sesion.html)
        
        # Si hubo un error en el registro, puedes redirigir o mostrar un mensaje de error
        return render_template('crear_cuenta.html', error=True, mensaje="Error en el registro.")
    
    return render_template('crear_cuenta.html') # Redirecciona a la página de crear cuenta

@app.route('/crear_publicacion', methods=['POST'])
def crear_publicacion():
    if 'id_usuario' not in session: # Verifica que exista una sesión activa
        return redirect(url_for('inicio')) # De no ser así lo direcciona al login

    contenido = request.form['contenido']
    id_usuario = session['id_usuario']
    
    publicacion_dao = factory.crear_publicacion_dao(MONGO_DB_CONFIG)
     # Procesar la imagen si se subió un archivo
    if 'foto_publicacion' in request.files:
        file = request.files['foto_publicacion']
        if file and file.filename != '':
            image = Image.open(file)

            if image.width > 580:
                ratio = 580 / image.width
                new_height = int(image.height * ratio)
                image = image.resize((580, new_height), Image.LANCZOS)

            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            foto_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            resultado = publicacion_dao.crear_publicacion(id_usuario, contenido,foto_base64) # Se almacena la publicación en la base de datos

    resultado = publicacion_dao.crear_publicacion(id_usuario, contenido)

    return redirect(url_for('publicaciones'))  # Redirigir a la página donde se muestran las publicaciones

@app.route('/responder_publicacion/<int:id_publicacion>', methods=['POST'])
def responder_publicacion(id_publicacion):
    if 'id_usuario' not in session: # Verifica que exista una sesión activa
        return redirect(url_for('inicio')) # De no ser así lo direcciona al login

    contenido = request.form['respuesta']
    id_usuario = session['id_usuario']
    
    # Obtener el DAO de publicaciones
    publicacion_dao = factory.crear_publicacion_dao(MONGO_DB_CONFIG)
    resultado = publicacion_dao.responder_publicacion(id_usuario, contenido, id_publicacion) # Se almacena la publicación en la base de datos

    return redirect(url_for('publicaciones'))  # Redirigir a la página donde se muestran las publicaciones

@app.route('/publicaciones')
def publicaciones():
    if 'id_usuario' not in session:  # Verifica que exista una sesión activa
        return redirect(url_for('inicio'))  # Si no, redirige al login
    
    publicacion_dao = factory.crear_publicacion_dao(MONGO_DB_CONFIG)
    usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)
    foto_perfil_dao = factory.crear_foto_perfil_dao(MONGO_DB_CONFIG)

    # Métodos DTO
    usuario_info = UsuarioDTO.obtener_informacion_usuario(usuario_dao, foto_perfil_dao, session['id_usuario'])
    publicaciones = PublicacionDTO.obtener_informacion_publicaciones(publicacion_dao, usuario_dao, session['id_usuario'])

    return render_template('publicaciones.html', publicaciones=publicaciones, user=usuario_info)

@app.route('/likear_publicacion/<int:id_publicacion>')
@app.route('/likear_publicacion/<int:id_publicacion>', methods=['GET'])
def likear_publicacion(id_publicacion):
    id_usuario = session['id_usuario']

    usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)
    likeado = usuario_dao.verificar_like(id_publicacion, id_usuario)

    if likeado:
        usuario_dao.unlikear_publicacion(id_publicacion, id_usuario)
    else:
        usuario_dao.likear_publicacion(id_publicacion, id_usuario)

    # Obtener la URL de redirección desde next_url o por defecto redirigir al perfil
    next_url = request.args.get('next_url', url_for('perfil', id_usuario=id_usuario))

    return redirect(next_url)


@app.route('/perfil/<int:id_usuario>')
def perfil(id_usuario=None):
    if 'id_usuario' not in session:
        return redirect(url_for('inicio'))

    usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)
    foto_perfil_dao = factory.crear_foto_perfil_dao(MONGO_DB_CONFIG)
    publicacion_dao = factory.crear_publicacion_dao(MONGO_DB_CONFIG)

    if id_usuario is None:  
        id_usuario = session['id_usuario']  # Si no se proporciona, usa el usuario en sesión

    publicaciones_usuario = PublicacionDTO.obtener_informacion_publicaciones(publicacion_dao, usuario_dao, session['id_usuario'],id_usuario)  # Obtener publicaciones del usuario
    publicaciones = PublicacionDTO.obtener_informacion_publicaciones(publicacion_dao, usuario_dao, session['id_usuario'])
    usuario_info = UsuarioDTO.obtener_informacion_usuario(usuario_dao, foto_perfil_dao, id_usuario)

    # Verificar si el usuario en sesión ya sigue al perfil visitado
    id_usuario_sesion = session['id_usuario']
    sigue_al_usuario = usuario_dao.verificar_seguimiento(id_usuario_sesion, id_usuario)

    return render_template('perfil.html', publicaciones_usuario=publicaciones_usuario, publicaciones=publicaciones, user=usuario_info, sigue_al_usuario=sigue_al_usuario)

@app.route('/editar_perfil', methods=['GET', 'POST'])
def editar_perfil():
    if 'id_usuario' not in session:
        return redirect(url_for('inicio'))

    usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)
    foto_perfil_dao = factory.crear_foto_perfil_dao(MONGO_DB_CONFIG)
    user_data = UsuarioDTO.obtener_informacion_usuario(usuario_dao, foto_perfil_dao, session['id_usuario'])
    if request.method == 'POST':
        nuevo_nombre = request.form['nuevo_nombre']
        nuevo_mensaje = request.form['nuevo_mensaje']
        id_usuario = session['id_usuario']

        # Procesar la imagen si se subió un archivo
        if 'foto_perfil' in request.files:
            file = request.files['foto_perfil']
            if file and file.filename != '':
                file_bytes = file.read()

                tipo_imagen = imghdr.what(None, file_bytes)
                if not tipo_imagen or tipo_imagen not in ['jpeg', 'png', 'gif']:
                    return render_template('editar_perfil.html', error=True, mensaje="Formato de imagen no válido", user=user_data)

                # Abrir la imagen y hacerla cuadrada
                image = Image.open(io.BytesIO(file_bytes))

                # Determinar el lado más corto para recortar
                min_side = min(image.width, image.height)
                left = (image.width - min_side) // 2
                top = (image.height - min_side) // 2
                right = left + min_side
                bottom = top + min_side

                image = image.crop((left, top, right, bottom))  # Recortar a cuadrado
                image = image.resize((400, 400), Image.LANCZOS)  # Redimensionar a 400x400 px

                # Convertir la imagen editada a Base64
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                foto_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

                foto_perfil_dao.actualizar_foto_perfil(id_usuario, foto_base64)

        # Actualizar los datos del usuario en SQL Server
        resultado = usuario_dao.actualizar_datos_usuario(id_usuario, nuevo_nombre, nuevo_mensaje)

        if resultado:
            session['nombre_usuario'] = nuevo_nombre
            return redirect(url_for('perfil', id_usuario=session['id_usuario']))
        else:
            user_data = usuario_dao.obtener_usuario_id(session['id_usuario'])
            return render_template('editar_perfil.html', error=True, mensaje="Error el usuario ya existe", user=user_data)
    
    return render_template('editar_perfil.html', user=user_data)

@app.route('/buscar_usuarios')
def buscar_usuarios():
    query = request.args.get('query', '') # Obtener el término de búsqueda desde la URL

    usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)
    resultados = usuario_dao.buscar_usuarios(query)  # Agregar método en el DAO

    return jsonify(resultados)

@app.route('/seguir_usuario/<int:id_usuario>')
def seguir_usuario(id_usuario):
    id_seguidor = session['id_usuario']
    usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)

    sigue = usuario_dao.verificar_seguimiento(id_seguidor, id_usuario)

    if sigue:
        usuario_dao.dejar_seguir_usuario(id_seguidor, id_usuario)
    else:
        print(f"{id_seguidor} comenzará a seguir a {id_usuario}")
        usuario_dao.seguir_usuario(id_seguidor, id_usuario)

    return redirect(url_for('perfil', id_usuario=id_usuario))

@app.route('/logout')
def logout(): # Se elimina la sesión activa
    session.pop('id_usuario', None)
    session.pop('nombre_usuario', None)
    return redirect(url_for('inicio')) # Se redirecciona al login

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
