"""Diccionario ENDI consolidado y vínculos verificables con columnas y restricciones."""

import argparse
import hashlib
from importlib import import_module
import json
from pathlib import Path

import pandas as pd
from psycopg import sql
from sqlalchemy import (CheckConstraint, Column, ForeignKeyConstraint, MetaData,
                        PrimaryKeyConstraint, Table, UniqueConstraint, inspect, text)
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

mapeo = import_module('02_MAPEO_POSTGRESQL')
modelo = import_module('05_MODELO_RELACIONAL')

CONSULTA_COLUMNAS = '''SELECT n.nspname AS esquema, t.relname AS tabla, a.attname AS variable,
    a.attnum AS posicion, pg_catalog.format_type(a.atttypid,a.atttypmod) AS tipo_postgresql,
    NOT a.attnotnull AS admite_nulos
    FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class t ON t.oid=a.attrelid
    JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace
    WHERE n.nspname=:esquema AND t.relname=ANY(:tablas)
      AND a.attnum>0 AND NOT a.attisdropped ORDER BY t.relname,a.attnum'''

BASE_RESTRICCIONES = '''SELECT n.nspname AS esquema, t.relname AS tabla, c.conname AS restriccion,
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
    LEFT JOIN pg_catalog.pg_attribute ar ON ar.attrelid=tr.oid AND ar.attnum=c.confkey[k.orden::int]'''


def leer_excel(raiz, esquema='endi'):
    """Lee todas las hojas declaradas, verifica hashes y conserva nombres y etiquetas originales."""
    raiz = Path(raiz)
    config = json.loads((raiz/'05_CONFIGURACIONES/01_PROYECTO.json').read_text(encoding='utf-8'))
    registros = []
    esperadas = {f['tabla'] for f in config['fuentes']}
    for entrada in config['diccionarios']:
        archivo = raiz/config['rutas']['fuentes']/entrada['archivo']
        if hashlib.sha256(archivo.read_bytes()).hexdigest() != entrada['sha256']:
            raise ValueError(f'{archivo.name}: el diccionario difiere de la entrega aprobada.')
        for hoja, df in mapeo.leer_fuente(archivo, dtype='string').items():
            df.columns = df.columns.str.strip()
            if not {'Variable', 'Etiqueta'}.issubset(df.columns):
                raise ValueError(f'{hoja}: faltan columnas Variable/Etiqueta.')
            tabla = 'f3_desarrollo_inf' if hoja == 'f3_desarrollo_infantil' else hoja
            if tabla not in esperadas:
                raise ValueError(f'Hoja no declarada: {hoja}')
            aliases = {v: k for k, v in config.get('aliases_etiquetas', {}).get(tabla, {}).items()}
            for variable, etiqueta in df[['Variable', 'Etiqueta']].itertuples(index=False, name=None):
                if pd.isna(variable) or pd.isna(etiqueta) or not variable.strip() or not etiqueta.strip():
                    raise ValueError(f'{hoja}: nombre o etiqueta vacíos; no se eliminan filas silenciosamente.')
                original = variable.strip()
                registros.append({'esquema': esquema, 'tabla': tabla, 'variable': aliases.get(original, original),
                    'formulario': tabla.split('_')[0], 'etiqueta': etiqueta,
                    'archivo_diccionario': archivo.name, 'hoja': hoja,
                    'variable_diccionario': original, 'procedencia': 'excel'})
    df = pd.DataFrame(registros)
    if df.empty or set(df.tabla) != esperadas or df.duplicated(['esquema','tabla','variable']).any():
        raise ValueError('El diccionario no cubre las seis tablas o contiene variables duplicadas.')
    return df


def preparar(raiz, conexion, esquema='endi'):
    modelo.identificador(esquema)
    etiquetas = leer_excel(raiz, esquema)
    derivada = {'esquema': esquema, 'tabla': 'f2_salud_ninez', 'variable': 'id_per_miembro',
        'formulario': 'f2', 'etiqueta': 'Identificador de persona miembro del hogar; NULL para no miembros con id_per terminado en 77.',
        'archivo_diccionario': None, 'hoja': None, 'variable_diccionario': None, 'procedencia': 'derivada'}
    etiquetas = pd.concat([etiquetas, pd.DataFrame([derivada])], ignore_index=True)
    parametros = {'esquema': esquema, 'tablas': list(modelo.TABLAS)}
    columnas = pd.DataFrame([dict(r) for r in conexion.execute(text(CONSULTA_COLUMNAS), parametros).mappings()])
    df = etiquetas.merge(columnas, on=['esquema','tabla','variable'], how='outer', validate='one_to_one', indicator=True)
    if (df['_merge'] != 'both').any():
        faltan = df.loc[df['_merge'] != 'both', ['tabla','variable','_merge']].to_dict(orient='records')
        raise ValueError(f'Columnas físicas y diccionario no coinciden: {faltan}')
    df = df.drop(columns='_merge').sort_values(['tabla','posicion']).reset_index(drop=True)
    consulta = BASE_RESTRICCIONES+''' WHERE n.nspname=:esquema AND t.relname=ANY(:tablas)
        AND c.contype IN ('p','f','u','c','n') ORDER BY t.relname,c.conname,k.orden'''
    relaciones = pd.DataFrame([dict(r) for r in conexion.execute(text(consulta), parametros).mappings()])
    if relaciones.empty:
        raise ValueError('No hay restricciones del modelo para documentar; aplicar el modelo primero.')
    externas = relaciones[relaciones.esquema_referencia.notna() & (relaciones.esquema_referencia != esquema)]
    if not externas.empty:
        raise ValueError('El modelo ENDI de este diccionario no admite referencias a otro esquema.')
    relaciones = relaciones.drop(columns='esquema_referencia')
    resultados = {}
    for nombre, datos, textos in [('diccionario_variables', df, {'etiqueta':'TEXT'}),
                                  ('diccionario_restricciones', relaciones, {'definicion':'TEXT'})]:
        for columna in datos:
            if columna not in ('posicion','admite_nulos'):
                datos[columna] = datos[columna].astype('string')
        declaraciones = dict(textos, posicion='SMALLINT')
        if 'admite_nulos' in datos:
            declaraciones['admite_nulos'] = 'BOOLEAN'
        resultados[nombre] = mapeo.mapear_dataframe(datos, declaraciones=declaraciones, margen=10)
    return resultados


def tablas_metadatos(preparados, esquema='endi'):
    modelo.identificador(esquema)
    metadata = MetaData()
    variables = Table('diccionario_variables', metadata,
        *(Column(c, t, nullable=c in ('archivo_diccionario','hoja','variable_diccionario'))
          for c,t in preparados['diccionario_variables'][1].items()),
        PrimaryKeyConstraint('esquema','tabla','variable', name='pk_diccionario_variables'),
        UniqueConstraint('esquema','tabla','posicion', name='uq_diccionario_variables_posicion'),
        CheckConstraint("formulario IN ('f1','f2','f3') AND formulario=split_part(tabla,'_',1)", name='ck_diccionario_formulario'),
        CheckConstraint("length(btrim(etiqueta))>0 AND posicion>0", name='ck_diccionario_etiqueta_posicion'),
        CheckConstraint("(procedencia='excel' AND archivo_diccionario IS NOT NULL AND hoja IS NOT NULL AND variable_diccionario IS NOT NULL) OR "
                        "(procedencia='derivada' AND archivo_diccionario IS NULL AND hoja IS NULL AND variable_diccionario IS NULL)", name='ck_diccionario_procedencia'),
        schema=esquema)
    Table('diccionario_restricciones', metadata,
        *(Column(c, t, nullable=c in ('tabla_referencia','variable_referencia'))
          for c,t in preparados['diccionario_restricciones'][1].items()),
        PrimaryKeyConstraint('esquema','tabla','restriccion','variable', name='pk_diccionario_restricciones'),
        UniqueConstraint('esquema','tabla','restriccion','posicion', name='uq_diccionario_restriccion_posicion'),
        ForeignKeyConstraint(['esquema','tabla','variable'],
            [variables.c.esquema,variables.c.tabla,variables.c.variable],
            name='fk_diccionario_restricciones_variable', ondelete='RESTRICT'),
        ForeignKeyConstraint(['esquema','tabla_referencia','variable_referencia'],
            [variables.c.esquema,variables.c.tabla,variables.c.variable],
            name='fk_diccionario_restricciones_referencia', ondelete='RESTRICT'),
        CheckConstraint("tipo_restriccion IN ('PRIMARY KEY','FOREIGN KEY','UNIQUE','CHECK','NOT NULL') AND posicion>0", name='ck_diccionario_tipo_posicion'),
        CheckConstraint("(tipo_restriccion='FOREIGN KEY' AND tabla_referencia IS NOT NULL AND variable_referencia IS NOT NULL) OR "
                        "(tipo_restriccion<>'FOREIGN KEY' AND tabla_referencia IS NULL AND variable_referencia IS NULL)", name='ck_diccionario_referencia'),
        schema=esquema)
    return metadata


def sql_complementario(esquema='endi'):
    modelo.identificador(esquema)
    comprobar_restriccion = BASE_RESTRICCIONES+''' WHERE n.nspname=NEW.esquema AND t.relname=NEW.tabla
        AND c.conname=NEW.restriccion AND a.attname=NEW.variable AND c.contype IN ('p','f','u','c','n')'''
    return [f'''CREATE OR REPLACE FUNCTION {esquema}.validar_columna_diccionario() RETURNS trigger
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
        END IF; RETURN NEW; END $func$''',
        f'''CREATE OR REPLACE FUNCTION {esquema}.validar_restriccion_diccionario() RETURNS trigger
        LANGUAGE plpgsql AS $func$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM ({comprobar_restriccion}) r
            WHERE r.tipo_restriccion=NEW.tipo_restriccion AND r.posicion=NEW.posicion
            AND r.tabla_referencia IS NOT DISTINCT FROM NEW.tabla_referencia
            AND r.variable_referencia IS NOT DISTINCT FROM NEW.variable_referencia
            AND (r.esquema_referencia IS NULL OR r.esquema_referencia=NEW.esquema)
            AND r.definicion=NEW.definicion) THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='Restricción inexistente o vínculo de columna incoherente: '||NEW.restriccion;
        END IF; RETURN NEW; END $func$''',
        f'DROP TRIGGER IF EXISTS ct_diccionario_columna ON {esquema}.diccionario_variables',
        f'''CREATE CONSTRAINT TRIGGER ct_diccionario_columna AFTER INSERT OR UPDATE
            ON {esquema}.diccionario_variables DEFERRABLE INITIALLY IMMEDIATE
            FOR EACH ROW EXECUTE FUNCTION {esquema}.validar_columna_diccionario()''',
        f'DROP TRIGGER IF EXISTS ct_diccionario_restriccion ON {esquema}.diccionario_restricciones',
        f'''CREATE CONSTRAINT TRIGGER ct_diccionario_restriccion AFTER INSERT OR UPDATE
            ON {esquema}.diccionario_restricciones DEFERRABLE INITIALLY IMMEDIATE
            FOR EACH ROW EXECUTE FUNCTION {esquema}.validar_restriccion_diccionario()''',
        f'CREATE INDEX IF NOT EXISTS ix_diccionario_restricciones_variable ON {esquema}.diccionario_restricciones (esquema,tabla,variable)',
        f'CREATE INDEX IF NOT EXISTS ix_diccionario_restricciones_referencia ON {esquema}.diccionario_restricciones (esquema,tabla_referencia,variable_referencia)',
        f'''CREATE OR REPLACE VIEW {esquema}.v_diccionario_variables AS SELECT d.*,
            COALESCE(r.es_pk,false) AS es_pk, COALESCE(r.es_fk,false) AS es_fk,
            COALESCE(r.es_unique,false) AS es_unique, r.restricciones
            FROM {esquema}.diccionario_variables d LEFT JOIN LATERAL (
                SELECT bool_or(tipo_restriccion='PRIMARY KEY') AS es_pk,
                    bool_or(tipo_restriccion='FOREIGN KEY') AS es_fk,
                    bool_or(tipo_restriccion='UNIQUE') AS es_unique,
                    string_agg(DISTINCT restriccion, ', ' ORDER BY restriccion) AS restricciones
                FROM {esquema}.diccionario_restricciones x
                WHERE (x.esquema,x.tabla,x.variable)=(d.esquema,d.tabla,d.variable)
            ) r ON true''']


def generar_artefactos(raiz, preparados, esquema='endi'):
    salida = Path(raiz)/'02_DOCUMENTACION/08_MAPEO_ENDI'
    salida.mkdir(parents=True, exist_ok=True)
    metadata = tablas_metadatos(preparados, esquema)
    declaraciones = [str(CreateTable(t, if_not_exists=True).compile(dialect=postgresql.dialect())).strip()
                     for t in metadata.sorted_tables]
    (salida/'05_DICCIONARIO_POSTGRESQL.sql').write_text(
        '-- ESTRUCTURA Y VÍNCULOS DEL DICCIONARIO. La carga Excel se realiza con 07_DICCIONARIO_VARIABLES.py.\nBEGIN;\n'
        + ';\n'.join('\n'.join(linea.rstrip() for linea in sql.splitlines()) for sql in declaraciones+sql_complementario(esquema))+';\nCOMMIT;\n', encoding='utf-8', newline='\n')
    tipos = []
    for tabla, (_, _, columnas) in preparados.items():
        tipos.extend(dict(c, tabla=tabla) for c in columnas)
    pd.DataFrame(tipos).to_csv(salida/'06_MAPEO_DICCIONARIO.csv',index=False,encoding='utf-8-sig',lineterminator='\n')


def cargar_diccionario(raiz, conexion, esquema='endi'):
    """Carga metadatos y comentarios dentro de la transacción recibida, sin tocar valores fuente."""
    if not conexion.in_transaction():
        raise ValueError('El diccionario requiere una transacción activa.')
    modelo.identificador(esquema)
    conexion.exec_driver_sql("SET LOCAL lock_timeout='10s'")
    conexion.exec_driver_sql('LOCK TABLE '+', '.join(f'{esquema}.{t}' for t in modelo.TABLAS)+' IN SHARE ROW EXCLUSIVE MODE')
    preparados = preparar(raiz, conexion, esquema)
    generar_artefactos(raiz, preparados, esquema)
    metadata = tablas_metadatos(preparados, esquema)
    metadata.create_all(conexion)
    for nombre, (_, tipos, _) in preparados.items():
        reales = {c['name']:str(c['type'].compile(dialect=postgresql.dialect()))
                  for c in inspect(conexion).get_columns(nombre,schema=esquema)}
        if reales != {c:str(t.compile(dialect=postgresql.dialect())) for c,t in tipos.items()}:
            raise ValueError(f'{nombre}: estructura existente distinta del mapeo; requiere una migración explícita.')
    for sentencia in sql_complementario(esquema):
        conexion.exec_driver_sql(sentencia)
    conexion.exec_driver_sql(f'DELETE FROM {esquema}.diccionario_restricciones')
    conexion.exec_driver_sql(f'DELETE FROM {esquema}.diccionario_variables')
    for nombre, (df, _, _) in preparados.items():
        mapeo.copiar_dataframe(conexion,df,metadata.tables[f'{esquema}.{nombre}'])
        if conexion.exec_driver_sql(f'SELECT count(*) FROM {esquema}.{nombre}').scalar_one()!=len(df):
            raise ValueError(f'{nombre}: no se cargó todo el diccionario.')
    variables = preparados['diccionario_variables'][0]
    with conexion.connection.driver_connection.cursor() as cursor:
        for r in variables.itertuples(index=False):
            cursor.execute(sql.SQL('COMMENT ON COLUMN {}.{}.{} IS {}').format(
                sql.Identifier(esquema),sql.Identifier(r.tabla),sql.Identifier(r.variable),sql.Literal(r.etiqueta)))
    coincidencias = conexion.exec_driver_sql(f'''SELECT count(*) FROM {esquema}.diccionario_variables d
        JOIN pg_catalog.pg_namespace n ON n.nspname=d.esquema
        JOIN pg_catalog.pg_class t ON t.relnamespace=n.oid AND t.relname=d.tabla
        JOIN pg_catalog.pg_attribute a ON a.attrelid=t.oid AND a.attname=d.variable AND NOT a.attisdropped
        WHERE a.attnum=d.posicion AND pg_catalog.format_type(a.atttypid,a.atttypmod)=d.tipo_postgresql
        AND (NOT a.attnotnull)=d.admite_nulos AND pg_catalog.col_description(t.oid,a.attnum)=d.etiqueta''').scalar_one()
    if coincidencias!=len(variables):
        raise ValueError('El diccionario no coincide con las columnas y sus comentarios.')
    relaciones = preparados['diccionario_restricciones'][0]
    nombres = ['pk_diccionario_variables','pk_diccionario_restricciones',
               'fk_diccionario_restricciones_variable','fk_diccionario_restricciones_referencia']
    claves = conexion.execute(text('''SELECT c.conname,c.convalidated FROM pg_catalog.pg_constraint c
        JOIN pg_catalog.pg_class t ON t.oid=c.conrelid JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace
        WHERE n.nspname=:esquema AND c.conname=ANY(:nombres)'''),{'esquema':esquema,'nombres':nombres}).all()
    if len(claves)!=len(nombres) or not all(r.convalidated for r in claves):
        raise ValueError('Faltan claves validadas en las tablas de metadatos.')
    datos = {nombre: df.to_dict(orient='records') for nombre,(df,_,_) in preparados.items()}
    return {'tabla':f'{esquema}.diccionario_variables', 'variables':len(variables),
            'variables_excel':int((variables.procedencia=='excel').sum()),
            'variables_derivadas':int((variables.procedencia=='derivada').sum()),
            'tabla_vinculos':f'{esquema}.diccionario_restricciones',
            'restricciones_distintas':int(relaciones[['tabla','restriccion']].drop_duplicates().shape[0]),
            'vinculos_columna_restriccion':len(relaciones),'comentarios_verificados':coincidencias,
            'cobertura_completa':True,'pk_y_fk_metadatos_validadas':True,
            'sha256_contenido':hashlib.sha256(json.dumps(datos,sort_keys=True,ensure_ascii=False).encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cargar',action='store_true',help='Carga/actualiza el diccionario de las seis tablas ya existentes.')
    args = parser.parse_args()
    if not args.cargar:
        parser.error('Se requiere --cargar. La recarga completa lo ejecuta automáticamente.')
    raiz = Path(__file__).resolve().parents[1]
    config = json.loads((raiz/'05_CONFIGURACIONES/01_PROYECTO.json').read_text(encoding='utf-8'))
    motor = import_module('01_ETL_FUENTES').ETL_ENDI().engine
    try:
        with motor.begin() as conexion:
            if conexion.exec_driver_sql('SELECT current_database()').scalar_one()!=config['postgresql']['base']:
                raise ValueError('Base distinta de la configurada; no se carga el diccionario.')
            resultado = cargar_diccionario(raiz,conexion,config['postgresql']['esquema'])
        print(json.dumps(resultado,ensure_ascii=False,indent=2))
    finally:
        motor.dispose()


if __name__=='__main__':
    main()
