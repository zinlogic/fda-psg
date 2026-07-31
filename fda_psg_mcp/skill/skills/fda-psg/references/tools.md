# MCP Tools

## search_guidances

Busca guías mediante filtros estructurados.

Parámetros:

- molecule
- route
- dosage_form
- guidance_type
- rld_rs_number
- date_from
- date_to
- limit
- offset

Ejemplo:

```json
{
  "molecule": "Amlodipine",
  "route": "Oral",
  "dosage_form": "Tablet",
  "limit": 20
}
```

## get_guidance

Recupera metadatos y contenido de una guía.

Ejemplo:

```json
{
  "guidance_id": 42,
  "include_markdown": true
}
```

## get_guidance_context

Recupera chunks consecutivos.

Ejemplo por rango:

```json
{
  "guidance_id": 42,
  "chunk_from": 5,
  "chunk_to": 12
}
```

Ejemplo por chunk central:

```json
{
  "guidance_id": 42,
  "chunk_index": 8,
  "before": 2,
  "after": 3
}
```

## execute_readonly_sql

Ejecuta consultas PostgreSQL de solo lectura sobre vistas autorizadas.

Ejemplo:

```json
{
  "sql": "SELECT dosage_form, COUNT(*) AS total FROM mcp_guidance_catalog GROUP BY dosage_form ORDER BY total DESC LIMIT 20"
}
```
