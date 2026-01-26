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

        # Oracle does not support semicolons at the end of SQL statements via its drivers.
        # We wrap the run method to automatically strip it.
        if self.db_type == "oracle":
            self._wrap_run_for_oracle()

    def _wrap_run_for_oracle(self):
        original_run = self.db.run
        def wrapped_run(command, *args, **kwargs):
            if isinstance(command, str):
                # Strip leading/trailing whitespace and trailing semicolon
                command = command.strip().rstrip(';')
            return original_run(command, *args, **kwargs)
        # Bind the wrapped method to the instance
        self.db.run = wrapped_run

    def _create_engine(self):
        if self.db_type == "sqlite":
            return create_engine(f"sqlite:///{Config.SQLITE_PATH}")
        
        elif self.db_type == "mysql":
            user = Config.MYSQL_USER
            password = Config.MYSQL_PASSWORD
            host = Config.MYSQL_HOST
            port = Config.MYSQL_PORT
            database = Config.MYSQL_DB

            if not all([user, host, database]):
                print("Warning: MySQL credentials not fully provided. Falling back to SQLite.")
                return create_engine(f"sqlite:///{Config.SQLITE_PATH}")

            try:
                connection_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
                engine = create_engine(connection_url)
                # Test connection
                with engine.connect() as conn:
                    pass
                return engine
            except Exception as e:
                print(f"Warning: Failed to connect to MySQL ({e}). Falling back to SQLite.")
                return create_engine(f"sqlite:///{Config.SQLITE_PATH}")

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
        if self.db_type == "oracle" and isinstance(query, str):
            query = query.strip().rstrip(';')
        with self.engine.connect() as connection:
            result = connection.execute(text(query))
            return result.fetchall()
