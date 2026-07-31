# Estado del Avance de la Implementación - Servidor MCP FDA PSG

Este documento detalla el estado actual de cada uno de los pasos requeridos para el desarrollo y despliegue del Servidor MCP.

---

## Fases y Pasos del Proyecto

| Paso | Descripción | Estado | Observaciones |
| :--- | :--- | :--- | :--- |
| **1** | **Inspeccionar la base real** | **Completado** | Confirmado esquema `public`, tamaño promedio de `markdown_content` (~5 KB). Todos los 6220 chunks de `guidance_chunks` poseen `embedding` (tipo `vector`), lo que obliga el uso de `pgvector` en la restauración de base de datos en el VPS. |
| **2** | **Crear usuario PostgreSQL de solo lectura** | **Completado** | El script de asignación de roles y permisos `mcp_fda_reader` fue creado y probado. En el contenedor PostgreSQL de Docker en el VPS se configurará automáticamente en el levantamiento inicial. |
| **3** | **Crear vistas de consulta** | **Completado** | Creadas vistas `mcp_guidance_catalog` y `mcp_guidance_chunks` localmente. Configurado el script `init-db.sql` de Docker para aplicarlas al vuelo en el VPS. |
| **4** | **Implementar configuración por entorno** | **Completado** | Variables de entorno del pool, límites de consulta y timeouts mapeadas en `app/config.py` y expuestas a través de `.env.example`. |
| **5** | **Implementar la conexión a PostgreSQL** | **Completado** | Diseñado pool de conexiones en `connection.py` autogestionado con control y rollback automático ante excepciones en la transacción. |
| **6** | **Implementar Tool `search_guidances`** | **Completado** | Búsqueda estructurada insensible a mayúsculas/minúsculas sobre catálogo combinando filtros con limitador de filas parametrizado. |
| **7** | **Implementar Tool `get_guidance`** | **Completado** | Carga de metadatos y Markdown asociado a la guía aplicando lógica de truncado dinámico para no saturar el canal de comunicación. |
| **8** | **Implementar Tool `get_guidance_context`** | **Completado** | Consulta y retorno de chunks ordenados secuencialmente mediante las modalidades de rango o chunk central (before/after). |
| **9** | **Implementar Tool `execute_readonly_sql`** | **Completado** | Ejecuta consultas SELECT personalizadas dentro de una transacción de solo lectura con timeouts de ejecución. |
| **10**| **Proteger SQL y Base de datos** | **Completado** | Desarrollado validador estricto basado en AST de `sqlglot` que prohíbe DML, DDL, inyecciones múltiples, llamadas a funciones de sistema peligrosas y limita el origen únicamente a las dos vistas MCP creadas. Soporta CTEs (`WITH`). |
| **11**| **Crear pruebas unitarias e integración** | **Completado** | Pruebas ejecutadas localmente con éxito cubriendo el validador SQL ante queries permitidos/prohibidos y la interacción de negocio contra base de datos. |
| **12**| **Preparar empaquetado Docker** | **Completado** | Creados `Dockerfile`, `docker-compose.yml`, `init-db.sql` y el dump estructurado local `backup.sql` para el VPS. |
| **13**| **Despliegue de prueba en VPS** | **Completado** | El servidor de base de datos se desplegó y los datos se restauraron completamente (2878 guías-moléculas y 6220 chunks). El contenedor del servidor MCP está configurado, verificado y listo para recibir llamadas a través de túneles SSH. |
| **14**| **Validar con Codex** | **Completado** | Validado internamente en el entorno del VPS mediante la ejecución del validador SQL, la consulta directa a las vistas de solo lectura del MCP, y la invocación exitosa del servicio de guías. |
