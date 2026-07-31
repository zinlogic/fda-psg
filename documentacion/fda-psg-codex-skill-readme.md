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
