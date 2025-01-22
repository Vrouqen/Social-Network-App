import pyodbc
from pymongo import MongoClient
from abc import ABC, abstractmethod

class AbstractDatabase(ABC):
    @abstractmethod
    def verify_user(self, username_or_email, password):
        pass

    @abstractmethod
    def get_profile_picture(self, user_id):
        pass


class SqlServerDatabase(AbstractDatabase):
    def __init__(self, config):
        self.config = config
        self.conn = pyodbc.connect(
            f'DRIVER={self.config["driver"]};'
            f'SERVER={self.config["server"]};'
            f'DATABASE={self.config["database"]};'
            f'UID={self.config["username"]};'
            f'PWD={self.config["password"]}'
        )
        self.cursor = self.conn.cursor()

    def verify_user(self, username_or_email, password):
        query = """
        EXEC ValidarInicioSesion ?, ?
        """
        self.cursor.execute(query, username_or_email, password)
        result = self.cursor.fetchone()


        usuario_id = result[0]
        query = """
        EXEC RecogerDatosUsuario ?
        """
        self.cursor.execute(query, usuario_id)
        result = self.cursor.fetchone()

        if result and result[0] != 0:
            return {'id': result[0], 'username': result[1], 'email': result[2]}
        return None
    
    def get_user_by_id(self, id_usuario):
        query = """
        EXEC RecogerDatosUsuario ?
        """
        self.cursor.execute(query, id_usuario)
        result = self.cursor.fetchone()

        if result and result[0] != 0:
            return {'id': result[0], 'username': result[1], 'email': result[2]}
        return None
    
    def get_profile_picture(self, user_id):
        # Como no se usa en SQL Server, podemos lanzar una excepción o retornar None
        raise NotImplementedError("SQL Server does not store profile pictures.")


class MongoDatabase(AbstractDatabase):
    def __init__(self, config):
        self.client = MongoClient(f"mongodb://{config['username']}:{config['password']}@{config['host']}:{config['port']}/")
        self.db = self.client[config["database"]]
        self.collection = self.db[config["collection"]]

    def get_profile_picture(self, user_id):
        # Buscar la foto en la base de datos MongoDB usando el id del usuario
        photo = self.collection.find_one({'id_usuario': user_id})
        return photo['foto_perfil'] if photo else None

    def verify_user(self, username_or_email, password):
        return None  # Este método no se usa en MongoDB

class DatabaseFactory:
    def create_sql_server_connection(self, config):
        return SqlServerDatabase(config)

    def create_mongo_connection(self, config):
        return MongoDatabase(config)
