import sqlglot
from sqlglot import exp

class SQLValidator:
    """
    Validador estricto de sentencias SQL para el servidor MCP.
    Utiliza el analizador AST de sqlglot para evitar inyecciones,
    múltiples comandos y asegurar de forma determinista que solo se ejecuten
    consultas SELECT de solo lectura en las vistas permitidas.
    """
    ALLOWED_OBJECTS = {"mcp_guidance_catalog", "mcp_guidance_chunks"}

    # Funciones del sistema potencialmente peligrosas
    BLOCKED_FUNCTIONS = {
        # Control de procesos y sesiones
        "pg_sleep",
        "pg_cancel_backend",
        "pg_terminate_backend",
        "pg_reload_conf",
        # Acceso a archivos
        "pg_read_file",
        "pg_write_file",
        "pg_ls_dir",
        "pg_read_binary_file",
        "lo_import",
        "lo_export",
        "lo_unlink",
        # Configuración de sesión
        "set_config",
        # Ejecución dinámica
        "pg_execute_server_program",
    }

    @classmethod
    def validate_sql(cls, sql_query: str) -> dict:
        """
        Valida que la consulta SQL cumpla con las restricciones de seguridad.
        Retorna un diccionario indicando el estado de validación.
        """
        if not sql_query or not sql_query.strip():
            return {"valid": False, "reason": "La consulta SQL está vacía."}

        try:
            # 1. Parsear el SQL en expresiones AST
            expressions = sqlglot.parse(sql_query, read="postgres")
        except sqlglot.errors.ParseError as e:
            return {"valid": False, "reason": f"Error de sintaxis SQL: {str(e)}"}

        # 2. Exigir exactamente una sola sentencia SQL
        if len(expressions) != 1 or not expressions[0]:
            return {"valid": False, "reason": "Se permite únicamente una sola sentencia SQL."}

        expression = expressions[0]

        # 3. Validar tipo de sentencia (únicamente SELECT o WITH SELECT)
        if expression.key not in ("select", "subquery"):
            return {"valid": False, "reason": "Operación no permitida. Solo se aceptan consultas SELECT."}

        # 4. Guardar nombres de CTEs para no tratarlos como tablas externas no autorizadas
        cte_names = set()
        if hasattr(expression, "args") and "with_" in expression.args and expression.args["with_"]:
            for cte in expression.args["with_"].expressions:
                if hasattr(cte, "alias"):
                    cte_names.add(cte.alias.lower())

        # 5. Inspeccionar el árbol AST completo
        for node in expression.walk():

            # 5a. Rechazar cualquier nodo DDL o DML
            if isinstance(node, (exp.Insert, exp.Update, exp.Delete, exp.Drop,
                                  exp.Create, exp.Alter, exp.Command,
                                  exp.Merge, exp.Transaction)):
                return {"valid": False, "reason": f"Instrucción SQL prohibida detectada: {node.key.upper()}"}

            # 5b. Rechazar SELECT ... FOR UPDATE / FOR SHARE
            if isinstance(node, exp.Select):
                locks = node.args.get("locks") or []
                if locks:
                    return {"valid": False, "reason": "SELECT con bloqueo de filas (FOR UPDATE / FOR SHARE) no está permitido."}

            # 5c. Validar tablas y vistas de origen
            if isinstance(node, exp.Table):
                table_name = node.name.lower()
                # Permitir CTEs internas definidas en el mismo query
                if table_name in cte_names:
                    continue
                if table_name not in cls.ALLOWED_OBJECTS:
                    return {
                        "valid": False,
                        "reason": (
                            f"Acceso no autorizado al objeto '{table_name}'. "
                            f"Solo se permite consultar las vistas: {', '.join(sorted(cls.ALLOWED_OBJECTS))}"
                        )
                    }

            # 5d. Prohibir funciones peligrosas (detectadas como Anonymous o funciones builtin)
            if isinstance(node, exp.Anonymous):
                func_name = node.name.lower()
                if func_name in cls.BLOCKED_FUNCTIONS:
                    return {"valid": False, "reason": f"Función prohibida '{func_name}' detectada."}

        return {"valid": True}
