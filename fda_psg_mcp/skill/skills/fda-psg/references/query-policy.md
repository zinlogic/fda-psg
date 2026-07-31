# Política de consultas SQL

Solo están permitidas consultas:

- SELECT
- WITH ... SELECT

Las consultas deben:

- utilizar vistas autorizadas;
- tener un propósito exclusivamente analítico;
- seleccionar únicamente las columnas necesarias;
- limitar la cantidad de resultados;
- evitar recuperar documentos completos innecesariamente.

No están permitidas operaciones de:

- escritura;
- modificación de estructura;
- administración;
- bloqueo;
- acceso al sistema;
- ejecución de funciones no autorizadas.
