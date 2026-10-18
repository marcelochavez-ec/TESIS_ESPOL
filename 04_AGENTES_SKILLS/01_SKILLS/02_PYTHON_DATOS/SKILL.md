---
name: python-datos
description: Crear o modificar Python del proyecto ESPOL para mapeo previo de variables, ETL, RDS/RData, Excel y PostgreSQL con SQLAlchemy y Psycopg 3.
---

# Python para datos

1. Lee `04_AGENTES_SKILLS/AGENTS.md`, el módulo afectado y `05_CONFIGURACIONES/01_PROYECTO.json` desde la raíz TESIS_ESPOL. Usa el entorno espol y su único requirements.txt.
2. El flujo permite mapeo y recarga explícita de fuentes en research_lab.endi; la recarga incluye el modelo de 05_MODELO_RELACIONAL.py. Antes de modificar claves lee 02_DOCUMENTACION/07_MODULOS/07_MODELO_ENTIDAD_RELACION.md. El CLI `03_PROCESOS_ETL/01_ETL_FUENTES.py` produce solo metadatos. No añadas cargas ni PK/FK/UNIQUE/CHECK a una solicitud de mapeo.
3. Reutiliza `02_MAPEO_POSTGRESQL.py`: leer_fuente recupera todos los objetos/hojas; mapear_dataframe recorre cada variable, devuelve copia, tipos y catálogo. Los módulos numerados se cargan con importlib, sin duplicar la lógica de tipos.
4. Una futura escritura debe usar almacenamiento_postgresql o almacenar_dataframe, que mapean antes de CREATE/COPY y rechazan tablas existentes. Para el reemplazo autorizado por lote usa recargar_fuentes_postgresql/recargar_tablas en una única transacción. Solo afectan las seis tablas del manifiesto, no eliminan el esquema ni usan CASCADE. No ejecutes cargas para probar imports.
5. DATE solo para fechas completas; conservar hora/zona en TIMESTAMP. Textos: longitud observada más margen (10 por defecto). Enteros por rango; reales DOUBLE; Decimal NUMERIC. No truncar, inferir fechas en códigos ni transformar componentes año/mes/día con sentinelas.
6. Si un object totalmente nulo, una mezcla o un formato no permiten inferencia fiel, pedir o documentar una declaración explícita. Conservar ceros iniciales, nulos y códigos especiales; no deduplicar registros por conveniencia.
7. Usa Path desde __file__ y manifiesto, nunca rutas del equipo. Preserva nombres originales de variables; aliases de etiquetas solo en la configuración y con trazabilidad al diccionario.
8. Conexión por URL.create y PG* o pgpass. Dialecto postgresql+psycopg, versión mayor 3. No registrar secretos ni incorporar contraseñas a ejemplos o configuración.
9. Conserva importaciones sin efectos externos y un guard de entrada en cada script ejecutable. La suite numerada se carga explícitamente: discovery puede omitir archivos que comienzan con dígitos. Nunca aceptar cero pruebas como validación.
10. Ejecuta `04_GESTION_PROYECTO.py reproducir` cuando cambies el mapeo o sus dependencias; compara los artefactos en dos ejecuciones y entre plataformas. Documenta funciones, entradas, salidas y límites en `02_DOCUMENTACION/07_MODULOS/` y regenera el inventario al terminar.

11. En ENDI R2, Salud usa id_hijo_ord como PK; id_per puede repetirse para no miembros terminados en 77. La FK a Personas usa id_per_miembro calculada STORED, sin cambiar id_per original. Cuidadores referencian Personas, no necesariamente MEF; MEF referencia la clave secundaria id_mef de Personas, sin exigir que todas las mujeres tengan formulario MEF. No imponer FK entre subconjuntos con cobertura parcial. Aplicar y verificar el modelo tras COPY en la transacción de recarga.
