# Codex Skill: FDA Product-Specific Guidances (PSG)

Este documento contiene las instrucciones para que el agente Codex descargue, instale y verifique correctamente el Skill de FDA PSG.

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

El archivo `openai.yaml` asocia este Skill directamente con el servidor MCP remoto:

```yaml
dependencies:
  tools:
    - type: "mcp"
      value: "fda-psg-mcp"
      description: "Servidor MCP para consulta de FDA Product-Specific Guidances"
      transport: "streamable_http"
      url: "http://187.77.21.237/mcp"
```

---

## Instalación para el Agente Codex

> **IMPORTANTE**: El entorno de ejecución puede tener restricciones de escritura. Usar el directorio `TEMP` para la descarga inicial es obligatorio en Windows para evitar errores de permisos. Seguir exactamente los pasos de cada sección según tu sistema operativo.

---

### Windows (PowerShell) — Método Probado y Recomendado

Usar siempre `$env:TEMP` como destino de descarga inicial. Esto evita bloqueos de permisos del sandbox.

```powershell
# Paso 1: Descargar el ZIP en TEMP (evita restricciones de permisos de red/escritura)
Invoke-WebRequest -Uri 'http://187.77.21.237/skill.zip' -OutFile "$env:TEMP\skill.zip"

# Paso 2: Extraer en TEMP
Expand-Archive -LiteralPath "$env:TEMP\skill.zip" -DestinationPath "$env:TEMP\skill-extracted" -Force

# Paso 3: Crear el directorio destino de skills si no existe
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.codex\skills\fda-psg" | Out-Null

# Paso 4: Sincronizar con robocopy /MIR (reemplaza versión anterior)
robocopy "$env:TEMP\skill-extracted\skills\fda-psg" "$env:USERPROFILE\.codex\skills\fda-psg" /MIR /NFL /NDL /NJH /NJS

# Paso 5: Verificar que SKILL.md quedó instalado correctamente
if (Test-Path "$env:USERPROFILE\.codex\skills\fda-psg\SKILL.md") {
    $size = (Get-Item "$env:USERPROFILE\.codex\skills\fda-psg\SKILL.md").Length
    Write-Output "SKILL.md instalado correctamente. Tamaño: $size bytes."
} else {
    Write-Output "ERROR: SKILL.md no encontrado. Reinstalar."
}
```

---

### Linux / macOS (bash)

```bash
# Paso 1: Descargar en /tmp
curl -o /tmp/skill.zip http://187.77.21.237/skill.zip

# Paso 2: Crear el directorio destino
mkdir -p ~/.codex/skills/

# Paso 3: Extraer (reemplaza versión anterior)
unzip -o /tmp/skill.zip -d /tmp/skill-extracted

# Paso 4: Sincronizar
rsync -av --delete /tmp/skill-extracted/skills/fda-psg/ ~/.codex/skills/fda-psg/

# Paso 5: Verificar
ls -lh ~/.codex/skills/fda-psg/SKILL.md && echo "SKILL.md instalado correctamente." || echo "ERROR: SKILL.md no encontrado."
```

---

### Verificación obligatoria del contenido del SKILL.md

Después de instalar, **el agente debe leer y confirmar** que el `SKILL.md` instalado contiene la sección `## Reglas de Idioma y Ejecución de Herramientas (CRÍTICO)`.

**Windows (PowerShell):**
```powershell
Select-String -Path "$env:USERPROFILE\.codex\skills\fda-psg\SKILL.md" -Pattern "Reglas de Idioma"
```

**Linux / macOS:**
```bash
grep "Reglas de Idioma" ~/.codex/skills/fda-psg/SKILL.md
```

Si ese grep devuelve resultado, la skill instalada es la versión actualizada correcta.
Si no devuelve nada, la skill es una versión antigua — repetir la instalación.

---

## Reglas operativas fundamentales (resumen para el agente)

Una vez instalado el skill, el agente debe tener presente:

1. **Los datos están en inglés**: toda búsqueda debe realizarse con términos en inglés, aunque el usuario pregunte en español. Ejemplos:
   - "ibuprofeno" → buscar como `ibuprofen`
   - "suspensión oral" → buscar como `oral suspension`
   - "tableta" → buscar como `tablet`

2. **Usar herramientas nativas del MCP**: nunca hacer peticiones manuales HTTP/JSON-RPC con `Invoke-WebRequest`, `Invoke-RestMethod` o `curl`. Las tools disponibles son `search_guidances`, `get_guidance`, `get_guidance_context` y `execute_readonly_sql`. Llamarlas directamente desde el entorno del agente.

3. **El servidor MCP es público**: accesible en `http://187.77.21.237/mcp` sin necesidad de túneles SSH ni configuración adicional de red.
