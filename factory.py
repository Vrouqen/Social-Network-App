import pyodbc
from pymongo import MongoClient
from abc import ABC, abstractmethod
import os
import base64
from datetime import datetime

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
            f'PWD={self.config["password"]}',
            autocommit=False
        )
        self.cursor = self.conexion.cursor() #Se conecta con la configuración
    
    def commit(self):
        try:
            print("Realizando commit...")
            self.conexion.commit()
            print("Commit realizado correctamente.")
        except Exception as e:
            print(f"Error en commit: {e}")
    
    def rollback(self):
        """Revierte la transacción actual."""
        self.conexion.rollback()

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

    def actualizar_nombre_usuario(self, id_usuario, nuevo_nombre):
        try:
            query = "EXEC ActualizarUsuario ?, ?"
            self.cursor.execute(query, id_usuario, nuevo_nombre)
            self.conexion.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar usuario: {e}")
            self.conexion.rollback()
            return False

    def obtener_usuario_id(self, id_usuario): #Método que devuelve los datos del usuario ingresando su id
        query = "EXEC RecogerDatosUsuario ?"
        self.cursor.execute(query, id_usuario)
        result = self.cursor.fetchone()
        if result: #Valida que haya retornado una respuesta
            return {'id': result[0], 'username': result[1], 'email': result[2]} #Devuelve en un diccionario los datos del usuario
        return None
    
    def obtener_cant_seguidores(self, id_usuario):
        query = "EXEC ObtenerCantSeguidores ?"
        self.cursor.execute(query, id_usuario)
        result = self.cursor.fetchone()
        if result: #Valida que haya retornado una respuesta
            return result[0] # Devuelve el resultado de la consulta
        return None
    
    def obtener_cant_seguidos(self, id_usuario):
        query = "EXEC ObtenerCantSeguidos ?"
        self.cursor.execute(query, id_usuario)
        result = self.cursor.fetchone()
        if result: #Valida que haya retornado una respuesta
            return result[0] # Devuelve el resultado de la consulta
        return None

    def registrar_usuario(self, nombre_usuario, correo, contrasena, confirmar_contrasena):
        try:
            query = """DECLARE @Mensaje NVARCHAR(MAX);
                    EXEC CrearUsuario ?, ?, ?, ?, @Mensaje OUTPUT;
                    SELECT @Mensaje;"""
            self.cursor.execute(query, (nombre_usuario, correo, contrasena, confirmar_contrasena))

            # Capturar el mensaje devuelto
            mensaje = self.cursor.fetchone()
            self.conexion.commit()
            return mensaje[0] if mensaje else "Error desconocido al registrar el usuario."
        except Exception as e:
            print(f"Error al registrar usuario: {e}")
            self.conexion.rollback()
            return f"Error al registrar usuario: {e}"

# DAO para conexión a la colección Fotos_Perfil en MongoDB
class FotoPerfilDAO:
    def __init__(self, conexion_mongo, ruta_foto_defecto="./static/images/foto_defecto.png"):
        self.conexion = conexion_mongo  # Se guarda la conexión a MongoDB
        self.collection = self.conexion.collection  # Referencia a la colección Fotos_Perfil
        self.ruta_foto_defecto = ruta_foto_defecto  # Ruta de la foto por defecto
    
    def obtener_foto_perfil(self, user_id):
        try:
            photo = self.collection.find_one({'id_usuario': user_id}, {"_id": 0, "foto_perfil": 1}) #Busca la foto de perfil en la Base de Mongo
            if photo:
                return photo['foto_perfil']
            else:
                return self.obtener_foto_defecto() #Si no la encuentra llama a la imagen por defecto
        except Exception as e:
            return self.obtener_foto_defecto()

    def obtener_foto_defecto(self):
        if os.path.exists(self.ruta_foto_defecto):
            with open(self.ruta_foto_defecto, "rb") as image_file: #Carga la imagen por defecto desde los archivos del proyecto
                return base64.b64encode(image_file.read()).decode("utf-8")
        else:
            return None
        
class PublicacionDAO:
    def __init__(self, conexion_mongo):
        self.conexion = conexion_mongo  # Conexión a MongoDB
        self.collection = self.conexion.db["Publicaciones"]  # Referencia a la colección de publicaciones

    def obtener_nuevo_id_publicacion(self):
        """Obtiene el último id_publicacion y lo incrementa."""
        ultima_publicacion = self.collection.find_one({}, sort=[("id_publicacion", -1)])
        if ultima_publicacion and "id_publicacion" in ultima_publicacion:
            return ultima_publicacion["id_publicacion"] + 1
        return 1  # Si no hay publicaciones, comenzamos desde 1.

    def crear_publicacion(self, id_usuario, contenido):
        """Crea una nueva publicación con un id_publicacion autonumérico."""
        nuevo_id = self.obtener_nuevo_id_publicacion()
        nueva_publicacion = {
            "id_publicacion": nuevo_id,
            "id_usuario": id_usuario,
            "contenido": contenido,
            "fecha": datetime.utcnow().isoformat(),
            "foto_publicacion": None,
            "id_respuesta": None
        }
        self.collection.insert_one(nueva_publicacion)
        return nueva_publicacion
        
    def obtener_publicaciones(self, id_usuario=None):
        try:
            filtro = {"id_usuario": id_usuario} if id_usuario else {}  # Filtrar por usuario si se proporciona
            publicaciones = list(self.collection.find(filtro).sort("fecha", -1))  # Ordenar por fecha descendente
            
            for publicacion in publicaciones:  # Convertir ObjectId a string y limpiar campos innecesarios
                publicacion["_id"] = str(publicacion["_id"])
            
            return publicaciones
        except Exception as e:
            return {"error": f"Error al obtener publicaciones: {str(e)}"}


class DatabaseFactory:
    def crear_usuario_dao(self, config):
        conexion = ConexionSQLServer(config)
        return UsuarioDAO(conexion)

    def crear_foto_perfil_dao(self, config):
        conexion = ConexionMongo(config)
        return FotoPerfilDAO(conexion)

    def crear_publicacion_dao(self, config):
        conexion = ConexionMongo(config)
        return PublicacionDAO(conexion)
