"""Catálogo INEC 2026 verticalizado; mapeo y carga explícita en catalogos.dpa_inec."""

import argparse
import hashlib
from importlib import import_module
import json
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd
from sqlalchemy import CheckConstraint, Column, MetaData, PrimaryKeyConstraint, Table, inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.schema import CreateTable

mapeo = import_module('02_MAPEO_POSTGRESQL')
RAIZ = Path(__file__).resolve().parents[1]


def configuracion(raiz):
    return json.loads((Path(raiz)/'05_CONFIGURACIONES/01_PROYECTO.json').read_text(encoding='utf-8'))


def preparar(raiz=RAIZ, descargar=False):
    """Valida el Excel fijado, verticaliza sus niveles y mapea las tres columnas."""
    config = configuracion(raiz)
    cat = config['catalogo_dpa']
    archivo = Path(raiz)/config['rutas']['fuentes']/cat['archivo']
    if not archivo.exists() and descargar:
        datos = urlopen(Request(cat['url'], headers={'User-Agent':'Mozilla/5.0'}), timeout=60).read()
        if hashlib.sha256(datos).hexdigest() != cat['sha256']:
            raise ValueError('La descarga cambió; no se aprueba automáticamente otra edición.')
        archivo.parent.mkdir(parents=True, exist_ok=True)
        with archivo.open('xb') as salida:
            salida.write(datos)
    if not archivo.is_file() or hashlib.sha256(archivo.read_bytes()).hexdigest() != cat['sha256']:
        raise ValueError(f'Falta el Excel aprobado o cambió su hash: {archivo.name}')
    hojas = mapeo.leer_fuente(archivo, header=1, dtype='string', keep_default_na=False)
    registros = {}
    excluidos = set(cat['codigos_excluidos'])
    for hoja, codigo, etiqueta, tipo, longitud in (
        ('PROVINCIAS','DPA_PROVIN','DPA_DESPRO','PROVINCIA',2),
        ('CANTONES','DPA_CANTON','DPA_DESCAN','CANTON',4),
        ('PARROQUIAS','DPA_PARROQ','DPA_DESPAR','PARROQUIA',6),
        ('PARROQUIAS','DPA_PARURB','DPA_DESPARURB','PARROQUIA',6),
    ):
        df = hojas[hoja]
        for cod, nombre in df[[codigo,etiqueta]].itertuples(index=False,name=None):
            cod, nombre = cod.strip(), nombre.strip()
            if not cod:
                if nombre:
                    raise ValueError(f'{hoja}: descripción sin código: {nombre}')
                continue
            if not cod.isascii() or not cod.isdecimal() or len(cod) != longitud or not nombre:
                raise ValueError(f'{hoja}: código o descripción inválidos: {cod!r}, {nombre!r}')
            if cod in excluidos:
                continue
            fila = (cod,tipo,nombre)
            if cod in registros and registros[cod] != fila:
                raise ValueError(f'Descripciones incompatibles para {cod}.')
            registros[cod] = fila
    for cod,tipo,_ in registros.values():
        if tipo != 'PROVINCIA' and registros.get(cod[:2], (None,None))[1] != 'PROVINCIA':
            raise ValueError(f'Provincia padre inexistente: {cod}')
        if tipo == 'PARROQUIA' and registros.get(cod[:4], (None,None))[1] != 'CANTON':
            raise ValueError(f'Cantón padre inexistente: {cod}')
    df = pd.DataFrame(sorted(registros.values()), columns=['pk_dpa','tipo_dpa','descripcion_dpa'])
    conteos = {k:int(v) for k,v in df.tipo_dpa.value_counts().items()}
    if conteos != cat['conteos']:
        raise ValueError(f'Conteos distintos de la entrega aprobada: {conteos}')
    return mapeo.mapear_dataframe(df, {'pk_dpa':'VARCHAR(6)','descripcion_dpa':'TEXT'}, margen=10)


def tabla_catalogo(tipos, esquema='catalogos'):
    if esquema != 'catalogos':
        raise ValueError('El catálogo autorizado pertenece a catalogos.')
    return Table('dpa_inec', MetaData(),
        *(Column(c,t,nullable=False) for c,t in tipos.items()),
        PrimaryKeyConstraint('pk_dpa',name='pk_dpa_inec'),
        CheckConstraint("(tipo_dpa='PROVINCIA' AND pk_dpa ~ '^[0-9]{2}$') OR "
                        "(tipo_dpa='CANTON' AND pk_dpa ~ '^[0-9]{4}$') OR "
                        "(tipo_dpa='PARROQUIA' AND pk_dpa ~ '^[0-9]{6}$')",name='ck_dpa_inec_tipo_codigo'),
        CheckConstraint('length(btrim(descripcion_dpa))>0',name='ck_dpa_inec_descripcion'),
        schema=esquema)


def generar_artefactos(raiz, preparados):
    config = configuracion(raiz)
    cat = config['catalogo_dpa']
    df, tipos, columnas = preparados
    tabla = tabla_catalogo(tipos)
    ddl = str(CreateTable(tabla,if_not_exists=True).compile(dialect=postgresql.dialect())).strip()
    literal = lambda valor: "'"+valor.replace("'","''")+"'"
    valores = ',\n'.join('('+','.join(literal(v) for v in fila)+')'
                         for fila in df.itertuples(index=False,name=None))
    sql = f"""-- CATÁLOGO DPA INEC {cat['edicion']}; corte {cat['corte']}.
-- Fuente: {cat['url']}
-- SHA-256 Excel: {cat['sha256']}
-- Tres niveles ordinarios; excluye zonas en estudio documentadas en el módulo 12.
-- Incluye cabeceras cantonales (50), parroquias rurales y urbanas desagregadas.
BEGIN;
SET LOCAL standard_conforming_strings=on;
SET LOCAL lock_timeout='10s';
DO $guard$ BEGIN
 IF current_database()<>'research_lab' THEN RAISE EXCEPTION 'Base distinta de research_lab'; END IF;
END $guard$;
CREATE SCHEMA IF NOT EXISTS catalogos;
{ddl};
LOCK TABLE catalogos.dpa_inec IN SHARE ROW EXCLUSIVE MODE;
DO $estructura$ BEGIN
 IF (SELECT count(*) FROM pg_catalog.pg_constraint WHERE conrelid='catalogos.dpa_inec'::regclass
  AND conname IN ('pk_dpa_inec','ck_dpa_inec_tipo_codigo','ck_dpa_inec_descripcion')
  AND convalidated AND conenforced)<>3 THEN
  RAISE EXCEPTION 'Faltan restricciones validadas del catálogo';
 END IF;
 IF (SELECT count(*) FROM pg_catalog.pg_attribute WHERE attrelid='catalogos.dpa_inec'::regclass
  AND attnum>0 AND NOT attisdropped)<>3 OR
 (SELECT count(*) FROM pg_catalog.pg_attribute a JOIN (VALUES
  ('pk_dpa','character varying(6)'),('tipo_dpa','character varying(19)'),('descripcion_dpa','text')) e(nombre,tipo)
  ON a.attname=e.nombre AND pg_catalog.format_type(a.atttypid,a.atttypmod)=e.tipo
  WHERE a.attrelid='catalogos.dpa_inec'::regclass AND a.attnotnull AND NOT a.attisdropped)<>3 THEN
  RAISE EXCEPTION 'Estructura existente distinta del mapeo; requiere migración explícita';
 END IF;
END $estructura$;
INSERT INTO catalogos.dpa_inec (pk_dpa,tipo_dpa,descripcion_dpa) VALUES
{valores}
ON CONFLICT (pk_dpa) DO UPDATE SET
 tipo_dpa=EXCLUDED.tipo_dpa,descripcion_dpa=EXCLUDED.descripcion_dpa
WHERE (dpa_inec.tipo_dpa,dpa_inec.descripcion_dpa)
 IS DISTINCT FROM (EXCLUDED.tipo_dpa,EXCLUDED.descripcion_dpa);
COMMENT ON TABLE catalogos.dpa_inec IS 'INEC CGE 2026, corte 2025-12-31; códigos ordinarios de 2/4/6 dígitos. No sustituye versiones históricas ENDI.';
COMMENT ON COLUMN catalogos.dpa_inec.pk_dpa IS 'Código oficial DPA como texto: provincia 2, cantón 4, parroquia/cabecera 6 dígitos. Conserva ceros iniciales.';
COMMENT ON COLUMN catalogos.dpa_inec.tipo_dpa IS 'Nivel del código: PROVINCIA, CANTON o PARROQUIA. El nivel parroquial incluye cabeceras cantonales, rurales y urbanas.';
COMMENT ON COLUMN catalogos.dpa_inec.descripcion_dpa IS 'Denominación oficial de las hojas detalladas PROVINCIAS, CANTONES y PARROQUIAS del Excel INEC 2026.';
DO $check$ BEGIN
 IF (SELECT count(*) FROM catalogos.dpa_inec)<>{len(df)} THEN
  RAISE EXCEPTION 'Conteo distinto de la entrega; no se borran filas ajenas';
 END IF;
 IF EXISTS (SELECT 1 FROM catalogos.dpa_inec h WHERE
  (h.tipo_dpa<>'PROVINCIA' AND NOT EXISTS (SELECT 1 FROM catalogos.dpa_inec p WHERE p.pk_dpa=left(h.pk_dpa,2) AND p.tipo_dpa='PROVINCIA')) OR
  (h.tipo_dpa='PARROQUIA' AND NOT EXISTS (SELECT 1 FROM catalogos.dpa_inec p WHERE p.pk_dpa=left(h.pk_dpa,4) AND p.tipo_dpa='CANTON')))
 THEN RAISE EXCEPTION 'Falta provincia o cantón padre'; END IF;
END $check$;
SELECT tipo_dpa,count(*) AS registros FROM catalogos.dpa_inec GROUP BY tipo_dpa ORDER BY tipo_dpa;
COMMIT;
"""
    destino = Path(raiz)/cat['sql']
    destino.parent.mkdir(parents=True,exist_ok=True)
    destino.write_text('\n'.join(l.rstrip() for l in sql.splitlines())+'\n',encoding='utf-8',newline='\n')
    pd.DataFrame(columnas).to_csv(Path(raiz)/cat['mapeo'],index=False,encoding='utf-8-sig',lineterminator='\n')
    return destino


def cargar(raiz, preparados, conexion):
    """UPSERT y verificación integral en la transacción recibida; sin commit propio."""
    config = configuracion(raiz)
    if not conexion.in_transaction() or conexion.exec_driver_sql('SELECT current_database()').scalar_one() != config['postgresql']['base']:
        raise ValueError('La carga requiere una transacción en research_lab.')
    df,tipos,_ = preparados
    tabla = tabla_catalogo(tipos)
    conexion.exec_driver_sql("SET LOCAL lock_timeout='10s'")
    conexion.exec_driver_sql('CREATE SCHEMA IF NOT EXISTS catalogos')
    tabla.metadata.create_all(conexion)
    conexion.exec_driver_sql('LOCK TABLE catalogos.dpa_inec IN SHARE ROW EXCLUSIVE MODE')
    reales = inspect(conexion).get_columns('dpa_inec',schema='catalogos')
    if {c['name']:str(c['type']) for c in reales} != {c:str(t) for c,t in tipos.items()} or any(c['nullable'] for c in reales):
        raise ValueError('Estructura existente distinta del mapeo; se requiere migración explícita.')
    pk = inspect(conexion).get_pk_constraint('dpa_inec',schema='catalogos')
    checks = inspect(conexion).get_check_constraints('dpa_inec',schema='catalogos')
    if pk['constrained_columns'] != ['pk_dpa'] or {c['name'] for c in checks} != {'ck_dpa_inec_tipo_codigo','ck_dpa_inec_descripcion'}:
        raise ValueError('Faltan las restricciones del catálogo.')
    sentencia = insert(tabla)
    sentencia = sentencia.on_conflict_do_update(index_elements=[tabla.c.pk_dpa],
        set_={'tipo_dpa':sentencia.excluded.tipo_dpa,'descripcion_dpa':sentencia.excluded.descripcion_dpa},
        where=tabla.c.tipo_dpa.is_distinct_from(sentencia.excluded.tipo_dpa) |
              tabla.c.descripcion_dpa.is_distinct_from(sentencia.excluded.descripcion_dpa))
    conexion.execute(sentencia,df.to_dict(orient='records'))
    esperadas = list(df.itertuples(index=False,name=None))
    reales = [tuple(f) for f in conexion.exec_driver_sql('SELECT pk_dpa,tipo_dpa,descripcion_dpa FROM catalogos.dpa_inec ORDER BY pk_dpa')]
    if reales != esperadas:
        raise ValueError('Contenido distinto del catálogo aprobado; la transacción se revierte sin borrar filas ajenas.')
    # Reutilizar los comentarios del SQL exportado conserva exactamente su documentación.
    for linea in (Path(raiz)/config['catalogo_dpa']['sql']).read_text(encoding='utf-8').splitlines():
        if linea.startswith('COMMENT ON '):
            conexion.exec_driver_sql(linea)
    return {'base':'research_lab','tabla':'catalogos.dpa_inec','edicion':2026,
            'conteos':config['catalogo_dpa']['conteos'],'total':len(df),'contenido_verificado':True,
            'sha256_contenido':hashlib.sha256(json.dumps(reales,ensure_ascii=False).encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cargar',action='store_true',help='Carga explícitamente el catálogo; sin esta opción solo genera SQL/mapeo.')
    parser.add_argument('--descargar',action='store_true',help='Descarga el Excel oficial fijado solamente si falta la copia local.')
    args = parser.parse_args()
    preparados = preparar(RAIZ,args.descargar)
    destino = generar_artefactos(RAIZ,preparados)
    if not args.cargar:
        print(f'Mapeo y SQL generados: {destino.relative_to(RAIZ)}. Sin escritura PostgreSQL.')
        return
    motor = import_module('01_ETL_FUENTES').ETL_ENDI().engine
    try:
        with motor.begin() as conexion:
            resultado = cargar(RAIZ,preparados,conexion)
        reporte = RAIZ/configuracion(RAIZ)['catalogo_dpa']['validacion']
        reporte.parent.mkdir(parents=True,exist_ok=True)
        reporte.write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps(resultado,ensure_ascii=False,indent=2))
    finally:
        motor.dispose()


if __name__ == '__main__':
    main()
