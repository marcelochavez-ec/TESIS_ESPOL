# REPRODUCIBILIDAD LOCAL Y EN CONTENEDOR

1. **Objetivo.** Repetir el mapeo con las mismas fuentes, versiones y reglas, y comprobar igualdad de los artefactos entre Windows y Linux amd64. La acción reproducir conserva este alcance. La acción ejecutar y el servicio recarga añaden la sustitución transaccional autorizada de las seis tablas y la creación/verificación del modelo relacional dentro de esa transacción.
2. **Archivos.** 01_PROYECTO.json es el manifiesto; environment.yml fija Python 3.15.0, pip y pyreadr; requirements.txt fija la lista completa de distribuciones Python. Dockerfile y compose.yaml están en 05_CONFIGURACIONES. No existen requirements alternativos ni rutas personales en el código de ejecución.
3. **Flujo.** 04_GESTION_PROYECTO.py reproducir comprueba once hashes originales, versiones exactas, pruebas y pip check; produce dos mapeos temporales; compara SHA-256 de sus tres artefactos entre sí y con resultado_referencia del manifiesto; solo después copia los resultados definitivos. Una salida diferente no se aprueba por ser repetible y no sobrescribe los artefactos anteriores. Registra la plataforma en un único informe y compara sus hashes con los de otras plataformas ya verificadas.
4. **Entradas.** Ocho archivos de datos/diccionarios disponibles localmente, tres PDF para control documental, versiones declaradas y configuración del proyecto. Las fuentes no están en GitHub: después de clonar se recuperan por separado con los nombres del manifiesto y sus mismos hashes.
5. **Salidas.** 09_VALIDACIONES/01_ENTORNO_ESPOL.json, 02_PRUEBAS_MAPEO.json y 03_REPRODUCIBILIDAD.json; catálogo, resumen y SQL de revisión en 08_MAPEO_ENDI. El informe 03 conserva una entrada por plataforma y su comparación; no agrega copias de los catálogos por cada ejecución.
6. **Fuentes y base.** Se leen los archivos declarados, no tablas SQL. PostgreSQL es un servicio externo existente; la reproducción no lo instala, reinicia ni cambia su configuración.
7. **Reglas deterministas.** Orden explícito de fuentes, recorrido completo de columnas, margen configurado, aliases explícitos de etiquetas, saltos de línea LF y rutas relativas. No se incorporan horas de ejecución, rutas absolutas ni números aleatorios a los artefactos de mapeo. La suite local se carga expresamente porque sus archivos están numerados; si existe con cero casos produce fallo. No se publica en GitHub: cuando falta, reproducir informa pruebas=null y conserva las demás comprobaciones obligatorias.
8. **UI.** Consola. Se usa una terminal con Conda para la ejecución local o Docker Desktop/Engine en modo Linux para el contenedor.
9. **Funciones.** sha256() lee por bloques; verificar_fuentes() rechaza ausencias o cambios; ejecutar_pruebas() exige casos y devuelve conteos; reproducir() comprueba dos salidas idénticas y la comparación entre plataformas; inventariar() regenera el catálogo global al final de los cambios.
10. **SQL y conexiones.** PGHOST, PGPORT, PGDATABASE y PGUSER sustituyen los valores no sensibles del manifiesto. PGPASSWORD o pgpass proporcionan la clave sin guardarla. En Compose, PGHOST_CONTENEDOR es host.docker.internal por defecto; localhost dentro de un contenedor no es el servidor del host. --postgres del verificador abre una transacción de solo lectura y ejecuta SELECT; no se requieren credenciales para el mapeo ordinario.
11. **Dependencias e imagen.** Docker Compose fija linux/amd64; la imagen base mambaorg/micromamba 2.3.3 se fija mediante digest SHA-256. El entorno se llama espol. Dockerfile conserva el entrypoint de micromamba y ENV_NAME=espol. Durante la construcción se comprueban entorno y pip check; si está disponible la suite local, también se ejecuta. La suite actual tiene 37 casos y no se distribuye por GitHub.
12. **Datos y permisos.** Dockerfile.dockerignore evita enviar fuentes, documentación y metadata Git al build. La imagen solo contiene scripts, agente/skills y configuración de ejecución. Compose monta 01_DATOS_FUENTE en solo lectura y 02_DOCUMENTACION para conservar resultados. No hay volúmenes de datos SQL ni puertos de una base nueva. Compose ejecuta con ESPOL_UID/ESPOL_GID (1000/1000 por defecto). En Linux se proporcionan los identificadores del propietario de la carpeta de documentación para escribir sin modificar permisos del host. Las fuentes permanecen de solo lectura.
13. **Validaciones ejecutadas.** Se construyó la imagen en Docker y se ejecutó la suite durante el build. Se probaron las versiones y conexiones de lectura tanto desde Windows como desde Linux. La repetición completa y comparación de hashes queda registrada en el informe 03; se repitió además desde otra ubicación con espacios, sin resultados previos, comprobando los hashes aprobados y las 34 pruebas existentes en aquel ensayo. Después de excluir la suite de la distribución se construyó una copia filtrada equivalente al respaldo de GitHub y se comprobaron los archivos publicables de ejecución de implementación, agente/skills y configuración incluidos en la imagen: coinciden por SHA-256 con el proyecto tras normalizar CRLF a LF en esos archivos de texto, el proceso usa UID 1000 y el montaje de fuentes es de solo lectura. La identidad de la imagen se guarda en 09_IMAGEN_CONTENEDOR.json y los detalles en 11_PORTABILIDAD_RUTA.json. Los logs 04–06 permiten revisar la ejecución real.
14. **Límites de la garantía.** Las mismas entradas, reglas y versiones se comprueban mediante hashes de resultados. Windows y Linux tienen binarios diferentes. Una versión de Conda/PyPI fijada no garantiza por sí sola un build binario idéntico para siempre: para conservar exactamente el artefacto probado se guarda la imagen construida, identificada por su ID inmutable, fuera del repositorio. La prueba de ubicación nueva utiliza el entorno local ya instalado; no equivale a crear Conda desde cero en un tercer equipo. La construcción y ejecución aislada Linux se ensayó en Docker.
15. **Rendimiento.** La validación completa mapea dos veces todas las columnas y utiliza temporales que se eliminan al finalizar; no duplica las fuentes. Los enteros ya inferidos se normalizan de forma vectorizada. Docker reutiliza la capa de dependencias cuando solo cambia el código.
16. **Cambios.** Se fijaron versiones y digest, consolidó requirements, parametrizó PostgreSQL, creó contenedor y gestor de reproducción y se estandarizaron rutas/nombres. Se retiraron documentos y diagnósticos obsoletos. Posteriormente se añadió y ejecutó la recarga explícita de las seis tablas de research_lab.endi; su módulo y pruebas SQL se documentan en 06_RECARGA_POSTGRESQL.md.
17. **Operación posterior.** Después de cambios se ejecuta reproducir, se reconstruye/prueba la imagen si corresponde y se regenera el inventario como último paso. Si cambian fuentes, sus hashes no se actualizan por comodidad: se documenta una nueva entrega y se revisa su significado.

## Ejecución local

El autor abre una terminal con Conda disponible, se sitúa en TESIS_ESPOL y crea el entorno solo si aún no existe.

```powershell
conda env create -f 05_CONFIGURACIONES/environment.yml
```

Se ejecuta la reproducción completa sin escribir en PostgreSQL.

```powershell
conda run -n espol python -B 03_PROCESOS_ETL/04_GESTION_PROYECTO.py reproducir
```

Se actualiza el único inventario tras finalizar los cambios.

```powershell
conda run -n espol python -B 03_PROCESOS_ETL/04_GESTION_PROYECTO.py inventariar
```

## Ejecución en Docker

El autor inicia Docker en modo Linux y construye la imagen desde la raíz del proyecto.

```powershell
docker compose -f 05_CONFIGURACIONES/compose.yaml build
```

Se ejecuta el mismo flujo; las fuentes deben estar recuperadas en 01_DATOS_FUENTE.

```powershell
docker compose -f 05_CONFIGURACIONES/compose.yaml run --rm mapeo
```

Si se desea comprobar el servidor externo, primero se dispone PGPASSWORD de forma transitoria o un mecanismo pgpass; no se escribe la clave en un comando guardado ni en un archivo versionado. Se comprueba desde el contenedor únicamente con lectura.

```powershell
docker compose -f 05_CONFIGURACIONES/compose.yaml run --rm mapeo python -B 03_PROCESOS_ETL/03_VERIFICAR_ENTORNO.py --postgres
```

Opcionalmente, el autor conserva la imagen exacta en una ubicación externa al repositorio, sin añadir un TAR a GitHub.

```powershell
docker image save --output ../TESIS_ESPOL_IMAGEN.tar tesis-espol:py315
```

En otro host con arquitectura compatible puede restaurarla sin reconstruir dependencias.

```powershell
docker image load --input ../TESIS_ESPOL_IMAGEN.tar
```

La fijación por digest sigue las [recomendaciones oficiales de Docker](https://docs.docker.com/build/building/best-practices/). La activación del entorno conserva el [entrypoint documentado de micromamba](https://micromamba-docker.readthedocs.io/en/latest/quick_start.html).

## Alcance comprobable al trasladar el proyecto

1. Se conserva el mismo código y manifiesto, los ocho archivos de datos/diccionarios y los tres PDF originales. Los originales son entradas externas: el programa no puede regenerar una encuesta ni el manual a partir del código. Su copia se valida mediante SHA-256.
2. Los tres productos de mapeo deben coincidir exactamente con la referencia aprobada guardada en 01_PROYECTO.json, incluso en una carpeta nueva sin resultados previos. Si falta una entrada, cambia una versión o difiere un hash, la ejecución falla y no publica un catálogo nuevo.
3. Los reportes de entorno, inventario y logs describen la ejecución y el equipo; no son los tres productos de cálculo sujetos a igualdad binaria. Los agentes y documentos son archivos de código/configuración conservados por Git, no resultados que una ejecución estadística deba redactar de nuevo.
4. La escritura de las seis tablas de research_lab.endi fue confirmada por el usuario y ensayada. El servicio recarga verifica primero el mapeo y después valida filas, tipos y nulos dentro de una sola transacción. La repetición real se documenta mediante huellas de contenido en 15_REPETICION_RECARGA.json. El modelo relacional se crea y verifica en la misma transacción; su SQL y diagrama se documentan en 07_MODELO_ENTIDAD_RELACION.md.
5. La portabilidad de rutas se ensaya en una copia temporal con espacios, desde un directorio de trabajo exterior y sin productos anteriores. La evidencia queda en 09_VALIDACIONES/11_PORTABILIDAD_RUTA.json. Este ensayo no equivale a disponer de todos los sistemas operativos y arquitecturas posibles.
6. Para repetir los binarios exactos sin depender de la futura disponibilidad de paquetes se conserva/restaura la imagen Docker ya construida. Para reconstruir se necesita acceso a los repositorios de las versiones fijadas. En ambos casos se requieren Docker Linux/amd64 o emulación compatible, espacio suficiente, entradas originales y acceso a PostgreSQL cuando se utiliza recarga o la verificación SQL opcional.

En un servidor Linux, el autor proporciona su UID al servicio. Este comando se ejecuta en Bash.

```bash
export ESPOL_UID="$(id -u)"
```

Se proporciona también el GID del propietario de los archivos.

```bash
export ESPOL_GID="$(id -g)"
```

Después se ejecuta la reproducción desde la raíz.

```bash
docker compose -f 05_CONFIGURACIONES/compose.yaml run --rm mapeo
```

Las referencias aprobadas no se recalculan automáticamente para hacer pasar una diferencia. Un cambio intencionado de fuentes, reglas o resultados requiere revisar y documentar una nueva referencia.

## Ejecución completa con sustitución de fuentes

El autor se sitúa en la raíz y utiliza el servicio recarga. El mismo comando construye o actualiza la imagen, comprueba el mapeo y sustituye las seis tablas. La consola solicita la clave si no se proporcionó temporalmente mediante PGPASSWORD. Los requisitos y efectos se detallan en 06_RECARGA_POSTGRESQL.md.

```powershell
docker compose -f 05_CONFIGURACIONES/compose.yaml run --build --rm recarga
```

## Exclusión de evidencias y suite local

Las carpetas 09_VALIDACIONES y 05_PRUEBAS se conservan localmente y se excluyen de GitHub. Una copia publicada regenera sus reportes al ejecutarse. La ausencia de la suite no se contabiliza como un resultado correcto: se registra explícitamente y permanecen obligatorios los hashes fuente, versiones, dos mapeos y referencia aprobada. La acción pruebas requiere la suite local.
