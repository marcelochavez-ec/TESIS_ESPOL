# ENTORNO espol

1. **Objetivo.** Mantener una pila Python reproducible para datos, RDS/RData, Excel y PostgreSQL sin alterar otros entornos del host.
2. **Archivos.** `05_CONFIGURACIONES/environment.yml` fija el bootstrap Conda; `requirements.txt` es la única lista de versiones Python. `03_PROCESOS_ETL/03_VERIFICAR_ENTORNO.py` produce `02_DOCUMENTACION/09_VALIDACIONES/01_ENTORNO_ESPOL.json`.
3. **Estado.** El entorno es espol, en minúsculas; Python 3.15.0. Se conservaron base y msp_01. El contenedor usa también un entorno espol.
4. **Flujo.** Conda obtiene Python, pip y pyreadr; la sección pip del YAML lee el requirements de su misma carpeta. Se comprueban todas las versiones fijadas, once importaciones, operaciones sintéticas y pip check.
5. **Entradas.** Windows o Linux amd64, acceso a conda-forge/PyPI y los manifiestos. Las pruebas ordinarias no necesitan fuentes ENDI ni PostgreSQL en ejecución.
6. **Salidas.** Entorno y reporte JSON con versiones esperadas/instaladas, importaciones y resultados. No se exportan ejecutables dentro del repositorio ni se generan requirements paralelos.
7. **Fuentes.** conda-forge y PyPI. pyreadr se instala con Conda porque no había wheel pip para Windows/CPython 3.15 en la verificación inicial. No se hace compilación improvisada ni se rebaja Python.
8. **Reglas.** El YAML referencia la única lista de paquetes. Si cambia una versión, se actualiza esa lista y se repiten pruebas y comparación local/contenedor. La definición fija versiones Python, no convierte binarios Windows en Linux.
9. **UI.** No aplica. CLI con --salida opcional y --postgres opcional.
10. **Funciones.** verificar() devuelve versiones y pruebas sin acceder a la base; main() escribe un reporte si se solicita y devuelve código distinto de cero si falla. --postgres usa la configuración central y PG* en una transacción de lectura.
11. **SQL.** La prueba ordinaria construye un motor postgresql+psycopg sin conectarse. --postgres ejecuta SET TRANSACTION READ ONLY y SELECT current_database(), sin DDL ni carga.
12. **Paquetes.** pandas 3.0.6, NumPy 2.5.4, SciPy 1.18.1, scikit-learn 1.9.1, pyreadr 0.5.7, xlrd 2.0.2, openpyxl 3.1.5, XlsxWriter 3.2.9, SQLAlchemy 2.1.5, Psycopg 3.3.6 y PyYAML 6.0.3; el mismo requirements incluye dependencias transitivas fijadas y pip 26.2.1.
13. **Validaciones.** Comparación exacta de todas las distribuciones listadas con su metadata instalada y de Python con el manifiesto. Un paquete ausente o una versión distinta hacen fallar el control.
14. **Pruebas.** RDS sintético de dos filas; XLSX escrito con XlsxWriter y leído con openpyxl; conservación de códigos 01/09; dialecto Psycopg 3; pip check. El resultado real se consulta en los reportes 01 y 03 de 09_VALIDACIONES.
15. **Riesgos y rendimiento.** Los ensayos sintéticos no prueban todos los formatos RData ni el rendimiento de microdatos completos. Los repositorios de paquetes deben conservar los artefactos fijados para una recreación futura.
16. **Cambios.** Se fijaron versiones exactas, consolidó requirements y actualizó el verificador. Se retiraron las instantáneas duplicadas y la lista de paquetes exclusiva de Windows.
17. **Reproducción.** La creación se realiza con conda env create -f 05_CONFIGURACIONES/environment.yml. La reproducción completa utiliza 04_GESTION_PROYECTO.py reproducir y la receta de contenedor está en 05_REPRODUCIBILIDAD.md. No se recrea encima de un entorno homónimo sin inspeccionarlo.
