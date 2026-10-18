---
name: entorno-conda
description: Crear, comprobar o actualizar el entorno espol y su reproducción en contenedor usando environment.yml y el único requirements.txt fijado del proyecto ESPOL.
---

# Entorno espol reproducible

1. Lee `05_CONFIGURACIONES/01_PROYECTO.json`, `environment.yml`, `requirements.txt` y `02_DOCUMENTACION/07_MODULOS/05_REPRODUCIBILIDAD.md` desde la raíz.
2. El entorno exacto es `espol` y el intérprete fijado es Python 3.15.0. No instales en base ni msp_01 y no reemplaces entornos existentes sin inspeccionarlos.
3. `requirements.txt` es la única lista de paquetes Python con versiones exactas. No crees freeze ni requirements-versiones alternativos. El YAML fija el intérprete y bootstrap Conda (pip y pyreadr), y referencia ese mismo requirements para el resto.
4. Crea con `conda env create -f 05_CONFIGURACIONES/environment.yml`. pyreadr se obtiene de Conda porque no había wheel pip para Windows/CPython 3.15 en la comprobación del proyecto.
5. Usa `03_PROCESOS_ETL/03_VERIFICAR_ENTORNO.py` para versiones, RDS, Excel y Psycopg 3; su opción --postgres solo comprueba conexión de lectura y nunca recibe una contraseña como argumento de consola.
6. Usa `04_GESTION_PROYECTO.py reproducir` para comparar dos mapeos y pruebas; consulta el informe de reproducción local y Linux antes de declarar equivalencia.
7. La imagen base Docker está fijada por digest. No cambies el digest, versiones o plataforma sin comprobar el build y la reproducción, y documenta la nueva evidencia. Mantén fuentes fuera de la imagen y montadas en solo lectura.
8. Un contenedor usa PGHOST_CONTENEDOR/PGHOST para PostgreSQL externo; localhost dentro del contenedor no identifica el host. No modifiques la configuración del servidor ni guardes secretos para hacer pasar una prueba.
9. Después de cambios documenta versiones, pruebas, diferencias reales entre plataformas y regenera el único inventario. No prometas una reconstrucción binaria idéntica solo por usar versiones: para conservar exactamente la imagen construida debe conservarse su imagen inmutable.
