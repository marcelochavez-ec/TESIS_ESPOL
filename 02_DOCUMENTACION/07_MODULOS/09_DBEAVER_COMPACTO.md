# DIAGRAMA ENDI COMPACTO EN DBEAVER

1. **Nombre y objetivo.** Configurar DBeaver para presentar relaciones y columnas clave, evitando desplegar las cientos de variables de cada tabla ENDI.
2. **Archivos.** `03_PROCESOS_ETL/06_CONFIGURAR_DBEAVER.py` aplica o lee el ajuste. Se actualizan las referencias de README, guía del proyecto e inventario. La preferencia real pertenece al workspace local de DBeaver y no se publica.
3. **Flujo.** Se identifica el workspace existente y la preferencia ER; se cambia exclusivamente erd.attr.visibility de ALL a KEYS; se relee el archivo; se reinicia DBeaver después de guardar las consultas y se abre el diagrama del esquema endi. La aplicación visual requiere ese reinicio si la preferencia anterior sigue en memoria.
4. **Entradas.** DBeaver instalado; workspace existente con preferencias ER; ruta opcional --workspace. En Windows se utiliza por defecto %APPDATA%/DBeaverData/workspace6. No se necesitan credenciales PostgreSQL para cambiar esta preferencia visual.
5. **Salidas.** Preferencia erd.attr.visibility=KEYS y confirmación JSON en consola. No se generan archivos de conexiones, contraseñas ni respaldos duplicados de preferencias.
6. **Fuentes.** Configuración del cliente DBeaver 26.2.1 y claves reales de research_lab.endi ya documentadas en 07_MODELO_ENTIDAD_RELACION.md. No se ejecutan consultas ni DDL para configurar la vista.
7. **Regla de visualización.** KEYS corresponde a Show Attributes → Any keys: columnas de claves primarias y foráneas. No es un límite arbitrario de seis columnas que pueda ocultar una relación. Para este modelo deja entre una y cuatro columnas por tabla; se conserva cada línea FK.

| Tabla | Columnas necesarias para PK/FK |
| --- | --- |
| f1_hogar | id_hogar |
| f1_personas | id_per, id_hogar |
| f2_mef | id_mef, id_hogar |
| f2_lactancia | id_per, id_mef, id_hogar |
| f2_salud_ninez | id_hijo_ord, id_hogar, id_mef, id_per_miembro |
| f3_desarrollo_inf | id_per, id_hogar, id_cuid |

8. **UI.** Tras guardar trabajo y reiniciar DBeaver, el usuario abre LOCALHOST → Databases → research_lab → Schemas → endi y su pestaña ER Diagram. Si un diagrama tiene una opción particular previa, hace clic derecho en el lienzo y selecciona Show Attributes → Any keys. Arrange Diagram organiza las seis tablas. Show Attributes → None permite ver solo cajas y líneas; no se usa como ajuste predeterminado porque ocultaría también las claves.
9. **Server.** No aplica. Es una preferencia del cliente; no cambia columnas físicas, PK, FK, permisos ni datos de PostgreSQL. El valor predeterminado se aplica al workspace, no exclusivamente a una base.
10. **Lógica del script.** configurar(workspace, visibilidad, verificar) recibe el workspace y una opción ALL/KEYS/PRIMARY/NONE; devuelve valor anterior/actual y ruta comprobada. Conserva las otras líneas del archivo y utiliza sustitución atómica si hay cambios. --verificar lee sin escribir. No crea un workspace inexistente.
11. **SQL y ETL.** No se altera el ETL ni se recargan tablas. El esquema conserva todas sus variables; el ajuste modifica solo la representación del diagrama. El script se ejecuta en el anfitrión donde está DBeaver, separado de la carga Docker.
12. **Dependencias.** Python estándar; no se agregan paquetes a requirements.txt. El entorno espol permite ejecutar el script en Windows. Otras ubicaciones se indican expresamente con --workspace.
13. **Validaciones.** Se comprobó en la instalación local que ALL era el valor previo y que el enum de DBeaver admite KEYS. Se verifica la escritura y preservación de las demás preferencias, la repetición sin cambios y la lectura con --verificar.
14. **Límite de la verificación visual.** La ventana de DBeaver abierta no respondió a las acciones automatizadas; no se afirma haber visto el diagrama final. El archivo queda configurado y se requiere guardar las consultas y reiniciar DBeaver para comprobar la vista en esa sesión. No se fuerza el cierre ni se ejecuta el contenido de los editores SQL abiertos.
15. **Riesgos.** Una sesión que conserva preferencias antiguas puede requerir reabrir el diagrama. Si DBeaver se cierra después de editar preferencias desde su interfaz, conviene volver a verificar el archivo. El script también permite aplicar PRIMARY, NONE o restaurar ALL de forma explícita.
16. **Cambios realizados.** Se añadió un configurador reproducible, se guardó KEYS en el workspace local y se documentó cómo recuperar la vista compacta en otro equipo. El proyecto no incorpora la configuración privada de DBeaver.
17. **Referencias y ejecución.** La [documentación de diagramas](https://dbeaver.com/docs/dbeaver/ER-Diagrams/) describe Any keys y las opciones de atributos. El [enum oficial](https://github.com/dbeaver/dbeaver/blob/devel/plugins/org.jkiss.dbeaver.model.erd/src/org/jkiss/dbeaver/model/erd/ERDAttributeVisibility.java) confirma el valor KEYS.

El usuario guarda sus consultas y cierra DBeaver antes de ejecutar el ajuste en futuros equipos.

```powershell
conda run -n espol python -B 03_PROCESOS_ETL/06_CONFIGURAR_DBEAVER.py
```

Se puede comprobar el valor guardado sin modificarlo.

```powershell
conda run -n espol python -B 03_PROCESOS_ETL/06_CONFIGURAR_DBEAVER.py --verificar
```

Después se abre DBeaver y se muestra el diagrama de endi. La verificación en archivo no sustituye comprobar visualmente una sesión que todavía conserve el ajuste anterior.
