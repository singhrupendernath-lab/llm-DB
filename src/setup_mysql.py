import pymysql
from src.config import Config

def setup_mysql():
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=int(Config.MYSQL_PORT),
            database=Config.MYSQL_DB
        )

        with connection.cursor() as cursor:
            with open('src/init_mysql.sql', 'r') as f:
                sql_script = f.read()

            # Split by semicolon to execute one by one
            # Note: This is a simple splitter and might fail on complex SQL
            for statement in sql_script.split(';'):
                if statement.strip():
                    cursor.execute(statement)

        connection.commit()
        connection.close()
        print("MySQL database initialized successfully.")
    except Exception as e:
        print(f"Error initializing MySQL: {e}")

if __name__ == "__main__":
    setup_mysql()
