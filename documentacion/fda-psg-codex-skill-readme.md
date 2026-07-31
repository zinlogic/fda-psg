# Codex Skill: FDA Product-Specific Guidances (PSG)

Este directorio documenta la configuración del Skill compatible con Codex para la interacción estructurada con la base de datos de guías de la FDA a través de MCP.

## Estructura del Skill

```text
skills/fda-psg/
├── SKILL.md                  # Reglas principales, flujo de trabajo y comportamiento
├── agents/
│   └── openai.yaml           # Declaración de dependencias MCP y metadatos para Codex
├── references/
│   ├── tools.md              # Documentación técnica de las tools
│   ├── database-schema.md    # Esquema lógico expuesto (mcp_guidance_catalog, mcp_guidance_chunks)
│   ├── query-policy.md       # Reglas de validación SQL del validador AST
│   └── response-guidelines.md# Formato estructurado de respuestas regulatorias
└── assets/
    ├── icon-small.svg        # Logo pequeño del skill
    └── icon-large.png        # Logo grande del skill
```

## Configuración y Dependencia MCP
El archivo `openai.yaml` asocia este Skill directamente con el servidor MCP remoto expuesto por el VPS a través del túnel interactivo:

```yaml
dependencies:
  tools:
    - type: "mcp"
      value: "fda-psg-mcp"
      description: "Servidor MCP para consulta de FDA Product-Specific Guidances"
      transport: "streamable_http"
      url: "http://localhost:8000/mcp"
```

## Instrucciones de Descarga e Instalación para el Agente Codex

Sigue estos pasos para descargar, extraer e instalar el Skill en tu entorno:

### 1. Descargar el archivo `skill.zip`
Puedes descargar el paquete comprimido directamente por HTTP o usando SCP desde el VPS:

* **Opción A (HTTP Directo):**
  ```bash
  curl -O http://187.77.21.237/skill.zip
  ```

* **Opción B (SCP Seguro):**
  ```bash
  scp -P 49222 root@187.77.21.237:/opt/fda-psg-mcp/skill.zip .
  ```

### 2. Descomprimir e Instalar en el Workspace
Para instalar la skill localmente en el espacio de trabajo actual (donde se autodetectará automáticamente):

```bash
# Crear el directorio de skills del proyecto si no existe
mkdir -p .agents/skills/

# Extraer el contenido en la ruta adecuada
unzip skill.zip -d .agents/

# (Opcional) Si quieres copiar también la configuración de conexión MCP
cp .agents/mcp_config.json .agents/mcp_config.json
```

### 3. Verificar la Configuración
Una vez extraído, confirma que la estructura del directorio sea:
`.agents/skills/fda-psg/SKILL.md`

El agente Codex detectará y activará el skill automáticamente al procesar consultas relacionadas con Product-Specific Guidances de la FDA.

