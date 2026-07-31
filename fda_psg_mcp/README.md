# Servidor MCP para consulta de guías FDA PSG

Este es el servidor MCP Python desarrollado para Codex, Claude y otros agentes compatibles. Permite buscar metadatos de guías, leer el contenido en Markdown, obtener fragmentos (chunks) secuenciales y ejecutar consultas SQL de solo lectura controladas y seguras.

---

## Estructura del Proyecto

```text
fda_psg_mcp/
├── app/
│   ├── main.py                     # Inicialización de FastMCP y definición de Tools
│   ├── config.py                   # Carga de variables de entorno y límites
│   ├── database/
│   │   ├── connection.py           # Gestión del pool de conexiones PostgreSQL
│   │   └── repositories.py         # Consultas de acceso a datos estructurados
│   ├── services/
│   │   ├── guidance_service.py     # Lógica y validación de las guías
│   │   └── sql_service.py          # Lógica para ejecución segura de SELECTs
│   └── security/
│       └── sql_validator.py        # Validador AST estricto usando sqlglot
└── tests/
    ├── unit/                       # Pruebas de seguridad SQL unitarias
    └── integration/                # Pruebas de integración locales con PostgreSQL
```

---

## Requisitos
* Python 3.10 o superior
* PostgreSQL con la extensión `pgvector` instalada.

---

## Instalación y Configuración Local

1. Instalar dependencias en el entorno virtual:
   ```bash
   pip install -r requirements.txt
   ```
2. Crear un archivo `.env` basado en `.env.example`:
   ```bash
   cp .env.example .env
   ```
   E introduce los datos de conexión a PostgreSQL.

3. Ejecutar los tests para asegurar que todo funciona correctamente:
   ```bash
   PYTHONPATH=fda_psg_mcp python -m unittest discover fda_psg_mcp/tests/
   ```

---

## Ejecución Local del Servidor MCP

Para iniciar el servidor MCP en modo `stdio` (entrada/salida estándar para agentes locales):
```bash
PYTHONPATH=fda_psg_mcp python fda_psg_mcp/app/main.py
```
o mediante la herramienta `mcp dev`:
```bash
mcp dev fda_psg_mcp/app/main.py
```

---

## Tools Ofrecidas por el Servidor

1. `search_guidances`: Busca guías usando filtros estructurados (molécula, vía, forma farmacéutica, tipo, etc.).
2. `get_guidance`: Obtiene los metadatos y, opcionalmente, el Markdown de una guía.
3. `get_guidance_context`: Permite leer chunks consecutivos ordenados por rango o index central.
4. `execute_readonly_sql`: Permite ejecutar consultas SQL personalizadas directamente sobre las vistas `mcp_guidance_catalog` y `mcp_guidance_chunks`.
