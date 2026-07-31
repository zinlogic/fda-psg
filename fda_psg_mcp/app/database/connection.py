import time
import logging
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from app.config import Config

# Configurar logging básico
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL, logging.INFO))
logger = logging.getLogger("mcp_database")

class DatabaseConnection:
    _pool = None

    @classmethod
    def get_pool(cls):
        if cls._pool is None:
            try:
                # Ocultar la contraseña en los logs de inicialización
                logger.info(f"Inicializando pool de conexiones a PostgreSQL ({Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}) con usuario '{Config.DB_USER}'")
                cls._pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=2,
                    maxconn=10,
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    database=Config.DB_NAME,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    options=f"-c statement_timeout={Config.SQL_STATEMENT_TIMEOUT_MS} -c lock_timeout={Config.SQL_LOCK_TIMEOUT_MS}"
                )
            except Exception as e:
                logger.critical(f"No se pudo crear el pool de conexiones de la base de datos: {e}")
                raise
        return cls._pool

    @classmethod
    @contextmanager
    def get_connection(cls):
        """
        Context manager para obtener y liberar conexiones del pool.
        Maneja transacciones de forma segura y hace rollback en caso de error.
        """
        conn_pool = cls.get_pool()
        conn = None
        try:
            conn = conn_pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception as rollback_err:
                    logger.error(f"Error al realizar rollback de transacción: {rollback_err}")
            logger.error(f"Error durante la transacción de base de datos: {e}")
            raise
        finally:
            if conn:
                conn_pool.putconn(conn)

    @classmethod
    def close_pool(cls):
        if cls._pool:
            cls._pool.closeall()
            logger.info("Pool de conexiones de base de datos cerrado correctamente.")
            cls._pool = None
