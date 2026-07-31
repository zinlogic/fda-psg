# Proyecto: FDA Product-Specific Guidances — Servidor MCP

La documentación técnica completa del proyecto está en:
`documentacion/proyecto_mcp.md`

El estado de avance de la implementación está en:
`avance_implementacion/estado_mcp.md`

---

## ⚠️ REGLA CRÍTICA: NUNCA PUBLICAR CREDENCIALES

**Jamás incluir en ningún archivo de código, documentación, comentario, log, commit, README, SKILL.md, ni mensaje de chat:**

- Contraseñas de bases de datos
- Contraseñas de servidores o VPS
- Tokens de acceso (GitHub, APIs, etc.)
- Claves privadas o certificados
- Cualquier secreto o credencial de acceso

Las credenciales del proyecto se almacenan **únicamente** en:
- `.env` (local, nunca versionado)
- `credenciales/credenciales.txt` (local, nunca versionado)

El archivo `.gitignore` debe siempre excluir estos archivos. Verificar antes de cada commit.

---

## Tecnologías del proyecto

### Servidor MCP (Python)
- **FastMCP** como framework del servidor MCP.
- **psycopg2** para conexión a PostgreSQL con pool de conexiones.
- **sqlglot** para validación AST de consultas SQL.
- **pydantic** para validación de parámetros de entrada.
- **python-dotenv** para gestión de configuración por entorno.
- **uvicorn** como servidor ASGI en modo `streamable-http`.

### Base de Datos
- **PostgreSQL 16** con extensión **pgvector**.
- Usuario de solo lectura `mcp_fda_reader` con acceso exclusivo a las vistas del MCP.
- Dos vistas expuestas al MCP: `mcp_guidance_catalog` y `mcp_guidance_chunks`.

### Infraestructura
- **Docker + Docker Compose** para orquestación de contenedores en el VPS.
- **Apache2** como proxy reverso que expone el endpoint `/mcp` públicamente.
- **VPS** en `187.77.21.237` (acceso SSH por puerto `49222`).

### Scripts de datos (Python)
- Scrapers y procesadores en `src/` para sincronización con FDA y conversión de PDFs.

---

## Arquitectura del proyecto

### Raíz del repositorio
```
.
├── fda_psg_mcp/          # Servidor MCP (código principal)
├── src/                  # Scripts de scraping y procesamiento de PDFs
├── documentacion/        # Documentación técnica y funcional
├── avance_implementacion/# Estado y tareas de implementación
├── credenciales/         # Credenciales locales (NO versionado)
├── data/                 # Datos auxiliares locales
├── .agents/              # Configuración de skills y MCP para agentes de IA
├── .env                  # Variables de entorno locales (NO versionado)
└── .env.example          # Plantilla de variables de entorno
```

### Servidor MCP (`fda_psg_mcp/`)
```
fda_psg_mcp/
├── app/
│   ├── main.py             # Entrypoint FastMCP — define las 4 tools MCP
│   ├── config.py           # Carga de variables de entorno y límites
│   ├── database/
│   │   ├── connection.py   # Pool de conexiones PostgreSQL
│   │   └── repositories.py # Consultas SQL parametrizadas
│   ├── services/
│   │   ├── guidance_service.py  # Lógica de búsqueda y recuperación de guías
│   │   └── sql_service.py       # Ejecución controlada de SQL libre
│   └── security/
│       └── sql_validator.py     # Validador AST estricto de consultas SQL
├── scripts/
│   └── init-db.sql         # Script de inicialización del DB en Docker
├── data/                   # Backup de la base de datos para Docker
├── tests/
│   ├── unit/               # Tests del validador SQL
│   └── integration/        # Tests contra la base de datos real
├── skill/                  # Plugin/Skill para Codex y Antigravity
│   ├── plugin.json
│   ├── mcp_config.json
│   └── skills/fda-psg/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       ├── assets/
│       └── references/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

### Scripts de datos (`src/`)
```
src/
├── scrapers/
│   ├── sync_metadata.py    # Sincroniza metadatos de guías desde FDA
│   └── download_pdfs.py    # Descarga PDFs de guías
├── processors/
│   ├── convert_pdfs.py     # Convierte PDFs a Markdown
│   └── populate_db.py      # Carga datos procesados a PostgreSQL
└── update_pipeline.py      # Pipeline completo de actualización
```

---

## Tools MCP expuestas

| Tool | Descripción |
|---|---|
| `search_guidances` | Busca guías por molécula, vía, forma farmacéutica, tipo, número RLD/RS o fecha |
| `get_guidance` | Recupera metadatos y contenido Markdown de una guía por `guidance_id` |
| `get_guidance_context` | Recupera chunks consecutivos de una guía por índice central o rango |
| `execute_readonly_sql` | Ejecuta SELECT sobre las vistas autorizadas (`mcp_guidance_catalog`, `mcp_guidance_chunks`) |

---

## Endpoint MCP público

El servidor MCP está disponible en:
`http://187.77.21.237/mcp`

Transport: `streamable-http`
Puerto interno del contenedor: `8000`
Proxy reverso: Apache2 en el VPS

---

## Reglas de desarrollo

- Las consultas SQL de `execute_readonly_sql` deben pasar siempre por `SQLValidator` antes de ejecutarse.
- Nunca devolver la columna `embedding` en ninguna respuesta del MCP.
- Nunca acceder a tablas base directamente; solo a las vistas `mcp_guidance_catalog` y `mcp_guidance_chunks`.
- Toda variable de entorno sensible debe cargarse desde `.env` usando `python-dotenv`.
- Nunca hacer `docker compose down -v` sin confirmar explícitamente con el usuario: elimina los datos de la base.
- El archivo `fda_psg_mcp/data/backup.sql` contiene el dump completo de la base de datos y **no debe versionarse**.
