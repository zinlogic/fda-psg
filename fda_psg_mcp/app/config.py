import os
from dotenv import load_dotenv

# Cargar variables del entorno
load_dotenv()

class Config:
    # Base de Datos
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "db_dlab")
    DB_USER = os.getenv("DB_USER", "dlab")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "dl0041")

    # Timeouts e hilos
    SQL_STATEMENT_TIMEOUT_MS = int(os.getenv("SQL_STATEMENT_TIMEOUT_MS", "5000"))
    SQL_LOCK_TIMEOUT_MS = int(os.getenv("SQL_LOCK_TIMEOUT_MS", "1000"))
    
    # Límites de salida
    SQL_MAX_ROWS = int(os.getenv("SQL_MAX_ROWS", "200"))
    SQL_MAX_RESPONSE_BYTES = int(os.getenv("SQL_MAX_RESPONSE_BYTES", "1048576")) # 1 MB default
    
    GUIDANCE_MAX_MARKDOWN_BYTES = int(os.getenv("GUIDANCE_MAX_MARKDOWN_BYTES", "50000"))
    GUIDANCE_CONTEXT_MAX_CHUNKS = int(os.getenv("GUIDANCE_CONTEXT_MAX_CHUNKS", "20"))
    
    # Servidor MCP Config
    MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
    MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")  # stdio o sse

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
