# RESPALDO, SINCRONIZACIÓN Y EJECUCIÓN EN OTRO EQUIPO

## 1. Contenido del repositorio

El autor conserva el proyecto en [marcelochavez-ec/TESIS_ESPOL](https://github.com/marcelochavez-ec/TESIS_ESPOL), rama main, respetando su historial. La licencia original se conserva en 05_CONFIGURACIONES/LICENSE. Los scripts, agentes, skills, configuración, esquemas SQL, catálogo de variables y documentos metodológicos se incluyen en el respaldo. Las fuentes, pruebas, evidencias de ejecución, cachés y temporales permanecen locales.

Los comandos se ejecutan **uno por uno** en PowerShell. El archivo de exclusiones se guarda en 05_CONFIGURACIONES/.gitignore y se registra mediante core.excludesFile en cada clonación; Git no comparte esa configuración local automáticamente. No se introducen contraseñas en archivos ni en la URL.

## 2. Recuperación en otro Windows

1. El autor instala Git, Docker Desktop con contenedores Linux y acceso a un servidor PostgreSQL. El servidor debe disponer de la base research_lab y el esquema endi. Si faltan, el administrador los crea antes de la carga; el ETL no instala un servidor ni crea otra base por error. La cuenta necesita permisos para sustituir las seis tablas fuente.

2. Se clona el repositorio desde la carpeta que contendrá el proyecto.

```powershell
git clone https://github.com/marcelochavez-ec/TESIS_ESPOL.git
```

3. Se entra en la copia recuperada.

```powershell
Set-Location .\TESIS_ESPOL
```

4. Se activa el archivo de exclusiones antes de copiar fuentes o preparar cambios.

```powershell
git config --local core.excludesFile (Join-Path (Get-Location).Path '05_CONFIGURACIONES\.gitignore')
```

5. El autor recupera por separado la carpeta 01_DATOS_FUENTE con los seis RDS y el Excel 07 consolidado del manifiesto versión 2 05_CONFIGURACIONES/01_PROYECTO.json. Conserva nombres y bytes originales. Estas entradas no están en GitHub. Los tres PDF metodológicos sí se recuperan del repositorio. La carpeta 02_DOCUMENTACION debe permitir escritura para los resultados.

6. Se verifica que Git excluya las fuentes.

```powershell
git check-ignore --no-index -v -- 01_DATOS_FUENTE/01_BDD_ENDI_R2_F1_HOGAR.rds
```

7. Se verifica que las pruebas locales también estén excluidas.

```powershell
git check-ignore --no-index -v -- 03_PROCESOS_ETL/05_PRUEBAS/01_PRUEBAS_MAPEO.py
```

8. Se verifica la exclusión de los reportes regenerados.

```powershell
git check-ignore --no-index -v -- 02_DOCUMENTACION/09_VALIDACIONES/12_RECARGA_POSTGRESQL.json
```

9. Si PostgreSQL se ejecuta en el mismo Windows, el contenedor utiliza host.docker.internal. Si se utiliza otro servidor, el autor indica su dirección; sustituye el ejemplo por el nombre o IP reales y omite este paso cuando usa el servidor local.

```powershell
$env:PGHOST_CONTENEDOR = 'SERVIDOR_POSTGRESQL'
```

10. El autor inicia Docker Desktop en modo Linux y ejecuta la carga completa desde la raíz. Se construye el entorno espol con las versiones fijadas, se validan las fuentes y el mapeo y se sustituyen las seis fuentes de research_lab.endi y se sincronizan el diccionario, sus vínculos y comentarios. La consola solicita la clave de PostgreSQL si no fue proporcionada mediante un mecanismo externo. Los detalles y efectos se describen en 07_MODULOS/06_RECARGA_POSTGRESQL.md.

```powershell
docker compose -f 05_CONFIGURACIONES/compose.yaml run --build --rm recarga
```

11. Para comprobar el mapeo sin sustituir tablas se utiliza este comando alternativo.

```powershell
docker compose -f 05_CONFIGURACIONES/compose.yaml run --build --rm mapeo
```

El autor utiliza la alternativa de Conda descrita en 07_MODULOS/05_REPRODUCIBILIDAD.md si ejecuta sin Docker. El contenedor evita depender de los paquetes instalados en el Windows anfitrión. Los mismos datos, versiones y reglas deben coincidir con la referencia aprobada; la ausencia de una fuente o una diferencia produce error. La suite de pruebas no se distribuye y su ausencia no se presenta como pruebas aprobadas.

## 3. Sincronización de cambios

1. El autor se sitúa en la copia de TESIS_ESPOL y consulta el estado.

```powershell
git status --short --branch
```

2. Con el árbol de trabajo limpio descarga cambios remotos. Si hay modificaciones propias, las revisa y guarda primero mediante los pasos siguientes antes de integrar cambios ajenos.

```powershell
git pull --ff-only origin main
```

3. Se comprueba la ubicación efectiva de las exclusiones.

```powershell
git config --local --get core.excludesFile
```

4. Se revisan los archivos preparados para respaldo; se comprueba que las fuentes, pruebas y evidencias no estén rastreadas. El resultado de este comando debe estar vacío.

```powershell
git ls-files -- 01_DATOS_FUENTE/ 03_PROCESOS_ETL/05_PRUEBAS/ 02_DOCUMENTACION/09_VALIDACIONES/
```

5. Se actualiza el inventario con el entorno espol si se modificaron archivos locales. Si se utiliza Docker, la recarga completa ya lo actualiza al terminar; una copia sin los datos originales no puede ejecutar el ETL completo.

```powershell
conda run -n espol python -B 03_PROCESOS_ETL/04_GESTION_PROYECTO.py inventariar
```

6. Se preparan los archivos respetando las exclusiones. No se utiliza git add --force.

```powershell
git add --all
```

7. Se revisa el resumen.

```powershell
git diff --cached --stat
```

8. Se inspecciona el contenido, incluidos scripts y configuración, antes de crear el commit.

```powershell
git diff --cached
```

9. Se guarda un commit con un mensaje que describa el cambio real.

```powershell
git commit -m 'Actualiza procesos y documentación de la tesis'
```

10. Se incorporan cambios remotos conservando el trabajo. Si aparecen conflictos, se resuelven y revisan antes de publicar.

```powershell
git pull --rebase origin main
```

11. Se publica sin forzar el historial. Git solicita autenticación mediante el mecanismo configurado cuando corresponde.

```powershell
git push origin main
```

12. Se verifica la sincronización.

```powershell
git status --short --branch
```

## 4. Alcance y conservación

1. La exclusión no elimina archivos que ya estuvieran rastreados ni los retira del historial. Antes de publicar se comprueba la lista rastreada; los datos de 01 requieren su propio respaldo independiente.
2. No se bloquean formatos completos: PDF, DOCX, XLSX, SQL y Markdown permanecen publicables fuera de las carpetas excluidas. Los archivos temporales de Office sí se omiten.
3. Git crea su carpeta técnica .git al clonar; no se publica y no se mueve manualmente.
4. En Linux se configuran ESPOL_UID y ESPOL_GID según el propietario de la carpeta de documentación; los pasos están en el módulo 05_REPRODUCIBILIDAD. La imagen requiere Linux/amd64 o emulación compatible.
5. Se necesita acceso a los repositorios de dependencias durante la construcción. Para conservar exactamente el binario ensayado se puede guardar y restaurar la imagen Docker, como explica el módulo de reproducción.
6. Los reportes locales 09_VALIDACIONES registran las comprobaciones y no se publican. El resultado de la carga se consulta en 12_RECARGA_POSTGRESQL.json; una diferencia o fallo SQL anterior al commit revierte la tanda completa.
