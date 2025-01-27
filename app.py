from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from factory import DatabaseFactory
from flask import jsonify

app = Flask(__name__)

# Configuración de las bases de datos
SQL_SERVER_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': 'localhost,1433',
    'database': 'Registros',
    'username': 'sa',
    'password': 'ProyectoGrupo5'
}
MONGO_DB_CONFIG = {
    'host': 'localhost',
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

@app.route('/editar_perfil', methods=['GET', 'POST'])
def editar_perfil():
    if 'id_usuario' not in session:
        return redirect(url_for('inicio'))

    usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)

    if request.method == 'POST':
        nuevo_nombre = request.form['nuevo_nombre']
        nuevo_mensaje = request.form['nuevo_mensaje']
        id_usuario = session['id_usuario']

        # Actualizar tanto el nombre como el mensaje del usuario
        resultado = usuario_dao.actualizar_datos_usuario(id_usuario, nuevo_nombre, nuevo_mensaje)

        if resultado:
            session['nombre_usuario'] = nuevo_nombre  # Actualiza el nombre en la sesión
            return redirect(url_for('perfil', id_usuario=session['id_usuario']))
        else:
            # Mostrar un error si no se pudo actualizar
            user_data = usuario_dao.obtener_usuario_id(session['id_usuario'])
            return render_template('editar_perfil.html', error=True, mensaje="Error el usuario ya existe", user=user_data)

    # Obtener los datos actuales del usuario para mostrarlos en el formulario
    user_data = usuario_dao.obtener_usuario_id(session['id_usuario'])
    return render_template('editar_perfil.html', user=user_data)

@app.route('/crear_publicacion', methods=['POST'])
def crear_publicacion():
    if 'id_usuario' not in session: # Verifica que exista una sesión activa
        return redirect(url_for('inicio')) # De no ser así lo direcciona al login

    contenido = request.form['contenido']
    id_usuario = session['id_usuario']
    
    # Obtener el DAO de publicaciones
    publicacion_dao = factory.crear_publicacion_dao(MONGO_DB_CONFIG)
    resultado = publicacion_dao.crear_publicacion(id_usuario, contenido) # Se almacena la publicación en la base de datos

    return redirect(url_for('publicaciones'))  # Redirigir a la página donde se muestran las publicaciones

@app.route('/publicaciones')
def publicaciones():
    if 'id_usuario' not in session: # Verifica que exista una sesión activa
        return redirect(url_for('inicio')) # De no ser así lo direcciona al login
    
    publicacion_dao = factory.crear_publicacion_dao(MONGO_DB_CONFIG)
    publicaciones = publicacion_dao.obtener_publicaciones() # Se obtiene un JSON con las publicaciones

    usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)

    # Enriquecer cada publicación con nombre de usuario y cantidad de likes
    for publicacion in publicaciones:
        usuario = usuario_dao.obtener_usuario_id(publicacion["id_usuario"]) # Obtiene la información del usuario por id
        cant_likes = usuario_dao.obtener_cant_likes(publicacion["id_publicacion"]) # Obtiene la cantidad de likes de la publicación
        verificar_like = usuario_dao.verificar_like(publicacion["id_publicacion"], session['id_usuario']) # Verifica que el usuario haya likeado
        if usuario: 
            publicacion["nombre_usuario"] = usuario["username"] # Se le asigna al nombre de usuario de la publicación el username de la consulta
            publicacion["cant_likes"] = cant_likes # Se le asigna la cantidad de likes a la publicación  
            publicacion["like"] = verificar_like
    
    user_data = usuario_dao.obtener_usuario_id(session['id_usuario']) # Obtener información del usuario en sesión

    foto_perfil_dao = factory.crear_foto_perfil_dao(MONGO_DB_CONFIG)
    foto_perfil = foto_perfil_dao.obtener_foto_perfil(session['id_usuario']) # Obtener foto de perfil

    return render_template('publicaciones.html', publicaciones=publicaciones, user=user_data, profile_picture=foto_perfil)

@app.route('/likear_publicacion/<int:id_publicacion>')
def likear_publicacion(id_publicacion):
    id_usuario = session['id_usuario']
    usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)

    likeado = usuario_dao.verificar_like(id_publicacion, id_usuario)

    if likeado:
        usuario_dao.unlikear_publicacion(id_publicacion, id_usuario)
    else:
        usuario_dao.likear_publicacion(id_publicacion, id_usuario)

    next_url = request.args.get('next_url', url_for('publicaciones'))

    return redirect(next_url)

@app.route('/perfil/<int:id_usuario>')
def perfil(id_usuario=None):
    if 'id_usuario' not in session:
        return redirect(url_for('inicio'))

    usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)

    if id_usuario is None:  
        id_usuario = session['id_usuario']  # Si no se proporciona, usa el usuario en sesión

    user_data = usuario_dao.obtener_usuario_id(id_usuario)  # Obtener datos del usuario
    if not user_data:
        return redirect(url_for('publicaciones'))  # Redirige si el usuario no existe

    publicacion_dao = factory.crear_publicacion_dao(MONGO_DB_CONFIG)
    publicaciones = publicacion_dao.obtener_publicaciones(id_usuario)  # Obtener publicaciones del usuario

    for publicacion in publicaciones:
        usuario = usuario_dao.obtener_usuario_id(publicacion["id_usuario"])
        cant_likes = usuario_dao.obtener_cant_likes(publicacion["id_publicacion"])
        verificar_like = usuario_dao.verificar_like(publicacion["id_publicacion"], session['id_usuario']) 
         # Verificar los likes en la publicaciones
        publicacion["cant_likes"] = cant_likes  
        publicacion["nombre_usuario"] = usuario['username']
        publicacion["like"] = verificar_like

    cant_seguidores = usuario_dao.obtener_cant_seguidores(id_usuario)
    cant_seguidos = usuario_dao.obtener_cant_seguidos(id_usuario)

    foto_perfil_dao = factory.crear_foto_perfil_dao(MONGO_DB_CONFIG)
    foto_perfil = foto_perfil_dao.obtener_foto_perfil(id_usuario)

    # Verificar si el usuario en sesión ya sigue al perfil visitado
    id_usuario_sesion = session['id_usuario']
    sigue_al_usuario = usuario_dao.verificar_seguimiento(id_usuario_sesion, id_usuario)

    return render_template('perfil.html', publicaciones=publicaciones, user=user_data, 
                           profile_picture=foto_perfil, cant_seguidores=cant_seguidores, 
                           cant_seguidos=cant_seguidos, sigue_al_usuario=sigue_al_usuario)

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
    app.run(debug=True)
