from flask import Flask, render_template, request, redirect, url_for, session
from factory import DatabaseFactory

app = Flask(__name__)

# Configuración de las bases de datos (Conexión de ejemplo)
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

# Factory abstract
factory = DatabaseFactory()

@app.route('/')
def home():
    return render_template('inicio_sesion.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # Verificar credenciales usando la factory de SQL Server
    user_data = factory.create_sql_server_connection(SQL_SERVER_CONFIG).verify_user(username, password)
    
    if user_data:
        # Guardar la información del usuario en la sesión
        session['user_id'] = user_data['id']
        session['username'] = user_data['username']
        
        # Recuperar foto de perfil usando MongoDB
        user_id = user_data['id']
        profile_picture = factory.create_mongo_connection(MONGO_DB_CONFIG).get_profile_picture(user_id)
        
        return render_template('perfil.html', user=user_data, profile_picture=profile_picture)
    else:
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    # Eliminar la sesión cuando el usuario cierre sesión
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
