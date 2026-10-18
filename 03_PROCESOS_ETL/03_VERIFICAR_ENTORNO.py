"""Comprueba la pila Python con archivos sintéticos y sin acceso a PostgreSQL."""

import argparse
import importlib
import importlib.metadata
import json
from pathlib import Path
import sys
import tempfile
import re


DEPENDENCIAS = {
    'pandas': 'pandas',
    'numpy': 'numpy',
    'scipy': 'scipy',
    'scikit-learn': 'sklearn',
    'pyreadr': 'pyreadr',
    'xlrd': 'xlrd',
    'openpyxl': 'openpyxl',
    'XlsxWriter': 'xlsxwriter',
    'SQLAlchemy': 'sqlalchemy',
    'psycopg': 'psycopg',
    'PyYAML': 'yaml',
}


def verificar():
    """Devuelve estado, versiones y pruebas; solo escribe en un temporal propio."""
    raiz = Path(__file__).resolve().parents[1]
    config = json.loads((raiz / '05_CONFIGURACIONES/01_PROYECTO.json').read_text(encoding='utf-8'))
    resultado = {
        'python': sys.version.split()[0],
        'version_solicitada': sys.version.split()[0] == config['python'],
        'dependencias': {},
        'pruebas': {},
    }
    resultado['versiones_fijadas'] = {}
    for linea in (raiz / '05_CONFIGURACIONES/requirements.txt').read_text(encoding='utf-8').splitlines():
        if not linea.strip() or linea.lstrip().startswith('#'):
            continue
        coincidencia = re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s]+)', linea.strip())
        if not coincidencia:
            raise ValueError('requirements.txt debe contener exclusivamente versiones exactas paquete==version.')
        paquete, esperada = coincidencia.groups()
        try:
            instalada = importlib.metadata.version(paquete)
        except importlib.metadata.PackageNotFoundError:
            instalada = None
        resultado['versiones_fijadas'][paquete] = {'esperada': esperada, 'instalada': instalada, 'coincide': esperada == instalada}
    modulos = {}
    for paquete, modulo in DEPENDENCIAS.items():
        try:
            modulos[modulo] = importlib.import_module(modulo)
            resultado['dependencias'][paquete] = {
                'estado': 'PASO',
                'version': importlib.metadata.version(paquete),
            }
        except Exception as error:
            resultado['dependencias'][paquete] = {
                'estado': 'FALLO',
                'error': str(error),
            }

    if all(modulo in modulos for modulo in ('pandas', 'pyreadr', 'openpyxl', 'xlsxwriter')):
        try:
            pd = modulos['pandas']
            esperado = pd.DataFrame({'codigo': ['01', '09'], 'valor': [1.5, 2.5]})
            with tempfile.TemporaryDirectory(prefix='espol_validacion_') as temporal:
                carpeta = Path(temporal)
                ruta_rds = carpeta / 'sintetico.rds'
                modulos['pyreadr'].write_rds(str(ruta_rds), esperado)
                recuperado = modulos['pyreadr'].read_r(str(ruta_rds))[None].reset_index(drop=True)
                pd.testing.assert_frame_equal(esperado, recuperado, check_dtype=False)
                resultado['pruebas']['rds_sintetico'] = 'PASO'

                ruta_excel = carpeta / 'sintetico.xlsx'
                esperado.to_excel(ruta_excel, index=False, engine='xlsxwriter')
                recuperado = pd.read_excel(ruta_excel, dtype={'codigo': str}, engine='openpyxl')
                pd.testing.assert_frame_equal(esperado, recuperado, check_dtype=False)
                resultado['pruebas']['excel_sintetico'] = 'PASO'
        except Exception as error:
            resultado['pruebas']['archivos_sinteticos'] = f'FALLO: {error}'
    else:
        resultado['pruebas']['archivos_sinteticos'] = 'NO EJECUTADO: faltan dependencias'

    if 'sqlalchemy' in modulos and 'psycopg' in modulos:
        try:
            sqlalchemy = modulos['sqlalchemy']
            motor = sqlalchemy.create_engine('postgresql+psycopg://localhost/research_lab')
            assert motor.dialect.driver == 'psycopg'
            motor.dispose()
            assert int(importlib.metadata.version('psycopg').split('.')[0]) == 3
            resultado['pruebas']['dialecto_psycopg3_sin_conectar'] = 'PASO'
        except Exception as error:
            resultado['pruebas']['dialecto_psycopg3_sin_conectar'] = f'FALLO: {error}'
    else:
        resultado['pruebas']['dialecto_psycopg3_sin_conectar'] = 'NO EJECUTADO: faltan dependencias'

    resultado['correcto'] = (
        resultado['version_solicitada']
        and all(info['coincide'] for info in resultado['versiones_fijadas'].values())
        and all(info['estado'] == 'PASO' for info in resultado['dependencias'].values())
        and all(estado == 'PASO' for estado in resultado['pruebas'].values())
    )
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, help='Ruta del informe JSON opcional.')
    parser.add_argument('--postgres', action='store_true', help='Verifica la conexión mediante SELECT y transacción de solo lectura.')
    argumentos = parser.parse_args()
    resultado = verificar()
    if argumentos.postgres:
        from importlib import import_module
        from sqlalchemy import text
        motor = import_module('01_ETL_FUENTES').ETL_ENDI().engine
        try:
            with motor.connect() as conexion:
                conexion.execute(text('SET TRANSACTION READ ONLY'))
                base = conexion.execute(text('SELECT current_database()')).scalar_one()
            resultado['conexion_postgresql'] = {'estado': 'PASO', 'base': base, 'solo_lectura': True}
        except Exception as error:
            resultado['conexion_postgresql'] = {'estado': 'FALLO', 'tipo_error': type(error).__name__}
            resultado['correcto'] = False
        finally:
            motor.dispose()
    informe = json.dumps(resultado, ensure_ascii=False, indent=2)
    if argumentos.salida:
        argumentos.salida.write_text(informe + '\n', encoding='utf-8', newline='\n')
    print(informe)
    return 0 if resultado['correcto'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
