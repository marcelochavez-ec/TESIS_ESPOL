# CATÁLOGO VERTICAL DPA INEC 2026

1. **Nombre y objetivo.** Cargar un catálogo único de códigos territoriales en `research_lab.catalogos.dpa_inec`, con `pk_dpa`, `tipo_dpa`, `descripcion_dpa` y la columna adicional calculada `orden_dpa`. Permite consultar nombres oficiales y relacionar provincias, cantones y códigos parroquiales sin escribir nombres provinciales manualmente en cada consulta.
2. **Archivos.** `03_PROCESOS_ETL/09_CATALOGO_DPA_INEC.py` implementa preparación, generación y carga. `05_CONFIGURACIONES/01_PROYECTO.json`, sección `catalogo_dpa`, fija edición, fuente, hash, exclusiones, conteos y salidas. `02_DOCUMENTACION/02_MAPEO_ENDI/08_DPA_INEC.sql` contiene estructura y los 1.562 registros necesarios para reproducir el catálogo sin Excel ni Python. `09_MAPEO_DPA_INEC.csv` describe los tipos de sus cuatro campos. Este documento registra las decisiones. El informe local `02_DOCUMENTACION/03_VALIDACIONES/30_CATALOGO_DPA_INEC.json` queda excluido de GitHub.
3. **Fuente y versión.** Se usa el [Excel oficial Códigos DPA 2026 del INEC](https://aplicaciones2.ecuadorencifras.gob.ec/SIN/descargas/cdpa2026.xlsx), publicado en el [Sistema de Clasificaciones del INEC](https://aplicaciones2.ecuadorencifras.gob.ec/SIN/). Su SHA-256 es `0d0ae33a0a0023ed44abcaa6b38a1c173fbda423e368a8f12bedda59d65d8f3a`, 129.401 bytes. Se comprobó que coincide byte a byte con el archivo local del autor `01_DATOS_FUENTE/09_CODIFICACION_2026.xlsx`. El PDF `02_DOCUMENTACION/04_BIBLIOGRAFIA/04_CLASIFICADOR_GEOGRÁFICO_ESTADISTICO_2026.pdf` declara edición 2026, corte al 31 de diciembre de 2025; se contrastaron la parroquia SHUAR PASTAZA (p. 37) y las zonas en estudio (p. 49). No se sustituye la clasificación histórica utilizada por ENDI R2.
4. **Entradas.** Excel aprobado, manifiesto, paquetes del entorno `espol` y PostgreSQL accesible por las variables PG* o pgpass existentes. La conexión predeterminada usa `research_lab`. La primera carga requiere permisos para crear la tabla en `catalogos`; el esquema ya existía localmente. La reproducción en otra instalación puede crear ese esquema con `CREATE SCHEMA IF NOT EXISTS`, sin alterar otros esquemas. No se almacenan contraseñas.
5. **Flujo paso a paso.** Se comprueba el hash del Excel; se leen todas sus hojas como texto; se toman los pares código/nombre de PROVINCIAS, CANTONES y PARROQUIAS; se añaden las parroquias urbanas de `DPA_PARURB/DPA_DESPARURB`; se verticalizan los niveles, conservando una entrada por código. Se rechazan códigos incompletos, descripciones vacías, conflictos entre nombres o padres inexistentes. Se comprueban los conteos fijados y se mapean las cuatro columnas antes de generar DDL y UPSERT. Solo la opción `--cargar` abre la conexión y escribe el catálogo.
6. **Reglas de lectura y diferencias de la fuente.** La hoja resumida CODIGOS no se utiliza como tabla principal: omite `160167 SHUAR PASTAZA`, presente en PARROQUIAS y en el PDF; además representa SINAÍ-CUCHAENTZA con `900951`, mientras PARROQUIAS/PDF emplean `140190` para la zona interparroquial. Se utilizan las hojas detalladas y se excluyen de esta tabla de tres niveles ordinarios los códigos especiales `90`, `9006`, `9009`, `900651`, `900951` y `140190`. Se conserva el Excel íntegro; no se inventan provincias/cantones para zonas en estudio ni se fusionan códigos incompatibles. Las repeticiones de cabeceras al desagregar parroquias urbanas se consolidan solo si código y descripción coinciden exactamente. Se eliminan únicamente espacios exteriores de códigos/nombres y las filas vacías o notas que no contienen datos en las columnas seleccionadas.
7. **Estructura.** `pk_dpa VARCHAR(6) NOT NULL` conserva el código oficial completo: dos dígitos para PROVINCIA, cuatro para CANTON y seis para PARROQUIA. Se declara explícitamente la longitud semántica del código; no es un entero autogenerado. `tipo_dpa VARCHAR(19) NOT NULL` resulta de nueve caracteres observados más margen de diez. `descripcion_dpa TEXT NOT NULL` conserva denominaciones, tildes y nombres largos. El nivel de seis dígitos incluye cabeceras cantonales (terminación 50), parroquias rurales y parroquias urbanas desagregadas; no equivale a un conteo exclusivo de gobiernos parroquiales rurales. `orden_dpa SMALLINT GENERATED ALWAYS AS (...) STORED NOT NULL` asigna automáticamente 1 a PROVINCIA, 2 a CANTON y 3 a PARROQUIA; no se inserta ni actualiza manualmente.
8. **Constraints y jerarquía.** `pk_dpa_inec` es la PK sobre `pk_dpa`; `ck_dpa_inec_tipo_codigo` comprueba tipo y longitud decimal 2/4/6; `ck_dpa_inec_descripcion` rechaza descripciones vacías; los cuatro campos son NOT NULL. Provincia y cantón padre se verifican por prefijos en Python y al ejecutar el SQL exportado. No se añade una columna para padre ni una FK artificial sobre expresiones de prefijo. Una inserción manual posterior no tiene una FK jerárquica que obligue a conservar padres: debe pasar por el cargador y sus verificaciones. Las tablas ENDI mantienen su estructura y sus relaciones anteriores.
9. **Salidas comprobadas.** 1.562 registros: 24 PROVINCIA, 222 CANTON y 1.316 PARROQUIA. La PK conserva ceros, por ejemplo `09` y `010101`. La carga verifica todos los valores código/tipo/descripción/orden contra el DataFrame preparado, no solamente el conteo. El hash del contenido ordenado de las cuatro columnas es `9034c69581b6313abdd1709d60f2ca4d960377475d3d35a84cae435aba021723`. El hash original de las tres columnas fuente permanece `646cbfc10207699457e580d8a5744ab00a15b1eaeb443ba94eaa3c744b4b28c6`. Las zonas especiales excluidas no se cuentan como provincias adicionales.
10. **SQL y repetición.** El SQL autónomo incorpora una transacción, guarda de base, estructura, verificaciones de tipos/restricciones, UPSERT, comentarios y controles finales. `ON CONFLICT (pk_dpa) DO UPDATE` solo actualiza una fila cuando tipo o descripción difieren; no duplica registros ni ejecuta DROP, TRUNCATE o DELETE. Si existen filas adicionales ajenas a esta entrega, la comprobación final falla y revierte la operación. El cargador Python comprueba estructura, PK y CHECK antes de cargar y compara el contenido completo antes del commit. No acepta otra edición o hash automáticamente.
11. **Funciones implementadas.** `preparar(raiz, descargar)` devuelve DataFrame, tipos y mapeo; puede descargar la fuente fijada únicamente si falta y se solicita. `tabla_catalogo(tipos)` define columnas y constraints. `generar_artefactos(raiz, preparados)` escribe el SQL completo y el catálogo de tipos. `cargar(raiz, preparados, conexion)` recibe una transacción activa, comprueba la base y sincroniza/verifica el catálogo sin commit interno. `main()` controla las opciones y confirma la transacción solo si todas las validaciones pasan. Los imports no leen fuentes ni conectan a PostgreSQL.
12. **Ejecución reproducible.** Desde la raíz se ejecuta el siguiente comando, con la credencial proporcionada externamente. `--descargar` recupera el Excel oficial fijado si no está presente; si el servidor publica otro contenido, el hash lo rechaza.

```powershell
conda run -n espol python -B 03_PROCESOS_ETL/09_CATALOGO_DPA_INEC.py --descargar --cargar
```

Para generar únicamente SQL y mapeo, se omite `--cargar`.

```powershell
conda run -n espol python -B 03_PROCESOS_ETL/09_CATALOGO_DPA_INEC.py
```

Como alternativa sin Python ni conexión a internet, se abre `02_DOCUMENTACION/02_MAPEO_ENDI/08_DPA_INEC.sql` en DBeaver, conectado a `research_lab`, y se ejecuta el archivo completo como script. Requiere PostgreSQL 18 por las comprobaciones del catálogo `conenforced`.

13. **Consultas y uso.** Se consulta el catálogo completo o un nivel concreto sin escribir datos.

```sql
SELECT orden_dpa, pk_dpa, tipo_dpa, descripcion_dpa
FROM catalogos.dpa_inec
ORDER BY orden_dpa, pk_dpa;
```

Para contar los niveles:

```sql
SELECT orden_dpa, tipo_dpa, COUNT(*) AS registros
FROM catalogos.dpa_inec
GROUP BY orden_dpa, tipo_dpa
ORDER BY orden_dpa;
```

Para obtener nombres provinciales desde Personas, conservando su granularidad:

```sql
SELECT c.pk_dpa AS codigo_provincia,
       c.descripcion_dpa AS provincia,
       COUNT(*) AS personas_muestra
FROM endi.f1_personas p
LEFT JOIN catalogos.dpa_inec c
  ON c.pk_dpa = LPAD(p.prov::integer::text, 2, '0')
 AND c.tipo_dpa = 'PROVINCIA'
GROUP BY c.pk_dpa, c.descripcion_dpa
ORDER BY c.pk_dpa;
```

Este cruce se comprobó para las 93.242 personas, sin códigos provinciales sin correspondencia ni multiplicación de filas. No modifica el SQL provincial histórico ni añade FK sobre `prov DOUBLE PRECISION`; una relación física nueva exige una migración explícita. Para análisis históricos por cantón/parroquia se necesita el catálogo de la edición aplicable, no asumir equivalencia con 2026.

14. **UI y servidor.** No hay interfaz Shiny. La consola informa conteos y hash; DBeaver muestra las cuatro columnas y los comentarios del catálogo. El servidor ejecuta creación inicial y UPSERT de una sola tabla, dentro de una transacción con bloqueo local de la tabla. No se altera la configuración del servidor ni las credenciales. No se crean índices adicionales porque la PK y el tamaño actual son suficientes.
15. **Dependencias.** Se reutilizan pandas, openpyxl, SQLAlchemy, Psycopg 3 y el mapeador común, ya fijados en `requirements.txt`. La descarga utiliza urllib de la biblioteca estándar. No se instalaron paquetes nuevos. El Excel y las evidencias locales permanecen excluidos; el SQL publicado contiene únicamente el catálogo territorial público, no microdatos ENDI.
16. **Validaciones realizadas.** Se cargó la tabla real en Windows; el SQL autónomo se ejecutó dos veces y produjo contenido idéntico. Cinco escrituras inválidas fueron rechazadas y revertidas: PK duplicada, código provincial incompleto, tipo incompatible con longitud, descripción vacía y PK nula. Se contrastaron las 1.562 ternas, sus padres, ceros y SHUAR PASTAZA; las tablas ENDI/datasets conservaron sus OID. Se repitió la carga Python en Docker Linux usando el módulo y manifiesto actuales montados sobre la imagen existente, sin reconstruirla; contenido, SQL y CSV de mapeo coincidieron con Windows. También se verificó la descarga y preparación en una copia temporal sin fuentes preexistentes. El informe indica expresamente ese alcance y no afirma que la imagen incluya ya el nuevo módulo.
17. **Cambios, riesgos y límites.** Se añadió la tabla autorizada, cargador numerado, fuente fijada en manifiesto, SQL completo, mapeo y documentación; se extendió la exclusión de evidencias a la carpeta `03_VALIDACIONES` que el autor reorganizó. Se respetó la reorganización local y no se restauraron carpetas antiguas ni se publicaron archivos ajenos en desarrollo. La tabla representa una sola edición; no mezclar versiones históricas bajo la misma PK. La descarga inicial necesita internet si falta el Excel; el SQL completo permite reproducción sin esa dependencia. La jerarquía se comprueba durante las cargas, según el límite descrito en el punto 8.

18. **Orden solicitado y migración comprobada.** Se añadió `orden_dpa` calculada y persistida, sin reemplazar la tabla ni alterar la PK o las tres columnas originales. La migración usa ADD COLUMN IF NOT EXISTS y se integra tanto al cargador como al SQL autónomo; se verifican tipo SMALLINT, NOT NULL y carácter generado. El DataFrame mapea los cuatro campos; el UPSERT solo envía los tres originales, porque PostgreSQL calcula el orden. Se comprobó la creación desde cero en un esquema temporal revertido, migración local, ejecución repetida del SQL y rechazo de escritura manual en la columna calculada (SQLSTATE 428C9). Los conteos son 1/PROVINCIA/24, 2/CANTON/222 y 3/PARROQUIA/1.316. La carga actual también se comprobó en Docker Linux y produjo el mismo hash de cuatro columnas y los mismos artefactos. Las evidencias están en 03_VALIDACIONES/31_ORDEN_DPA_INEC.json y no se publican. **Una tabla SQL no tiene orden de lectura garantizado: se consulta siempre con ORDER BY orden_dpa, pk_dpa.** En DBeaver se actualizan los metadatos para ver la columna nueva y se aplica ese orden en la cuadrícula o consulta.
