import unittest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.security.sql_validator import SQLValidator

class TestSQLValidator(unittest.TestCase):

    # --- Consultas válidas ---

    def test_allowed_select(self):
        queries = [
            "SELECT * FROM mcp_guidance_catalog",
            "SELECT dosage_form, COUNT(*) FROM mcp_guidance_catalog GROUP BY dosage_form",
            "SELECT * FROM mcp_guidance_chunks WHERE guidance_id = 42 ORDER BY chunk_index",
            "WITH cte AS (SELECT * FROM mcp_guidance_catalog) SELECT * FROM cte",
        ]
        for q in queries:
            with self.subTest(q=q):
                res = SQLValidator.validate_sql(q)
                self.assertTrue(res["valid"], f"Debería ser válida: {q}\nRazón: {res.get('reason')}")

    # --- Tablas no autorizadas ---

    def test_forbidden_tables(self):
        queries = [
            "SELECT * FROM guidances",
            "SELECT * FROM molecules",
            "SELECT * FROM guidance_chunks",
            "SELECT * FROM pg_catalog.pg_roles",
            "SELECT * FROM information_schema.tables",
        ]
        for q in queries:
            with self.subTest(q=q):
                res = SQLValidator.validate_sql(q)
                self.assertFalse(res["valid"], f"Debería rechazarse por tabla prohibida: {q}")
                self.assertIn("Acceso no autorizado", res["reason"])

    # --- Operaciones DML/DDL prohibidas ---

    def test_forbidden_operations(self):
        queries = [
            "DROP TABLE mcp_guidance_catalog",
            "DELETE FROM mcp_guidance_catalog",
            "UPDATE mcp_guidance_catalog SET rld_rs_number = 'RLD'",
            "INSERT INTO mcp_guidance_catalog (guidance_id) VALUES (1)",
            "ALTER TABLE mcp_guidance_catalog ADD COLUMN test int",
        ]
        for q in queries:
            with self.subTest(q=q):
                res = SQLValidator.validate_sql(q)
                self.assertFalse(res["valid"], f"Debería rechazarse: {q}")

    # --- Múltiples sentencias ---

    def test_multiple_statements(self):
        q = "SELECT * FROM mcp_guidance_catalog; SELECT * FROM mcp_guidance_chunks;"
        res = SQLValidator.validate_sql(q)
        self.assertFalse(res["valid"])
        self.assertIn("únicamente una sola sentencia", res["reason"])

    # --- Funciones peligrosas ---

    def test_dangerous_functions(self):
        dangerous = [
            "SELECT pg_sleep(10) FROM mcp_guidance_catalog",
            "SELECT pg_cancel_backend(123)",
            "SELECT pg_terminate_backend(123)",
            "SELECT lo_export(1, '/tmp/x')",
        ]
        for q in dangerous:
            with self.subTest(q=q):
                res = SQLValidator.validate_sql(q)
                self.assertFalse(res["valid"], f"Debería rechazarse: {q}")
                self.assertIn("prohibida", res["reason"])

    # --- FOR UPDATE / FOR SHARE ---

    def test_for_update_rejected(self):
        q = "SELECT * FROM mcp_guidance_catalog FOR UPDATE"
        res = SQLValidator.validate_sql(q)
        self.assertFalse(res["valid"])
        self.assertIn("bloqueo", res["reason"])

    # --- CTE con DML oculto (adversarial) ---

    def test_cte_with_hidden_delete(self):
        q = """
        WITH deleted AS (
            DELETE FROM guidances RETURNING *
        )
        SELECT * FROM deleted
        """
        res = SQLValidator.validate_sql(q)
        self.assertFalse(res["valid"])

    # --- Consulta vacía ---

    def test_empty_query(self):
        res = SQLValidator.validate_sql("")
        self.assertFalse(res["valid"])
        self.assertIn("vacía", res["reason"])


if __name__ == "__main__":
    unittest.main()
