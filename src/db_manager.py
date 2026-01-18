import oracledb
import os
from sqlalchemy import create_engine, text
from langchain_community.utilities import SQLDatabase
from src.config import Config

class DBManager:
    def __init__(self, use_sqlite=None, sqlite_path=None):
        self.use_sqlite = use_sqlite if use_sqlite is not None else Config.USE_SQLITE
        self.sqlite_path = sqlite_path if sqlite_path is not None else Config.SQLITE_PATH
        self.engine = self._create_engine()
        self.db = SQLDatabase(self.engine)

    def _create_engine(self):
        if self.use_sqlite:
            return create_engine(f"sqlite:///{self.sqlite_path}")
        
        # Oracle connection details from Config
        user = Config.ORACLE_USER
        password = Config.ORACLE_PASSWORD
        dsn = Config.ORACLE_DSN
        
        if not all([user, password, dsn]):
            print("Warning: Oracle credentials not fully provided. Falling back to SQLite for demo.")
            return create_engine(f"sqlite:///{self.sqlite_path}")

        # Construct Oracle SQLAlchemy URL
        # Format: oracle+oracledb://user:password@dsn
        connection_url = f"oracle+oracledb://{user}:{password}@{dsn}"
        return create_engine(connection_url)

    def get_db(self):
        return self.db

    def execute_query(self, query):
        with self.engine.connect() as connection:
            result = connection.execute(text(query))
            return result.fetchall()
