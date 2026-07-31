import logging
from typing import Dict, List, Any, Optional
from app.database.repositories import GuidanceRepository

logger = logging.getLogger("mcp_guidance_service")

class GuidanceService:
    """
    Capa de servicio para aplicar validaciones de negocio sobre las consultas de guías FDA.
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
    ) -> Dict[str, Any]:
        
        # Exigir al menos un filtro estructurado para evitar escaneos completos accidentales
        has_filter = any([molecule, route, dosage_form, guidance_type, rld_rs_number, date_from, date_to])
        if not has_filter:
            return {
                "success": False,
                "error_code": "INVALID_PARAMETERS",
                "message": "Debes especificar al menos un parámetro de filtro (molecule, route, dosage_form, guidance_type, rld_rs_number, date_from o date_to) para realizar la búsqueda."
            }

        try:
            results = GuidanceRepository.search_guidances(
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
            return {
                "success": True,
                "total_returned": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"Error en search_guidances: {e}")
            return {
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": f"Ocurrió un error interno al buscar las guías: {str(e)}"
            }

    @staticmethod
    def get_guidance(guidance_id: int, include_markdown: bool = False) -> Dict[str, Any]:
        try:
            guidance = GuidanceRepository.get_guidance(guidance_id, include_markdown)
            if not guidance:
                return {
                    "success": False,
                    "error_code": "GUIDANCE_NOT_FOUND",
                    "message": f"No se encontró ninguna guía con el identificador {guidance_id}."
                }
            return {
                "success": True,
                "guidance": guidance
            }
        except Exception as e:
            logger.error(f"Error en get_guidance para ID {guidance_id}: {e}")
            return {
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": f"Ocurrió un error al obtener la guía {guidance_id}: {str(e)}"
            }

    @staticmethod
    def get_guidance_context(
        guidance_id: int,
        chunk_index: Optional[int] = None,
        before: Optional[int] = None,
        after: Optional[int] = None,
        chunk_from: Optional[int] = None,
        chunk_to: Optional[int] = None
    ) -> Dict[str, Any]:
        # Validar parámetros obligatorios
        if chunk_index is not None and chunk_from is not None:
            return {
                "success": False,
                "error_code": "INVALID_PARAMETERS",
                "message": "No puedes usar la modalidad por chunk central y rango simultáneamente. Elige una."
            }

        try:
            # Obtener metadatos básicos de la guía primero
            metadata = GuidanceRepository.get_guidance(guidance_id, include_markdown=False)
            if not metadata:
                return {
                    "success": False,
                    "error_code": "GUIDANCE_NOT_FOUND",
                    "message": f"No se encontró la guía con identificador {guidance_id}."
                }
            
            # Formatear la guía simplificada en la respuesta
            guidance_data = {
                "guidance_id": metadata["guidance_id"],
                "route": metadata["route"],
                "dosage_form": metadata["dosage_form"],
                "molecules": [m["name"] for m in metadata["molecules"]],
                "pdf_url": metadata["pdf_url"]
            }

            chunks = []
            requested_range = {}

            if chunk_index is not None:
                # Modalidad chunk central
                b = before if before is not None else 2
                a = after if after is not None else 2
                chunks = GuidanceRepository.get_guidance_chunks_by_center(guidance_id, chunk_index, b, a)
                requested_range = {
                    "from": max(0, chunk_index - b),
                    "to": chunk_index + a
                }
            elif chunk_from is not None and chunk_to is not None:
                # Modalidad rango
                if chunk_from > chunk_to:
                    return {
                        "success": False,
                        "error_code": "INVALID_CHUNK_RANGE",
                        "message": f"El índice inicial 'chunk_from' ({chunk_from}) no puede ser mayor que 'chunk_to' ({chunk_to})."
                    }
                # Límite máximo de chunks por rango
                from app.config import Config
                if (chunk_to - chunk_from + 1) > Config.GUIDANCE_CONTEXT_MAX_CHUNKS:
                    return {
                        "success": False,
                        "error_code": "INVALID_CHUNK_RANGE",
                        "message": f"El rango solicitado supera el límite máximo permitido de {Config.GUIDANCE_CONTEXT_MAX_CHUNKS} chunks."
                    }
                chunks = GuidanceRepository.get_guidance_chunks_by_range(guidance_id, chunk_from, chunk_to)
                requested_range = {
                    "from": chunk_from,
                    "to": chunk_to
                }
            else:
                return {
                    "success": False,
                    "error_code": "INVALID_PARAMETERS",
                    "message": "Debes especificar parámetros válidos para la recuperación de chunks (modalidad chunk central o rango)."
                }

            return {
                "success": True,
                "guidance": guidance_data,
                "requested_range": requested_range,
                "chunks": chunks
            }

        except Exception as e:
            logger.error(f"Error en get_guidance_context para ID {guidance_id}: {e}")
            return {
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": f"Ocurrió un error al obtener el contexto de la guía: {str(e)}"
            }
