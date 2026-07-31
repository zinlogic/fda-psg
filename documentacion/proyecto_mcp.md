# Proyecto: Implementación de un servidor MCP para consulta de guías FDA PSG

## 1. Contexto general

El sistema existente descarga, procesa y almacena en PostgreSQL las **Product-Specific Guidances (PSG)** publicadas por la FDA. La base contiene metadatos, moléculas relacionadas, documentos convertidos a Markdown y fragmentos o chunks asociados a cada guía. 

El objetivo de esta nueva etapa es implementar un **servidor MCP remoto** que permita a Codex, Claude y otros agentes compatibles consultar esa información de forma estructurada.

La arquitectura general será:

```text
Codex / Claude
       │
       │ MCP
       ▼
Servidor MCP Python
       │
       ▼
PostgreSQL
Base FDA PSG
```

---

# 2. Objetivo inmediato

En esta primera etapa se deberá construir un **MCP funcional de demostración**, orientado exclusivamente a validar:

* la conexión con PostgreSQL;
* el descubrimiento de las tools por parte del agente;
* la búsqueda estructurada de guías;
* la recuperación de documentos;
* la recuperación secuencial de chunks;
* la ejecución controlada de consultas SQL de solo lectura;
* la estabilidad del MCP en local y posteriormente en un VPS.

## Restricción principal de esta etapa

La primera versión **no deberá implementar autenticación comercial, licenciamiento ni monetización**.

El objetivo actual es comprobar que el MCP funciona correctamente y que resulta útil para un agente de IA.

La autenticación, los límites por cliente, las suscripciones y el empaquetado como Skill o Plugin se evaluarán una vez validado técnicamente el servidor MCP.

---

# 3. Visión final del producto

Aunque no forma parte de la implementación inmediata, la visión comercial es ofrecer el acceso al MCP como un servicio integrado con Skills o Plugins para plataformas como:

* Codex;
* Claude Code;
* Claude Cowork;
* otros clientes compatibles con MCP.

El producto final podría incluir:

```text
Skill o Plugin
      +
Acceso al MCP remoto
      +
Base FDA PSG actualizada
      +
Autenticación y licenciamiento
      +
Soporte y mantenimiento
```

Esta etapa comercial deberá mantenerse desacoplada del desarrollo inicial.

---

# 4. Alcance de la primera versión

## Incluido

* Servidor MCP desarrollado en Python.
* Conexión a PostgreSQL.
* Pool de conexiones.
* Tools MCP:

  * `search_guidances`
  * `get_guidance`
  * `get_guidance_context`
  * `execute_readonly_sql`
* Usuario PostgreSQL exclusivo de solo lectura.
* Validación de consultas SQL.
* Límites de filas, duración y tamaño de respuesta.
* Manejo estructurado de errores.
* Logs técnicos.
* Pruebas unitarias.
* Pruebas de integración con PostgreSQL.
* Pruebas reales desde Codex.
* Ejecución local.
* Despliegue de prueba en VPS.

## Fuera de alcance

No implementar en esta etapa:

* autenticación Bearer;
* OAuth;
* usuarios o cuentas de clientes;
* claves de activación;
* licencias;
* límites mensuales por cliente;
* facturación;
* monetización;
* Skill o Plugin distribuible;
* archivo `skill.zip`;
* panel administrativo;
* búsqueda semántica;
* generación de embeddings;
* tool `semantic_search_chunks`;
* modificaciones sobre la base;
* sincronización con FDA;
* descarga o actualización de PDFs;
* conversión de PDFs a Markdown.

---

# 5. Estado actual de la base de datos

La base PostgreSQL contiene las siguientes tablas principales.

## `molecules`

Catálogo de moléculas o principios activos.

Campos relevantes:

```text
id
name
chembl_id
created_at
```

## `guidances`

Contiene los metadatos y el contenido completo de cada guía.

Campos relevantes:

```text
id
rld_rs_number
type
route
dosage_form
date_recommended
pdf_url
pdf_path
markdown_path
markdown_content
pdf_hash
created_at
updated_at
```

## `guidance_molecules`

Tabla intermedia que representa la relación muchos-a-muchos entre guías y moléculas.

Campos:

```text
guidance_id
molecule_id
```

## `guidance_chunks`

Contiene los fragmentos secuenciales de cada guía.

Campos relevantes:

```text
id
guidance_id
chunk_index
chunk_content
embedding
created_at
```

La columna `embedding` existe, pero todavía no fue poblada. Por lo tanto:

* los chunks pueden recuperarse por índice;
* no se deberá realizar búsqueda vectorial;
* `get_guidance_context` sí puede implementarse;
* `semantic_search_chunks` queda pendiente.

---

# 6. Arquitectura del MCP de demostración

```text
Codex
   │
   │ MCP local o remoto
   ▼
Servidor MCP
   │
   ├── Definición de tools
   ├── Validación de parámetros
   ├── Capa de servicios
   ├── Validador SQL
   ├── Límites de consulta
   └── Logs
   │
   ▼
PostgreSQL
Usuario read-only
```

La lógica de acceso a datos deberá estar separada de la implementación MCP.

Esto permitirá reutilizarla posteriormente desde:

* una API REST;
* un panel web;
* otros agentes;
* procesos internos;
* una futura versión comercial.

---

# 7. Estructura sugerida del proyecto

```text
fda_psg_mcp/
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── repositories.py
│   │   └── models.py
│   │
│   ├── services/
│   │   ├── guidance_service.py
│   │   └── sql_service.py
│   │
│   ├── mcp/
│   │   ├── server.py
│   │   └── tools/
│   │       ├── search_guidances.py
│   │       ├── get_guidance.py
│   │       ├── get_guidance_context.py
│   │       └── execute_readonly_sql.py
│   │
│   ├── security/
│   │   ├── sql_validator.py
│   │   ├── query_limits.py
│   │   └── allowed_objects.py
│   │
│   └── logging/
│       └── audit.py
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── scripts/
│   └── create_readonly_user.sql
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

# 8. Etapas de implementación

## Paso 1: inspeccionar la base real

Antes de implementar las tools, el agente de programación deberá conectarse a PostgreSQL y verificar:

1. Nombre exacto del esquema.
2. Nombre exacto de las tablas.
3. Tipos de cada columna.
4. Claves primarias.
5. Claves foráneas.
6. Restricciones de unicidad.
7. Índices existentes.
8. Cantidad de guías.
9. Cantidad de moléculas.
10. Cantidad de chunks.
11. Tamaño promedio de `markdown_content`.
12. Valores reales de:

    * `type`
    * `route`
    * `dosage_form`
13. Estado de la columna `embedding`.
14. Existencia y continuidad de `chunk_index`.

### Resultado esperado

Generar un breve informe técnico con:

* esquema confirmado;
* diferencias respecto del diseño esperado;
* índices faltantes;
* posibles inconsistencias;
* ejemplos reales de datos.

No asumir que la imagen o la documentación coinciden exactamente con el esquema desplegado.

---

## Paso 2: crear un usuario PostgreSQL de solo lectura

Aunque todavía no se implemente autenticación en el MCP, la conexión a la base deberá utilizar un usuario restringido.

El usuario deberá:

* tener permiso de conexión;
* tener permiso de `SELECT`;
* no poder insertar;
* no poder actualizar;
* no poder eliminar;
* no poder crear ni modificar estructuras;
* no ser superusuario.

Ejemplo conceptual:

```text
Usuario: mcp_fda_reader
Permisos: CONNECT + SELECT
```

Preferentemente, el usuario deberá acceder solamente a vistas preparadas para el MCP.

---

## Paso 3: crear vistas de consulta

### Vista `mcp_guidance_catalog`

Deberá reunir:

* `guidance_id`;
* número RLD/RS;
* tipo;
* vía;
* forma farmacéutica;
* fecha recomendada;
* URL FDA;
* identificador de molécula;
* nombre de molécula;
* identificador ChEMBL.

### Vista `mcp_guidance_chunks`

Deberá reunir:

* identificador del chunk;
* identificador de guía;
* índice del chunk;
* contenido;
* metadatos principales de la guía.

La tool SQL libre deberá acceder preferentemente solo a estas vistas.

---

## Paso 4: implementar configuración por entorno

Variables mínimas:

```text
DATABASE_HOST
DATABASE_PORT
DATABASE_NAME
DATABASE_USER
DATABASE_PASSWORD

MCP_HOST
MCP_PORT
MCP_TRANSPORT

SQL_STATEMENT_TIMEOUT_MS
SQL_LOCK_TIMEOUT_MS
SQL_MAX_ROWS
SQL_MAX_RESPONSE_BYTES

GUIDANCE_MAX_MARKDOWN_BYTES
GUIDANCE_CONTEXT_MAX_CHUNKS

LOG_LEVEL
```

No implementar todavía:

```text
MCP_AUTH_TOKEN
OAUTH_CLIENT_ID
LICENSE_KEY
CUSTOMER_ID
BILLING_PLAN
```

Estas variables corresponden a la futura etapa de autenticación y monetización.

---

## Paso 5: implementar la conexión a PostgreSQL

La capa de base de datos deberá:

* utilizar un pool de conexiones;
* reutilizar conexiones;
* aplicar timeouts;
* usar consultas parametrizadas;
* hacer rollback ante errores;
* devolver resultados estructurados;
* ocultar credenciales en los logs;
* cerrar correctamente las conexiones;
* manejar pérdidas temporales de conexión.

Las consultas de `execute_readonly_sql` deberán ejecutarse dentro de una transacción de solo lectura.

---

# 9. Tools MCP

## 9.1 `search_guidances`

### Propósito

Buscar guías mediante filtros estructurados.

### Entrada propuesta

```json
{
  "molecule": "Amlodipine",
  "route": "Oral",
  "dosage_form": "Tablet",
  "guidance_type": null,
  "rld_rs_number": null,
  "date_from": null,
  "date_to": null,
  "limit": 20,
  "offset": 0
}
```

### Reglas

* Todos los filtros pueden ser opcionales.
* Exigir al menos un filtro para evitar búsquedas generales accidentales.
* La búsqueda de moléculas deberá admitir coincidencia parcial.
* La búsqueda deberá ser independiente de mayúsculas y minúsculas.
* Todas las consultas deberán estar parametrizadas.
* El límite deberá tener un máximo configurable.
* Una guía con varias moléculas no deberá aparecer duplicada.

### Respuesta esperada

```json
{
  "success": true,
  "total_returned": 1,
  "results": [
    {
      "guidance_id": 42,
      "rld_rs_number": "RLD",
      "type": "New",
      "route": "Oral",
      "dosage_form": "Tablet",
      "date_recommended": "2024-01-15",
      "molecules": [
        {
          "id": 8,
          "name": "Amlodipine Besylate",
          "chembl_id": "CHEMBL..."
        }
      ],
      "pdf_url": "https://..."
    }
  ]
}
```

No devolver en esta tool:

* `markdown_content`;
* chunks;
* embeddings;
* rutas internas del VPS.

---

## 9.2 `get_guidance`

### Propósito

Recuperar una guía específica con sus metadatos y, opcionalmente, el contenido Markdown.

### Entrada

```json
{
  "guidance_id": 42,
  "include_markdown": true
}
```

### Respuesta

```json
{
  "success": true,
  "guidance": {
    "guidance_id": 42,
    "rld_rs_number": "RLD",
    "type": "New",
    "route": "Oral",
    "dosage_form": "Tablet",
    "date_recommended": "2024-01-15",
    "molecules": [
      {
        "id": 8,
        "name": "Amlodipine Besylate"
      }
    ],
    "pdf_url": "https://...",
    "markdown_content": "..."
  },
  "content_truncated": false
}
```

### Reglas

* Si la guía no existe, devolver un error controlado.
* Limitar el tamaño máximo del Markdown.
* Informar cuando el contenido sea truncado.
* No devolver el `embedding`.
* No devolver rutas internas salvo que sea estrictamente necesario.

---

## 9.3 `get_guidance_context`

### Propósito

Recuperar chunks consecutivos de una guía sin utilizar embeddings.

### Modalidad por chunk central

```json
{
  "guidance_id": 42,
  "chunk_index": 8,
  "before": 2,
  "after": 3
}
```

Esto devolvería los chunks:

```text
6, 7, 8, 9, 10 y 11
```

### Modalidad por rango

```json
{
  "guidance_id": 42,
  "chunk_from": 5,
  "chunk_to": 12
}
```

### Reglas

* Solo se podrá utilizar una modalidad por llamada.
* `before` y `after` tendrán un máximo.
* `chunk_from` no podrá ser mayor que `chunk_to`.
* El rango total tendrá un máximo configurable.
* Los chunks deberán pertenecer a la misma guía.
* Los resultados deberán estar ordenados por `chunk_index`.
* No se deberá consultar ni devolver la columna `embedding`.

### Respuesta

```json
{
  "success": true,
  "guidance": {
    "guidance_id": 42,
    "route": "Oral",
    "dosage_form": "Tablet",
    "molecules": ["Amlodipine Besylate"],
    "pdf_url": "https://..."
  },
  "requested_range": {
    "from": 5,
    "to": 12
  },
  "chunks": [
    {
      "chunk_id": 100,
      "chunk_index": 5,
      "chunk_content": "..."
    }
  ]
}
```

---

## 9.4 `execute_readonly_sql`

### Propósito

Permitir consultas complejas que no puedan resolverse fácilmente mediante `search_guidances`.

Ejemplos:

* agrupaciones;
* conteos;
* cruces entre moléculas;
* combinaciones avanzadas de filtros;
* análisis de cobertura documental;
* detección de registros incompletos.

### Entrada

```json
{
  "sql": "SELECT dosage_form, COUNT(*) AS total FROM mcp_guidance_catalog GROUP BY dosage_form ORDER BY total DESC LIMIT 20"
}
```

### Operaciones permitidas

Únicamente:

```text
SELECT
WITH ... SELECT
```

### Operaciones prohibidas

```text
INSERT
UPDATE
DELETE
MERGE
CREATE
ALTER
DROP
TRUNCATE
COPY
CALL
DO
GRANT
REVOKE
VACUUM
ANALYZE
SET
RESET
LOCK
```

También se deberán rechazar:

* múltiples sentencias;
* tablas no autorizadas;
* acceso a `pg_catalog`;
* acceso a `information_schema`;
* funciones peligrosas;
* `SELECT ... FOR UPDATE`;
* operaciones de archivos;
* operaciones de red;
* consultas excesivamente costosas;
* resultados sin límite razonable;
* instrucciones ocultas dentro de un `WITH`;
* consultas ambiguas que el validador no pueda interpretar.

---

# 10. Seguridad de las consultas SQL

Aunque el MCP no tenga autenticación en esta etapa, la ejecución de SQL deberá estar protegida.

## Flujo obligatorio

```text
SQL recibido
    ↓
Parser SQL
    ↓
Validación de una única sentencia
    ↓
Validación SELECT / WITH SELECT
    ↓
Whitelist de vistas y funciones
    ↓
EXPLAIN sin ANALYZE
    ↓
Control de costo y filas estimadas
    ↓
Transacción READ ONLY
    ↓
Timeout
    ↓
Resultado limitado
```

## Parser

No utilizar solamente expresiones regulares.

El parser deberá identificar:

* tipo de sentencia;
* objetos consultados;
* funciones;
* subconsultas;
* CTE;
* operaciones ocultas;
* bloqueos;
* cantidad de sentencias.

## Revisión mediante LLM

La revisión de seguridad mediante LLM podrá agregarse como capa complementaria, pero no deberá ser un requisito inicial para que el demo funcione.

Si se implementa:

```text
parser_ok
AND whitelist_ok
AND llm_allowed
AND explain_ok
AND database_permissions_ok
```

Una aprobación del LLM nunca deberá reemplazar los controles determinísticos.

---

# 11. Límites iniciales

Valores sugeridos para el demo:

```text
Tiempo máximo de consulta SQL: 5 segundos
Tiempo máximo de espera por bloqueo: 1 segundo
Cantidad máxima de filas: 200
Cantidad máxima de chunks: 20
Cantidad máxima de resultados de búsqueda: 100
Tamaño máximo de respuesta: configurable
```

Si una respuesta excede los límites:

* truncar de forma controlada;
* informar que fue truncada;
* indicar la cantidad devuelta;
* sugerir refinar la consulta.

---

# 12. Manejo de errores

Formato general:

```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "message": "Descripción comprensible del error."
}
```

Errores previstos:

```text
GUIDANCE_NOT_FOUND
INVALID_PARAMETERS
INVALID_CHUNK_RANGE
SQL_NOT_ALLOWED
SQL_PARSE_ERROR
QUERY_TIMEOUT
QUERY_TOO_EXPENSIVE
RESULT_TOO_LARGE
DATABASE_UNAVAILABLE
INTERNAL_ERROR
```

No devolver:

* stack traces;
* contraseñas;
* cadenas de conexión;
* rutas sensibles;
* información interna de PostgreSQL.

---

# 13. Logs

Registrar:

* fecha y hora;
* nombre de la tool;
* parámetros sanitizados;
* duración;
* cantidad de resultados;
* consulta SQL normalizada o hash;
* motivo de rechazo;
* código de error.

No registrar:

* contraseñas;
* contenido completo de los documentos;
* credenciales del VPS;
* datos sensibles de configuración.

---

# 14. Pruebas

## Pruebas unitarias

Cubrir:

* filtros individuales;
* filtros combinados;
* búsqueda parcial de moléculas;
* paginación;
* recuperación de guía;
* Markdown truncado;
* recuperación de chunks;
* rangos inválidos;
* SQL permitido;
* SQL de escritura;
* múltiples sentencias;
* tablas prohibidas;
* funciones peligrosas;
* timeouts;
* límites de filas.

## Pruebas adversariales

Todas estas consultas deberán ser rechazadas:

```sql
DROP TABLE guidances;
```

```sql
SELECT * FROM guidances; DELETE FROM guidances;
```

```sql
SELECT pg_sleep(60);
```

```sql
SELECT * FROM pg_catalog.pg_roles;
```

```sql
SELECT * FROM mcp_guidance_catalog FOR UPDATE;
```

```sql
WITH deleted AS (
    DELETE FROM guidances RETURNING *
)
SELECT * FROM deleted;
```

## Pruebas de integración

Validar:

1. Conexión a PostgreSQL.
2. Ejecución de las cuatro tools.
3. Transacciones de solo lectura.
4. Límites de consultas.
5. Manejo de errores.
6. Descubrimiento de tools desde Codex.
7. Uso real sobre guías FDA.

---

# 15. Estrategia de despliegue para el demo

## Etapa local

Primero ejecutar:

```text
Codex
   ↓
MCP local
   ↓
PostgreSQL
```

Validar todas las tools antes de exponer el servicio.

## Etapa VPS

Luego desplegar:

```text
Codex
   ↓
MCP en VPS
   ↓
PostgreSQL
```

Como todavía no habrá autenticación, el MCP no deberá quedar públicamente abierto.

Para el demo utilizar alguna de estas alternativas:

* acceso únicamente por localhost;
* túnel SSH;
* VPN;
* restricción por IP en el firewall;
* red privada;
* proxy temporal con acceso restringido.

No implementar todavía una solución de autenticación comercial dentro del código del MCP.

---

# 16. Integración con Codex

En esta etapa, Codex deberá conectarse directamente al MCP.

Todavía no se deberá crear el paquete comercial de Skill o Plugin.

Probar preguntas como:

```text
Buscá las guías FDA relacionadas con amlodipine por vía oral.
```

```text
Obtené la guía con identificador 42.
```

```text
Mostrame los chunks 10 a 15 de la guía 42.
```

```text
Contá cuántas guías existen por forma farmacéutica.
```

```text
Intentá eliminar una guía de la base.
```

La última prueba deberá ser rechazada por `execute_readonly_sql`.

---

# 17. Criterios de aceptación del demo

La primera versión se considerará terminada cuando:

1. El servidor MCP inicie correctamente.
2. Se conecte a PostgreSQL con un usuario de solo lectura.
3. Codex descubra las cuatro tools.
4. `search_guidances` combine correctamente múltiples filtros.
5. `get_guidance` recupere metadatos y Markdown.
6. `get_guidance_context` recupere chunks consecutivos.
7. `execute_readonly_sql` ejecute consultas complejas de lectura.
8. El sistema rechace cualquier intento de escritura.
9. Los límites y timeouts funcionen.
10. Los errores sean estructurados.
11. Existan pruebas automatizadas.
12. El MCP pueda ejecutarse localmente.
13. El MCP pueda probarse en el VPS mediante acceso restringido.
14. Codex pueda resolver consultas reales utilizando la base FDA PSG.

---

# 18. Etapas posteriores al demo

Estas etapas deberán comenzar únicamente después de validar el MCP.

## Fase posterior A: ajuste funcional

* analizar cómo usa Codex las tools;
* corregir parámetros;
* mejorar descripciones;
* optimizar respuestas;
* agregar nuevas tools si resulta necesario.

## Fase posterior B: búsqueda semántica

* generar chunks definitivos;
* generar embeddings;
* poblar `guidance_chunks.embedding`;
* crear índices vectoriales;
* implementar `semantic_search_chunks`;
* combinar filtros estructurados y similitud semántica.

## Fase posterior C: Skill o Plugin

* crear `SKILL.md`;
* definir instrucciones de uso;
* declarar la dependencia del MCP;
* preparar ejemplos;
* empaquetar el producto;
* probar instalación desde Codex y Claude.

## Fase posterior D: autenticación

* implementar Bearer Token, API keys u OAuth;
* identificar clientes;
* gestionar credenciales;
* revocar accesos;
* registrar consumo;
* definir roles y permisos.

## Fase posterior E: monetización

* planes comerciales;
* límites de consultas;
* vencimiento de accesos;
* suscripciones;
* licencias;
* métricas de uso;
* facturación;
* soporte;
* acceso empresarial.

---

# 19. Orden definitivo del proyecto

```text
1. Verificar base PostgreSQL
2. Implementar MCP local
3. Implementar las cuatro tools
4. Proteger SQL y base de datos
5. Crear pruebas automatizadas
6. Validar con Codex
7. Desplegar demo restringido en VPS
8. Ajustar funcionalidad
9. Crear Skill o Plugin
10. Incorporar autenticación
11. Incorporar licenciamiento y monetización
```

La prioridad actual termina en el punto 7.

No avanzar con autenticación, Skill, Plugin o monetización hasta que el MCP haya demostrado estabilidad y utilidad real.
