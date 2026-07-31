# Esquema lógico disponible

## mcp_guidance_catalog

Campos esperados:

- guidance_id
- rld_rs_number
- type
- route
- dosage_form
- date_recommended
- pdf_url
- molecule_id
- molecule_name
- chembl_id

## mcp_guidance_chunks

Campos esperados:

- chunk_id
- guidance_id
- chunk_index
- chunk_content
- rld_rs_number
- route
- dosage_form
- date_recommended
- pdf_url

No consultar directamente:

- tablas internas;
- pg_catalog;
- information_schema;
- rutas locales;
- credenciales;
- embeddings.
