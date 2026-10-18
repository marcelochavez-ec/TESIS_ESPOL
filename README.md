<p align="center">
  <img src="06_IMG/ConneXData.jpeg" alt="ConneXData — Marcelo Chávez, CEO" width="760">
</p>

# TESIS_ESPOL · Base analítica ENDI R2

## Autor

**Marcelo Chávez · CEO de ConneXData**

Marcelo Chávez es CEO de **ConneXData** y autor de este proyecto de tesis. Su trabajo en este repositorio reúne documentación metodológica, preparación de datos y modelado relacional para apoyar la investigación social y en salud. El proyecto organiza los microdatos de la Encuesta Nacional sobre Desnutrición Infantil y convierte su preparación en un proceso documentado, trazable y reproducible.

**ConneXData:** «Conectamos datos, personas y decisiones».

| Perfil | Enlace |
| --- | --- |
| LinkedIn | [Marcelo Chávez](https://www.linkedin.com/in/marcelochavezec/) |
| GitHub | [marcelochavez-ec](https://github.com/marcelochavez-ec) |
| Repositorio | [TESIS_ESPOL](https://github.com/marcelochavez-ec/TESIS_ESPOL) |

## 1. Contexto y propósito de la tesis

**TESIS_ESPOL** contiene la base técnica y documental para trabajar con información de investigación social, salud y nutrición infantil en el contexto de la tesis del autor vinculada a ESPOL. La implementación actual utiliza los seis conjuntos de microdatos de **ENDI R2, 2023–2024**, sus diccionarios y su documentación metodológica.

La finalidad de esta etapa es disponer de fuentes identificadas, variables correctamente tipadas y tablas relacionadas, antes de desarrollar análisis o indicadores de la tesis. El repositorio documenta cómo se pasa de los archivos originales a una base PostgreSQL y cómo se repite ese proceso en Windows o en un contenedor compatible.

El trabajo comprende:

1. Conservación de fuentes originales e identificación por SHA-256.
2. Lectura de RDS y diccionarios, con mapeo completo de cada variable.
3. Carga transaccional en `research_lab.endi`, con tipos PostgreSQL explícitos.
4. Creación y validación de claves primarias, foráneas y restricciones.
5. Entorno Conda `espol`, dependencias fijadas y ejecución con Docker.
6. Gestión documental, inventario, agentes y skills para mantener el proyecto.

La preparación de datos implementada no equivale a resultados estadísticos de la tesis. La interpretación de indicadores debe respetar población, denominadores, diseño muestral y factores de expansión de cada formulario.

**Lecturas principales:** [documento metodológico](02_DOCUMENTACION/01_DOCUMENTO_METODOLOGICO_ENDI_R2.PDF), [guía de la base de datos](02_DOCUMENTACION/02_GUIA_BASE_DATOS_ENDI_R2.PDF) y [nota técnica de anemia](02_DOCUMENTACION/03_NOTA_TECNICA_ANEMIA.PDF).

## 2. Cómo recorrer el proyecto

| Necesidad | Documento o archivo |
| --- | --- |
| Entender la organización general | [Guía del proyecto](02_DOCUMENTACION/04_GUIA_PROYECTO.md) |
| Clonar, ejecutar y sincronizar | [Receta de respaldo y ejecución](02_DOCUMENTACION/05_RESPALDO_GITHUB.md) |
| Consultar cada archivo y su integridad | [Inventario global](02_DOCUMENTACION/06_INVENTARIO_PROYECTO.csv) |
| Entender el mapeo de variables | [Módulo de mapeo](02_DOCUMENTACION/07_MODULOS/03_MAPEO_VARIABLES.md) |
| Preparar Conda y Docker | [Reproducibilidad](02_DOCUMENTACION/07_MODULOS/05_REPRODUCIBILIDAD.md) |
| Ejecutar la recarga de las seis tablas | [Módulo de recarga](02_DOCUMENTACION/07_MODULOS/06_RECARGA_POSTGRESQL.md) |
| Revisar claves, relaciones y diagrama | [Modelo entidad-relación](02_DOCUMENTACION/07_MODULOS/07_MODELO_ENTIDAD_RELACION.md) |
| Ver el diagrama compacto en DBeaver | [Configuración de DBeaver](02_DOCUMENTACION/07_MODULOS/09_DBEAVER_COMPACTO.md) |
| Consultar etiquetas y claves de cada variable | [Diccionario en PostgreSQL](02_DOCUMENTACION/07_MODULOS/10_DICCIONARIO_VARIABLES.md) |
| Trabajar con el agente del proyecto | [AGENTS.md](04_AGENTES_SKILLS/AGENTS.md) |

```text
TESIS_ESPOL/
├── README.md
├── 01_DATOS_FUENTE/                 # Entradas originales; solo locales
├── 02_DOCUMENTACION/
│   ├── 01–03 · PDF metodológicos
│   ├── 04–06 · Guías e inventario
│   ├── 07_MODULOS/                 # Documentación funcional y técnica
│   ├── 08_MAPEO_ENDI/              # Catálogo de variables y SQL
│   └── 09_VALIDACIONES/            # Evidencias de ejecución; solo locales
├── 03_PROCESOS_ETL/
│   ├── 01–07 · Scripts Python
│   └── 05_PRUEBAS/                 # Suite de desarrollo; solo local
├── 04_AGENTES_SKILLS/
│   ├── AGENTS.md
│   └── 01_SKILLS/
├── 05_CONFIGURACIONES/
└── 06_IMG/                         # Identidad visual: ConneXData
```

`README.md` es la portada reconocida por GitHub y se conserva en la raíz. Los demás archivos del proyecto están encarpetados. La carpeta técnica `.git` pertenece a Git y no se publica.

## 3. Guía de carpetas y archivos

### 3.1. `01_DATOS_FUENTE` · Entradas originales

**Carpeta local, excluida de GitHub.** Se recupera desde un respaldo independiente antes de ejecutar el ETL. Los nombres originales y hashes esperados están en el [manifiesto](05_CONFIGURACIONES/01_PROYECTO.json).

| Archivo | Contenido y función |
| --- | --- |
| `01_BDD_ENDI_R2_F1_HOGAR.rds` | Información de hogares; origen de `endi.f1_hogar`. |
| `02_BDD_ENDI_R2_F1_PERSONAS.rds` | Miembros de hogar; origen de `endi.f1_personas`. |
| `03_BDD_ENDI_R2_F2_MEF.rds` | Madres en edad fértil del formulario MEF; origen de `endi.f2_mef`. |
| `04_BDD_ENDI_R2_F2_LACTANCIA.rds` | Lactancia materna; origen de `endi.f2_lactancia`. |
| `05_BDD_ENDI_R2_F2_SALUD_NINEZ.rds` | Salud de menores de cinco años; origen de `endi.f2_salud_ninez`. |
| `06_BDD_ENDI_R2_F3_DESARROLLO_INFANTIL.rds` | Desarrollo infantil; origen de `endi.f3_desarrollo_inf`. |
| `07_DICCIONARIO_ENDI.xlsx` | Diccionario consolidado de los formularios 1, 2 y 3: seis hojas y 1.423 variables; entrega aprobada del manifiesto versión 2. |

### 3.2. `02_DOCUMENTACION` · Fuentes metodológicas y guías

| Archivo | Contenido y función |
| --- | --- |
| [01_DOCUMENTO_METODOLOGICO_ENDI_R2.PDF](02_DOCUMENTACION/01_DOCUMENTO_METODOLOGICO_ENDI_R2.PDF) | Documento metodológico de ENDI R2. |
| [02_GUIA_BASE_DATOS_ENDI_R2.PDF](02_DOCUMENTACION/02_GUIA_BASE_DATOS_ENDI_R2.PDF) | Granularidades, identificadores, relaciones y pautas de uso de las tablas. |
| [03_NOTA_TECNICA_ANEMIA.PDF](02_DOCUMENTACION/03_NOTA_TECNICA_ANEMIA.PDF) | Referencia técnica específica para anemia. |
| [04_GUIA_PROYECTO.md](02_DOCUMENTACION/04_GUIA_PROYECTO.md) | Organización, configuración y puntos de entrada del proyecto. |
| [05_RESPALDO_GITHUB.md](02_DOCUMENTACION/05_RESPALDO_GITHUB.md) | Receta en tercera persona: clonar, configurar exclusiones, ejecutar y sincronizar. |
| [06_INVENTARIO_PROYECTO.csv](02_DOCUMENTACION/06_INVENTARIO_PROYECTO.csv) | Inventario local completo: ruta, tamaño, SHA-256 y nombre original cuando aplica. |

#### `07_MODULOS` · Documentación de implementación

| Archivo | Contenido y función |
| --- | --- |
| [01_ORGANIZACION.md](02_DOCUMENTACION/07_MODULOS/01_ORGANIZACION.md) | Convenciones, numeración e inventario documental. |
| [02_ENTORNO_ESPOL.md](02_DOCUMENTACION/07_MODULOS/02_ENTORNO_ESPOL.md) | Entorno Conda, versiones y comprobaciones técnicas. |
| [03_MAPEO_VARIABLES.md](02_DOCUMENTACION/07_MODULOS/03_MAPEO_VARIABLES.md) | Lectura de fuentes y reglas de tipos, nulos, fechas y longitudes. |
| [04_RESPALDO_GITHUB.md](02_DOCUMENTACION/07_MODULOS/04_RESPALDO_GITHUB.md) | Implementación de exclusiones y respaldo del repositorio. |
| [05_REPRODUCIBILIDAD.md](02_DOCUMENTACION/07_MODULOS/05_REPRODUCIBILIDAD.md) | Ejecución local y en contenedor, referencias aprobadas y límites de portabilidad. |
| [06_RECARGA_POSTGRESQL.md](02_DOCUMENTACION/07_MODULOS/06_RECARGA_POSTGRESQL.md) | Sustitución transaccional de las seis tablas y verificaciones de carga. |
| [07_MODELO_ENTIDAD_RELACION.md](02_DOCUMENTACION/07_MODULOS/07_MODELO_ENTIDAD_RELACION.md) | Diagrama, PK, FK, UNIQUE, CHECK y excepciones de población. |
| [08_PORTADA_Y_CATALOGO.md](02_DOCUMENTACION/07_MODULOS/08_PORTADA_Y_CATALOGO.md) | Mantenimiento del README, biografía, identidad visual y navegación. |
| [09_DBEAVER_COMPACTO.md](02_DOCUMENTACION/07_MODULOS/09_DBEAVER_COMPACTO.md) | Preferencia visual para mostrar claves y relaciones sin desplegar todas las columnas. |
| [10_DICCIONARIO_VARIABLES.md](02_DOCUMENTACION/07_MODULOS/10_DICCIONARIO_VARIABLES.md) | Tabla única de etiquetas, vínculos PK/FK/CHECK/UNIQUE/NOT NULL, comentarios y consultas SQL. |

#### `08_MAPEO_ENDI` · Catálogo y SQL reproducible

| Archivo | Contenido y función |
| --- | --- |
| [01_MAPEO_VARIABLES.csv](02_DOCUMENTACION/08_MAPEO_ENDI/01_MAPEO_VARIABLES.csv) | Catálogo de las 1.423 variables fuente: tipo, nulos, longitud, etiqueta y tabla. |
| [02_RESUMEN_MAPEO.json](02_DOCUMENTACION/08_MAPEO_ENDI/02_RESUMEN_MAPEO.json) | Resumen del mapeo, filas y columnas por fuente. |
| [03_TIPOS_POSTGRESQL.sql](02_DOCUMENTACION/08_MAPEO_ENDI/03_TIPOS_POSTGRESQL.sql) | Propuesta de columnas y tipos; el mapeo independiente no ejecuta este archivo. |
| [04_RESTRICCIONES_POSTGRESQL.sql](02_DOCUMENTACION/08_MAPEO_ENDI/04_RESTRICCIONES_POSTGRESQL.sql) | SQL transaccional del modelo relacional: claves, restricciones e índices. |
| [05_DICCIONARIO_POSTGRESQL.sql](02_DOCUMENTACION/08_MAPEO_ENDI/05_DICCIONARIO_POSTGRESQL.sql) | Estructura del diccionario, tabla de vínculos, validaciones y vista de consulta. |
| [06_MAPEO_DICCIONARIO.csv](02_DOCUMENTACION/08_MAPEO_ENDI/06_MAPEO_DICCIONARIO.csv) | Tipos y longitudes de los campos de las dos tablas de metadatos. |

<details>
<summary><strong>09_VALIDACIONES · Archivo por archivo de las evidencias locales</strong></summary>

Esta carpeta está excluida de GitHub. Los archivos siguientes describen verificaciones del equipo de trabajo; no son requisitos que deban descargarse para ejecutar una copia del repositorio. Las ejecuciones generan sus propios reportes. Las comprobaciones históricas corresponden a la etapa y versión que documentan.

| Archivo local | Contenido y función |
| --- | --- |
| `01_ENTORNO_ESPOL.json` | Comprobación del intérprete, paquetes e importaciones. |
| `02_PRUEBAS_MAPEO.json` | Resultado de la suite local, o indicación de que no se distribuye. |
| `03_REPRODUCIBILIDAD.json` | Hashes del mapeo y comparación de ejecuciones por plataforma. |
| `04_CONSTRUCCION_CONTENEDOR.txt` | Registro de construcción de la imagen. |
| `05_EJECUCION_LOCAL.txt` | Registro de reproducción en Windows. |
| `06_EJECUCION_CONTENEDOR.txt` | Registro de ejecución desde una copia recuperada. |
| `07_EXCLUSION_GIT.json` | Verificación de rutas excluidas y archivos publicables. |
| `08_CONEXIONES_POSTGRESQL.json` | Comprobaciones de conexión al servidor. |
| `09_IMAGEN_CONTENEDOR.json` | Identidad de la imagen Docker comprobada. |
| `10_RECONOCIMIENTO_AGENTE.json` | Comprobación del agente y referencias a skills. |
| `11_PORTABILIDAD_RUTA.json` | Comprobaciones de ubicación y archivos incluidos en la imagen. |
| `12_RECARGA_POSTGRESQL.json` | Resultado de la carga y del modelo relacional validado. |
| `13_PRUEBAS_RECARGA.txt` | Pruebas de repetición, rollback y dependencias externas. |
| `14_EJECUCION_RECARGA.txt` | Registro de una ejecución completa de recarga. |
| `15_REPETICION_RECARGA.json` | Comparación histórica de cargas antes del modelo relacional. |
| `16_PUBLICACION_GITHUB.json` | Comprobación de clonación y ejecución desde GitHub. |
| `18_PRUEBAS_MODELO.txt` | Pruebas de claves, relaciones y restricciones del modelo. |
| `19_RECARGA_CON_MODELO.txt` | Registro de carga y modelo desde Windows/Conda. |
| `20_CONTENEDOR_CON_MODELO.txt` | Registro de construcción y carga con el modelo desde Docker. |
| `21_REPETICION_MODELO.json` | Comparación de datos y restricciones entre Windows y Docker. |
| `22_CARGA_DICCIONARIO.txt` | Resultado de la carga inicial del Excel consolidado en PostgreSQL. |
| `23_PRUEBAS_DICCIONARIO.txt` | Integridad de TEXT, etiquetas, FK y constraint triggers de metadatos. |
| `24_ETL_CON_DICCIONARIO.txt` | Registro del ETL completo con modelo y diccionario. |
| `25_REPETICION_DICCIONARIO.json` | Comparación de fuentes, modelo y diccionario entre Windows y Docker. |
| `26_CONTENEDOR_DICCIONARIO.txt` | Construcción y ejecución de la distribución con diccionario. |

</details>

### 3.3. `03_PROCESOS_ETL` · Scripts de ejecución

| Archivo | Contenido y función |
| --- | --- |
| [01_ETL_FUENTES.py](03_PROCESOS_ETL/01_ETL_FUENTES.py) | Coordina lectura, catálogo, conexión y recarga de fuentes ENDI. Su ejecución independiente genera el mapeo. |
| [02_MAPEO_POSTGRESQL.py](03_PROCESOS_ETL/02_MAPEO_POSTGRESQL.py) | Biblioteca común de lectura, normalización, tipos SQLAlchemy y COPY con Psycopg 3. |
| [03_VERIFICAR_ENTORNO.py](03_PROCESOS_ETL/03_VERIFICAR_ENTORNO.py) | Comprueba versiones y operaciones técnicas; dispone de verificación SQL de lectura. |
| [04_GESTION_PROYECTO.py](03_PROCESOS_ETL/04_GESTION_PROYECTO.py) | Punto de entrada: inventario, integridad, reproducción y recarga completa. |
| [05_MODELO_RELACIONAL.py](03_PROCESOS_ETL/05_MODELO_RELACIONAL.py) | Genera, aplica y verifica el modelo relacional dentro de una transacción. |
| [06_CONFIGURAR_DBEAVER.py](03_PROCESOS_ETL/06_CONFIGURAR_DBEAVER.py) | Configura o verifica KEYS en el workspace del cliente DBeaver del anfitrión; no modifica PostgreSQL. |
| [07_DICCIONARIO_VARIABLES.py](03_PROCESOS_ETL/07_DICCIONARIO_VARIABLES.py) | Carga el Excel 07, sincroniza etiquetas y restricciones y comenta las columnas físicas. |

<details>
<summary><strong>05_PRUEBAS · Archivos locales de desarrollo</strong></summary>

Esta carpeta no se publica. Su ausencia en GitHub no se contabiliza como pruebas aprobadas; la ejecución conserva las validaciones de versiones, fuentes y mapeo aprobado.

| Archivo local | Contenido y función |
| --- | --- |
| `01_PRUEBAS_MAPEO.py` | Tipos, fechas, códigos, precisión y comparación con referencias aprobadas. |
| `02_PRUEBAS_RECARGA.py` | Integración PostgreSQL: COPY, repetición y reversión ante fallos. |
| `03_PRUEBAS_MODELO.py` | PK/FK/CHECK/NOT NULL, casos especiales y aplicación repetida del modelo. |
| `04_PRUEBAS_DICCIONARIO.py` | Textos largos, cobertura, carga repetida y rechazo de vínculos de metadatos incorrectos. |

</details>

### 3.4. `04_AGENTES_SKILLS` · Continuidad del trabajo

| Archivo o ruta | Contenido y función |
| --- | --- |
| [AGENTS.md](04_AGENTES_SKILLS/AGENTS.md) | Instrucciones del proyecto, arquitectura, documentación e invariantes ENDI. |
| [01_SKILLS/01_ORTOGRAFIA_TECNICA/SKILL.md](04_AGENTES_SKILLS/01_SKILLS/01_ORTOGRAFIA_TECNICA/SKILL.md) | Redacción y corrección del español técnico, preservando datos y citas. |
| [01_SKILLS/02_PYTHON_DATOS/SKILL.md](04_AGENTES_SKILLS/01_SKILLS/02_PYTHON_DATOS/SKILL.md) | Python, lectura de datos, mapeo PostgreSQL y reglas de integridad. |
| [01_SKILLS/03_ANALITICA_NARRATIVA/SKILL.md](04_AGENTES_SKILLS/01_SKILLS/03_ANALITICA_NARRATIVA/SKILL.md) | Interpretación y comunicación de hallazgos con límites metodológicos. |
| [01_SKILLS/04_ENTORNO_CONDA/SKILL.md](04_AGENTES_SKILLS/01_SKILLS/04_ENTORNO_CONDA/SKILL.md) | Entorno espol, dependencias y reproducción local/contenedor. |

Para iniciar trabajo en Codex se abre `04_AGENTES_SKILLS`, donde se encuentra el único `AGENTS.md` del proyecto. Sus rutas se interpretan desde la raíz `TESIS_ESPOL`.

### 3.5. `05_CONFIGURACIONES` · Entorno y despliegue

| Archivo | Contenido y función |
| --- | --- |
| [01_PROYECTO.json](05_CONFIGURACIONES/01_PROYECTO.json) | Manifiesto: fuentes, nombres originales, hashes, rutas, referencias y parámetros no sensibles. |
| [environment.yml](05_CONFIGURACIONES/environment.yml) | Definición del entorno Conda `espol`, con Python 3.15.0. |
| [requirements.txt](05_CONFIGURACIONES/requirements.txt) | Única lista de versiones fijadas de los paquetes Python. |
| [Dockerfile](05_CONFIGURACIONES/Dockerfile) | Construcción del entorno en una imagen base fijada mediante digest. |
| [Dockerfile.dockerignore](05_CONFIGURACIONES/Dockerfile.dockerignore) | Exclusiones del contexto de construcción de Docker. |
| [compose.yaml](05_CONFIGURACIONES/compose.yaml) | Servicios `mapeo` y `recarga`, conexión externa y montajes de fuentes/documentación. |
| [.gitignore](05_CONFIGURACIONES/.gitignore) | Exclusión de fuentes, pruebas, evidencias y residuos; requiere registrar `core.excludesFile`. |
| [LICENSE](05_CONFIGURACIONES/LICENSE) | Licencia original conservada del repositorio. |

### 3.6. `06_IMG` · Identidad visual

| Archivo | Contenido y función |
| --- | --- |
| [ConneXData.jpeg](06_IMG/ConneXData.jpeg) | Imagen proporcionada por el autor con la identidad de ConneXData y su identificación como CEO; se utiliza en esta portada. |

## 4. Base de datos y modelo relacional

**Destino:** base `research_lab`, esquema `endi`.

| Tabla | Filas comprobadas | Variables fuente | Clave primaria |
| --- | ---: | ---: | --- |
| `endi.f1_hogar` | 20.186 | 133 | `id_hogar` |
| `endi.f1_personas` | 93.242 | 124 | `id_per` |
| `endi.f2_mef` | 19.846 | 289 | `id_mef` |
| `endi.f2_lactancia` | 12.141 | 71 | `id_per` |
| `endi.f2_salud_ninez` | 22.188 | 413 | `id_hijo_ord` |
| `endi.f3_desarrollo_inf` | 9.836 | 393 | `id_per` |
| **Total** | **177.439** | **1.423** | |

El modelo incluye **6 PK, 12 FK, 7 UNIQUE y 11 CHECK**, además de NOT NULL e índices auxiliares. Salud incorpora una columna calculada `id_per_miembro`: permite relacionar con Personas a los miembros del hogar y conserva los 171 registros de no miembros cuyos identificadores terminan en `77`. Los originales mantienen sus valores; hay 1.423 variables fuente y una derivada, con 1.424 columnas físicas.

Los cuidadores se vinculan con Personas y no necesariamente con MEF. Las excepciones, cardinalidades y el diagrama completo se consultan en el [modelo entidad-relación](02_DOCUMENTACION/07_MODULOS/07_MODELO_ENTIDAD_RELACION.md).

### Diccionario consultable en PostgreSQL

El Excel 07 alimenta **una sola tabla de diccionario**, `endi.diccionario_variables`: 1.423 entradas del Excel y una columna derivada. La tabla auxiliar `endi.diccionario_restricciones` vincula cada variable con sus restricciones reales y con la variable referenciada cuando es FK. Los enlaces entre metadatos tienen PK/FK y se contrastan con los catálogos nativos mediante constraint triggers. Las etiquetas se conservan como TEXT y también como comentarios de columnas.

La siguiente consulta muestra qué significa cada variable y si participa en claves:

```sql
SELECT tabla, variable, etiqueta, tipo_postgresql, es_pk, es_fk, restricciones
FROM endi.v_diccionario_variables
WHERE tabla = 'f1_personas'
ORDER BY posicion;
```

El [módulo del diccionario](02_DOCUMENTACION/07_MODULOS/10_DICCIONARIO_VARIABLES.md) explica el modelo de metadatos, los vínculos y las consultas. Las seis fuentes conservan sus 177.439 filas; las dos tablas adicionales contienen documentación del esquema, no copias de microdatos.

## 5. Ejecución desde una copia de GitHub

### Requisitos

1. Git y Docker con contenedores Linux/amd64 o emulación compatible.
2. Las siete entradas aprobadas de `01_DATOS_FUENTE` (seis RDS y el Excel 07 consolidado), recuperadas por separado y con los hashes del manifiesto.
3. PostgreSQL accesible con la base `research_lab`, el esquema `endi` y permisos para sustituir las seis tablas.
4. Credenciales suministradas fuera del repositorio y permisos de escritura en `02_DOCUMENTACION`.

### Pasos

1. El autor clona el repositorio.

```powershell
git clone https://github.com/marcelochavez-ec/TESIS_ESPOL.git
```

2. Se sitúa en la raíz recuperada.

```powershell
Set-Location .\TESIS_ESPOL
```

3. Se activa el archivo de exclusiones antes de incorporar datos o preparar un respaldo.

```powershell
git config --local core.excludesFile (Join-Path (Get-Location).Path '05_CONFIGURACIONES\.gitignore')
```

4. Se recupera la carpeta `01_DATOS_FUENTE` desde su respaldo independiente y se inicia Docker. La configuración predeterminada conecta con PostgreSQL del mismo equipo mediante `host.docker.internal`; si el servidor es otro, se configura `PGHOST_CONTENEDOR` como explica la [receta](02_DOCUMENTACION/05_RESPALDO_GITHUB.md).

5. Se ejecuta el flujo completo. **Este comando sustituye las seis tablas fuente, recrea sus relaciones y sincroniza el diccionario y sus comentarios.** Solicita la contraseña si no se proporcionó mediante un mecanismo externo. Si falla una validación SQL antes del commit, se revierte la tanda completa.

```powershell
docker compose -f 05_CONFIGURACIONES/compose.yaml run --build --rm recarga
```

6. Para reproducir únicamente el mapeo, sin modificar PostgreSQL, se utiliza esta alternativa.

```powershell
docker compose -f 05_CONFIGURACIONES/compose.yaml run --build --rm mapeo
```

La alternativa de Conda, los requisitos de UID/GID en Linux y la conservación de la imagen están explicados en [reproducibilidad](02_DOCUMENTACION/07_MODULOS/05_REPRODUCIBILIDAD.md). El escenario comprobado utiliza Windows como anfitrión, PostgreSQL 18.3 y un contenedor Linux/amd64. Otro equipo debe aportar las mismas entradas y cumplir los requisitos indicados.

### Diagrama compacto en DBeaver

Para visualizar las relaciones de ENDI sin desplegar todas las variables, se utiliza **Show Attributes → Any keys**. El ajuste reproducible se aplica en el anfitrión donde está DBeaver. El autor guarda sus consultas, cierra DBeaver y ejecuta:

```powershell
conda run -n espol python -B 03_PROCESOS_ETL/06_CONFIGURAR_DBEAVER.py
```

Después abre DBeaver y el diagrama del esquema endi. Si el diagrama conserva una opción particular, selecciona Show Attributes → Any keys en su menú contextual. Los pasos y límites de verificación están en [DBeaver compacto](02_DOCUMENTACION/07_MODULOS/09_DBEAVER_COMPACTO.md).

## 6. Qué se publica y qué permanece local

| Se publica en GitHub | Permanece local |
| --- | --- |
| README, guías y documentación de módulos | `01_DATOS_FUENTE/` |
| Documentos metodológicos y demás PDF/Word/libros incorporados fuera de las rutas excluidas | `03_PROCESOS_ETL/05_PRUEBAS/` |
| Scripts ETL, SQL, catálogos y modelo relacional | `02_DOCUMENTACION/09_VALIDACIONES/` |
| Agentes, skills, configuración e imagen de ConneXData | Cachés, bytecode, logs y temporales |

No se versionan contraseñas. Las exclusiones se guardan en [05_CONFIGURACIONES/.gitignore](05_CONFIGURACIONES/.gitignore) y deben activarse en cada clonación. Los datos excluidos requieren un respaldo independiente; GitHub conserva el código y la documentación para procesarlos.

## 7. Mantenimiento documental

Cada cambio funcional se documenta en `02_DOCUMENTACION/07_MODULOS`. Cuando se agregan, retiran o renombran archivos, se actualizan las referencias de esta portada y el inventario global. Los nombres y hashes del inventario representan el estado de la copia local donde se generó, incluidos archivos que deliberadamente no se distribuyen.

El repositorio mantiene separados los datos originales, los procesos, la configuración y la documentación, de modo que el trabajo de tesis pueda revisarse, continuarse y reproducirse a partir de sus entradas verificadas.
