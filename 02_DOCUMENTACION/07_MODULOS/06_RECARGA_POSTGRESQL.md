# RECARGA REPRODUCIBLE DE FUENTES EN POSTGRESQL

1. **Objetivo funcional.** Ejecutar las comprobaciones del proyecto y sustituir las seis tablas fuente en `research_lab.endi`, destino confirmado por el autor. Primero se mapea cada variable; las relaciones y constraints de negocio se definirán después.

2. **Archivos.** `03_PROCESOS_ETL/01_ETL_FUENTES.py` incorpora `recargar_fuentes_postgresql`; `02_MAPEO_POSTGRESQL.py` implementa `recargar_tablas` y COPY; `04_GESTION_PROYECTO.py` añade la acción ejecutar. `05_PRUEBAS/01_PRUEBAS_MAPEO.py` verifica condiciones previas y `02_PRUEBAS_RECARGA.py` comprueba PostgreSQL real. `05_CONFIGURACIONES/compose.yaml` define recarga. AGENTS.md y la skill Python describen esta ruta explícita.

3. **Flujo paso a paso.** El coordinador comprueba versiones, once hashes originales, dependencias y la suite local de 37 pruebas cuando está disponible; genera dos mapeos y compara los tres artefactos con la referencia aprobada. Después vuelve a verificar las seis fuentes, lee y normaliza todas sus columnas antes de modificar tablas. Abre una sola transacción, comprueba el nombre de la base y la existencia del esquema, obtiene un bloqueo asesor para impedir otra recarga simultánea y limita a diez segundos la espera por bloqueos SQL. Sustituye las seis tablas, copia las filas y comprueba resultados. Solo entonces confirma la transacción, escribe el informe y actualiza el inventario.

4. **Entradas y requisitos.** Se requieren las fuentes originales en 01_DATOS_FUENTE y los diccionarios/PDF declarados en el manifiesto; Docker Linux/amd64 o emulación compatible; espacio y memoria para las seis fuentes normalizadas; PostgreSQL accesible con research_lab y endi ya existentes; permisos para eliminar y crear las seis tablas. El contenedor conecta por host.docker.internal; PGHOST_CONTENEDOR permite indicar otro servidor. PGPORT, PGDATABASE y PGUSER se reciben del entorno. Un destino diferente de la base/esquema declarados se rechaza. La contraseña se solicita en consola si no existe PGPASSWORD o un mecanismo pgpass utilizable. No se guarda en el repositorio.

5. **Salidas.** Las seis tablas sustituidas; los tres artefactos de mapeo; los reportes de entorno/reproducción; `09_VALIDACIONES/12_RECARGA_POSTGRESQL.json` con filas, columnas, tipos/nulos verificados y huella por tabla; inventario actualizado. `15_REPETICION_RECARGA.json` documenta la comparación efectuada durante esta tarea; la ejecución habitual no simula ni sobrescribe esa evidencia con una sola carga.

6. **Fuentes y tablas comprobadas.** Los seis RDS se identifican por nombre y SHA-256 en `01_PROYECTO.json`. En PostgreSQL 18.3 se obtuvieron:

| Tabla en research_lab | Filas | Variables |
| --- | ---: | ---: |
| endi.f1_hogar | 20.186 | 133 |
| endi.f1_personas | 93.242 | 124 |
| endi.f2_mef | 19.846 | 289 |
| endi.f2_lactancia | 12.141 | 71 |
| endi.f2_salud_ninez | 22.188 | 413 |
| endi.f3_desarrollo_inf | 9.836 | 393 |
| Total | 177.439 | 1.423 |

7. **Reglas de negocio.** Se preservan filas, códigos, nulos y nombres originales de variables. VARCHAR usa longitud máxima completa más diez caracteres; los tipos DATE/TIMESTAMP, enteros por rango, DOUBLE, NUMERIC y BOOLEAN siguen el mapeador común. No se crean PK/FK/UNIQUE/CHECK, no se filtran registros y no se reinterpretan fechas parciales. No se reemplaza todo el esquema ni se tocan tablas ajenas a las seis declaradas.

8. **Interfaz de usuario.** La consola presenta tres etapas: comprobación, recarga y confirmación. El autor abre la terminal en la raíz del proyecto y ejecuta el siguiente comando; este construye la imagen cuando corresponde y realiza todo el flujo. Si aparece la solicitud de contraseña, el autor introduce la clave sin guardarla en un archivo.

```powershell
docker compose -f 05_CONFIGURACIONES/compose.yaml run --build --rm recarga
```

9. **Alternativa local.** Con el entorno espol ya instalado, el autor puede ejecutar el mismo coordinador sin Docker. Este comando también sustituye las seis tablas; se elige una de las dos formas de ejecución.

```powershell
conda run --no-capture-output -n espol python -B 03_PROCESOS_ETL/04_GESTION_PROYECTO.py ejecutar --sobrescribir-fuentes
```

10. **Lógica de servicio.** No hay Shiny/UI web. `recargar_fuentes_postgresql(raiz, esquema, sobrescribir, solicitar_clave)` recibe la ubicación del proyecto y opciones explícitas, devuelve un informe después del commit y tiene como efecto sustituir las seis fuentes. `recargar_tablas(conexion, esquema, fuentes, sobrescribir)` recibe una conexión dentro de una transacción y un diccionario de DataFrames/tipos/metadatos ya normalizados; devuelve comprobaciones por tabla sin confirmar por su cuenta. El coordinador exige `--sobrescribir-fuentes`; ejecutar sin esa bandera falla antes de cargar.

11. **SQL relevante.** La transacción comprueba `current_database()` y el catálogo del esquema. `pg_try_advisory_xact_lock` evita dos tandas simultáneas. Un único `DROP TABLE IF EXISTS` enumera las seis tablas con `RESTRICT`, sin CASCADE; SQLAlchemy crea columnas con tipos explícitos y Psycopg 3 realiza COPY. Se contrastan COUNT(*), tipos reflejados y COUNT(columna) contra el origen normalizado. La huella utiliza MD5 de cada fila serializada mediante row_to_json, ordena las huellas e incluye duplicados antes de calcular la huella de la tabla.

12. **Dependencias.** Python 3.15.0, pandas, NumPy, pyreadr, SQLAlchemy y Psycopg 3, junto con los lectores Excel y dependencias exactas del único requirements.txt. El entorno Conda se llama espol; la imagen y arquitectura se describen en 05_REPRODUCIBILIDAD.md. PostgreSQL es externo: este flujo no instala ni configura un servidor.

13. **Validaciones.** Se rechazan fuentes alteradas, nombres inválidos, mapeos ambiguos, base/esquema diferentes, ausencia de autorización explícita en el comando, discrepancias de filas/tipos/nulos y recargas concurrentes. Una dependencia externa que impida DROP produce error. Cualquier error SQL anterior al commit revierte conjuntamente las seis tablas; no deja una tanda parcialmente confirmada.

14. **Pruebas ejecutadas.** Se pasó la suite de 37 casos y se construyó la imagen. La prueba SQL de integración pasó tanto desde Windows como desde el contenedor: insertó fechas, textos con cero inicial, DOUBLE y enteros nulos; repitió la carga; provocó un fallo al copiar la segunda tabla y verificó la restauración del contenido anterior; creó una vista dependiente y comprobó el rechazo de DROP RESTRICT. El esquema de prueba se eliminó mediante rollback. Además, se ejecutaron dos recargas completas reales de las seis fuentes y coincidieron nombres, filas, columnas y huellas de contenido, sin acumulación. Los informes 12–15 conservan la evidencia.

15. **Riesgos y rendimiento.** La sustitución elimina los índices, permisos específicos y constraints que se hubieran añadido dentro de esas seis tablas: se reconstruyen como fuentes sin restricciones de negocio. Las dependencias externas detienen la operación. La transacción necesita permisos y espacio de trabajo; carga todas las fuentes normalizadas en memoria y bloquea las tablas mientras las sustituye. MD5 es una comprobación práctica de repetición en el mismo servidor y serialización, no una garantía criptográfica ni una comparación binaria entre versiones distintas de PostgreSQL. Las fuentes originales deben recuperarse por separado en otro equipo; no se regeneran desde el código.

16. **Cambios de esta tarea.** Se habilitó la recarga expresamente confirmada en research_lab.endi, con mapeo previo, sustitución por lote, COPY, comprobaciones y rollback. Se añadió el servicio recarga y la documentación del comando único; el servicio mapeo y la acción reproducir conservan la opción de comprobar sin escribir en PostgreSQL.

17. **Etapa posterior.** Las relaciones y constraints se diseñarán tras revisar el catálogo completo y el manual ENDI. Cualquier incorporación deberá coordinarse con esta recarga de fuentes antes de depender de índices o restricciones añadidos manualmente.

18. **Distribución.** Las pruebas y los reportes 09_VALIDACIONES permanecen en el equipo y no se publican. Una copia de GitHub genera sus propios reportes y verifica fuentes, entorno y mapeo aprobado; indica expresamente la ausencia de suite local, sin inventar una aprobación. Los scripts de recarga sí se publican.

19. **Recuperación real desde GitHub.** Se clonó y ejecutó el commit a5cfd41a6d43b8c801376c7c983dd7640df7f061 en el host Windows, con las fuentes recuperadas por separado y la imagen reconstruida. La carga completa obtuvo las mismas seis tablas, filas, tipos, nulos y huellas que la ejecución local. Se comprobó este escenario con PostgreSQL 18.3 y Docker Linux/amd64; otros equipos deben cumplir los requisitos de entradas, permisos, servidor y arquitectura descritos.
