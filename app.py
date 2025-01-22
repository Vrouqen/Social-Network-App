from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from factory import DatabaseFactory

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

# Factory
factory = DatabaseFactory()

@app.route('/')
def inicio():
    return render_template('inicio_sesion.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Obtener DAO de usuarios
        usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)
        user_data = usuario_dao.verificar_usuario(username, password)
        
        if user_data:
            session['id_usuario'] = user_data['id']
            session['nombre_usuario'] = user_data['username']
            
            # Obtener DAO de fotos de perfil
            foto_perfil_dao = factory.crear_foto_perfil_dao(MONGO_DB_CONFIG)
            profile_picture = foto_perfil_dao.obtener_foto_perfil(user_data['id'])
            
            return redirect(url_for('perfil'))
        
        return redirect(url_for('inicio'))
    
    return redirect(url_for('inicio'))

@app.route('/perfil')
def perfil():
    if 'id_usuario' not in session:
        return redirect(url_for('inicio'))

    usuario_dao = factory.crear_usuario_dao(SQL_SERVER_CONFIG)
    user_data = usuario_dao.obtener_usuario_id(session['id_usuario'])

    foto_perfil_dao = factory.crear_foto_perfil_dao(MONGO_DB_CONFIG)
    foto_perfil = foto_perfil_dao.obtener_foto_perfil(session['id_usuario'])
    
    return render_template('perfil.html', user=user_data, profile_picture=foto_perfil)

@app.route('/logout')
def logout():
    session.pop('id_usuario', None)
    session.pop('nombre_usuario', None)
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    app.run(debug=True)
