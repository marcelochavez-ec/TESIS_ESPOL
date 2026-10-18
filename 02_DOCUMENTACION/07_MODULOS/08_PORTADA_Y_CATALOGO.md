# PORTADA, BIOGRAFÍA Y CATÁLOGO DEL REPOSITORIO

1. **Nombre.** Portada y catálogo documental de TESIS_ESPOL.
2. **Objetivo.** Presentar al autor, el contexto de la tesis y una guía por carpeta y archivo desde la portada de GitHub.
3. **Archivos.** README.md en la raíz; imagen existente 06_IMG/ConneXData.jpeg; referencias en 04_GUIA_PROYECTO.md, 01_ORGANIZACION.md y AGENTS.md; inventario global actualizado.
4. **Flujo.** Se revisan los archivos existentes, se redacta la biografía con datos confirmados, se enlazan los documentos publicados, se enumeran las entradas y evidencias locales sin enlaces inexistentes y se comprueban rutas, catálogo y exclusiones.
5. **Entradas.** Nombre Marcelo Chávez, cargo CEO de ConneXData y perfil LinkedIn proporcionados por el autor; documentación técnica e inventario; imagen local proporcionada. No se incorporan grados, cargos ni datos personales no confirmados. El contenido del perfil LinkedIn no pudo recuperarse automáticamente; se incluye el enlace público aportado.
6. **Salidas.** README visible en GitHub con presentación, contexto, navegación, catálogo, requisitos y comandos independientes; imagen de ConneXData versionada.
7. **Fuentes.** Archivos del repositorio y datos declarados por el autor. No se consulta ninguna tabla PostgreSQL para crear la portada ni se modifica la base.
8. **Reglas editoriales.** La marca se escribe ConneXData. Se omiten referencias a empleadores que el autor pidió retirar. Por indicación expresa no se utiliza el logo de ESPOL. La biografía distingue al autor del alcance técnico del repositorio y no atribuye resultados estadísticos no implementados.
9. **UI.** GitHub renderiza Markdown, tablas, enlaces relativos y la imagen original mediante HTML img. Los catálogos de evidencias y pruebas locales quedan en bloques desplegables. No hay imágenes ni enlaces locales rotos a carpetas excluidas.
10. **Server.** No aplica; la portada es estática y no ejecuta servicios ni scripts al abrirse.
11. **SQL y ETL.** El README describe el flujo existente y enlaza su modelo. No altera tipos, restricciones, credenciales ni lógica de carga. El comando de recarga se identifica como sustitución de las seis tablas.
12. **Dependencias.** Renderizador Markdown/HTML de GitHub; no se añaden paquetes al entorno espol. La imagen se conserva sin editar sus bytes.
13. **Validaciones.** Se comprueban destinos de enlaces relativos, ruta y formato de la imagen, cobertura de cada archivo del proyecto en el catálogo y conservación de exclusiones. El inventario se regenera al terminar.
14. **Pruebas.** Comprobaciones documentales y de Git; no se repite la carga SQL ni la suite ETL por un cambio de presentación sin modificaciones funcionales.
15. **Riesgos y supuestos.** El catálogo requiere mantenimiento al cambiar archivos. Las fuentes y evidencias locales no están disponibles por navegación en GitHub; se describen explícitamente como locales. La biografía puede ampliarse cuando el autor facilite información adicional confirmada.
16. **Cambios.** Se crea README.md como excepción explícita a la regla anterior de no dejar archivos en la raíz, porque GitHub lo usa como portada. Se incorpora 06_IMG al esquema documental y se publica la imagen ConneXData que antes estaba sin rastrear.
17. **Mantenimiento.** Actualizar README e inventario cuando cambie la estructura o el autor indique nuevos datos públicos; conservar un solo README de portada y un único AGENTS.md.
