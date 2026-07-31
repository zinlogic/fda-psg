-- Habilitar extensión pgvector si no existe
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;

-- Vistas para catálogo de guías
CREATE OR REPLACE VIEW public.mcp_guidance_catalog AS
SELECT 
    g.id AS guidance_id,
    g.rld_rs_number,
    g.type,
    g.route,
    g.dosage_form,
    g.date_recommended,
    g.pdf_url,
    m.id AS molecule_id,
    m.name AS molecule_name,
    m.chembl_id
FROM public.guidances g
LEFT JOIN public.guidance_molecules gm ON g.id = gm.guidance_id
LEFT JOIN public.molecules m ON gm.molecule_id = m.id;

-- Vista para chunks
CREATE OR REPLACE VIEW public.mcp_guidance_chunks AS
SELECT 
    gc.id AS chunk_id,
    gc.guidance_id,
    gc.chunk_index,
    gc.chunk_content,
    g.rld_rs_number,
    g.route,
    g.dosage_form
FROM public.guidance_chunks gc
JOIN public.guidances g ON gc.guidance_id = g.id;

-- Crear el usuario de solo lectura para el servidor MCP
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mcp_fda_reader') THEN
        CREATE ROLE mcp_fda_reader WITH LOGIN PASSWORD 'mcp_secure_pass_123';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE db_dlab TO mcp_fda_reader;
GRANT USAGE ON SCHEMA public TO mcp_fda_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_fda_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mcp_fda_reader;
