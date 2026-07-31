import unittest
import os
import sys
import json

# Configurar path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import DatabaseConnection
from app.services.guidance_service import GuidanceService
from app.services.sql_service import SQLService

class TestIntegrationMCP(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Aseguramos la inicialización del pool usando las credenciales del entorno
        DatabaseConnection.get_pool()

    @classmethod
    def tearDownClass(cls):
        DatabaseConnection.close_pool()

    def test_search_guidances_flow(self):
        # 1. Búsqueda válida con molécula 'Ibuprofen'
        res = GuidanceService.search_guidances(molecule="Ibuprofen")
        self.assertTrue(res["success"])
        self.assertGreaterEqual(res["total_returned"], 0)
        
        # 2. Búsqueda inválida por falta de filtros
        res_no_filters = GuidanceService.search_guidances()
        self.assertFalse(res_no_filters["success"])
        self.assertEqual(res_no_filters["error_code"], "INVALID_PARAMETERS")

    def test_get_guidance_and_markdown(self):
        # Buscar primero alguna guía para obtener un ID válido
        res = GuidanceService.search_guidances(molecule="Ibuprofen")
        if res["success"] and res["total_returned"] > 0:
            guidance_id = res["results"][0]["guidance_id"]
            
            # Obtener guía con Markdown
            guid_res = GuidanceService.get_guidance(guidance_id, include_markdown=True)
            self.assertTrue(guid_res["success"])
            self.assertIn("markdown_content", guid_res["guidance"])
            self.assertEqual(guid_res["guidance"]["guidance_id"], guidance_id)

    def test_get_guidance_context(self):
        res = GuidanceService.search_guidances(molecule="Ibuprofen")
        if res["success"] and res["total_returned"] > 0:
            guidance_id = res["results"][0]["guidance_id"]
            
            # Recuperar context por chunk central
            ctx_res = GuidanceService.get_guidance_context(guidance_id=guidance_id, chunk_index=0, before=1, after=1)
            self.assertTrue(ctx_res["success"])
            self.assertIn("chunks", ctx_res)

    def test_execute_readonly_sql_success(self):
        # Query SELECT válido sobre la vista de catálogo
        query = "SELECT dosage_form, COUNT(*) AS total FROM mcp_guidance_catalog GROUP BY dosage_form LIMIT 5"
        res = SQLService.execute_readonly_query(query)
        self.assertTrue(res["success"])
        self.assertGreaterEqual(len(res["results"]), 0)

if __name__ == "__main__":
    unittest.main()
