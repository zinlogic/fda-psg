# Tareas Pendientes y Plan de Implementación (FDA PSG)

Este documento detalla el estado actual del proyecto de búsqueda de Guías Específicas por Producto (PSG) de la FDA y define las tareas restantes necesarias para completar el sistema.

---

## 1. Resumen de lo Implementado hasta Ahora

Hemos completado la fase preparatoria y el diseño de la base de datos local:

1. **Análisis del Buscador de la FDA:** Se identificó que las consultas de moléculas por abecedario se realizan mediante peticiones `GET` con el formato: `index.cfm?event=Home.Letter&searchLetter={LETRA}`.
2. **Extracción del Índice Completo (Scraper de CSVs):** Se creó y ejecutó el script `download_csvs.py`, el cual generó **26 archivos CSV** (de la A a la Z) en la carpeta `/csv/` con un total de **2,229 registros de guías** con sus respectivas URLs oficiales de la FDA.
3. **Instalación y Configuración de PostgreSQL:** 
   * Se instaló PostgreSQL 16 localmente.
   * Se creó la base de datos `db_dlab` y el usuario dedicado `dlab`.
   * Se instaló e inicializó la extensión `pgvector` en la base de datos.
4. **Creación del Esquema de Tablas (DDL):** Se ejecutó el archivo `documentacion/schema.sql`, creando las tablas relacionales y vectoriales:
   * `molecules` (Principios activos únicos).
   * `guidances` (Metadatos de las guías y contenido Markdown completo).
   * `guidance_molecules` (Tabla intermedia Muchos a Muchos).
   * `guidance_chunks` (Fragmentos de texto indexados vectorialmente para RAG).
5. **Documentación del Proyecto:** Se redactó la idea inicial de arquitectura y RAG en `documentacion/proyecto.md` y se guardaron los accesos en `credenciales/database.md`.

---

## 2. Tareas Faltantes (Roadmap de Desarrollo)

Para tener el sistema 100% funcional en el VPS y listo para servir como base de conocimiento RAG, se deben implementar los siguientes componentes:

### [ ] Tarea 1: Script de Descarga Masiva de PDFs (`download_pdfs.py`)
* **Objetivo:** Descargar los 2,229 archivos PDF oficiales desde la FDA y guardarlos localmente en `data/pdf/`.
* **Características:**
  * Debe ser **reanudable** (si se corta, no vuelve a descargar los PDFs que ya existen en el disco).
  * Debe aplicar una pausa de cortesía (ej. 0.15s) entre peticiones para evitar bloqueos por parte del servidor de la FDA.
  * Debe sanitizar y estandarizar los nombres de los archivos PDF descargados (ej. `PSG_{rld_number}.pdf`).

### [ ] Tarea 2: Script de Conversión de PDF a Markdown (`convert_pdfs.py`)
* **Objetivo:** Convertir todos los PDFs descargados en archivos de texto estructurado en Markdown (`data/markdown/`).
* **Características:**
  * Elegir la biblioteca de conversión. Se sugiere iniciar con `pdfplumber` (ligera y excelente para tablas en CPU) o evaluar herramientas basadas en ML para tablas más complejas si fuera necesario.
  * Preservar la estructura del documento (títulos, listas y tablas de bioequivalencia).
  * Evitar reprocesar PDFs que ya tengan su archivo `.md` generado.

### [ ] Tarea 3: Script de Carga e Indexación Vectorial (`populate_db.py`)
* **Objetivo:** Insertar la metadata de los CSVs, asociarla a los archivos Markdown y generar los embeddings vectoriales.
* **Características:**
  * Cargar los ingredientes activos en la tabla `molecules` asegurando unicidad.
  * Insertar los metadatos de las guías en `guidances` asociando el texto completo en Markdown.
  * Implementar una estrategia de división del texto (chunking) de las guías (ej. fragmentos de 1000 caracteres con solapamiento).
  * Generar los embeddings para cada fragmento usando un modelo de embeddings (ej. local con `sentence-transformers` en CPU o mediante la API de OpenAI) y guardarlos en `guidance_chunks`.

### [ ] Tarea 4: Script de Sincronización Automática (`sync_metadata.py`)
* **Objetivo:** Mantener la base de datos actualizada periódicamente en el VPS (Fase 0 de la arquitectura).
* **Características:**
  * Realizar un escaneo rápido de la web de la FDA (A-Z).
  * Comparar contra la base de datos local para detectar si hay registros nuevos, si se eliminaron o si cambió la fecha de recomendación.
  * Descargar, convertir e indexar únicamente las diferencias encontradas.

### [ ] Tarea 5: Interfaz de Búsqueda Híbrida (Ejemplo RAG)
* **Objetivo:** Escribir un script de prueba de consulta (`query_agent.py`) que demuestre cómo el agente de IA buscará en la base de datos.
* **Características:**
  * Filtrado estructurado SQL por metadatos (ej: filtrar por ingrediente y vía de administración).
  * Búsqueda semántica (vectorial) con similitud de coseno sobre los fragmentos resultantes.
