import os
import csv
import glob
import re
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

# Configuración de Base de Datos
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fda_psg_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mysecretpassword")

# Configuración de Rutas
CSV_STORAGE_DIR = os.getenv("CSV_STORAGE_DIR", "data/csv")
PDF_STORAGE_DIR = os.getenv("PDF_STORAGE_DIR", "data/pdf")
MARKDOWN_STORAGE_DIR = os.getenv("MARKDOWN_STORAGE_DIR", "data/markdown")

# Configuración de Embeddings
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "none").lower() # 'openai', 'sentence-transformers', o 'none'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Dimensiones por defecto
# pgvector por defecto en schema.sql es 1536 (OpenAI). 
# Si se usa sentence-transformers (all-MiniLM-L6-v2), suele ser 384.
EMBEDDING_DIM = 384 if EMBEDDING_PROVIDER == "sentence-transformers" else 1536

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def parse_date(date_str):
    """
    Parses date string (e.g. '10/30/2024') to standard YYYY-MM-DD.
    """
    if not date_str:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    # Si no se puede parsear, devolver None o un valor por defecto
    return None

class EmbeddingGenerator:
    def __init__(self, provider=EMBEDDING_PROVIDER):
        self.provider = provider
        self.model = None
        
        if self.provider == "sentence-transformers":
            try:
                from sentence_transformers import SentenceTransformer
                print("Cargando modelo local de SentenceTransformers...")
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
            except ImportError:
                print("[WARNING] sentence-transformers no está instalado. Instalándolo podría solucionar esto. Usando dummy embeddings por ahora.")
                self.provider = "none"
        elif self.provider == "openai":
            if not OPENAI_API_KEY:
                print("[WARNING] OPENAI_API_KEY no está configurada. Usando dummy embeddings.")
                self.provider = "none"
            else:
                try:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=OPENAI_API_KEY)
                except ImportError:
                    print("[WARNING] Librería 'openai' no instalada. Usando dummy embeddings.")
                    self.provider = "none"

    def get_embedding(self, text):
        if self.provider == "sentence-transformers" and self.model:
            emb = self.model.encode(text).tolist()
            return emb
        elif self.provider == "openai":
            try:
                response = self.client.embeddings.create(
                    input=[text],
                    model="text-embedding-3-small"
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"Error generando embedding con OpenAI: {e}")
                return [0.0] * 1536
        else:
            # Dummy vector matching schema dimensions
            return [0.0] * EMBEDDING_DIM

def chunk_markdown(content):
    """
    Splits markdown content into logical chunks (e.g. by pages '## Página X').
    Returns a list of tuples (chunk_content, chunk_index).
    """
    if not content:
        return []
        
    # Split by '## Página' headers
    pages = re.split(r'## Página \d+', content)
    chunks = []
    chunk_idx = 0
    
    for page in pages:
        page_clean = page.strip()
        if page_clean:
            # Reconstruct the page reference for context inside the chunk
            full_chunk = f"Página:\n{page_clean}"
            chunks.append((full_chunk, chunk_idx))
            chunk_idx += 1
            
    return chunks

def populate():
    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    csv_folder = os.path.join(workspace_dir, CSV_STORAGE_DIR) if not os.path.isabs(CSV_STORAGE_DIR) else CSV_STORAGE_DIR
    pdf_folder = os.path.join(workspace_dir, PDF_STORAGE_DIR) if not os.path.isabs(PDF_STORAGE_DIR) else PDF_STORAGE_DIR
    md_folder = os.path.join(workspace_dir, MARKDOWN_STORAGE_DIR) if not os.path.isabs(MARKDOWN_STORAGE_DIR) else MARKDOWN_STORAGE_DIR
    
    # Inicializar generador de embeddings
    emb_gen = EmbeddingGenerator()
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        print("Conexión a PostgreSQL establecida con éxito.")
        # Asegurar que existe el índice único para ON CONFLICT
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_guidances_unique ON guidances(rld_rs_number, dosage_form, route);")
        conn.commit()
    except Exception as e:
        print(f"Error al conectar a PostgreSQL: {e}")
        print("Por favor, asegúrate de que PostgreSQL está corriendo y las credenciales en .env son correctas.")
        return

    csv_files = glob.glob(os.path.join(csv_folder, "*.csv"))
    if not csv_files:
        print("No se encontraron CSVs de metadatos.")
        cur.close()
        conn.close()
        return

    print("Iniciando procesamiento y carga en la base de datos...")
    
    guidances_inserted = 0
    new_guidances_count = 0
    updated_guidances_count = 0
    skipped_guidances_count = 0
    molecules_cache = {} # name -> id
    
    for csv_file in csv_files:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 1. Metadatos básicos
                raw_active_ingredients = row.get("Active Ingredient (link to Specific Guidance)", "").strip()
                pdf_url = row.get("URL", "").strip()
                g_type = row.get("Type", "").strip()
                route = row.get("Route", "").strip()
                dosage_form = row.get("Dosage Form", "").strip()
                rld_rs_number = row.get("RLD or RS Number", "").strip()
                raw_date = row.get("Date Recommended", "").strip()
                
                if not pdf_url:
                    continue
                
                # Formatear la fecha
                date_recommended = parse_date(raw_date)
                if not date_recommended:
                    # Si no tiene fecha válida, usar hoy por defecto o un placeholder
                    date_recommended = datetime.now().date()
                
                # Buscar archivo local PDF y Markdown correspondiente
                pdf_filename = os.path.basename(pdf_url)
                pdf_path_local = os.path.join(pdf_folder, pdf_filename)
                md_filename = pdf_filename.replace(".pdf", ".md")
                md_path_local = os.path.join(md_folder, md_filename)
                
                # Si no existen los archivos locales, los dejamos en NULL en la BD
                db_pdf_path = pdf_path_local if os.path.exists(pdf_path_local) else None
                db_md_path = md_path_local if os.path.exists(md_path_local) else None
                
                # Leer contenido del Markdown
                markdown_content = ""
                if db_md_path:
                    try:
                        with open(db_md_path, "r", encoding="utf-8") as md_f:
                            markdown_content = md_f.read()
                    except Exception as e:
                        print(f"Error al leer markdown {db_md_path}: {e}")

                # 1.5 Verificar si ya existe en la BD y si el markdown no cambió
                cur.execute(
                    """
                    SELECT id, markdown_content FROM guidances 
                    WHERE rld_rs_number = %s AND dosage_form = %s AND route = %s;
                    """,
                    (rld_rs_number, dosage_form, route)
                )
                existing_record = cur.fetchone()
                
                skip_chunks = False
                if existing_record:
                    existing_id, existing_md = existing_record
                    # Si el markdown es exactamente igual, validamos si tiene chunks
                    if existing_md == markdown_content:
                        cur.execute("SELECT COUNT(*) FROM guidance_chunks WHERE guidance_id = %s;", (existing_id,))
                        if cur.fetchone()[0] > 0:
                            skip_chunks = True
                if not existing_record:
                    new_guidances_count += 1
                elif not skip_chunks:
                    updated_guidances_count += 1
                else:
                    skipped_guidances_count += 1

                # 2. Insertar / Actualizar la Guía en 'guidances'
                # Buscamos duplicados por (rld_rs_number, dosage_form, route)
                cur.execute(
                    """
                    INSERT INTO guidances (rld_rs_number, type, route, dosage_form, date_recommended, pdf_url, pdf_path, markdown_path, markdown_content, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (rld_rs_number, dosage_form, route) 
                    DO UPDATE SET 
                        type = EXCLUDED.type,
                        date_recommended = EXCLUDED.date_recommended,
                        pdf_url = EXCLUDED.pdf_url,
                        pdf_path = EXCLUDED.pdf_path,
                        markdown_path = EXCLUDED.markdown_path,
                        markdown_content = EXCLUDED.markdown_content,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id;
                    """,
                    (rld_rs_number, g_type, route, dosage_form, date_recommended, pdf_url, db_pdf_path, db_md_path, markdown_content)
                )
                guidance_id = cur.fetchone()[0]
                
                # 3. Procesar Moléculas (Principios Activos)
                # Separar por ";" para moléculas múltiples (ej. "Abacavir Sulfate; Lamivudine")
                molecules = [m.strip() for m in raw_active_ingredients.split(";") if m.strip()]
                
                for mol_name in molecules:
                    if mol_name not in molecules_cache:
                        # Insertar o buscar ID de la molécula
                        cur.execute(
                            """
                            INSERT INTO molecules (name) 
                            VALUES (%s) 
                            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                            RETURNING id;
                            """,
                            (mol_name,)
                        )
                        mol_id = cur.fetchone()[0]
                        molecules_cache[mol_name] = mol_id
                    else:
                        mol_id = molecules_cache[mol_name]
                        
                    # Asociar guía con la molécula en la tabla intermedia
                    cur.execute(
                        """
                        INSERT INTO guidance_molecules (guidance_id, molecule_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                        """,
                        (guidance_id, mol_id)
                    )
                
                # 4. Procesar fragmentos y embeddings si hay markdown y cambió (o no existían chunks)
                if markdown_content and not skip_chunks:
                    chunks = chunk_markdown(markdown_content)
                    
                    # Limpiar fragmentos anteriores para esta guía
                    cur.execute("DELETE FROM guidance_chunks WHERE guidance_id = %s;", (guidance_id,))
                    
                    for chunk_txt, chunk_idx in chunks:
                        emb = emb_gen.get_embedding(chunk_txt)
                        
                        # Guardar fragmento
                        cur.execute(
                            """
                            INSERT INTO guidance_chunks (guidance_id, chunk_content, chunk_index, embedding)
                            VALUES (%s, %s, %s, %s);
                            """,
                            (guidance_id, chunk_txt, chunk_idx, emb)
                        )
                
                guidances_inserted += 1
                if guidances_inserted % 100 == 0:
                    print(f"Cargadas {guidances_inserted} guías en la base de datos...")
                    conn.commit()

    conn.commit()
    cur.close()
    conn.close()
    
    print("\n--- Proceso de Carga Finalizado ---")
    print(f"Total de guías procesadas: {guidances_inserted}")
    print(f"  - Nuevas agregadas: {new_guidances_count}")
    print(f"  - Existentes actualizadas: {updated_guidances_count}")
    print(f"  - Omitidas (sin cambios): {skipped_guidances_count}")
    print(f"Total de moléculas únicas registradas: {len(molecules_cache)}")

if __name__ == "__main__":
    populate()
