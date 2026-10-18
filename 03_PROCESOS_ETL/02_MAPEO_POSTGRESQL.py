"""Lectura tabular y mapeo explícito de tipos antes de almacenar en PostgreSQL."""

from datetime import date, datetime, time
from decimal import Decimal
import numbers
from pathlib import Path
import re

import numpy as np
import pandas as pd
from pandas.api import types as pt
import pyreadr
from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, Double, Integer, MetaData,
    Numeric, SmallInteger, Table, Text, Unicode, inspect, func, select, text,
)
from sqlalchemy.dialects import postgresql
from psycopg import sql


def validar_identificador(nombre):
    if not isinstance(nombre, str) or not nombre or '\x00' in nombre or len(nombre.encode('utf-8')) > 63:
        raise ValueError('Identificador PostgreSQL vacío, inválido o mayor de 63 bytes.')
    return nombre


def leer_fuente(ruta, **opciones):
    """Devuelve todos los objetos/hojas tabulares; no escribe ni abre conexiones SQL."""
    ruta = Path(ruta)
    extension = ruta.suffix.lower()
    if extension in {'.rds', '.rda', '.rdata'}:
        objetos = pyreadr.read_r(str(ruta), **opciones)
        if not objetos:
            raise ValueError(f'No se recuperaron objetos tabulares de {ruta.name}.')
        return {str(k) if k is not None else ruta.stem: v for k, v in objetos.items()}
    if extension in {'.xlsx', '.xls'}:
        opciones.setdefault('sheet_name', None)
        datos = pd.read_excel(ruta, **opciones)
        return datos if isinstance(datos, dict) else {str(opciones['sheet_name']): datos}
    if extension in {'.csv', '.tsv'}:
        opciones.setdefault('sep', '\t' if extension == '.tsv' else ',')
        # Los archivos sin esquema se leen como texto para conservar códigos y ceros.
        opciones.setdefault('dtype', 'string')
        opciones.setdefault('keep_default_na', False)
        return {ruta.stem: pd.read_csv(ruta, **opciones)}
    if extension == '.parquet':
        return {ruta.stem: pd.read_parquet(ruta, **opciones)}
    raise ValueError(f'Formato no implementado: {extension}. Proveer un DataFrame o un lector explícito.')


def _entero(minimo, maximo):
    for clase, inferior, superior in (
        (SmallInteger, -32768, 32767),
        (Integer, -2147483648, 2147483647),
        (BigInteger, -9223372036854775808, 9223372036854775807),
    ):
        if inferior <= minimo <= maximo <= superior:
            return clase()
    # Un entero fuera de BIGINT se conserva exactamente, sin convertirlo a float.
    return Numeric(precision=max(len(str(abs(minimo))), len(str(abs(maximo)))), scale=0)


def _tipo_declarado(declaracion):
    especificacion = {'tipo': declaracion} if isinstance(declaracion, str) else dict(declaracion)
    nombre = especificacion['tipo'].upper().strip()
    clases = {
        'DATE': Date, 'TIMESTAMP': DateTime, 'BOOLEAN': Boolean,
        'SMALLINT': SmallInteger, 'INTEGER': Integer, 'BIGINT': BigInteger,
        'DOUBLE': Double, 'DOUBLE PRECISION': Double, 'NUMERIC': Numeric, 'TEXT': Text,
    }
    if nombre == 'TIMESTAMPTZ':
        return DateTime(timezone=True), especificacion
    if nombre in clases:
        return clases[nombre](), especificacion
    coincidencia = re.fullmatch(r'VARCHAR(?:\(([1-9][0-9]*)\))?', nombre)
    if coincidencia:
        return Unicode(int(coincidencia[1])) if coincidencia[1] else Unicode(), especificacion
    raise ValueError(f'Tipo declarado no implementado: {nombre}.')


def _inferir(serie, valores, margen):
    if pt.is_bool_dtype(serie.dtype):
        return Boolean()
    if pt.is_datetime64_any_dtype(serie.dtype):
        return DateTime(timezone=getattr(serie.dtype, 'tz', None) is not None)
    if pt.is_integer_dtype(serie.dtype):
        if valores.empty:
            return BigInteger() if serie.dtype.itemsize > 4 else Integer()
        return _entero(int(valores.min()), int(valores.max()))
    if pt.is_float_dtype(serie.dtype):
        return Double()
    if valores.empty:
        if isinstance(serie.dtype, pd.StringDtype):
            return Unicode(margen)
        raise ValueError(f'{serie.name}: columna sin valores y sin tipo recuperable; declarar tipo.')
    inferido = pt.infer_dtype(valores, skipna=True)
    if inferido == 'boolean':
        return Boolean()
    if inferido == 'integer':
        return _entero(int(valores.min()), int(valores.max()))
    if inferido in {'floating', 'mixed-integer-float'}:
        if inferido == 'mixed-integer-float' and any(
            isinstance(v, numbers.Integral) and abs(v) > 2**53 for v in valores
        ):
            raise ValueError(f'{serie.name}: mezcla numérica perdería precisión; declarar NUMERIC.')
        return Double()
    if inferido == 'decimal':
        return Numeric()
    if inferido == 'date':
        return Date()
    if inferido in {'datetime', 'datetime64'}:
        zonas = {v.tzinfo is not None and v.utcoffset() is not None for v in valores}
        if len(zonas) != 1:
            raise ValueError(f'{serie.name}: mezcla de fechas con y sin zona horaria.')
        return DateTime(timezone=zonas.pop())
    if inferido in {'string', 'unicode'}:
        return Unicode(max(map(len, valores)) + margen)
    raise ValueError(f'{serie.name}: tipo ambiguo o no soportado ({inferido}); declarar tipo.')


def _convertir(serie, tipo, especificacion, margen):
    valores = serie.dropna()
    # La inferencia ya comprobó clase y rango sobre todos los valores presentes.
    if not especificacion and isinstance(tipo, (SmallInteger, Integer, BigInteger)):
        objeto = serie.astype(object)
        return objeto.where(serie.notna(), None), tipo
    if not especificacion and isinstance(tipo, Double):
        return serie.copy(), tipo
    if isinstance(tipo, (Unicode, Text)):
        convertida = serie.map(lambda v: None if pd.isna(v) else str(v))
        presentes = convertida.dropna()
        longitud = max(map(len, presentes), default=0)
        if any('\x00' in v for v in presentes):
            raise ValueError(f'{serie.name}: PostgreSQL no admite NUL dentro de texto.')
        if isinstance(tipo, Text):
            return convertida, tipo
        if tipo.length is None:
            tipo = Unicode(longitud + margen)
        if longitud > tipo.length:
            raise ValueError(f'{serie.name}: longitud {longitud} excede VARCHAR({tipo.length}).')
        return convertida, tipo
    if isinstance(tipo, DateTime):
        if especificacion:
            opciones = {'errors': 'raise'}
            if especificacion.get('formato'):
                opciones['format'] = especificacion['formato']
            convertida = pd.to_datetime(serie, **opciones)
        else:
            convertida = serie.copy()
        fechas = convertida.dropna()
        if any(getattr(v, 'nanosecond', 0) for v in fechas):
            raise ValueError(f'{serie.name}: precisión submicrosegundo no representable en PostgreSQL.')
        if any((v.tzinfo is not None and v.utcoffset() is not None) != tipo.timezone for v in fechas):
            raise ValueError(f'{serie.name}: zona horaria incompatible con el tipo declarado.')
        return convertida, tipo
    if isinstance(tipo, Date):
        def fecha(v):
            if pd.isna(v):
                return None
            if isinstance(v, datetime):
                if v.time() != time() or v.tzinfo is not None:
                    raise ValueError(f'{serie.name}: convertir a DATE perdería hora o zona.')
                return v.date()
            if isinstance(v, date):
                return v
            if not isinstance(v, str):
                raise ValueError(f'{serie.name}: DATE requiere fecha, no un código numérico.')
            return datetime.strptime(v, especificacion.get('formato', '%Y-%m-%d')).date()
        return serie.map(fecha), tipo
    if isinstance(tipo, (SmallInteger, Integer, BigInteger)):
        limites = {SmallInteger: (-32768, 32767), Integer: (-2147483648, 2147483647),
                   BigInteger: (-9223372036854775808, 9223372036854775807)}
        minimo, maximo = limites[type(tipo)]
        def entero(v):
            if pd.isna(v):
                return None
            if isinstance(v, str) and re.fullmatch(r'[+-]?[0-9]+', v):
                v = int(v)
            if isinstance(v, (bool, np.bool_)) or not isinstance(v, (numbers.Real, Decimal)):
                raise ValueError(f'{serie.name}: valor no entero.')
            if not np.isfinite(float(v)) or int(v) != v or not minimo <= v <= maximo:
                raise ValueError(f'{serie.name}: entero fraccionario o fuera de rango.')
            return int(v)
        return pd.Series([entero(v) for v in serie], index=serie.index, name=serie.name, dtype=object), tipo
    if isinstance(tipo, Boolean):
        if not all(isinstance(v, (bool, np.bool_)) for v in valores):
            raise ValueError(f'{serie.name}: BOOLEAN requiere valores lógicos reales.')
        return serie.copy(), tipo
    if isinstance(tipo, Numeric):
        def decimal(v):
            if pd.isna(v):
                return None
            if isinstance(v, (bool, np.bool_)):
                raise ValueError(f'{serie.name}: booleano no es NUMERIC.')
            return v if isinstance(v, Decimal) else Decimal(str(v))
        return serie.map(decimal), tipo
    if isinstance(tipo, Double):
        def real(v):
            if pd.isna(v):
                return None
            if isinstance(v, (bool, np.bool_)) or not isinstance(v, (numbers.Real, Decimal, str)):
                raise ValueError(f'{serie.name}: DOUBLE requiere datos numéricos.')
            return float(v)
        return serie.map(real), tipo
    raise ValueError(f'Tipo no soportado para {serie.name}.')


def mapear_dataframe(df, declaraciones=None, margen=10):
    """Devuelve copia normalizada, tipos SQLAlchemy y metadatos; no escribe en SQL."""
    if not isinstance(df, pd.DataFrame) or df.columns.empty or df.columns.duplicated().any():
        raise ValueError('Se requiere DataFrame con columnas únicas y no vacío de columnas.')
    if not isinstance(margen, int) or margen < 0:
        raise ValueError('El margen VARCHAR debe ser un entero no negativo.')
    declaraciones = declaraciones or {}
    desconocidas = set(declaraciones) - set(df.columns)
    if desconocidas:
        raise ValueError(f'Declaraciones para columnas inexistentes: {sorted(desconocidas)}.')
    columnas_normalizadas = {}
    tipos, metadatos = {}, []
    for columna in df:
        validar_identificador(columna)
        serie = df[columna]
        valores = serie.dropna()
        especificacion = {}
        if columna in declaraciones:
            tipo, especificacion = _tipo_declarado(declaraciones[columna])
        else:
            tipo = _inferir(serie, valores, margen)
        convertida, tipo = _convertir(serie, tipo, especificacion, margen)
        columnas_normalizadas[columna] = convertida
        tipos[columna] = tipo
        metadatos.append({
            'variable': columna, 'tipo_origen': str(serie.dtype),
            'tipo_valores': pt.infer_dtype(valores, skipna=True),
            'tipo_sql': str(tipo.compile(dialect=postgresql.dialect())),
            'criterio': 'declarado' if especificacion else 'inferido',
            'nulos': int(serie.isna().sum()),
            'longitud_observada': max(map(len, convertida.dropna()), default=0) if isinstance(tipo, (Unicode, Text)) else None,
            'longitud_declarada': tipo.length if isinstance(tipo, Unicode) else None,
        })
    # Construir de una sola vez evita fragmentar DataFrames de cientos de columnas.
    return pd.DataFrame(columnas_normalizadas, index=df.index), tipos, metadatos


def definir_tabla(nombre, esquema, tipos, metadata=None):
    validar_identificador(nombre)
    validar_identificador(esquema)
    return Table(nombre, metadata if metadata is not None else MetaData(),
                 *(Column(c, t) for c, t in tipos.items()), schema=esquema)


def copiar_dataframe(conexion, df, tabla):
    """COPY sobre una transacción existente; nunca confirma ni reemplaza tablas."""
    sentencia = sql.SQL('COPY {}.{} ({}) FROM STDIN').format(
        sql.Identifier(tabla.schema), sql.Identifier(tabla.name),
        sql.SQL(', ').join(map(sql.Identifier, df.columns)),
    )
    def valor(v):
        if pd.isna(v):
            return None
        if isinstance(v, np.generic):
            return v.item()
        return v.to_pydatetime() if isinstance(v, pd.Timestamp) else v
    dbapi = conexion.connection.driver_connection
    with dbapi.cursor() as cursor, cursor.copy(sentencia) as copia:
        for fila in df.itertuples(index=False, name=None):
            copia.write_row(tuple(valor(v) for v in fila))


def almacenar_dataframe(df, motor, nombre, esquema='endi', declaraciones=None, margen=10):
    """Mapea antes de CREATE/COPY; rechaza tablas existentes y devuelve el mapeo."""
    normalizado, tipos, mapeo = mapear_dataframe(df, declaraciones, margen)
    tabla = definir_tabla(nombre, esquema, tipos)
    with motor.begin() as conexion:
        if not inspect(conexion).has_schema(esquema):
            raise ValueError(f'No existe el esquema {esquema}; no se crea implícitamente.')
        if inspect(conexion).has_table(nombre, schema=esquema):
            raise ValueError(f'La tabla {esquema}.{nombre} ya existe; no se reemplaza ni se duplica la carga.')
        tabla.create(conexion)
        copiar_dataframe(conexion, normalizado, tabla)
    return mapeo


def recargar_tablas(conexion, esquema, fuentes, *, sobrescribir=False):
    """Recrea un conjunto explícito de tablas en una transacción del llamador.

    fuentes: {nombre: (DataFrame ya normalizado, tipos SQLAlchemy, metadatos)}.
    No hace commit, no elimina el esquema y no utiliza CASCADE.
    """
    if not sobrescribir:
        raise ValueError('La recarga requiere sobrescribir=True de forma explícita.')
    validar_identificador(esquema)
    if not fuentes:
        raise ValueError('No se acepta una recarga sin tablas.')
    if not conexion.in_transaction():
        raise ValueError('La recarga requiere una transacción activa.')
    if not inspect(conexion).has_schema(esquema):
        raise ValueError(f'No existe el esquema {esquema}. No se crea otro por error de nombre.')
    metadata = MetaData()
    tablas = {}
    for nombre, (df, tipos, mapeo) in fuentes.items():
        validar_identificador(nombre)
        if list(df.columns) != list(tipos) or {v['variable'] for v in mapeo} != set(df.columns):
            raise ValueError(f'{nombre}: datos y mapeo no coinciden.')
        tablas[nombre] = definir_tabla(nombre, esquema, tipos, metadata)
    conexion.execute(text("SET LOCAL lock_timeout = '10s'"))
    bloqueo = conexion.execute(text('SELECT pg_try_advisory_xact_lock(hashtextextended(:clave, 0))'),
                                {'clave': f'tesis_espol.recarga.{esquema}'}).scalar_one()
    if not bloqueo:
        raise ValueError('Ya existe otra recarga en ejecución sobre este esquema.')
    sentencia = sql.SQL('DROP TABLE IF EXISTS {} RESTRICT').format(sql.SQL(', ').join(
        sql.SQL('{}.{}').format(sql.Identifier(esquema), sql.Identifier(n)) for n in fuentes
    ))
    with conexion.connection.driver_connection.cursor() as cursor:
        cursor.execute(sentencia)
    metadata.create_all(conexion, checkfirst=False)
    resultado = []
    for nombre, (df, tipos, mapeo) in fuentes.items():
        tabla = tablas[nombre]
        copiar_dataframe(conexion, df, tabla)
        filas = conexion.execute(select(func.count()).select_from(tabla)).scalar_one()
        no_nulos = conexion.execute(select(*(func.count(tabla.c[c]) for c in df.columns))).one()
        tipos_reales = {c['name']: str(c['type'].compile(dialect=postgresql.dialect()))
                        for c in inspect(conexion).get_columns(nombre, schema=esquema)}
        tipos_previstos = {c: str(t.compile(dialect=postgresql.dialect())) for c, t in tipos.items()}
        if filas != len(df) or tipos_reales != tipos_previstos:
            raise ValueError(f'{nombre}: conteo o tipos SQL distintos del mapeo; se revierte toda la recarga.')
        if list(no_nulos) != [len(df)-v['nulos'] for v in mapeo]:
            raise ValueError(f'{nombre}: conteos de nulos distintos; se revierte toda la recarga.')
        huella_sql = sql.SQL("""SELECT md5(COALESCE(string_agg(huella, '' ORDER BY huella), ''))
            FROM (SELECT md5(row_to_json(origen)::text) AS huella FROM {}.{} AS origen) AS filas""").format(
                sql.Identifier(esquema), sql.Identifier(nombre))
        with conexion.connection.driver_connection.cursor() as cursor:
            cursor.execute(huella_sql)
            huella = cursor.fetchone()[0]
        resultado.append({'tabla': f'{esquema}.{nombre}', 'registros': filas,
                          'variables': len(tipos), 'tipos_verificados': True, 'nulos_verificados': True,
                          'huella_contenido_md5': huella})
    return resultado
