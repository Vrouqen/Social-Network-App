import pyodbc
from pymongo import MongoClient
from abc import ABC, abstractmethod
import factory
import os
import base64
from datetime import datetime

# Clase abstracta para conexión
class Conexion(ABC):
    def __init__(self, config):
        self.config = config  # Parámetros que tendrán la conexión
        self.conectar()  # Se conecta instantáneamente al crear el objeto conexión

    @abstractmethod
    def conectar(self):
        pass

# Conexión a SQL Server
class ConexionSQLServer(Conexion):
    def conectar(self):
        try:
            self.conexion = pyodbc.connect(
                f"DRIVER={self.config['driver']};"
                f"SERVER={self.config['server']};"
                f"DATABASE={self.config['database']};"
                f"UID={self.config['username']};"
                f"PWD={self.config['password']}",
                autocommit=False
            )
            self.cursor = self.conexion.cursor() # Genera la conexión con los datos
        except pyodbc.Error as e:
            print(f"Error al conectar a SQL Server: {e}")
            raise

    def commit(self): # Confirmar insersiones de datos
        try:
            self.conexion.commit()
        except Exception as e:
            print(f"Error en commit: {e}")

    def rollback(self): # Cancelar si no se confirma la inserción de datos
        self.conexion.rollback()

# Conexión a MongoDB
class ConexionMongo(Conexion):
    def conectar(self):
        try:
            self.client = MongoClient(
                f"mongodb://{self.config['username']}:{self.config['password']}@{self.config['host']}:{self.config['port']}/"
            ) # Cadena de conexión a Mongo
            self.db = self.client[self.config["database"]] # Se toma la base de datos 
            self.collection = self.db[self.config["collection"]] # Se toma la colección de datos
            print("Conexión exitosa a MongoDB")
        except Exception as e:
            print(f"Error al conectar a MongoDB: {e}")
            raise
        
# DAO para usuarios en SQL Server
class UsuarioDAO:
    def __init__(self, conexion_sql):
        self.conexion = conexion_sql # Obtiene la conexión del objeto concreto ConexionSQLServer
        self.cursor = self.conexion.cursor # Se ejecuta la conexión
    
    def verificar_usuario(self, username_or_email, password): #Método que devuelve el id de usuario si ingresa credenciales correctamente
        query = "EXEC ValidarInicioSesion ?, ?" # Procedimiento almacenado
        self.cursor.execute(query, username_or_email, password) # Ejecuta el procedimiento
        result = self.cursor.fetchone()
        if result: #Valida que haya retornado una respuesta
            usuario_id = result[0]
            return self.obtener_usuario_id(usuario_id) #Retorna los datos del usuario
        return None

    def actualizar_datos_usuario(self, id_usuario, nuevo_nombre, nuevo_mensaje):
        query = "EXEC ActualizarUsuario @id_usuario=?, @nuevo_nombre=?, @nuevo_mensaje=?"  # Procedimiento almacenado
        self.cursor.execute(query, (id_usuario, nuevo_nombre, nuevo_mensaje)) # Se ejecuta el prodecimiento
        self.conexion.commit() # Se confirma la alteración de datos
        return True 

    def buscar_usuarios(self, query):
        query_sql = "EXEC BuscarUsuarios ?" # Procedimiento almacenado
        self.cursor.execute(query_sql, query) # Se ejecuta el procedimiento almacenado
        resultados = self.cursor.fetchall()

        # Retorna el id del usuario y el nombre para operar en la interfaz
        return [{'id': row[0], 'username': row[1]} for row in resultados] if resultados else [] 

    def likear_publicacion(self, id_publicacion, id_usuario):
        query = "EXEC LikearPublicacion ?, ?" # Procedimiento almacenado
        self.cursor.execute(query, id_publicacion, id_usuario) # Ejecuta el prodecimiento almacenado
        self.conexion.commit() # Se confirma la inserción de datos
        
    def unlikear_publicacion(self, id_publicacion, id_usuario):
        query = "EXEC UnlikearPublicacion ?, ?" # Procedimiento almacenado
        self.cursor.execute(query, id_publicacion, id_usuario) # Ejecuta el prodecimiento almacenado
        self.conexion.commit() # Se confirma la inserción de datos

    def verificar_like(self,id_publicacion, id_usuario):
        query = " EXEC VerificarLike ?, ?" # Procedimiento almacenado
        self.cursor.execute(query, (id_publicacion, id_usuario)) # Ejecuta el prodecimiento almacenado
        resultado = self.cursor.fetchone()
        return resultado[0] > 0 # Se confirma la inserción de datos

    def seguir_usuario(self, id_seguidor, id_seguido):
        query = "EXEC SeguirUsuario ?, ?" # Procedimiento almacenado 
        self.cursor.execute(query, id_seguidor, id_seguido) # Ejecuta el prodecimiento almacenado
        self.conexion.commit() # Se confirma la inserción de datos

    def dejar_seguir_usuario(self, id_seguidor, id_seguido):
        query = "EXEC DejarSeguirUsuario ?, ?" # Procedimiento almacenado 
        self.cursor.execute(query, id_seguidor, id_seguido) # Ejecuta el prodecimiento almacenado
        self.conexion.commit() # Se confirma la inserción de datos
    
    def verificar_seguimiento(self, id_seguidor, id_seguido):
        query = " EXEC VerificarSeguimiento ?, ?" # Procedimiento almacenado
        self.cursor.execute(query, (id_seguidor, id_seguido)) # Ejecuta el prodecimiento almacenado
        resultado = self.cursor.fetchone() # Se confirma la inserción de datos
        return resultado[0] > 0 # Retorna 0 si no sigue al usuario o 1 si lo sigue

    def obtener_usuario_id(self, id_usuario): #Método que devuelve los datos del usuario ingresando su id
        query = "EXEC RecogerDatosUsuario ?" # Procedimiento almacenado
        self.cursor.execute(query, id_usuario) # Ejecuta el prodecimiento almacenado
        result = self.cursor.fetchone()
        if result: #Valida que haya retornado una respuesta
            return {'id': result[0], 'username': result[1], 'email': result[2], 'descripcion':result[3]} #Devuelve en un diccionario los datos del usuario
        
        return None
    
    def obtener_cant_seguidores(self, id_usuario):
        query = "EXEC ObtenerCantSeguidores ?" # Procedimiento almacenado
        self.cursor.execute(query, id_usuario) # Ejecuta el prodecimiento almacenado
        result = self.cursor.fetchone()
        if result: #Valida que haya retornado una respuesta
            return result[0] # Devuelve el resultado de la consulta
        return None
    
    def obtener_cant_seguidos(self, id_usuario):
        query = "EXEC ObtenerCantSeguidos ?" # Procedimiento almacenado
        self.cursor.execute(query, id_usuario) # Ejecuta el prodecimiento almacenado
        result = self.cursor.fetchone()
        if result: #Valida que haya retornado una respuesta
            return result[0] # Devuelve el resultado de la consulta
        return None
    
    def obtener_cant_likes(self, id_publicacion):
        query = "EXEC ObtenerCantLikes ?" # Procedimiento almacenado
        self.cursor.execute(query, id_publicacion) # Ejecuta el prodecimiento almacenado
        result = self.cursor.fetchone()
        if result: #Valida que haya retornado una respuesta
            return result[0] # Devuelve el resultado de la consulta
        return None

    def registrar_usuario(self, nombre_usuario, correo, contrasena, confirmar_contrasena):
        try:
            query = """DECLARE @Mensaje NVARCHAR(MAX);
                    EXEC CrearUsuario ?, ?, ?, ?, @Mensaje OUTPUT;
                    SELECT @Mensaje;""" # Procedimiento almacenado
            self.cursor.execute(query,(nombre_usuario, correo, contrasena, confirmar_contrasena)) # Se ejectua el prodecimiento almacenado

            # Capturar el mensaje devuelto
            mensaje = self.cursor.fetchone()
            self.conexion.commit()
            return mensaje[0] if mensaje else "Error desconocido al registrar el usuario." # Obtiene mensaje de error
        except Exception as e: # En caso de que ocurra una excepción
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
        photo = self.collection.find_one({'id_usuario': user_id}, {"_id": 0, "foto_perfil": 1}) #Busca la foto de perfil por id en Mongo
        if photo: # Si existe 
            return photo['foto_perfil'] # Retorna la foto
        else:
            return self.obtener_foto_defecto() # Si no la encuentra, llama a la imagen por defecto
        
    def actualizar_foto_perfil(self, user_id, foto_base64):
        self.collection.update_one( # Actualiza el usuario por id
            {'id_usuario': user_id},
            {'$set': {'foto_perfil': foto_base64}},
            upsert=True
        )

    def obtener_foto_defecto(self):
        if os.path.exists(self.ruta_foto_defecto): # Verifica que exista la foto en los archivos del programa
            with open(self.ruta_foto_defecto, "rb") as image_file: # Carga la imagen por defecto desde los archivos del proyecto
                return base64.b64encode(image_file.read()).decode("utf-8") # La retorna en base64
        else:
            return None
        
# DAO para conexión a la colección Publicacion en MongoDB
class PublicacionDAO:
    def __init__(self, conexion_mongo):
        self.conexion = conexion_mongo  # Conexión a MongoDB
        self.collection = self.conexion.db["Publicaciones"]  # Referencia a la colección de publicaciones

    def obtener_nuevo_id_publicacion(self):
        ultima_publicacion = self.collection.find_one({}, sort=[("id_publicacion", -1)]) # Obtiene el id de la última publicación
        if ultima_publicacion and "id_publicacion" in ultima_publicacion:
            return ultima_publicacion["id_publicacion"] + 1 # Incrementa en 1 el 1 de la publicación
        return 1  # Si no hay publicaciones, comenzamos desde 1

    def crear_publicacion(self, id_usuario, contenido, foto_publicacion = None):
        nuevo_id = self.obtener_nuevo_id_publicacion() # Se obtiene el id de la nueva publicación
        nueva_publicacion = { # Se define en un diccionario los datos del nuevo registro
            "id_publicacion": nuevo_id,
            "id_usuario": id_usuario,
            "contenido": contenido,
            "fecha": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), # Formato de la fecha
            "foto_publicacion": foto_publicacion,
            "id_respuesta": None
        }
        self.collection.insert_one(nueva_publicacion) # Inserta el registro en la colección
        return nueva_publicacion

    def responder_publicacion(self, id_usuario, contenido, id_publicacion):
        nuevo_id = self.obtener_nuevo_id_publicacion() # Se obtiene el id de la nueva publicación
        nueva_publicacion = { # Se define en un diccionario los datos del nuevo registro
            "id_publicacion": nuevo_id,
            "id_usuario": id_usuario,
            "contenido": contenido,
            "fecha": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), # Formato de la fecha
            "foto_publicacion": None,
            "id_respuesta": id_publicacion
        }
        self.collection.insert_one(nueva_publicacion) # Inserta el registro en la colección
        return nueva_publicacion

    def obtener_publicaciones(self, id_usuario=None): # Obtiene las publicaciones de todos los usuarios o de uno en particular
        filtro = {"id_usuario": id_usuario} if id_usuario else {} # Verifica si se fitran las publicaciones por usuario
        publicaciones = list(self.collection.find(filtro).sort("fecha", -1)) # Obtiene las publicaciones de la más reciente a la más antigua
        for publicacion in publicaciones:
            publicacion["_id"] = str(publicacion["_id"]) # Se le asigna el atributo id a la publicacion
        return publicaciones

class UsuarioDTO:
    # Se incluyen todos los datos del usuario mezclando información tanto de SQL como MONGO
    def __init__(self, id_usuario, nombre_usuario, correo, descripcion, foto_perfil, cant_seguidos, cant_seguidores):
        self.id_usuario = id_usuario
        self.nombre_usuario = nombre_usuario
        self.correo = correo
        self.descripcion = descripcion
        self.foto_perfil = foto_perfil
        self.cant_seguidos = cant_seguidos
        self.cant_seguidores = cant_seguidores

    def to_dict(self): # Método que devuelve un diccionario para ser implementado en la interfaz
        return {
            "id_usuario": self.id_usuario,
            "nombre_usuario": self.nombre_usuario,
            "correo": self.correo,
            "descripcion": self.descripcion,
            "foto_perfil": self.foto_perfil,
            "cant_seguidos": self.cant_seguidos,
            "cant_seguidores": self.cant_seguidores
        }
    
    def obtener_informacion_usuario(UsuarioDAO, FotoPerfilDAO, id_usuario): # Método para obtenera la información de los DAOS
        data_usuario = UsuarioDAO.obtener_usuario_id(id_usuario) # Se obtiene la información del usuario
        foto_perfil = FotoPerfilDAO.obtener_foto_perfil(id_usuario) # Foto de perfil del usuario
        cant_seguidos = UsuarioDAO.obtener_cant_seguidos(id_usuario) #  Cantidad Seguidores
        cant_seguidores = UsuarioDAO.obtener_cant_seguidores(id_usuario) # Cantidad Seguidos

        # Se crea un objeto de tipo DTO que contiene la información del usuario
        usuario_dto = UsuarioDTO(data_usuario['id'], data_usuario['username'], data_usuario['email'], 
                                 data_usuario['descripcion'], foto_perfil, cant_seguidos, cant_seguidores) 
        return usuario_dto.to_dict() # Se retorna ese objeto en forma de diccionario

class PublicacionDTO:
    # Se incluyen todos los datos de la publicación mezclando información tanto de SQL como MONGO
    def __init__(self, id_publicacion, id_usuario, contenido, fecha, foto_publicacion, id_respuesta, 
                 cant_likes, nombre_usuario, cantidad_likes, like):
        self.id_publicacion = id_publicacion
        self.id_usuario = id_usuario
        self.contenido = contenido
        self.fecha = fecha
        self.foto_publicacion = foto_publicacion
        self.id_respuesta = id_respuesta
        self.cant_likes = cant_likes
        self.nombre_usuario = nombre_usuario
        self.cantidad_likes = cantidad_likes
        self.like = like

    def to_dict(self): # Método que devuelve un diccionario para ser implementado en la interfaz
        return {
            "id_publicacion": self.id_publicacion,
            "id_usuario": self.id_usuario,
            "contenido": self.contenido,
            "fecha": self.fecha,
            "foto_publicacion": self.foto_publicacion,
            "id_respuesta": self.id_respuesta,
            "cantidad_likes": self.cant_likes,
            "nombre_usuario": self.nombre_usuario,
            "cantidad_likes": self.cantidad_likes,
            "like": self.like
        }

    def obtener_informacion_publicaciones(PublicacionDAO, UsuarioDAO, id_usuario_logeado, id_usuario=None):
        if id_usuario is None: # Se verifica si se desea obtener publicaciones de un usuario
            data_publicaciones = PublicacionDAO.obtener_publicaciones()
        else: # De no ser así devuelve las publicaciones de todos los usuarios
            data_publicaciones = PublicacionDAO.obtener_publicaciones(id_usuario)

        publicaciones_enriquecidas = []  # Lista para almacenar los diccionarios de publicaciones

        for publicacion in data_publicaciones:
            nombre_usuario = UsuarioDAO.obtener_usuario_id(publicacion["id_usuario"])["username"] # Se obtiene el usuario de la publicación
            cantidad_likes = UsuarioDAO.obtener_cant_likes(publicacion["id_publicacion"])  # Se obtiene la cantidad de likes
            # Se verifica si el usuario en cuestión likeó la publicación
            verificar_like = UsuarioDAO.verificar_like(publicacion["id_publicacion"], id_usuario_logeado) 

            # Se agregan estos datos a la información de la publicación
            publicacion["nombre_usuario"] = nombre_usuario 
            publicacion["cantidad_likes"] = cantidad_likes
            publicacion["like"] = verificar_like

            # Se crea un objeto de tipo DTO que contiene toda la información de la publicación
            publicacion_dto = PublicacionDTO(
                publicacion['id_publicacion'],
                publicacion['id_usuario'],
                publicacion['contenido'],
                publicacion['fecha'],
                publicacion['foto_publicacion'],
                publicacion['id_respuesta'],
                publicacion['cantidad_likes'],
                publicacion['nombre_usuario'],
                publicacion['cantidad_likes'],
                publicacion['like']
            )
            # Se agrega la información de la publicación a la lista de publicaciones en forma de diccionario
            publicaciones_enriquecidas.append(publicacion_dto.to_dict())  

        return publicaciones_enriquecidas


 
class DatabaseFactory: # Clase padre de los DAO
    def crear_usuario_dao(self, config):
        conexion = ConexionSQLServer(config)
        return UsuarioDAO(conexion)

    def crear_foto_perfil_dao(self, config):
        conexion = ConexionMongo(config)
        return FotoPerfilDAO(conexion)

    def crear_publicacion_dao(self, config):
        conexion = ConexionMongo(config)
        return PublicacionDAO(conexion)

