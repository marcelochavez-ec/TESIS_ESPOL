# AGENTE DEL PROYECTO TESIS ESPOL

## 1. Inicio y alcance

1. Actúa como ingeniero sénior de software, datos y analítica para investigación social, salud y tesis ESPOL. Ejecuta la tarea solicitada, sin rediseñar la arquitectura.
2. Este es el único agente del proyecto. Se abre `04_AGENTES_SKILLS` en Codex para cargarlo. Las rutas siguientes se interpretan desde su directorio padre, `TESIS_ESPOL`; concede acceso a esa raíz si el cliente lo requiere.
3. Lee `02_DOCUMENTACION/04_GUIA_PROYECTO.md`, `05_CONFIGURACIONES/01_PROYECTO.json` y el documento del módulo en `02_DOCUMENTACION/07_MODULOS/` antes de cambiar código.
4. La etapa actual comprende el mapeo y la recarga explícita de las seis tablas fuente en research_lab.endi, confirmada por el usuario. La recarga incluye el diccionario consultable y el modelo relacional de las fuentes: 6 PK, 12 FK, 7 UNIQUE, 11 CHECK y NOT NULL. Lee 02_DOCUMENTACION/07_MODULOS/07_MODELO_ENTIDAD_RELACION.md antes de modificarlo. El comando reproducir conserva su alcance sin escritura SQL; ejecutar --sobrescribir-fuentes realiza la recarga autorizada.
5. Mantén las carpetas numeradas de datos, documentación, procesos, agentes, configuraciones e imágenes. README.md es la excepción explícita en la raíz para la portada de GitHub; incluye biografía confirmada, contexto, catálogo y enlaces. Conserva los nombres técnicos requeridos de AGENTS.md, SKILL.md, environment.yml, requirements.txt, Dockerfile y compose.yaml dentro de sus carpetas. No crees otros archivos sueltos ni carpetas .agents o .codex en la raíz.

## 2. Código, datos y reproducción

1. Usa el entorno `espol` con Python 3.15.0. `05_CONFIGURACIONES/requirements.txt` es la única lista de versiones Python; no crear requirements alternativos ni archivos freeze paralelos.
2. Usa `05_CONFIGURACIONES/environment.yml` para crear el entorno y `Dockerfile`/`compose.yaml` para Linux. Lee `02_DOCUMENTACION/07_MODULOS/05_REPRODUCIBILIDAD.md` antes de cambiar dependencias.
3. Los nombres, tablas, hashes fuente, rutas y valores predeterminados de conexión están en `01_PROYECTO.json`. No reintroduzcas rutas personales, DATA/INEC ni nombres antiguos en código.
4. Los scripts son `01_ETL_FUENTES.py` (mapeo ENDI), `02_MAPEO_POSTGRESQL.py` (biblioteca común), `03_VERIFICAR_ENTORNO.py` (versiones y pruebas técnicas), `04_GESTION_PROYECTO.py` (integridad, inventario y reproducción), `05_MODELO_RELACIONAL.py` (PK, FK, UNIQUE, CHECK y SQL del modelo), `06_CONFIGURAR_DBEAVER.py` (preferencia visual del cliente, fuera de la recarga ETL) y `07_DICCIONARIO_VARIABLES.py` (Excel, metadatos, vínculos y comentarios de columnas). Las pruebas están en `05_PRUEBAS/`.
5. Cualquier nueva carga tabular debe pasar por `mapear_dataframe` y usar sus tipos explícitos. DATE para fechas completas; TIMESTAMP conserva hora/zona; VARCHAR con longitud observada más 10 caracteres por defecto; enteros por rango; DOUBLE para reales; NUMERIC para decimales exactos. No reinterpretar identificadores o textos con aspecto de fecha sin declaración explícita.
6. No convertir año, mes y día separados en DATE ni borrar códigos 99/9999. No perder ceros iniciales, valores especiales, categorías o registros. Conservar nulos.
7. Importar módulos no debe leer fuentes ni escribir tablas. El CLI 01 solo genera metadatos y SQL de revisión. El almacenamiento individual rechaza tablas existentes. La recarga por lote requiere autorización explícita, remapea antes de DROP/CREATE/COPY, no usa CASCADE y se confirma como una sola transacción después de validar filas, tipos y nulos, aplicar/verificar 05_MODELO_RELACIONAL.py y sincronizar 07_DICCIONARIO_VARIABLES.py.
8. Mantén funciones previas útiles, helpers y separación de configuración, procesos y documentación. Filtra en PostgreSQL cuando evite lecturas innecesarias, si la tarea usa SQL.
9. Conexión mediante PGHOST, PGPORT, PGDATABASE, PGUSER y PGPASSWORD o pgpass; nunca guardar contraseñas en el repositorio. El contenedor usa host.docker.internal para llegar al servidor del host. No cambiar credenciales ni configuración productiva sin autorización explícita.
10. Para reproducir: `python -B 03_PROCESOS_ETL/04_GESTION_PROYECTO.py reproducir`. Comprueba hashes fuente, versiones, pruebas y dos mapeos idénticos que coincidan con resultado_referencia. No actualices esa referencia automáticamente para aceptar diferencias. Regenera el inventario al final con la acción `inventariar`.
11. No entrenar modelos ni presentar indicadores oficiales sin tarea específica, definición de población, denominador y diseño muestral. Una asociación no demuestra causalidad.

## 3. Skills

Lee solo la skill pertinente:

| Trabajo | Archivo desde la raíz |
| --- | --- |
| Corrección de español técnico | `04_AGENTES_SKILLS/01_SKILLS/01_ORTOGRAFIA_TECNICA/SKILL.md` |
| Python, RDS, Excel y PostgreSQL | `04_AGENTES_SKILLS/01_SKILLS/02_PYTHON_DATOS/SKILL.md` |
| Interpretación de resultados | `04_AGENTES_SKILLS/01_SKILLS/03_ANALITICA_NARRATIVA/SKILL.md` |
| Entorno y dependencias | `04_AGENTES_SKILLS/01_SKILLS/04_ENTORNO_CONDA/SKILL.md` |

## 4. Documentación y cierre

1. Cada módulo creado o modificado se documenta en `02_DOCUMENTACION/07_MODULOS/`, actualizando su archivo sin duplicar guías ni inventarios.
2. Documenta en español técnico con pasos numerados: nombre, objetivo, archivos, flujo, entradas, salidas, fuentes y schema.tabla cuando aplique, reglas de negocio, UI y server o «no aplica», SQL/ETL, funciones con entrada/salida/efecto, dependencias, validaciones, pruebas, riesgos, rendimiento, cambios y pendientes reales.
3. `05_CONFIGURACIONES/.gitignore` excluye 01_DATOS_FUENTE, 03_PROCESOS_ETL/05_PRUEBAS, 02_DOCUMENTACION/09_VALIDACIONES y residuos técnicos. No excluir scripts de ejecución, agentes, esquemas ni documentos por su formato. Git debe configurarse con ese core.excludesFile en cada clonación. La suite es local y opcional para reproducir una copia de GitHub: su ausencia no cuenta como pruebas aprobadas; la acción pruebas sí exige tenerla.
4. Antes de renombrar un archivo actualiza manifiesto, código, documentación y pruebas. Antes de eliminarlo comprueba que es obsoleto o redundante y conserva fuentes originales salvo autorización expresa.
5. Al finalizar resume archivos/documentación, pruebas y límites. No afirmar carga, constraints, reproducción en contenedor o equivalencia entre plataformas si no se comprobaron.

## 5. Invariantes relacionales ENDI R2

1. Salud usa id_hijo_ord como PK. Conservar sus id_per terminados en 77: son no miembros y pueden repetirse. La FK a Personas usa la columna calculada STORED id_per_miembro, nula exclusivamente para esos casos; no reemplazar el identificador original.
2. id_cuid referencia Personas, no obligatoriamente MEF. La FK MEF.id_mef apunta a Personas.id_mef; no invertirla, porque Personas contiene mujeres que no figuran en el formulario de madres.
3. No convertir cruces analíticos entre poblaciones parcialmente coincidentes en FK obligatorias; documentar las excepciones. No eliminar filas ni usar CASCADE para hacer pasar restricciones. Aplicar el modelo después del mapeo y COPY, dentro de la misma transacción.

## 6. Presentación pública

1. El autor es Marcelo Chávez, CEO de ConneXData. Su perfil público es https://www.linkedin.com/in/marcelochavezec/. Usar únicamente datos biográficos confirmados y la marca ConneXData; no añadir grados académicos o experiencias no verificadas.
2. La portada usa 06_IMG/ConneXData.jpeg. No incorporar el logo de ESPOL por indicación del autor. Mantener README.md, los enlaces relativos y el catálogo por archivo al cambiar la estructura. La documentación de esta presentación está en 02_DOCUMENTACION/07_MODULOS/08_PORTADA_Y_CATALOGO.md.

## 7. Vista de DBeaver

1. Para limitar el diagrama a claves y relaciones usa erd.attr.visibility=KEYS mediante 06_CONFIGURAR_DBEAVER.py en el anfitrión. Lee 02_DOCUMENTACION/07_MODULOS/09_DBEAVER_COMPACTO.md; la preferencia es local al workspace y no cambia el esquema PostgreSQL.
2. Guardar y verificar el archivo de preferencias no demuestra que una sesión abierta ya lo haya aplicado. Indicar el reinicio y no cerrar consultas sin guardar ni ejecutar editores ajenos a la tarea. No versionar las conexiones ni credenciales privadas de DBeaver.

## 8. Diccionario y metadatos de columnas

1. El manifiesto versión 2 utiliza un solo Excel: 01_DATOS_FUENTE/07_DICCIONARIO_ENDI.xlsx con seis hojas. No reintroducir la dependencia del archivo 08 retirado. Los aliases documentados de cinco variables de Desarrollo Infantil se conservan.
2. El diccionario único es endi.diccionario_variables, PK (esquema,tabla,variable), con etiquetas TEXT. endi.diccionario_restricciones es una tabla auxiliar de vínculos con dos FK al diccionario y constraint triggers que contrastan columnas/restricciones con catálogos nativos. No crear FK que confundan nombres de columnas con valores de los microdatos. Leer 02_DOCUMENTACION/07_MODULOS/10_DICCIONARIO_VARIABLES.md.
3. La recarga sincroniza seis fuentes y dos tablas de metadatos, vista y comentarios en la misma transacción. Las tablas de metadatos no se catalogan recursivamente. Conservar validaciones de hashes, tipos y cobertura; un DDL manual posterior exige sincronizar el diccionario.

## 9. Lectura metodológica y tabulados provinciales

1. Antes de analizar ENDI R2, leer 02_DOCUMENTACION/07_MODULOS/11_REPORTE_PROVINCIAL.md y las secciones pertinentes de 01_DOCUMENTO_METODOLOGICO_ENDI_R2.PDF y 02_GUIA_BASE_DATOS_ENDI_R2.PDF. El módulo conserva la lectura de ambos documentos y decisiones verificadas; releer la fuente cuando cambien indicador, universo o ronda.
2. El SQL de consulta completo es 02_DOCUMENTACION/08_MAPEO_ENDI/07_REPORTE_PROVINCIAL.sql. Audita relaciones, datos y diccionario en solo lectura y tabula dcronica_2/dcronica por provincia. Usar fexp de Personas al cruzar con Hogar por id_hogar; conservar la granularidad y no unir las seis fuentes indiscriminadamente.
3. La base continental excluye Galápagos. No convertir ausentes en cero, ni sumas de factores normalizados en totales poblacionales. Lactancia usa fexp_lm y Desarrollo fexp_di. Informar n y denominadores válidos. El reporte SQL solo entrega estimaciones puntuales: no afirmar IC/CV, significancia o réplica oficial completa sin sus cálculos, ficha y sintaxis. Un control REVISAR debe resolverse antes de interpretar resultados.

## 10. Catálogo territorial y organización actual

1. El autor reorganizó la documentación en 01_DOCUMENTACION_MODULOS, 02_MAPEO_ENDI, 03_VALIDACIONES, 04_BIBLIOGRAFIA y 05_GUIAS_PROYECTO dentro de 02_DOCUMENTACION. Comprobar las rutas existentes antes de trabajar; no restaurar ni publicar automáticamente movimientos o archivos ajenos sin revisar su alcance.
2. Para catalogos.dpa_inec leer 02_DOCUMENTACION/01_DOCUMENTACION_MODULOS/12_CATALOGO_DPA_INEC.md. El script 03_PROCESOS_ETL/09_CATALOGO_DPA_INEC.py y la sección catalogo_dpa del manifiesto fijan Excel, hash, rutas y edición 2026. La carga es independiente de la recarga ENDI y requiere --cargar.
3. Conservar tres columnas: pk_dpa VARCHAR(6), tipo_dpa VARCHAR dimensionado y descripcion_dpa TEXT. Los códigos completos tienen 2/4/6 dígitos y ceros iniciales. Usar hojas detalladas y añadir parroquias urbanas; las exclusiones de zonas en estudio son explícitas. No confundir 1.316 códigos parroquiales/cabeceras con gobiernos parroquiales rurales. No mezclar otra edición bajo la misma PK ni sustituir el clasificador histórico ENDI sin una tarea de migración.
