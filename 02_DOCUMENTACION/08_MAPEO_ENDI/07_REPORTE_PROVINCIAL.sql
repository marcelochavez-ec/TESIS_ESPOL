-- REPORTE PROVINCIAL Y AUDITORÍA ENDI R2 (2023-2024).
-- Abrir conectado a research_lab y ejecutar TODO como script en DBeaver.
-- PostgreSQL 18: diez resultados; solo lectura, sin crear ni reemplazar objetos.
-- Metodológico: pp. 25-34 y 59-65. Guía: pp. 9-17 y 20-22.
-- El último resultado es el tabulado de DCI; los anteriores auditan su base.
-- fexp es normalizado: sus sumas NO son totales poblacionales.
-- Estimaciones puntuales descriptivas, SIN IC/CV/errores de diseño muestral.
-- No es una certificación de réplica oficial sin ficha y sintaxis del indicador.
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '60s';
SET LOCAL lock_timeout = '10s';

-- 01. Contexto. La base debe ser research_lab y el modo solo lectura.
SELECT current_database() AS base, current_setting('server_version') AS postgresql,
       current_setting('transaction_read_only') AS solo_lectura,
       current_setting('session_replication_role') AS rol_replicacion,
       'ENDI R2 2023-2024; territorio continental, excluye Galápagos' AS alcance;

-- 02. Inventario físico, cobertura del diccionario y comentarios, por fuente.
WITH filas AS (SELECT 'f1_hogar'::text AS tabla, count(*) AS filas FROM endi.f1_hogar
UNION ALL
SELECT 'f1_personas'::text AS tabla, count(*) AS filas FROM endi.f1_personas
UNION ALL
SELECT 'f2_mef'::text AS tabla, count(*) AS filas FROM endi.f2_mef
UNION ALL
SELECT 'f2_lactancia'::text AS tabla, count(*) AS filas FROM endi.f2_lactancia
UNION ALL
SELECT 'f2_salud_ninez'::text AS tabla, count(*) AS filas FROM endi.f2_salud_ninez
UNION ALL
SELECT 'f3_desarrollo_inf'::text AS tabla, count(*) AS filas FROM endi.f3_desarrollo_inf), columnas AS (
 SELECT t.relname AS tabla, count(*) AS columnas,
        count(*) FILTER (WHERE dv.variable IS NOT NULL) AS descritas,
        count(*) FILTER (WHERE pg_catalog.col_description(t.oid,a.attnum)=dv.etiqueta) AS comentarios_coincidentes
 FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class t ON t.oid=a.attrelid
 JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace
 LEFT JOIN endi.diccionario_variables dv ON dv.esquema=n.nspname AND dv.tabla=t.relname AND dv.variable=a.attname
 WHERE n.nspname='endi' AND t.relname IN ('f1_hogar', 'f1_personas', 'f2_mef', 'f2_lactancia', 'f2_salud_ninez', 'f3_desarrollo_inf') AND a.attnum>0 AND NOT a.attisdropped
 GROUP BY t.relname
)
SELECT f.tabla, f.filas, c.columnas, c.descritas, c.comentarios_coincidentes,
       CASE WHEN c.columnas=c.descritas AND c.columnas=c.comentarios_coincidentes THEN 'OK' ELSE 'REVISAR' END AS estado
FROM filas f JOIN columnas c USING(tabla) ORDER BY f.tabla;

-- 03. Restricciones efectivamente registradas, validadas y aplicadas.
-- Fuentes: 6 PK, 12 FK, 7 UNIQUE, 11 CHECK y 30 NOT NULL.
-- Las dos tablas de metadatos poseen sus propias claves adicionales.
WITH esperado(tabla,pk,fk,unicas,checks,no_nulas) AS (VALUES ('f1_hogar',1,0,0,1,3),
 ('f1_personas',1,1,1,2,4),
 ('f2_mef',1,2,0,1,4),
 ('f2_lactancia',1,3,2,2,6),
 ('f2_salud_ninez',1,3,2,3,8),
 ('f3_desarrollo_inf',1,3,2,2,5),
 ('diccionario_variables',1,0,1,3,9),
 ('diccionario_restricciones',1,2,1,2,7)), actual AS (
SELECT t.relname AS tabla,
 count(*) FILTER (WHERE c.contype='p') AS pk,
 count(*) FILTER (WHERE c.contype='f') AS fk,
 count(*) FILTER (WHERE c.contype='u') AS unicas,
 count(*) FILTER (WHERE c.contype='c') AS checks,
 count(*) FILTER (WHERE c.contype='n') AS no_nulas,
 bool_and(c.convalidated) AS todas_validadas,
 bool_and(c.conenforced) AS todas_aplicadas,
 COALESCE((SELECT bool_and(g.tgenabled='A' OR (g.tgenabled='O' AND current_setting('session_replication_role')='origin')) FROM pg_catalog.pg_trigger g
           WHERE g.tgrelid=t.oid AND g.tgisinternal),true) AS triggers_integridad_habilitados
FROM pg_catalog.pg_constraint c JOIN pg_catalog.pg_class t ON t.oid=c.conrelid
JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace
WHERE n.nspname='endi' AND t.relname IN ('f1_hogar', 'f1_personas', 'f2_mef', 'f2_lactancia', 'f2_salud_ninez', 'f3_desarrollo_inf', 'diccionario_variables', 'diccionario_restricciones') AND c.contype IN ('p','f','u','c','n')
GROUP BY t.oid,t.relname)
SELECT a.*,
 CASE WHEN (a.pk,a.fk,a.unicas,a.checks,a.no_nulas)=(e.pk,e.fk,e.unicas,e.checks,e.no_nulas)
 AND a.todas_validadas AND a.todas_aplicadas AND a.triggers_integridad_habilitados
 THEN 'OK' ELSE 'REVISAR' END AS estado
FROM actual a JOIN esperado e USING(tabla) ORDER BY a.tabla;

-- 04. Relación real por cada columna de FK, enriquecida con sus etiquetas.
-- Incluye las 12 FK fuente y las dos FK compuestas del diccionario.
SELECT c.conname AS restriccion, t.relname AS tabla, a.attname AS variable,
       dv.etiqueta, tr.relname AS tabla_referencia, ar.attname AS variable_referencia,
       padre.etiqueta AS etiqueta_referenciada, k.orden AS posicion_en_clave,
       c.convalidated AS validada, c.conenforced AS aplicada,
       pg_catalog.pg_get_constraintdef(c.oid) AS definicion
FROM pg_catalog.pg_constraint c JOIN pg_catalog.pg_class t ON t.oid=c.conrelid
JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace
JOIN pg_catalog.pg_class tr ON tr.oid=c.confrelid
JOIN pg_catalog.pg_namespace nr ON nr.oid=tr.relnamespace
CROSS JOIN LATERAL unnest(c.conkey) WITH ORDINALITY k(numero,orden)
JOIN pg_catalog.pg_attribute a ON a.attrelid=t.oid AND a.attnum=k.numero
JOIN pg_catalog.pg_attribute ar ON ar.attrelid=tr.oid AND ar.attnum=c.confkey[k.orden::int]
LEFT JOIN endi.diccionario_variables dv ON (dv.esquema,dv.tabla,dv.variable)=(n.nspname,t.relname,a.attname)
LEFT JOIN endi.diccionario_variables padre ON (padre.esquema,padre.tabla,padre.variable)=(nr.nspname,tr.relname,ar.attname)
WHERE n.nspname='endi' AND t.relname IN ('f1_hogar', 'f1_personas', 'f2_mef', 'f2_lactancia', 'f2_salud_ninez', 'f3_desarrollo_inf', 'diccionario_variables', 'diccionario_restricciones') AND c.contype='f'
ORDER BY t.relname,c.conname,k.orden;

-- 05. Auditoría de los datos: todas las incidencias deben ser CERO.
-- PK cuenta grupos duplicados/nulos; UNIQUE ignora NULL conforme a su definición.
-- CHECK cuenta solo expresiones FALSE, como PostgreSQL; NOT NULL se revisa aparte.
WITH controles AS (
SELECT 'PK f1_hogar'::text AS control, (SELECT count(*) FROM (SELECT id_hogar FROM endi.f1_hogar GROUP BY id_hogar HAVING count(*)>1 OR id_hogar IS NULL) x)::bigint AS incidencias
UNION ALL
SELECT 'PK f1_personas'::text AS control, (SELECT count(*) FROM (SELECT id_per FROM endi.f1_personas GROUP BY id_per HAVING count(*)>1 OR id_per IS NULL) x)::bigint AS incidencias
UNION ALL
SELECT 'PK f2_mef'::text AS control, (SELECT count(*) FROM (SELECT id_mef FROM endi.f2_mef GROUP BY id_mef HAVING count(*)>1 OR id_mef IS NULL) x)::bigint AS incidencias
UNION ALL
SELECT 'PK f2_lactancia'::text AS control, (SELECT count(*) FROM (SELECT id_per FROM endi.f2_lactancia GROUP BY id_per HAVING count(*)>1 OR id_per IS NULL) x)::bigint AS incidencias
UNION ALL
SELECT 'PK f2_salud_ninez'::text AS control, (SELECT count(*) FROM (SELECT id_hijo_ord FROM endi.f2_salud_ninez GROUP BY id_hijo_ord HAVING count(*)>1 OR id_hijo_ord IS NULL) x)::bigint AS incidencias
UNION ALL
SELECT 'PK f3_desarrollo_inf'::text AS control, (SELECT count(*) FROM (SELECT id_per FROM endi.f3_desarrollo_inf GROUP BY id_per HAVING count(*)>1 OR id_per IS NULL) x)::bigint AS incidencias
UNION ALL
SELECT 'UNIQUE f1_personas.mef'::text AS control, (SELECT count(*) FROM (SELECT id_mef FROM endi.f1_personas WHERE id_mef IS NOT NULL GROUP BY id_mef HAVING count(*)>1) x)::bigint AS incidencias
UNION ALL
SELECT 'UNIQUE f2_lactancia.madre'::text AS control, (SELECT count(*) FROM (SELECT id_mef FROM endi.f2_lactancia WHERE id_mef IS NOT NULL GROUP BY id_mef HAVING count(*)>1) x)::bigint AS incidencias
UNION ALL
SELECT 'UNIQUE f2_lactancia.mef_per'::text AS control, (SELECT count(*) FROM (SELECT id_mef_per FROM endi.f2_lactancia WHERE id_mef_per IS NOT NULL GROUP BY id_mef_per HAVING count(*)>1) x)::bigint AS incidencias
UNION ALL
SELECT 'UNIQUE f2_salud_ninez.miembro'::text AS control, (SELECT count(*) FROM (SELECT id_per_miembro FROM endi.f2_salud_ninez WHERE id_per_miembro IS NOT NULL GROUP BY id_per_miembro HAVING count(*)>1) x)::bigint AS incidencias
UNION ALL
SELECT 'UNIQUE f2_salud_ninez.madre_orden'::text AS control, (SELECT count(*) FROM (SELECT id_mef,ord_hijo FROM endi.f2_salud_ninez WHERE id_mef IS NOT NULL AND ord_hijo IS NOT NULL GROUP BY id_mef,ord_hijo HAVING count(*)>1) x)::bigint AS incidencias
UNION ALL
SELECT 'UNIQUE f3_desarrollo_inf.hogar'::text AS control, (SELECT count(*) FROM (SELECT id_hogar FROM endi.f3_desarrollo_inf WHERE id_hogar IS NOT NULL GROUP BY id_hogar HAVING count(*)>1) x)::bigint AS incidencias
UNION ALL
SELECT 'UNIQUE f3_desarrollo_inf.cuidador'::text AS control, (SELECT count(*) FROM (SELECT id_cuid FROM endi.f3_desarrollo_inf WHERE id_cuid IS NOT NULL GROUP BY id_cuid HAVING count(*)>1) x)::bigint AS incidencias
UNION ALL
SELECT 'FK f1_personas.hogar'::text AS control, (SELECT count(*) FROM endi.f1_personas h WHERE h.id_hogar IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.f1_hogar p WHERE p.id_hogar=h.id_hogar))::bigint AS incidencias
UNION ALL
SELECT 'FK f2_mef.hogar'::text AS control, (SELECT count(*) FROM endi.f2_mef h WHERE h.id_hogar IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.f1_hogar p WHERE p.id_hogar=h.id_hogar))::bigint AS incidencias
UNION ALL
SELECT 'FK f2_mef.persona_mef'::text AS control, (SELECT count(*) FROM endi.f2_mef h WHERE h.id_mef IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.f1_personas p WHERE p.id_mef=h.id_mef))::bigint AS incidencias
UNION ALL
SELECT 'FK f2_lactancia.hogar'::text AS control, (SELECT count(*) FROM endi.f2_lactancia h WHERE h.id_hogar IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.f1_hogar p WHERE p.id_hogar=h.id_hogar))::bigint AS incidencias
UNION ALL
SELECT 'FK f2_lactancia.madre'::text AS control, (SELECT count(*) FROM endi.f2_lactancia h WHERE h.id_mef IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.f2_mef p WHERE p.id_mef=h.id_mef))::bigint AS incidencias
UNION ALL
SELECT 'FK f2_lactancia.persona'::text AS control, (SELECT count(*) FROM endi.f2_lactancia h WHERE h.id_per IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.f1_personas p WHERE p.id_per=h.id_per))::bigint AS incidencias
UNION ALL
SELECT 'FK f2_salud_ninez.hogar'::text AS control, (SELECT count(*) FROM endi.f2_salud_ninez h WHERE h.id_hogar IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.f1_hogar p WHERE p.id_hogar=h.id_hogar))::bigint AS incidencias
UNION ALL
SELECT 'FK f2_salud_ninez.madre'::text AS control, (SELECT count(*) FROM endi.f2_salud_ninez h WHERE h.id_mef IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.f2_mef p WHERE p.id_mef=h.id_mef))::bigint AS incidencias
UNION ALL
SELECT 'FK f2_salud_ninez.persona_miembro'::text AS control, (SELECT count(*) FROM endi.f2_salud_ninez h WHERE h.id_per_miembro IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.f1_personas p WHERE p.id_per=h.id_per_miembro))::bigint AS incidencias
UNION ALL
SELECT 'FK f3_desarrollo_inf.hogar'::text AS control, (SELECT count(*) FROM endi.f3_desarrollo_inf h WHERE h.id_hogar IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.f1_hogar p WHERE p.id_hogar=h.id_hogar))::bigint AS incidencias
UNION ALL
SELECT 'FK f3_desarrollo_inf.persona'::text AS control, (SELECT count(*) FROM endi.f3_desarrollo_inf h WHERE h.id_per IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.f1_personas p WHERE p.id_per=h.id_per))::bigint AS incidencias
UNION ALL
SELECT 'FK f3_desarrollo_inf.cuidador'::text AS control, (SELECT count(*) FROM endi.f3_desarrollo_inf h WHERE h.id_cuid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.f1_personas p WHERE p.id_per=h.id_cuid))::bigint AS incidencias
UNION ALL
SELECT 'ck_f1_hogar_identificadores'::text AS control, (SELECT count(*) FROM endi.f1_hogar WHERE (id_upm ~ '^[0-9]{10}$' AND id_viv ~ '^[0-9]{12}$' AND id_hogar ~ '^[0-9]{14}$' AND left(id_viv, 10) = id_upm AND left(id_hogar, 12) = id_viv) IS FALSE)::bigint AS incidencias
UNION ALL
SELECT 'ck_f1_personas_identificadores'::text AS control, (SELECT count(*) FROM endi.f1_personas WHERE (id_upm ~ '^[0-9]{10}$' AND id_viv ~ '^[0-9]{12}$' AND id_hogar ~ '^[0-9]{14}$' AND left(id_viv, 10) = id_upm AND left(id_hogar, 12) = id_viv AND (id_per IS NULL OR (id_per ~ '^[0-9]{16}$' AND left(id_per, 14) = id_hogar)) AND (id_mef IS NULL OR (id_mef ~ '^[0-9]{16}$' AND left(id_mef, 14) = id_hogar))) IS FALSE)::bigint AS incidencias
UNION ALL
SELECT 'ck_f2_mef_identificadores'::text AS control, (SELECT count(*) FROM endi.f2_mef WHERE (id_upm ~ '^[0-9]{10}$' AND id_viv ~ '^[0-9]{12}$' AND id_hogar ~ '^[0-9]{14}$' AND left(id_viv, 10) = id_upm AND left(id_hogar, 12) = id_viv AND (id_mef IS NULL OR (id_mef ~ '^[0-9]{16}$' AND left(id_mef, 14) = id_hogar))) IS FALSE)::bigint AS incidencias
UNION ALL
SELECT 'ck_f2_lactancia_identificadores'::text AS control, (SELECT count(*) FROM endi.f2_lactancia WHERE (id_upm ~ '^[0-9]{10}$' AND id_viv ~ '^[0-9]{12}$' AND id_hogar ~ '^[0-9]{14}$' AND left(id_viv, 10) = id_upm AND left(id_hogar, 12) = id_viv AND (id_per IS NULL OR (id_per ~ '^[0-9]{16}$' AND left(id_per, 14) = id_hogar)) AND (id_mef IS NULL OR (id_mef ~ '^[0-9]{16}$' AND left(id_mef, 14) = id_hogar))) IS FALSE)::bigint AS incidencias
UNION ALL
SELECT 'ck_f2_salud_ninez_identificadores'::text AS control, (SELECT count(*) FROM endi.f2_salud_ninez WHERE (id_upm ~ '^[0-9]{10}$' AND id_viv ~ '^[0-9]{12}$' AND id_hogar ~ '^[0-9]{14}$' AND left(id_viv, 10) = id_upm AND left(id_hogar, 12) = id_viv AND (id_per IS NULL OR (id_per ~ '^[0-9]{16}$' AND left(id_per, 14) = id_hogar)) AND (id_mef IS NULL OR (id_mef ~ '^[0-9]{16}$' AND left(id_mef, 14) = id_hogar))) IS FALSE)::bigint AS incidencias
UNION ALL
SELECT 'ck_f3_desarrollo_inf_identificadores'::text AS control, (SELECT count(*) FROM endi.f3_desarrollo_inf WHERE (id_upm ~ '^[0-9]{10}$' AND id_viv ~ '^[0-9]{12}$' AND id_hogar ~ '^[0-9]{14}$' AND left(id_viv, 10) = id_upm AND left(id_hogar, 12) = id_viv AND (id_per IS NULL OR (id_per ~ '^[0-9]{16}$' AND left(id_per, 14) = id_hogar)) AND (id_cuid IS NULL OR (id_cuid ~ '^[0-9]{16}$' AND left(id_cuid, 14) = id_hogar))) IS FALSE)::bigint AS incidencias
UNION ALL
SELECT 'ck_f1_personas_mef_persona'::text AS control, (SELECT count(*) FROM endi.f1_personas WHERE (id_mef IS NULL OR id_mef = id_per) IS FALSE)::bigint AS incidencias
UNION ALL
SELECT 'ck_f2_lactancia_mef_per'::text AS control, (SELECT count(*) FROM endi.f2_lactancia WHERE (id_mef_per = id_mef || right(id_per, 2)) IS FALSE)::bigint AS incidencias
UNION ALL
SELECT 'ck_f2_salud_ninez_mef_per'::text AS control, (SELECT count(*) FROM endi.f2_salud_ninez WHERE (id_mef_per = id_mef || right(id_per, 2)) IS FALSE)::bigint AS incidencias
UNION ALL
SELECT 'ck_f2_salud_ninez_hijo_orden'::text AS control, (SELECT count(*) FROM endi.f2_salud_ninez WHERE (ord_hijo IN ('01', '02') AND id_hijo_ord = id_mef_per || ord_hijo) IS FALSE)::bigint AS incidencias
UNION ALL
SELECT 'ck_f3_desarrollo_inf_cuidador_distinto'::text AS control, (SELECT count(*) FROM endi.f3_desarrollo_inf WHERE (id_cuid <> id_per) IS FALSE)::bigint AS incidencias
UNION ALL
SELECT 'NOT NULL f1_hogar'::text AS control, (SELECT count(*) FROM endi.f1_hogar WHERE id_upm IS NULL OR id_viv IS NULL OR id_hogar IS NULL)::bigint AS incidencias
UNION ALL
SELECT 'NOT NULL f1_personas'::text AS control, (SELECT count(*) FROM endi.f1_personas WHERE id_upm IS NULL OR id_viv IS NULL OR id_hogar IS NULL OR id_per IS NULL)::bigint AS incidencias
UNION ALL
SELECT 'NOT NULL f2_mef'::text AS control, (SELECT count(*) FROM endi.f2_mef WHERE id_upm IS NULL OR id_viv IS NULL OR id_hogar IS NULL OR id_mef IS NULL)::bigint AS incidencias
UNION ALL
SELECT 'NOT NULL f2_lactancia'::text AS control, (SELECT count(*) FROM endi.f2_lactancia WHERE id_upm IS NULL OR id_viv IS NULL OR id_hogar IS NULL OR id_per IS NULL OR id_mef IS NULL OR id_mef_per IS NULL)::bigint AS incidencias
UNION ALL
SELECT 'NOT NULL f2_salud_ninez'::text AS control, (SELECT count(*) FROM endi.f2_salud_ninez WHERE id_upm IS NULL OR id_viv IS NULL OR id_hogar IS NULL OR id_hijo_ord IS NULL OR id_per IS NULL OR id_mef IS NULL OR id_mef_per IS NULL OR ord_hijo IS NULL)::bigint AS incidencias
UNION ALL
SELECT 'NOT NULL f3_desarrollo_inf'::text AS control, (SELECT count(*) FROM endi.f3_desarrollo_inf WHERE id_upm IS NULL OR id_viv IS NULL OR id_hogar IS NULL OR id_per IS NULL OR id_cuid IS NULL)::bigint AS incidencias
UNION ALL
SELECT 'FK diccionario variable'::text AS control, (SELECT count(*) FROM endi.diccionario_restricciones r WHERE r.tabla IS NOT NULL AND r.variable IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.diccionario_variables v WHERE (v.esquema,v.tabla,v.variable)=(r.esquema,r.tabla,r.variable)))::bigint AS incidencias
UNION ALL
SELECT 'FK diccionario referencia'::text AS control, (SELECT count(*) FROM endi.diccionario_restricciones r WHERE r.tabla_referencia IS NOT NULL AND r.variable_referencia IS NOT NULL AND NOT EXISTS (SELECT 1 FROM endi.diccionario_variables v WHERE (v.esquema,v.tabla,v.variable)=(r.esquema,r.tabla_referencia,r.variable_referencia)))::bigint AS incidencias
UNION ALL
SELECT 'Geografía Personas-Hogar'::text AS control, (SELECT count(*) FROM endi.f1_personas p LEFT JOIN endi.f1_hogar h USING(id_hogar) WHERE p.prov IS DISTINCT FROM h.prov)::bigint AS incidencias
UNION ALL
SELECT 'Provincia continental f1_hogar'::text AS control, (SELECT count(*) FROM endi.f1_hogar WHERE prov IS NULL OR prov<>trunc(prov) OR prov NOT IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,21,22,23,24))::bigint AS incidencias
UNION ALL
SELECT 'Ponderador f1_hogar.fexp'::text AS control, (SELECT count(*) FROM endi.f1_hogar WHERE fexp IS NULL OR NOT (fexp>0 AND fexp<'Infinity'::double precision))::bigint AS incidencias
UNION ALL
SELECT 'Provincia continental f1_personas'::text AS control, (SELECT count(*) FROM endi.f1_personas WHERE prov IS NULL OR prov<>trunc(prov) OR prov NOT IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,21,22,23,24))::bigint AS incidencias
UNION ALL
SELECT 'Ponderador f1_personas.fexp'::text AS control, (SELECT count(*) FROM endi.f1_personas WHERE fexp IS NULL OR NOT (fexp>0 AND fexp<'Infinity'::double precision))::bigint AS incidencias
UNION ALL
SELECT 'Provincia continental f2_mef'::text AS control, (SELECT count(*) FROM endi.f2_mef WHERE prov IS NULL OR prov<>trunc(prov) OR prov NOT IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,21,22,23,24))::bigint AS incidencias
UNION ALL
SELECT 'Ponderador f2_mef.fexp'::text AS control, (SELECT count(*) FROM endi.f2_mef WHERE fexp IS NULL OR NOT (fexp>0 AND fexp<'Infinity'::double precision))::bigint AS incidencias
UNION ALL
SELECT 'Provincia continental f2_lactancia'::text AS control, (SELECT count(*) FROM endi.f2_lactancia WHERE prov IS NULL OR prov<>trunc(prov) OR prov NOT IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,21,22,23,24))::bigint AS incidencias
UNION ALL
SELECT 'Ponderador f2_lactancia.fexp_lm'::text AS control, (SELECT count(*) FROM endi.f2_lactancia WHERE fexp_lm IS NULL OR NOT (fexp_lm>0 AND fexp_lm<'Infinity'::double precision))::bigint AS incidencias
UNION ALL
SELECT 'Provincia continental f2_salud_ninez'::text AS control, (SELECT count(*) FROM endi.f2_salud_ninez WHERE prov IS NULL OR prov<>trunc(prov) OR prov NOT IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,21,22,23,24))::bigint AS incidencias
UNION ALL
SELECT 'Ponderador f2_salud_ninez.fexp'::text AS control, (SELECT count(*) FROM endi.f2_salud_ninez WHERE fexp IS NULL OR NOT (fexp>0 AND fexp<'Infinity'::double precision))::bigint AS incidencias
UNION ALL
SELECT 'Provincia continental f3_desarrollo_inf'::text AS control, (SELECT count(*) FROM endi.f3_desarrollo_inf WHERE prov IS NULL OR prov<>trunc(prov) OR prov NOT IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,21,22,23,24))::bigint AS incidencias
UNION ALL
SELECT 'Ponderador f3_desarrollo_inf.fexp_di'::text AS control, (SELECT count(*) FROM endi.f3_desarrollo_inf WHERE fexp_di IS NULL OR NOT (fexp_di>0 AND fexp_di<'Infinity'::double precision))::bigint AS incidencias
UNION ALL
SELECT 'Categorías dcronica'::text AS control, (SELECT count(*) FROM endi.f1_personas WHERE dcronica IS NOT NULL AND dcronica NOT IN (0,1))::bigint AS incidencias
UNION ALL
SELECT 'Categorías dcronica_2'::text AS control, (SELECT count(*) FROM endi.f1_personas WHERE dcronica_2 IS NOT NULL AND dcronica_2 NOT IN (0,1))::bigint AS incidencias
)
SELECT control, incidencias, CASE WHEN incidencias=0 THEN 'OK' ELSE 'REVISAR' END AS estado
FROM controles ORDER BY control;

-- 06. Diccionario contra el catálogo NATIVO: detecta omisiones y metadatos obsoletos.
WITH columnas AS (
 SELECT n.nspname AS esquema,t.relname AS tabla,a.attname AS variable,a.attnum AS posicion,
        pg_catalog.format_type(a.atttypid,a.atttypmod) AS tipo, NOT a.attnotnull AS admite_nulos,
        a.attgenerated<>'' AS derivada,pg_catalog.col_description(t.oid,a.attnum) AS comentario
 FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class t ON t.oid=a.attrelid
 JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace
 WHERE n.nspname='endi' AND t.relname IN ('f1_hogar', 'f1_personas', 'f2_mef', 'f2_lactancia', 'f2_salud_ninez', 'f3_desarrollo_inf') AND a.attnum>0 AND NOT a.attisdropped
), dc AS (
 SELECT c.variable AS real, d.variable AS registrada,
        c.posicion IS DISTINCT FROM d.posicion OR c.tipo IS DISTINCT FROM d.tipo_postgresql
        OR c.admite_nulos IS DISTINCT FROM d.admite_nulos
        OR c.derivada IS DISTINCT FROM (d.procedencia='derivada') AS difiere,
        c.comentario IS DISTINCT FROM d.etiqueta AS comentario_difiere
 FROM columnas c FULL JOIN endi.diccionario_variables d USING(esquema,tabla,variable)
), reales AS (SELECT n.nspname AS esquema, t.relname AS tabla, c.conname AS restriccion,
    CASE c.contype WHEN 'p' THEN 'PRIMARY KEY' WHEN 'f' THEN 'FOREIGN KEY'
        WHEN 'u' THEN 'UNIQUE' WHEN 'c' THEN 'CHECK' WHEN 'n' THEN 'NOT NULL' END AS tipo_restriccion,
    a.attname AS variable, k.orden AS posicion,
    nr.nspname AS esquema_referencia, tr.relname AS tabla_referencia,
    ar.attname AS variable_referencia, pg_catalog.pg_get_constraintdef(c.oid) AS definicion
    FROM pg_catalog.pg_constraint c JOIN pg_catalog.pg_class t ON t.oid=c.conrelid
    JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace
    CROSS JOIN LATERAL unnest(c.conkey) WITH ORDINALITY k(numero,orden)
    JOIN pg_catalog.pg_attribute a ON a.attrelid=t.oid AND a.attnum=k.numero
    LEFT JOIN pg_catalog.pg_class tr ON tr.oid=c.confrelid
    LEFT JOIN pg_catalog.pg_namespace nr ON nr.oid=tr.relnamespace
    LEFT JOIN pg_catalog.pg_attribute ar ON ar.attrelid=tr.oid AND ar.attnum=c.confkey[k.orden::int] WHERE n.nspname='endi' AND t.relname IN ('f1_hogar', 'f1_personas', 'f2_mef', 'f2_lactancia', 'f2_salud_ninez', 'f3_desarrollo_inf') AND c.contype IN ('p','f','u','c','n')), dr AS (
 SELECT r.restriccion AS real,d.restriccion AS registrada,
        r.tipo_restriccion IS DISTINCT FROM d.tipo_restriccion
        OR r.definicion IS DISTINCT FROM d.definicion
        OR r.tabla_referencia IS DISTINCT FROM d.tabla_referencia
        OR r.variable_referencia IS DISTINCT FROM d.variable_referencia AS difiere
 FROM reales r FULL JOIN endi.diccionario_restricciones d USING(esquema,tabla,variable,restriccion,posicion)
), controles AS (
 SELECT 'Columnas sin diccionario'::text AS control,count(*) AS incidencias FROM dc WHERE real IS NOT NULL AND registrada IS NULL
 UNION ALL SELECT 'Diccionario sin columna física',count(*) FROM dc WHERE real IS NULL AND registrada IS NOT NULL
 UNION ALL SELECT 'Tipo/posición/nulabilidad/procedencia distintos',count(*) FROM dc WHERE real IS NOT NULL AND registrada IS NOT NULL AND difiere
 UNION ALL SELECT 'Comentarios distintos de la etiqueta',count(*) FROM dc WHERE real IS NOT NULL AND registrada IS NOT NULL AND comentario_difiere
 UNION ALL SELECT 'Vínculos físicos sin catalogar',count(*) FROM dr WHERE real IS NOT NULL AND registrada IS NULL
 UNION ALL SELECT 'Vínculos catalogados inexistentes',count(*) FROM dr WHERE real IS NULL AND registrada IS NOT NULL
 UNION ALL SELECT 'Definición o destino de restricción distintos',count(*) FROM dr WHERE real IS NOT NULL AND registrada IS NOT NULL AND difiere
)
SELECT control,incidencias,CASE WHEN incidencias=0 THEN 'OK' ELSE 'REVISAR' END AS estado
FROM controles ORDER BY control;

-- 07. Validaciones activas de escritura del diccionario (no ejecuta INSERT/UPDATE).
WITH esperados(tabla,trigger_nombre) AS (VALUES
 ('diccionario_variables','ct_diccionario_columna'),
 ('diccionario_restricciones','ct_diccionario_restriccion'))
SELECT e.tabla,e.trigger_nombre,g.tgenabled AS habilitacion,
       g.tgdeferrable AS diferible,g.tginitdeferred AS inicialmente_diferido,
       CASE WHEN g.oid IS NOT NULL AND (g.tgenabled='A' OR
         (g.tgenabled='O' AND current_setting('session_replication_role')='origin'))
         THEN 'OK' ELSE 'REVISAR' END AS estado,
       pg_catalog.pg_get_triggerdef(g.oid) AS definicion
FROM esperados e LEFT JOIN pg_catalog.pg_namespace n ON n.nspname='endi'
LEFT JOIN pg_catalog.pg_class t ON t.relnamespace=n.oid AND t.relname=e.tabla
LEFT JOIN pg_catalog.pg_trigger g ON g.tgrelid=t.oid AND g.tgname=e.trigger_nombre
ORDER BY e.tabla;

-- 08. Significado y papel relacional de las variables utilizadas y los ponderadores.
SELECT formulario,tabla,variable,etiqueta,tipo_postgresql,admite_nulos,
       es_pk,es_fk,es_unique,restricciones
FROM endi.v_diccionario_variables
WHERE (tabla='f1_personas' AND variable IN ('prov','id_hogar','id_per','fexp','dcronica','dcronica_2'))
   OR (tabla='f1_hogar' AND variable IN ('prov','id_hogar','fexp'))
   OR (tabla='f2_lactancia' AND variable='fexp_lm')
   OR (tabla='f3_desarrollo_inf' AND variable='fexp_di')
ORDER BY tabla,posicion;

-- 09. Cobertura provincial de las seis fuentes: cada tabla se agrega ANTES del cruce.
-- Son registros muestrales de unidades distintas; no sumar las columnas entre sí.
WITH provincias(codigo,provincia) AS (VALUES (1,'Azuay'),
 (2,'Bolívar'),
 (3,'Cañar'),
 (4,'Carchi'),
 (5,'Cotopaxi'),
 (6,'Chimborazo'),
 (7,'El Oro'),
 (8,'Esmeraldas'),
 (9,'Guayas'),
 (10,'Imbabura'),
 (11,'Loja'),
 (12,'Los Ríos'),
 (13,'Manabí'),
 (14,'Morona Santiago'),
 (15,'Napo'),
 (16,'Pastaza'),
 (17,'Pichincha'),
 (18,'Tungurahua'),
 (19,'Zamora Chinchipe'),
 (21,'Sucumbíos'),
 (22,'Orellana'),
 (23,'Santo Domingo de los Tsáchilas'),
 (24,'Santa Elena')), conteos AS (SELECT 'f1_hogar'::text AS tabla, prov::integer AS codigo, count(*) AS n FROM endi.f1_hogar GROUP BY prov
UNION ALL
SELECT 'f1_personas'::text AS tabla, prov::integer AS codigo, count(*) AS n FROM endi.f1_personas GROUP BY prov
UNION ALL
SELECT 'f2_mef'::text AS tabla, prov::integer AS codigo, count(*) AS n FROM endi.f2_mef GROUP BY prov
UNION ALL
SELECT 'f2_lactancia'::text AS tabla, prov::integer AS codigo, count(*) AS n FROM endi.f2_lactancia GROUP BY prov
UNION ALL
SELECT 'f2_salud_ninez'::text AS tabla, prov::integer AS codigo, count(*) AS n FROM endi.f2_salud_ninez GROUP BY prov
UNION ALL
SELECT 'f3_desarrollo_inf'::text AS tabla, prov::integer AS codigo, count(*) AS n FROM endi.f3_desarrollo_inf GROUP BY prov)
SELECT lpad(p.codigo::text,2,'0') AS codigo_provincia,p.provincia,
 COALESCE(max(n) FILTER (WHERE tabla='f1_hogar'),0) AS f1_hogar,
 COALESCE(max(n) FILTER (WHERE tabla='f1_personas'),0) AS f1_personas,
 COALESCE(max(n) FILTER (WHERE tabla='f2_mef'),0) AS f2_mef,
 COALESCE(max(n) FILTER (WHERE tabla='f2_lactancia'),0) AS f2_lactancia,
 COALESCE(max(n) FILTER (WHERE tabla='f2_salud_ninez'),0) AS f2_salud_ninez,
 COALESCE(max(n) FILTER (WHERE tabla='f3_desarrollo_inf'),0) AS f3_desarrollo_inf
FROM provincias p LEFT JOIN conteos c USING(codigo)
GROUP BY p.codigo,p.provincia ORDER BY p.codigo;

-- 10. TABULADO PRINCIPAL: DCI en menores de 2 y 5 años, por provincia y total continental.
-- Se reutilizan dcronica_2/dcronica publicados (0=no,1=sí), sin recalcular antropometría.
-- Cada denominador usa solo su indicador 0/1 y un fexp positivo y finito.
-- No se convierten NULL en cero ni se filtran niños por una reconstrucción de edad.
-- LEFT JOIN Hogar no pierde personas; su PK garantiza que no multiplica filas.
-- No unir aquí todas las tablas: Salud puede tener varios hijos por madre.
-- Conservar fexp de PERSONAS, aunque se consulte información de Hogar.
-- Las etiquetas se obtienen del diccionario mediante su PK compuesta.
WITH provincias(codigo,provincia) AS (VALUES (1,'Azuay'),
 (2,'Bolívar'),
 (3,'Cañar'),
 (4,'Carchi'),
 (5,'Cotopaxi'),
 (6,'Chimborazo'),
 (7,'El Oro'),
 (8,'Esmeraldas'),
 (9,'Guayas'),
 (10,'Imbabura'),
 (11,'Loja'),
 (12,'Los Ríos'),
 (13,'Manabí'),
 (14,'Morona Santiago'),
 (15,'Napo'),
 (16,'Pastaza'),
 (17,'Pichincha'),
 (18,'Tungurahua'),
 (19,'Zamora Chinchipe'),
 (21,'Sucumbíos'),
 (22,'Orellana'),
 (23,'Santo Domingo de los Tsáchilas'),
 (24,'Santa Elena')), base AS (
 SELECT p.prov::integer AS codigo,i.variable,i.valor,
        CASE WHEN p.fexp>0 AND p.fexp<'Infinity'::double precision THEN p.fexp::numeric END AS peso
 FROM endi.f1_personas p LEFT JOIN endi.f1_hogar h ON h.id_hogar=p.id_hogar
 CROSS JOIN LATERAL (VALUES ('dcronica_2',p.dcronica_2),('dcronica',p.dcronica)) i(variable,valor)
 WHERE i.valor IN (0,1) AND p.prov IN (SELECT codigo FROM provincias)
), agregado AS (
 SELECT codigo,variable,GROUPING(codigo) AS es_total,
        count(*) AS n_indicador_valido,
        count(peso) AS n_analizados,
        count(*) FILTER (WHERE peso IS NULL) AS n_excluidos_peso,
        count(*) FILTER (WHERE valor=1 AND peso IS NOT NULL) AS n_con_dci,
        sum(peso) AS suma_pesos_normalizados,
        sum(peso) FILTER (WHERE valor=1) AS suma_pesos_con_dci
 FROM base GROUP BY GROUPING SETS ((codigo,variable),(variable))
)
SELECT CASE WHEN a.es_total=1 THEN '00' ELSE lpad(a.codigo::text,2,'0') END AS codigo_provincia,
       CASE WHEN a.es_total=1 THEN 'TOTAL CONTINENTAL' ELSE p.provincia END AS provincia,
       a.variable,d.etiqueta AS indicador,
       a.n_indicador_valido,a.n_analizados,a.n_excluidos_peso,a.n_con_dci,
       round(a.suma_pesos_normalizados,4) AS suma_pesos_normalizados,
       CASE WHEN a.n_analizados>0
            THEN round(100*COALESCE(a.suma_pesos_con_dci,0)/NULLIF(a.suma_pesos_normalizados,0),2)
       END AS prevalencia_ponderada_pct,
       round(100.0*a.n_con_dci/NULLIF(a.n_analizados,0),2) AS proporcion_muestral_pct,
       'Estimación puntual; IC y CV no calculados'::text AS alcance_estadistico
FROM agregado a LEFT JOIN provincias p USING(codigo)
LEFT JOIN endi.diccionario_variables d ON (d.esquema,d.tabla,d.variable)=('endi','f1_personas',a.variable)
ORDER BY CASE WHEN a.es_total=1 THEN 0 ELSE a.codigo END,
         CASE a.variable WHEN 'dcronica_2' THEN 1 ELSE 2 END;

COMMIT;
