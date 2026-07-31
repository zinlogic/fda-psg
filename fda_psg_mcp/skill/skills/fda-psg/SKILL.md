---
name: fda-psg-mcp
description: Busca, consulta y analiza Product-Specific Guidances de la FDA mediante el servidor MCP FDA PSG. Usar para preguntas sobre moléculas, vías de administración, formas farmacéuticas, recomendaciones de bioequivalencia y contenido de guías PSG. No usar para normativa FDA general que no corresponda a Product-Specific Guidances.
---

# FDA Product-Specific Guidances

Utilizar esta Skill para consultar la base de Product-Specific Guidances
de la FDA mediante las herramientas del servidor MCP `fda_psg`.

## Objetivo

Recuperar evidencia documental sobre guías específicas por producto
utilizando metadatos, documentos Markdown y fragmentos secuenciales.

No utilizar conocimiento general para completar información que no haya
sido recuperada desde el MCP.

## Herramientas disponibles

### `search_guidances`

Usar para localizar guías mediante uno o varios filtros:

- molécula o principio activo;
- vía de administración;
- forma farmacéutica;
- tipo;
- número RLD/RS;
- fecha de recomendación.

Esta debe ser la primera herramienta cuando todavía no se conoce el
`guidance_id`.

### `get_guidance`

Usar cuando se conoce el `guidance_id` y se necesita:

- consultar todos sus metadatos;
- conocer las moléculas asociadas;
- recuperar el contenido Markdown completo;
- consultar la URL original del documento FDA.

Evitar solicitar el Markdown completo cuando solamente se necesita una
sección limitada.

### `get_guidance_context`

Usar para recuperar chunks consecutivos pertenecientes a una guía.

Puede utilizarse:

- indicando un `chunk_index` central y una cantidad de chunks anteriores
  y posteriores;
- indicando un rango explícito de índices.

Esta herramienta no realiza búsqueda semántica.

### `execute_readonly_sql`

Usar únicamente cuando la consulta requiera operaciones que no puedan
resolverse adecuadamente con las herramientas anteriores, por ejemplo:

- conteos;
- agrupaciones;
- cruces complejos;
- estadísticas;
- filtros avanzados;
- detección de registros incompletos.

Solo generar consultas `SELECT` o `WITH ... SELECT`.

No generar sentencias que modifiquen datos, estructuras, permisos,
configuraciones o funciones de PostgreSQL.

## Flujo de trabajo

1. Identificar la molécula, vía, forma farmacéutica u otros filtros
   mencionados por el usuario.

2. Ejecutar `search_guidances`.

3. Revisar los resultados y seleccionar las guías relevantes.

4. Utilizar `get_guidance` cuando sea necesario consultar el documento
   completo.

5. Utilizar `get_guidance_context` cuando ya se conozca el índice o rango
   de chunks que debe analizarse.

6. Utilizar `execute_readonly_sql` solamente si las herramientas
   estructuradas no permiten resolver la consulta.

7. Construir la respuesta únicamente con información recuperada desde
   el MCP.

## Reglas documentales

- No afirmar que una guía contiene una recomendación sin recuperar el
  documento o los chunks correspondientes.
- No confundir una inferencia con una instrucción explícita de FDA.
- No inventar fechas, formas farmacéuticas, vías ni principios activos.
- No inferir el estado regulatorio de un documento si ese dato no está
  disponible.
- No presentar información de una guía como regla general aplicable a
  todos los productos.
- Diferenciar claramente información documental de interpretación
  técnica.
- Informar cuando no se encuentren guías compatibles con los filtros.

## Búsqueda semántica

La búsqueda semántica no está habilitada actualmente.

No intentar utilizar embeddings ni similitud vectorial hasta que el MCP
exponga una herramienta específica para esa función.

## Formato de respuesta

Para cada guía utilizada, informar cuando estén disponibles:

- molécula o combinación de moléculas;
- forma farmacéutica;
- vía de administración;
- fecha de recomendación;
- número RLD/RS;
- identificador interno de la guía;
- URL original de FDA.

Cuando la respuesta interprete el contenido, separar:

1. Evidencia recuperada.
2. Interpretación técnica.
3. Información faltante o limitaciones.

## Manejo de resultados extensos

Si el contenido es demasiado extenso:

1. No resumir información que no haya sido recuperada.
2. Solicitar o recuperar rangos más pequeños de chunks.
3. Priorizar las secciones directamente relacionadas con la pregunta.
4. Informar si el documento o resultado fue truncado.

## Consultas SQL

Antes de utilizar `execute_readonly_sql`:

1. Confirmar que la consulta no puede resolverse razonablemente con
   `search_guidances`.
2. Consultar únicamente las vistas autorizadas por el MCP.
3. Seleccionar solo las columnas necesarias.
4. Incluir un límite razonable cuando la consulta devuelva registros.
5. Evitar recuperar `markdown_content` mediante SQL salvo necesidad
   explícita.
6. No consultar ni devolver embeddings.
