import os
import sys
import logging
from typing import Optional, List, Dict, Any
from fastmcp import FastMCP

# Asegurar que el directorio raíz del proyecto esté en el path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from app.services.guidance_service import GuidanceService
from app.services.sql_service import SQLService
from app.security.sql_validator import SQLValidator
from app.database.connection import DatabaseConnection

# Configurar logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL, logging.INFO))
logger = logging.getLogger("fda_psg_mcp_server")

# Crear el servidor MCP
mcp = FastMCP("FDA PSG MCP Server")

@mcp.tool()
def search_guidances(
    molecule: Optional[str] = None,
    route: Optional[str] = None,
    dosage_form: Optional[str] = None,
    guidance_type: Optional[str] = None,
    rld_rs_number: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> str:
    """
    Busca guías FDA PSG mediante filtros estructurados. 
    Es obligatorio especificar al menos uno de los filtros (molecule, route, dosage_form, guidance_type, rld_rs_number, date_from o date_to).
    La búsqueda de moléculas admite coincidencia parcial e insensible a mayúsculas/minúsculas.
    """
    logger.info(f"Tool search_guidances invocada con filtros: molecule={molecule}, route={route}, dosage_form={dosage_form}")
    res = GuidanceService.search_guidances(
        molecule=molecule,
        route=route,
        dosage_form=dosage_form,
        guidance_type=guidance_type,
        rld_rs_number=rld_rs_number,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )
    import json
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def get_guidance(guidance_id: int, include_markdown: bool = False) -> str:
    """
    Recupera una guía FDA PSG específica por su identificador único (guidance_id).
    Permite obtener metadatos y, opcionalmente, el contenido Markdown completo.
    El Markdown se truncará de forma automática si supera el límite de tamaño configurado.
    """
    logger.info(f"Tool get_guidance invocada para ID={guidance_id}, include_markdown={include_markdown}")
    res = GuidanceService.get_guidance(guidance_id, include_markdown)
    import json
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def get_guidance_context(
    guidance_id: int,
    chunk_index: Optional[int] = None,
    before: Optional[int] = None,
    after: Optional[int] = None,
    chunk_from: Optional[int] = None,
    chunk_to: Optional[int] = None
) -> str:
    """
    Recupera fragmentos o chunks secuenciales específicos asociados a una guía.
    Admite dos modalidades exclusivas por llamada:
      1. Por chunk central: 'chunk_index' indicando el central, junto con 'before' y 'after' para definir el rango.
      2. Por rango: especificando los límites 'chunk_from' y 'chunk_to'.
    """
    logger.info(f"Tool get_guidance_context invocada para ID={guidance_id}, index={chunk_index}, range={chunk_from}-{chunk_to}")
    res = GuidanceService.get_guidance_context(
        guidance_id=guidance_id,
        chunk_index=chunk_index,
        before=before,
        after=after,
        chunk_from=chunk_from,
        chunk_to=chunk_to
    )
    import json
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def execute_readonly_sql(sql: str) -> str:
    """
    Ejecuta una consulta SQL personalizada de solo lectura sobre las vistas públicas del MCP.
    Solo se permiten consultas SELECT (o WITH...SELECT) que consulten exclusivamente las vistas:
      - mcp_guidance_catalog
      - mcp_guidance_chunks
    Cualquier otra tabla o comando SQL será inmediatamente rechazado por motivos de seguridad.
    """
    logger.info(f"Tool execute_readonly_sql invocada con query: {sql[:100]}...")
    import json
    
    # 1. Validar SQL
    validation = SQLValidator.validate_sql(sql)
    if not validation["valid"]:
        logger.warning(f"Consulta SQL rechazada: {validation['reason']}")
        return json.dumps({
            "success": False,
            "error_code": "SQL_NOT_ALLOWED",
            "message": validation["reason"]
        }, indent=2, ensure_ascii=False)

    # 2. Ejecutar consulta segura
    try:
        res = SQLService.execute_readonly_query(sql)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error al ejecutar query SQL: {e}")
        return json.dumps({
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "message": f"Ocurrió un error al ejecutar la consulta en la base de datos: {str(e)}"
        }, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # Inicializar pool al arrancar el servidor mcp directamente
    DatabaseConnection.get_pool()
    try:
        mcp.run()
    finally:
        DatabaseConnection.close_pool()
