# Codex Skill: FDA Product-Specific Guidances (PSG)

Este documento contiene las instrucciones para que el agente Codex instale el skill y registre el servidor MCP. Son dos pasos independientes: ambos son necesarios.

---

## Conceptos clave antes de empezar

- **Instalar el skill** (`~/.codex/skills/fda-psg/`) le da al agente las instrucciones de comportamiento (SKILL.md). Por sí solo NO habilita ninguna tool.
- **Registrar el servidor MCP** (`~/.codex/config.toml`) es lo que hace que las tools `search_guidances`, `get_guidance`, `get_guidance_context` y `execute_readonly_sql` estén disponibles de forma nativa en el entorno del agente.
- Ambos pasos son obligatorios. Sin el registro MCP, el agente no puede ejecutar búsquedas aunque el skill esté instalado.

---

## Paso 1 — Instalar el Skill

### Windows (PowerShell)

```powershell
# Descargar el ZIP en TEMP (evita bloqueos de permisos)
Invoke-WebRequest -Uri 'http://187.77.21.237/skill.zip' -OutFile "$env:TEMP\skill.zip"

# Extraer en TEMP
Expand-Archive -LiteralPath "$env:TEMP\skill.zip" -DestinationPath "$env:TEMP\skill-extracted" -Force

# Crear el directorio destino si no existe
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.codex\skills\fda-psg" | Out-Null

# Sincronizar con robocopy (reemplaza versión anterior sin errores de permisos)
robocopy "$env:TEMP\skill-extracted\skills\fda-psg" "$env:USERPROFILE\.codex\skills\fda-psg" /MIR /NFL /NDL /NJH /NJS

# Verificar
if (Test-Path "$env:USERPROFILE\.codex\skills\fda-psg\SKILL.md") {
    Write-Output "Skill instalado correctamente."
} else {
    Write-Output "ERROR: SKILL.md no encontrado. Reinstalar."
}
```

### Linux / macOS (bash)

```bash
curl -o /tmp/skill.zip http://187.77.21.237/skill.zip
mkdir -p ~/.codex/skills/
unzip -o /tmp/skill.zip -d /tmp/skill-extracted
rsync -av --delete /tmp/skill-extracted/skills/fda-psg/ ~/.codex/skills/fda-psg/
ls ~/.codex/skills/fda-psg/SKILL.md && echo "Skill instalado." || echo "ERROR."
```

---

## Paso 2 — Registrar el servidor MCP en Codex (OBLIGATORIO)

> **Este es el paso que habilita las tools nativas**. Sin esto, el agente no puede ejecutar búsquedas.

### Opción A — Usando el comando de Codex (recomendado)

```bash
codex mcp add fda-psg-mcp --url http://187.77.21.237/mcp
```

Verificar que quedó registrado:
```bash
codex mcp list
```
Debe aparecer `fda-psg-mcp` en la lista.

### Opción B — Editando `config.toml` manualmente

Agregar este bloque al archivo `~/.codex/config.toml` (crearlo si no existe):

**Windows (PowerShell):**
```powershell
$config = "$env:USERPROFILE\.codex\config.toml"
$entry = "`n[mcp_servers.fda-psg-mcp]`nurl = `"http://187.77.21.237/mcp`"`n"
Add-Content -Path $config -Value $entry
```

**Linux / macOS:**
```bash
cat >> ~/.codex/config.toml << 'EOF'

[mcp_servers.fda-psg-mcp]
url = "http://187.77.21.237/mcp"
EOF
```

**Contenido resultante esperado en `config.toml`:**
```toml
[mcp_servers.fda-psg-mcp]
url = "http://187.77.21.237/mcp"
```

---

## Paso 3 — Verificar que las tools están disponibles

Tras registrar el servidor MCP, verificar conectividad:

```bash
codex mcp list
```

Debe mostrar `fda-psg-mcp` con estado conectado o la URL registrada.

Luego pedir al agente:
> "Buscá las Product-Specific Guidances de Ibuprofen"

Si responde con resultados reales de la base de datos (guías, fechas, RLD/RS), la configuración es correcta.
Si dice que no tiene las tools disponibles, verificar que el Paso 2 se ejecutó y reiniciar Codex.

---

## Reglas operativas que el agente debe seguir

1. **Los datos están en inglés**: traducir términos antes de buscar.
   - "ibuprofeno" → `Ibuprofen`
   - "suspensión oral" → `Oral Suspension`
   - "tableta" → `Tablet`

2. **Usar solo las tools nativas del MCP**: nunca hacer peticiones HTTP manuales con PowerShell o bash al endpoint `/mcp`.

3. **El servidor es público**: no requiere túneles SSH. La URL `http://187.77.21.237/mcp` es directamente accesible.

---

## Estructura del skill (referencia)

```text
skills/fda-psg/
├── SKILL.md                   # Instrucciones de comportamiento del agente
├── agents/
│   └── openai.yaml            # Declaración de dependencias MCP
├── references/
│   ├── tools.md               # Documentación técnica de las tools
│   ├── database-schema.md     # Esquema lógico de las vistas expuestas
│   ├── query-policy.md        # Reglas de validación SQL
│   └── response-guidelines.md # Formato de respuestas regulatorias
└── assets/
    ├── icon-small.svg
    └── icon-large.png
```
