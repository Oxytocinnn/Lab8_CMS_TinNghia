import os
import sys
import urllib.parse

try:
    import pyodbc
except ImportError:
    pyodbc = None

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SQL_SERVER = os.environ.get("SQL_SERVER", r"localhost\SQLEXPRESS")
DB_NAME = os.environ.get("SQL_DATABASE", "FoodieNest_Lab8")
ODBC_DRIVER = os.environ.get("ODBC_DRIVER", "ODBC Driver 17 for SQL Server")


def ensure_database_exists(db_name=DB_NAME, server=SQL_SERVER):
    if not pyodbc:
        return False
    try:
        conn_str = (
            f"Driver={{{ODBC_DRIVER}}};"
            f"Server={server};"
            "Database=master;"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )
        conn = pyodbc.connect(conn_str, autocommit=True, timeout=3)
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{db_name}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE [{db_name}]")
            print(f"[SQL Server] Đã tạo CSDL: {db_name}")
        conn.close()
        return True
    except Exception as e:
        print(f"[SQL Server] Không thể kết nối SQL Server ({e}). Sẽ chuyển sang SQLite fallback.")
        return False


def get_database_uri():
    # Ưu tiên biến môi trường CSDL đám mây (Neon / Supabase / PostgreSQL / MySQL)
    env_db = os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL")
    if env_db:
        if env_db.startswith("postgres://"):
            env_db = env_db.replace("postgres://", "postgresql://", 1)
        return env_db

    # Thử kết nối SQL Server nếu có pyodbc
    if pyodbc:
        try:
            conn_str = (
                f"Driver={{{ODBC_DRIVER}}};"
                f"Server={SQL_SERVER};"
                "Database=master;"
                "Trusted_Connection=yes;"
                "TrustServerCertificate=yes;"
            )
            test_conn = pyodbc.connect(conn_str, autocommit=True, timeout=2)
            test_conn.close()

            odbc_str = (
                f"Driver={{{ODBC_DRIVER}}};"
                f"Server={SQL_SERVER};"
                f"Database={DB_NAME};"
                "Trusted_Connection=yes;"
                "TrustServerCertificate=yes;"
            )
            encoded = urllib.parse.quote_plus(odbc_str)
            return f"mssql+pyodbc:///?odbc_connect={encoded}"
        except Exception:
            pass

    # Fallback SQLite local
    sqlite_path = os.path.join(BASE_DIR, "foodienest.db").replace("\\", "/")
    return f"sqlite:///{sqlite_path}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "foodienest-lab8-community-secret-pwd301")
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
