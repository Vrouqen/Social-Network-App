import pyodbc
from pymongo import MongoClient
from abc import ABC, abstractmethod
import os
import base64
from datetime import datetime

# Clase abstracta para las conexiones
class Conexion(ABC):
    def __init__(self, config):
        self.config = config # Parámetros que tendrán la conexión
        self.conectar() # Se conecta instantáneamente al crear el objeto conexión
    
    @abstractmethod # Método que estará en todos los objetos que sean de tipo conexión
    def conectar(self):
        pass

# Conexión a SQL Server
class ConexionSQLServer(Conexion):
    def conectar(self): # Función que conecta a la base de datos
        self.conexion = pyodbc.connect(
            f'DRIVER={self.config["driver"]};'
            f'SERVER={self.config["server"]};'
            f'DATABASE={self.config["database"]};'
            f'UID={self.config["username"]};'
            f'PWD={self.config["password"]}',
            autocommit=False
        )
        self.cursor = self.conexion.cursor() # Se conecta con la configuración
    
    def commit(self): # Se confirma la transacción
        try:
            self.conexion.commit()
        except Exception as e:
            print(f"Error en commit: {e}")
    
    def rollback(self): # Se revierte la transacción en caso de error
        self.conexion.rollback()

# Conexión a MongoDB
class ConexionMongo(Conexion):
    def conectar(self):
        self.client = MongoClient( # Se crea la cadena de conexión
            f"mongodb://{self.config['username']}:{self.config['password']}@{self.config['host']}:{self.config['port']}/"
        )
        self.db = self.client[self.config["database"]] #Hace referencia la base de datos
        self.collection = self.db[self.config["collection"]] #Hace referencia a la colección de datos en MongoDB

# DAO para usuarios en SQL Server
class UsuarioDAO:
    def __init__(self, conexion_sql):
        self.conexion = conexion_sql # Obtiene la conexión del objeto concreto ConexionSQLServer
        self.cursor = self.conexion.cursor # Se ejecuta la conexión
    
    def verificar_usuario(self, username_or_email, password): #Método que devuelve el id de usuario si ingresa credenciales correctamente
        query = "EXEC ValidarInicioSesion ?, ?"
        self.cursor.execute(query, username_or_email, password)
        result = self.cursor.fetchone()
        if result: #Valida que haya retornado una respuesta
            usuario_id = result[0]
            return self.obtener_usuario_id(usuario_id) #Retorna los datos del usuario
        return None

    def actualizar_datos_usuario(self, id_usuario, nuevo_nombre, nuevo_mensaje):
        try:
            # Llamada al procedimiento almacenado 'ActualizarUsuario'
            query = "EXEC ActualizarUsuario @id_usuario=?, @nuevo_nombre=?, @nuevo_mensaje=?"
            self.cursor.execute(query, (id_usuario, nuevo_nombre, nuevo_mensaje))
            self.conexion.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar los datos del usuario: {e}")
            self.conexion.rollback()
            return False

    def buscar_usuarios(self, query):
        query_sql = "EXEC BuscarUsuarios ?"  
        self.cursor.execute(query_sql, query)
        resultados = self.cursor.fetchall()
        return [{'id': row[0], 'username': row[1]} for row in resultados] if resultados else []

    def likear_publicacion(self, id_publicacion, id_usuario):
        try:
            query = "EXEC LikearPublicacion ?, ?" 
            self.cursor.execute(query, id_publicacion, id_usuario)
            self.conexion.commit() # Ejecuta el prodecimiento almacenado para insertar registros
        except Exception as e: # En tal caso de que ocurra un error
            print(f"Error al dar like: {e}")
            self.conexion.rollback()
            return False
        
    def unlikear_publicacion(self, id_publicacion, id_usuario):
        try:
            query = "EXEC UnlikearPublicacion ?, ?"
            self.cursor.execute(query, id_publicacion, id_usuario)
            self.conexion.commit() # Ejecuta el prodecimiento almacenado para insertar registros
        except Exception as e: # En tal caso de que ocurra un error
            print(f"Error al quitar like: {e}")
            self.conexion.rollback()
            return False

    def verificar_like(self,id_publicacion, id_usuario):
        try:
            query = " EXEC VerificarLike ?, ?"
            self.cursor.execute(query, (id_publicacion, id_usuario))
            resultado = self.cursor.fetchone()
            return resultado[0] > 0
        except Exception as e:
            print(f"Error al verificar seguimiento: {e}")
            return False

    def seguir_usuario(self, id_seguidor, id_seguido):
        try:
            query = "EXEC SeguirUsuario ?, ?" 
            self.cursor.execute(query, id_seguidor, id_seguido)
            self.conexion.commit() # Ejecuta el prodecimiento almacenado para insertar registros
        except Exception as e: # En tal caso de que ocurra un error
            print(f"Error al dar like: {e}")
            self.conexion.rollback()
            return False

    def dejar_seguir_usuario(self, id_seguidor, id_seguido):
        try:
            query = "EXEC DejarSeguirUsuario ?, ?" 
            self.cursor.execute(query, id_seguidor, id_seguido)
            self.conexion.commit() # Ejecuta el prodecimiento almacenado para insertar registros
        except Exception as e: # En tal caso de que ocurra un error
            print(f"Error al dar like: {e}")
            self.conexion.rollback()
            return False   
    
    def verificar_seguimiento(self, id_seguidor, id_seguido):
        try:
            query = " EXEC VerificarSeguimiento ?, ?"
            self.cursor.execute(query, (id_seguidor, id_seguido))
            resultado = self.cursor.fetchone()
            return resultado[0] > 0
        except Exception as e:
            print(f"Error al verificar seguimiento: {e}")
            return False

    def obtener_usuario_id(self, id_usuario): #Método que devuelve los datos del usuario ingresando su id
        query = "EXEC RecogerDatosUsuario ?"
        self.cursor.execute(query, id_usuario)
        result = self.cursor.fetchone()
        if result: #Valida que haya retornado una respuesta
            return {'id': result[0], 'username': result[1], 'email': result[2], 'descripcion':result[3]} #Devuelve en un diccionario los datos del usuario
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
    
    def obtener_cant_likes(self, id_publicacion):
        query = "EXEC ObtenerCantLikes ?"
        self.cursor.execute(query, id_publicacion)
        result = self.cursor.fetchone()
        if result: #Valida que haya retornado una respuesta
            return result[0] # Devuelve el resultado de la consulta
        return None

    def registrar_usuario(self, nombre_usuario, correo, contrasena, confirmar_contrasena):
        try:
            query = """DECLARE @Mensaje NVARCHAR(MAX);
                    EXEC CrearUsuario ?, ?, ?, ?, @Mensaje OUTPUT;
                    SELECT @Mensaje;"""
            self.cursor.execute(query,(nombre_usuario, correo, contrasena, confirmar_contrasena)) # Se ejectua el prodecimiento almacenado

            # Capturar el mensaje devuelto
            mensaje = self.cursor.fetchone()
            self.conexion.commit()
            return mensaje[0] if mensaje else "Error desconocido al registrar el usuario." # Obtiene mensaje de error
        except Exception as e:
            print(f"Error al registrar usuario: {e}")
            self.conexion.rollback()
            return f"Error al registrar usuario: {e}"

# DAO para conexión a la colección Fotos_Perfil en MongoDB
class FotoPerfilDAO:
    def __init__(self, conexion_mongo, ruta_foto_defecto="./static/images/foto_defecto.png"):
        self.conexion = conexion_mongo
        self.collection = self.conexion.db["Fotos_Perfil"]  # Definir explícitamente la colección
        self.ruta_foto_defecto = ruta_foto_defecto # Ruta para cargar la foto por defecto
    
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
        ultima_publicacion = self.collection.find_one({}, sort=[("id_publicacion", -1)]) # Obtiene el id de la última publicación
        if ultima_publicacion and "id_publicacion" in ultima_publicacion:
            return ultima_publicacion["id_publicacion"] + 1 # Incrementa en 1 el 1 de la publicación
        return 1  # Si no hay publicaciones, comenzamos desde 1.

    def crear_publicacion(self, id_usuario, contenido):
        nuevo_id = self.obtener_nuevo_id_publicacion() # Se obtiene el id de la nueva publicación
        nueva_publicacion = { # Se define en un diccionario los datos del nuevo registro
            "id_publicacion": nuevo_id,
            "id_usuario": id_usuario,
            "contenido": contenido,
            "fecha": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "foto_publicacion": None,
            "id_respuesta": None
        }
        self.collection.insert_one(nueva_publicacion) # Inserta el registro en la colección
        return nueva_publicacion

    def obtener_publicaciones(self, id_usuario=None): # Obtiene las publicaciones de todos los usuarios o de uno en particular
        filtro = {"id_usuario": id_usuario} if id_usuario else {}
        publicaciones = list(self.collection.find(filtro).sort("fecha", -1))
        for publicacion in publicaciones:
            publicacion["_id"] = str(publicacion["_id"])
        return publicaciones

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
