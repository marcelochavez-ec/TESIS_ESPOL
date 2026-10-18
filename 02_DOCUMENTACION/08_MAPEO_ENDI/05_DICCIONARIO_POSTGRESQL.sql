-- ESTRUCTURA Y VÍNCULOS DEL DICCIONARIO. La carga Excel se realiza con 07_DICCIONARIO_VARIABLES.py.
BEGIN;
CREATE TABLE IF NOT EXISTS endi.diccionario_variables (
	esquema VARCHAR(14) NOT NULL,
	tabla VARCHAR(27) NOT NULL,
	variable VARCHAR(30) NOT NULL,
	formulario VARCHAR(12) NOT NULL,
	etiqueta TEXT NOT NULL,
	archivo_diccionario VARCHAR(34),
	hoja VARCHAR(32),
	variable_diccionario VARCHAR(30),
	procedencia VARCHAR(18) NOT NULL,
	posicion SMALLINT NOT NULL,
	tipo_postgresql VARCHAR(31) NOT NULL,
	admite_nulos BOOLEAN NOT NULL,
	CONSTRAINT pk_diccionario_variables PRIMARY KEY (esquema, tabla, variable),
	CONSTRAINT uq_diccionario_variables_posicion UNIQUE (esquema, tabla, posicion),
	CONSTRAINT ck_diccionario_formulario CHECK (formulario IN ('f1','f2','f3') AND formulario=split_part(tabla,'_',1)),
	CONSTRAINT ck_diccionario_etiqueta_posicion CHECK (length(btrim(etiqueta))>0 AND posicion>0),
	CONSTRAINT ck_diccionario_procedencia CHECK ((procedencia='excel' AND archivo_diccionario IS NOT NULL AND hoja IS NOT NULL AND variable_diccionario IS NOT NULL) OR (procedencia='derivada' AND archivo_diccionario IS NULL AND hoja IS NULL AND variable_diccionario IS NULL))
);
CREATE TABLE IF NOT EXISTS endi.diccionario_restricciones (
	esquema VARCHAR(14) NOT NULL,
	tabla VARCHAR(27) NOT NULL,
	restriccion VARCHAR(48) NOT NULL,
	tipo_restriccion VARCHAR(21) NOT NULL,
	variable VARCHAR(24) NOT NULL,
	posicion SMALLINT NOT NULL,
	tabla_referencia VARCHAR(21),
	variable_referencia VARCHAR(18),
	definicion TEXT NOT NULL,
	CONSTRAINT pk_diccionario_restricciones PRIMARY KEY (esquema, tabla, restriccion, variable),
	CONSTRAINT uq_diccionario_restriccion_posicion UNIQUE (esquema, tabla, restriccion, posicion),
	CONSTRAINT fk_diccionario_restricciones_variable FOREIGN KEY(esquema, tabla, variable) REFERENCES endi.diccionario_variables (esquema, tabla, variable) ON DELETE RESTRICT,
	CONSTRAINT fk_diccionario_restricciones_referencia FOREIGN KEY(esquema, tabla_referencia, variable_referencia) REFERENCES endi.diccionario_variables (esquema, tabla, variable) ON DELETE RESTRICT,
	CONSTRAINT ck_diccionario_tipo_posicion CHECK (tipo_restriccion IN ('PRIMARY KEY','FOREIGN KEY','UNIQUE','CHECK','NOT NULL') AND posicion>0),
	CONSTRAINT ck_diccionario_referencia CHECK ((tipo_restriccion='FOREIGN KEY' AND tabla_referencia IS NOT NULL AND variable_referencia IS NOT NULL) OR (tipo_restriccion<>'FOREIGN KEY' AND tabla_referencia IS NULL AND variable_referencia IS NULL))
);
CREATE OR REPLACE FUNCTION endi.validar_columna_diccionario() RETURNS trigger
        LANGUAGE plpgsql AS $func$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_attribute a
            JOIN pg_catalog.pg_class t ON t.oid=a.attrelid
            JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace
            WHERE n.nspname=NEW.esquema AND t.relname=NEW.tabla AND a.attname=NEW.variable
            AND a.attnum=NEW.posicion AND a.attnum>0 AND NOT a.attisdropped
            AND pg_catalog.format_type(a.atttypid,a.atttypmod)=NEW.tipo_postgresql
            AND (NOT a.attnotnull)=NEW.admite_nulos
            AND (a.attgenerated<>'')=(NEW.procedencia='derivada')) THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='Columna inexistente o metadatos físicos incoherentes: '||NEW.tabla||'.'||NEW.variable;
        END IF; RETURN NEW; END $func$;
CREATE OR REPLACE FUNCTION endi.validar_restriccion_diccionario() RETURNS trigger
        LANGUAGE plpgsql AS $func$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM (SELECT n.nspname AS esquema, t.relname AS tabla, c.conname AS restriccion,
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
    LEFT JOIN pg_catalog.pg_attribute ar ON ar.attrelid=tr.oid AND ar.attnum=c.confkey[k.orden::int] WHERE n.nspname=NEW.esquema AND t.relname=NEW.tabla
        AND c.conname=NEW.restriccion AND a.attname=NEW.variable AND c.contype IN ('p','f','u','c','n')) r
            WHERE r.tipo_restriccion=NEW.tipo_restriccion AND r.posicion=NEW.posicion
            AND r.tabla_referencia IS NOT DISTINCT FROM NEW.tabla_referencia
            AND r.variable_referencia IS NOT DISTINCT FROM NEW.variable_referencia
            AND (r.esquema_referencia IS NULL OR r.esquema_referencia=NEW.esquema)
            AND r.definicion=NEW.definicion) THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='Restricción inexistente o vínculo de columna incoherente: '||NEW.restriccion;
        END IF; RETURN NEW; END $func$;
DROP TRIGGER IF EXISTS ct_diccionario_columna ON endi.diccionario_variables;
CREATE CONSTRAINT TRIGGER ct_diccionario_columna AFTER INSERT OR UPDATE
            ON endi.diccionario_variables DEFERRABLE INITIALLY IMMEDIATE
            FOR EACH ROW EXECUTE FUNCTION endi.validar_columna_diccionario();
DROP TRIGGER IF EXISTS ct_diccionario_restriccion ON endi.diccionario_restricciones;
CREATE CONSTRAINT TRIGGER ct_diccionario_restriccion AFTER INSERT OR UPDATE
            ON endi.diccionario_restricciones DEFERRABLE INITIALLY IMMEDIATE
            FOR EACH ROW EXECUTE FUNCTION endi.validar_restriccion_diccionario();
CREATE INDEX IF NOT EXISTS ix_diccionario_restricciones_variable ON endi.diccionario_restricciones (esquema,tabla,variable);
CREATE INDEX IF NOT EXISTS ix_diccionario_restricciones_referencia ON endi.diccionario_restricciones (esquema,tabla_referencia,variable_referencia);
CREATE OR REPLACE VIEW endi.v_diccionario_variables AS SELECT d.*,
            COALESCE(r.es_pk,false) AS es_pk, COALESCE(r.es_fk,false) AS es_fk,
            COALESCE(r.es_unique,false) AS es_unique, r.restricciones
            FROM endi.diccionario_variables d LEFT JOIN LATERAL (
                SELECT bool_or(tipo_restriccion='PRIMARY KEY') AS es_pk,
                    bool_or(tipo_restriccion='FOREIGN KEY') AS es_fk,
                    bool_or(tipo_restriccion='UNIQUE') AS es_unique,
                    string_agg(DISTINCT restriccion, ', ' ORDER BY restriccion) AS restricciones
                FROM endi.diccionario_restricciones x
                WHERE (x.esquema,x.tabla,x.variable)=(d.esquema,d.tabla,d.variable)
            ) r ON true;
COMMIT;
