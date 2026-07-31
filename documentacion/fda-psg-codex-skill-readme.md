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

### 2. Descomprimir e Instalar la Skill

Dependiendo de tu entorno de ejecución, puedes instalar la skill de dos formas:

#### Opción A: Directorio Global de Codex (Recomendado para el Agente Codex)
El directorio por defecto para instalar skills de Codex a nivel global es `~/.codex/skills/` (o `$CODEX_HOME/skills`).

**En Linux/macOS:**
```bash
# Crear el directorio de skills de Codex si no existe
mkdir -p ~/.codex/skills/

# Extraer el contenido de la skill en la ruta global de Codex
unzip skill.zip -d ~/.codex/
```

**En Windows (PowerShell):**
La ruta por defecto equivale a `"$env:USERPROFILE\.codex\skills\"`:
```powershell
# Crear el directorio de skills en Windows
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.codex\skills"

# Descomprimir el archivo zip
Expand-Archive -Path "skill.zip" -DestinationPath "$env:USERPROFILE\.codex" -Force
```

#### Opción B: Directorio Local del Proyecto (Workspace)
Para entornos de desarrollo de Antigravity o si prefieres mantener la skill dentro del repositorio del proyecto actual:

```bash
# Crear el directorio de personalizaciones local
mkdir -p .agents/skills/

# Extraer la skill localmente
unzip skill.zip -d .agents/
```

### 3. Configurar el Servidor MCP
Si vas a utilizar el servidor MCP remoto, asegúrate de copiar el archivo `mcp_config.json` (incluido en el zip) al directorio de configuración global de tu agente (ej. `~/.gemini/config/mcp_config.json` o `.agents/mcp_config.json` en tu workspace).

### 4. Verificar la Configuración
Confirma que la estructura de directorios resultante contenga:
* **Global (Codex):** `~/.codex/skills/fda-psg/SKILL.md`
* **Local (Workspace):** `.agents/skills/fda-psg/SKILL.md`

El agente Codex/Antigravity detectará y activará el skill automáticamente al procesar consultas relacionadas con las Product-Specific Guidances de la FDA.

