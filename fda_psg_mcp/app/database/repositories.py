import logging
import json
from typing import Dict, List, Any, Optional
from app.database.connection import DatabaseConnection
from app.config import Config

logger = logging.getLogger("mcp_repositories")

class GuidanceRepository:
    """
    Repositorio de datos para consulta estructurada de guías FDA y sus chunks.
    """

    @staticmethod
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
    ) -> List[Dict[str, Any]]:
        """
        Busca y retorna metadatos de las guías según filtros estructurados.
        """
        # Limitar el valor máximo de limit para evitar sobrecargas
        limit = min(limit, Config.SQL_MAX_ROWS)

        query = """
            SELECT 
                g.id AS guidance_id,
                g.rld_rs_number,
                g.type,
                g.route,
                g.dosage_form,
                g.date_recommended,
                g.pdf_url,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'id', m.id,
                            'name', m.name,
                            'chembl_id', m.chembl_id
                        )
                    ) FILTER (WHERE m.id IS NOT NULL), '[]'
                ) AS molecules
            FROM public.guidances g
            LEFT JOIN public.guidance_molecules gm ON g.id = gm.guidance_id
            LEFT JOIN public.molecules m ON gm.molecule_id = m.id
            WHERE 1=1
        """
        params = []

        if molecule:
            query += " AND m.name ILIKE %s"
            params.append(f"%{molecule}%")
        if route:
            query += " AND g.route ILIKE %s"
            params.append(f"%{route}%")
        if dosage_form:
            query += " AND g.dosage_form ILIKE %s"
            params.append(f"%{dosage_form}%")
        if guidance_type:
            query += " AND g.type ILIKE %s"
            params.append(f"%{guidance_type}%")
        if rld_rs_number:
            query += " AND g.rld_rs_number ILIKE %s"
            params.append(f"%{rld_rs_number}%")
        if date_from:
            query += " AND g.date_recommended >= %s"
            params.append(date_from)
        if date_to:
            query += " AND g.date_recommended <= %s"
            params.append(date_to)

        query += """
            GROUP BY g.id, g.rld_rs_number, g.type, g.route, g.dosage_form, g.date_recommended, g.pdf_url
            ORDER BY g.date_recommended DESC, g.id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                cols = [desc[0] for desc in cur.description]
                results = []
                for row in cur.fetchall():
                    row_dict = dict(zip(cols, row))
                    if row_dict["date_recommended"] is not None:
                        row_dict["date_recommended"] = str(row_dict["date_recommended"])
                    if isinstance(row_dict["molecules"], str):
                        row_dict["molecules"] = json.loads(row_dict["molecules"])
                    results.append(row_dict)
                return results

    @staticmethod
    def get_guidance(guidance_id: int, include_markdown: bool = False) -> Optional[Dict[str, Any]]:
        """
        Obtiene los metadatos y opcionalmente el contenido Markdown de una guía.
        """
        query = """
            SELECT 
                g.id AS guidance_id,
                g.rld_rs_number,
                g.type,
                g.route,
                g.dosage_form,
                g.date_recommended,
                g.pdf_url,
                g.markdown_content,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'id', m.id,
                            'name', m.name
                        )
                    ) FILTER (WHERE m.id IS NOT NULL), '[]'
                ) AS molecules
            FROM public.guidances g
            LEFT JOIN public.guidance_molecules gm ON g.id = gm.guidance_id
            LEFT JOIN public.molecules m ON gm.molecule_id = m.id
            WHERE g.id = %s
            GROUP BY g.id, g.rld_rs_number, g.type, g.route, g.dosage_form, g.date_recommended, g.pdf_url, g.markdown_content
        """
        
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (guidance_id,))
                row = cur.fetchone()
                if not row:
                    return None
                
                cols = [desc[0] for desc in cur.description]
                row_dict = dict(zip(cols, row))
                row_dict["date_recommended"] = str(row_dict["date_recommended"])
                if isinstance(row_dict["molecules"], str):
                    row_dict["molecules"] = json.loads(row_dict["molecules"])
                
                # Manejar presencia y truncado del Markdown
                markdown = row_dict.pop("markdown_content") or ""
                row_dict["content_truncated"] = False
                
                if include_markdown:
                    if len(markdown) > Config.GUIDANCE_MAX_MARKDOWN_BYTES:
                        row_dict["markdown_content"] = markdown[:Config.GUIDANCE_MAX_MARKDOWN_BYTES] + "\n\n... [CONTENIDO TRUNCADO POR LÍMITE DE TAMAÑO] ..."
                        row_dict["content_truncated"] = True
                    else:
                        row_dict["markdown_content"] = markdown
                
                return row_dict

    @staticmethod
    def get_guidance_chunks_by_range(guidance_id: int, chunk_from: int, chunk_to: int) -> List[Dict[str, Any]]:
        """
        Recupera chunks ordenados por un rango de índices.
        """
        query = """
            SELECT id AS chunk_id, chunk_index, chunk_content
            FROM public.guidance_chunks
            WHERE guidance_id = %s AND chunk_index >= %s AND chunk_index <= %s
            ORDER BY chunk_index ASC
        """
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (guidance_id, chunk_from, chunk_to))
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]

    @staticmethod
    def get_guidance_chunks_by_center(guidance_id: int, chunk_index: int, before: int, after: int) -> List[Dict[str, Any]]:
        """
        Recupera chunks ordenados tomando un índice central y un margen antes/después.
        """
        chunk_from = max(0, chunk_index - before)
        chunk_to = chunk_index + after
        return GuidanceRepository.get_guidance_chunks_by_range(guidance_id, chunk_from, chunk_to)
