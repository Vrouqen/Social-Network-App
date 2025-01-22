import pyodbc
from pymongo import MongoClient
from abc import ABC, abstractmethod

# Clase abstracta para las conexiones
class Conexion(ABC):
    def __init__(self, config):
        self.config = config #Parámetros que tendrán la conexión
        self.conectar() #Se conecta instantáneamente al crear el objeto conexión
    
    @abstractmethod #Método que estará en todos los objetos que sen de tipo conexión
    def conectar(self):
        pass

# Conexión a SQL Server
class ConexionSQLServer(Conexion):
    def conectar(self): #Función que conecta a la base de datos
        self.conexion = pyodbc.connect(
            f'DRIVER={self.config["driver"]};'
            f'SERVER={self.config["server"]};'
            f'DATABASE={self.config["database"]};'
            f'UID={self.config["username"]};'
            f'PWD={self.config["password"]}'
        )
        self.cursor = self.conexion.cursor() #Se conecta con la configuración

# Conexión a MongoDB
class ConexionMongo(Conexion):
    def conectar(self):
        self.client = MongoClient( #Se crea la cadena de conexión
            f"mongodb://{self.config['username']}:{self.config['password']}@{self.config['host']}:{self.config['port']}/"
        )
        self.db = self.client[self.config["database"]] #Hace referencia la base de datos
        self.collection = self.db[self.config["collection"]] #Hace referencia a la colección de datos en MongoDB

# DAO para usuarios en SQL Server
class UsuarioDAO:
    def __init__(self, conexion_sql):
        self.conexion = conexion_sql #Obtiene la conexión del objeto concreto ConexionSQLServer
        self.cursor = self.conexion.cursor #???? revisar conjuntamente a la linea 25
    
    def verificar_usuario(self, username_or_email, password): #Método que devuelve el id de usuario si ingresa credenciales correctamente
        query = "EXEC ValidarInicioSesion ?, ?"
        self.cursor.execute(query, username_or_email, password)
        result = self.cursor.fetchone()
        if result: #Valida que haya retornado una respuesta
            usuario_id = result[0]
            return self.obtener_usuario_id(usuario_id) #Retorna los datos del usuario
        return None

    def obtener_usuario_id(self, id_usuario): #Método que devuelve los datos del usuario ingresando su id
        query = "EXEC RecogerDatosUsuario ?"
        self.cursor.execute(query, id_usuario)
        result = self.cursor.fetchone()
        if result: #Valida que haya retornado una respuesta
            return {'id': result[0], 'username': result[1], 'email': result[2]} #Devuelve en un diccionario los datos del usuario
        return None

# DAO para conexión a la colección Fotos_Perfil en MongoDB
class FotoPerfilDAO:
    def __init__(self, conexion_mongo):
        self.conexion = conexion_mongo #Indica como atributo conexión el objeto concreto conexión MongoDB
        self.collection = self.conexion.collection #Hace referencia a la colección del objeto concreto
    
    def obtener_foto_perfil(self, user_id): #Toca hacerlo procedimiento almacenado!!!
        photo = self.collection.find_one({'id_usuario': user_id})
        return photo['foto_perfil'] if photo else None

# Factory que devuelve DAOs en lugar de solo conexiones
class DatabaseFactory:
    def crear_usuario_dao(self, config):
        conexion = ConexionSQLServer(config)
        return UsuarioDAO(conexion) #Se crea un objeto padre que retornará un objeto hijo DAO proveniente de un objeto concreto conexión 

    def crear_foto_perfil_dao(self, config):
        conexion = ConexionMongo(config)
        return FotoPerfilDAO(conexion) #Se crea un objeto padre que retornará un objeto hijo DAO proveniente de un objeto concreto conexión 
