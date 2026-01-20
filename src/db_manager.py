import oracledb
import os
from sqlalchemy import create_engine, text
from langchain_community.utilities import SQLDatabase
from config import Config

class DBManager:
    def __init__(self, db_type=None, include_tables=None):
        self.db_type = db_type if db_type is not None else Config.DB_TYPE
        self.engine = self._create_engine()
        # allow limiting tables to reduce prompt size
        self.db = SQLDatabase(self.engine, include_tables=include_tables, sample_rows_in_table_info=2)

    def _create_engine(self):
        if self.db_type == "sqlite":
            return create_engine(f"sqlite:///{Config.SQLITE_PATH}")
        
        elif self.db_type == "mysql":
            user = Config.MYSQL_USER
            password = Config.MYSQL_PASSWORD
            host = Config.MYSQL_HOST
            port = Config.MYSQL_PORT
            database = Config.MYSQL_DB

            connection_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
            return create_engine(connection_url)

        elif self.db_type == "oracle":
            user = Config.ORACLE_USER
            password = Config.ORACLE_PASSWORD
            dsn = Config.ORACLE_DSN

            if not all([user, password, dsn]):
                print("Warning: Oracle credentials not fully provided. Falling back to SQLite.")
                return create_engine(f"sqlite:///{Config.SQLITE_PATH}")

            connection_url = f"oracle+oracledb://{user}:{password}@{dsn}"
            return create_engine(connection_url)

        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def get_db(self):
        return self.db

    def execute_query(self, query):
        with self.engine.connect() as connection:
            result = connection.execute(text(query))
            return result.fetchall()
