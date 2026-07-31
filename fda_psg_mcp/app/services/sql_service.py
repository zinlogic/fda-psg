import logging
import json
from typing import Dict, List, Any, Optional
from app.database.connection import DatabaseConnection
from app.config import Config

logger = logging.getLogger("mcp_sql_service")

class SQLService:
    """
    Servicio encargado de ejecutar de manera controlada consultas SQL personalizadas y de solo lectura.
    """

    @staticmethod
    def execute_readonly_query(sql_query: str) -> Dict[str, Any]:
        """
        Ejecuta la consulta SQL recibida dentro de una transacción explícita de solo lectura,
        aplicando límites de tiempo y tamaño.
        """
        results = []
        truncated = False

        with DatabaseConnection.get_connection() as conn:
            # 1. Asegurar que la conexión reutilizada del pool esté en estado limpio
            #    antes de cambiar el modo de sesión (set_session falla dentro de una transacción activa)
            try:
                conn.rollback()
            except Exception:
                pass

            # 2. Forzar modo READ ONLY a nivel de sesión
            conn.set_session(readonly=True, autocommit=False)

            with conn.cursor() as cur:
                # 3. Establecer timeouts locales a la transacción
                cur.execute(f"SET LOCAL statement_timeout = {Config.SQL_STATEMENT_TIMEOUT_MS};")
                cur.execute(f"SET LOCAL lock_timeout = {Config.SQL_LOCK_TIMEOUT_MS};")

                # 4. Ejecutar la consulta del cliente
                cur.execute(sql_query)

                # 5. Leer columnas
                if cur.description is not None:
                    cols = [desc[0] for desc in cur.description]

                    row_count = 0
                    total_bytes = 0

                    while True:
                        row = cur.fetchone()
                        if row is None:
                            break

                        row_count += 1

                        # Formatear fila a diccionario con tipos serializables
                        row_dict = {}
                        for col_name, val in zip(cols, row):
                            if hasattr(val, "isoformat"):
                                row_dict[col_name] = val.isoformat()
                            elif isinstance(val, (dict, list)):
                                row_dict[col_name] = val
                            else:
                                row_dict[col_name] = str(val) if val is not None else None

                        row_bytes = len(json_dumps_safe(row_dict))
                        total_bytes += row_bytes

                        if row_count > Config.SQL_MAX_ROWS or total_bytes > Config.SQL_MAX_RESPONSE_BYTES:
                            truncated = True
                            break

                        results.append(row_dict)
                else:
                    results = []

            # 6. Para queries de solo lectura el ROLLBACK es la operación correcta de cierre
            #    (no hay nada que persistir). Restaurar la sesión a modo normal
            #    para que la conexión quede limpia al volver al pool.
            try:
                conn.rollback()
                conn.set_session(readonly=False, autocommit=False)
            except Exception:
                pass

        return {
            "success": True,
            "total_returned": len(results),
            "results": results,
            "content_truncated": truncated
        }


def json_dumps_safe(obj: Any) -> str:
    try:
        return json.dumps(obj)
    except Exception:
        return str(obj)
