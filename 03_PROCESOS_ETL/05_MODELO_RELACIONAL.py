"""Claves y relaciones ENDI R2 según la guía, cuadros 2, 4 y 7 (pp. 9-20)."""

import argparse
import hashlib
from importlib import import_module
import json
from pathlib import Path
import re

from sqlalchemy import text


TABLAS = ('f1_hogar', 'f1_personas', 'f2_mef', 'f2_lactancia',
          'f2_salud_ninez', 'f3_desarrollo_inf')
PRIMARIAS = dict(zip(TABLAS, ('id_hogar', 'id_per', 'id_mef', 'id_per', 'id_hijo_ord', 'id_per')))
UNICAS = (
    ('f1_personas', 'mef', ('id_mef',)),
    ('f2_lactancia', 'madre', ('id_mef',)),
    ('f2_lactancia', 'mef_per', ('id_mef_per',)),
    ('f2_salud_ninez', 'miembro', ('id_per_miembro',)),
    ('f2_salud_ninez', 'madre_orden', ('id_mef', 'ord_hijo')),
    ('f3_desarrollo_inf', 'hogar', ('id_hogar',)),
    ('f3_desarrollo_inf', 'cuidador', ('id_cuid',)),
)
FORANEAS = (
    ('f1_personas', 'hogar', 'id_hogar', 'f1_hogar', 'id_hogar'),
    ('f2_mef', 'hogar', 'id_hogar', 'f1_hogar', 'id_hogar'),
    ('f2_mef', 'persona_mef', 'id_mef', 'f1_personas', 'id_mef'),
    ('f2_lactancia', 'hogar', 'id_hogar', 'f1_hogar', 'id_hogar'),
    ('f2_lactancia', 'madre', 'id_mef', 'f2_mef', 'id_mef'),
    ('f2_lactancia', 'persona', 'id_per', 'f1_personas', 'id_per'),
    ('f2_salud_ninez', 'hogar', 'id_hogar', 'f1_hogar', 'id_hogar'),
    ('f2_salud_ninez', 'madre', 'id_mef', 'f2_mef', 'id_mef'),
    ('f2_salud_ninez', 'persona_miembro', 'id_per_miembro', 'f1_personas', 'id_per'),
    ('f3_desarrollo_inf', 'hogar', 'id_hogar', 'f1_hogar', 'id_hogar'),
    ('f3_desarrollo_inf', 'persona', 'id_per', 'f1_personas', 'id_per'),
    ('f3_desarrollo_inf', 'cuidador', 'id_cuid', 'f1_personas', 'id_per'),
)
EXPRESION_MIEMBRO = "CASE WHEN right(id_per::text, 2) = '77'::text THEN NULL::text ELSE id_per::text END"


def identificador(valor):
    if not re.fullmatch(r'[a-z_][a-z_0-9]{0,62}', valor):
        raise ValueError(f'Identificador no admitido: {valor!r}')
    return valor


def reglas_modelo():
    """Devuelve declaraciones únicas del modelo, reutilizadas por SQL y ejecución."""
    reglas = []
    for tabla, clave in PRIMARIAS.items():
        reglas.append((tabla, f'pk_{tabla}', 'p', f'PRIMARY KEY ({clave})'))
    for tabla, sufijo, columnas in UNICAS:
        reglas.append((tabla, f'uq_{tabla}_{sufijo}', 'u', f"UNIQUE ({', '.join(columnas)})"))
    for tabla in TABLAS:
        condiciones = ["id_upm ~ '^[0-9]{10}$'", "id_viv ~ '^[0-9]{12}$'",
                       "id_hogar ~ '^[0-9]{14}$'", 'left(id_viv, 10) = id_upm',
                       'left(id_hogar, 12) = id_viv']
        roles = [] if tabla == 'f1_hogar' else (['id_mef'] if tabla == 'f2_mef' else ['id_per'])
        if tabla in ('f1_personas', 'f2_lactancia', 'f2_salud_ninez'):
            roles.append('id_mef')
        if tabla == 'f3_desarrollo_inf':
            roles.append('id_cuid')
        for rol in roles:
            condiciones.append(f"({rol} IS NULL OR ({rol} ~ '^[0-9]{{16}}$' AND left({rol}, 14) = id_hogar))")
        reglas.append((tabla, f'ck_{tabla}_identificadores', 'c', 'CHECK ('+' AND '.join(condiciones)+')'))
    extras = (
        ('f1_personas', 'mef_persona', 'id_mef IS NULL OR id_mef = id_per'),
        ('f2_lactancia', 'mef_per', 'id_mef_per = id_mef || right(id_per, 2)'),
        ('f2_salud_ninez', 'mef_per', 'id_mef_per = id_mef || right(id_per, 2)'),
        ('f2_salud_ninez', 'hijo_orden', "ord_hijo IN ('01', '02') AND id_hijo_ord = id_mef_per || ord_hijo"),
        ('f3_desarrollo_inf', 'cuidador_distinto', 'id_cuid <> id_per'),
    )
    for tabla, sufijo, expresion in extras:
        reglas.append((tabla, f'ck_{tabla}_{sufijo}', 'c', f'CHECK ({expresion})'))
    return reglas


def columnas_obligatorias():
    columnas = {t: ['id_upm', 'id_viv', 'id_hogar'] for t in TABLAS}
    for tabla, clave in PRIMARIAS.items():
        if clave not in columnas[tabla]:
            columnas[tabla].append(clave)
    columnas['f2_lactancia'] += ['id_mef', 'id_mef_per']
    columnas['f2_salud_ninez'] += ['id_per', 'id_mef', 'id_mef_per', 'ord_hijo']
    columnas['f3_desarrollo_inf'] += ['id_cuid']
    return columnas


def sentencias_modelo(esquema='endi'):
    """SQL determinista, repetible sobre las seis tablas; sin CASCADE ni cambios de datos."""
    identificador(esquema)
    reglas = reglas_modelo()
    fks = [(t, f'fk_{t}_{s}', 'f',
            f'FOREIGN KEY ({c}) REFERENCES {esquema}.{p} ({k}) ON UPDATE NO ACTION ON DELETE RESTRICT')
           for t, s, c, p, k in FORANEAS]
    sentencias = ["SET LOCAL lock_timeout = '10s'",
                  'LOCK TABLE '+', '.join(f'{esquema}.{t}' for t in TABLAS)+' IN SHARE ROW EXCLUSIVE MODE']
    # Retirar únicamente las restricciones de este modelo; dependencias ajenas bloquean RESTRICT.
    for tabla, nombre, _, _ in fks + [r for r in reglas if r[2] != 'p'] + [r for r in reglas if r[2] == 'p']:
        sentencias.append(f'ALTER TABLE {esquema}.{tabla} DROP CONSTRAINT IF EXISTS {nombre} RESTRICT')
    sentencias.append(f'ALTER TABLE {esquema}.f2_salud_ninez ADD COLUMN IF NOT EXISTS '
                      f'id_per_miembro TEXT GENERATED ALWAYS AS ({EXPRESION_MIEMBRO}) STORED')
    for tabla, columnas in columnas_obligatorias().items():
        sentencias.append(f'ALTER TABLE {esquema}.{tabla} '+', '.join(f'ALTER COLUMN {c} SET NOT NULL' for c in columnas))
    for tabla, nombre, _, definicion in reglas + fks:
        sentencias.append(f'ALTER TABLE {esquema}.{tabla} ADD CONSTRAINT {nombre} {definicion}')
    for tabla in ('f1_personas', 'f2_mef', 'f2_lactancia', 'f2_salud_ninez'):
        sentencias.append(f'CREATE INDEX IF NOT EXISTS ix_{tabla}_id_hogar ON {esquema}.{tabla} (id_hogar)')
    sentencias.append(f"COMMENT ON COLUMN {esquema}.f2_salud_ninez.id_per_miembro IS "
                      "'Derivada ENDI: NULL para id_per terminado en 77 (no miembro); conserva id_per original y habilita FK a Personas.'")
    return sentencias


def generar_sql(raiz, esquema='endi'):
    salida = Path(raiz)/'02_DOCUMENTACION/08_MAPEO_ENDI/04_RESTRICCIONES_POSTGRESQL.sql'
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text('-- MODELO ENDI R2. Guía pp. 9-20. Ejecutar en research_lab sobre las seis fuentes.\n'
                      '-- No elimina filas ni usa CASCADE. Cualquier error revierte la transacción.\nBEGIN;\n'
                      + ';\n'.join(sentencias_modelo(esquema))+';\nCOMMIT;\n', encoding='utf-8', newline='\n')
    return salida


def verificar_modelo(conexion, esquema='endi'):
    """Comprueba catálogo, validación de restricciones y columna calculada, sin escribir."""
    identificador(esquema)
    esperadas = {nombre: (tabla, tipo) for tabla, nombre, tipo, _ in reglas_modelo()}
    esperadas.update({f'fk_{t}_{s}': (t, 'f') for t, s, _, _, _ in FORANEAS})
    filas = conexion.execute(text('''SELECT t.relname AS tabla, c.conname AS nombre,
        c.contype AS tipo, c.convalidated AS validada, pg_get_constraintdef(c.oid) AS definicion
        FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid
        JOIN pg_namespace n ON n.oid=t.relnamespace
        WHERE n.nspname=:esquema AND c.contype IN ('p','f','u','c') ORDER BY t.relname,c.conname'''),
        {'esquema': esquema}).mappings().all()
    existentes = {f['nombre']: f for f in filas}
    for nombre, (tabla, tipo) in esperadas.items():
        fila = existentes.get(nombre)
        if not fila or (fila['tabla'], fila['tipo'], fila['validada']) != (tabla, tipo, True):
            raise ValueError(f'Falta una restricción válida del modelo: {nombre}')
    generada = conexion.execute(text('''SELECT a.attgenerated, format_type(a.atttypid,a.atttypmod) AS tipo,
        pg_get_expr(d.adbin,d.adrelid) AS expresion FROM pg_attribute a
        JOIN pg_class t ON t.oid=a.attrelid JOIN pg_namespace n ON n.oid=t.relnamespace
        JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
        WHERE n.nspname=:esquema AND t.relname='f2_salud_ninez' AND a.attname='id_per_miembro' '''),
        {'esquema': esquema}).mappings().one()
    normalizar = lambda s: re.sub(r'[\s()"]', '', s).lower().replace('::text', '')
    if generada['attgenerated'] != 's' or generada['tipo'] != 'text' or normalizar(generada['expresion']) != normalizar(EXPRESION_MIEMBRO):
        raise ValueError('La columna id_per_miembro no corresponde a la regla calculada del manual.')
    for tabla, columnas in columnas_obligatorias().items():
        obligatorias = set(conexion.execute(text('''SELECT column_name FROM information_schema.columns
            WHERE table_schema=:esquema AND table_name=:tabla AND is_nullable='NO' '''),
            {'esquema': esquema, 'tabla': tabla}).scalars())
        if not set(columnas).issubset(obligatorias):
            raise ValueError(f'{tabla}: faltan columnas NOT NULL del modelo.')
    seleccion = [dict(existentes[n]) for n in sorted(esperadas)]
    conteos = {tipo: sum(f['tipo'] == tipo for f in seleccion) for tipo in ('p', 'f', 'u', 'c')}
    return {'pk': conteos['p'], 'fk': conteos['f'], 'unique': conteos['u'], 'check': conteos['c'],
            'todas_validadas': True, 'columna_derivada': 'f2_salud_ninez.id_per_miembro',
            'variables_fuente': 1423, 'variables_derivadas': 1, 'restricciones': seleccion,
            'sha256_definiciones': hashlib.sha256(json.dumps(seleccion, sort_keys=True).encode()).hexdigest()}


def aplicar_modelo(conexion, esquema='endi'):
    """Aplica y valida el modelo en la transacción del llamador; nunca confirma por su cuenta."""
    if not conexion.in_transaction():
        raise ValueError('El modelo requiere una transacción activa.')
    for sentencia in sentencias_modelo(esquema):
        conexion.exec_driver_sql(sentencia)
    return verificar_modelo(conexion, esquema)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accion', choices=('generar-sql', 'verificar', 'aplicar'))
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parents[1]
    config = json.loads((raiz/'05_CONFIGURACIONES/01_PROYECTO.json').read_text(encoding='utf-8'))
    esquema = config['postgresql']['esquema']
    if args.accion == 'generar-sql':
        print(generar_sql(raiz, esquema))
        return
    motor = import_module('01_ETL_FUENTES').ETL_ENDI().engine
    try:
        with motor.begin() as conexion:
            if args.accion == 'verificar':
                conexion.exec_driver_sql('SET TRANSACTION READ ONLY')
            if conexion.exec_driver_sql('SELECT current_database()').scalar_one() != config['postgresql']['base']:
                raise ValueError('La conexión no corresponde a la base confirmada.')
            resultado = aplicar_modelo(conexion, esquema) if args.accion == 'aplicar' else verificar_modelo(conexion, esquema)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    finally:
        motor.dispose()


if __name__ == '__main__':
    main()
