-- Script de Creación del Esquema de Base de Datos para db_dlab
-- Activar extensión pgvector (ya habilitada, pero por seguridad)
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Tabla de Moléculas (Principios Activos Individuales)
CREATE TABLE IF NOT EXISTS molecules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    chembl_id VARCHAR(50) UNIQUE, -- Para futuras integraciones con la BD de ChEMBL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Guías Específicas por Producto (PSG)
CREATE TABLE IF NOT EXISTS guidances (
    id SERIAL PRIMARY KEY,
    rld_rs_number VARCHAR(100) NOT NULL, -- Número de referencia del medicamento (ej: "022545")
    type VARCHAR(50) NOT NULL,            -- "Draft" o "Revised"
    route VARCHAR(150) NOT NULL,           -- Vía de administración (ej: "Oral")
    dosage_form VARCHAR(255) NOT NULL,     -- Forma de dosificación (ej: "Tablet")
    date_recommended DATE NOT NULL,        -- Fecha de recomendación
    pdf_url TEXT NOT NULL,                 -- URL original en el sitio de la FDA
    pdf_path TEXT,                         -- Ruta del PDF descargado en el VPS
    markdown_path TEXT,                    -- Ruta del archivo Markdown en el VPS
    markdown_content TEXT,                 -- Contenido completo de la guía en Markdown
    pdf_hash VARCHAR(64),                  -- Hash SHA-256 para control de cambios del PDF
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla Intermedia para Relación Muchos a Muchos (Guidance <-> Molecules)
CREATE TABLE IF NOT EXISTS guidance_molecules (
    guidance_id INT REFERENCES guidances(id) ON DELETE CASCADE,
    molecule_id INT REFERENCES molecules(id) ON DELETE CASCADE,
    PRIMARY KEY (guidance_id, molecule_id)
);

-- 4. Tabla de Fragmentos (Chunks) para Búsqueda Vectorial (RAG)
-- Nota sobre la columna "embedding":
-- * Si usas OpenAI (text-embedding-3-small o ada-002), el tamaño es 1536.
-- * Si usas un modelo local ligero de SentenceTransformers (como all-MiniLM-L6-v2), el tamaño es 384.
-- Definimos por defecto 1536 (estándar OpenAI), pero puedes modificar este valor según tu modelo.
CREATE TABLE IF NOT EXISTS guidance_chunks (
    id SERIAL PRIMARY KEY,
    guidance_id INT REFERENCES guidances(id) ON DELETE CASCADE,
    chunk_content TEXT NOT NULL,
    chunk_index INT NOT NULL,                  -- Orden secuencial del fragmento en el documento
    embedding vector(1536),                    -- Ajustar dimensión según el modelo de embeddings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimizar las búsquedas
CREATE INDEX IF NOT EXISTS idx_molecules_name ON molecules(name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_guidances_unique ON guidances(rld_rs_number, dosage_form, route);

-- Índice HNSW para búsqueda vectorial rápida por similitud del coseno (Cosine Distance <=> )
-- Reemplazar el número 1536 si se cambia la dimensión del vector
CREATE INDEX IF NOT EXISTS idx_guidance_chunks_embedding ON guidance_chunks USING hnsw (embedding vector_cosine_ops);
