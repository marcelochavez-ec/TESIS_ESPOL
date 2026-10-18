"""Inventario, reproducción verificable y recarga explícita de fuentes."""

import argparse
import csv
import hashlib
from importlib import import_module
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
RAIZ = Path(__file__).resolve().parents[1]


def configuracion():
    return json.loads((RAIZ / '05_CONFIGURACIONES/01_PROYECTO.json').read_text(encoding='utf-8'))


def sha256(ruta):
    calculo = hashlib.sha256()
    with Path(ruta).open('rb') as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b''):
            calculo.update(bloque)
    return calculo.hexdigest()


def guardar_json(ruta, contenido):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(contenido, ensure_ascii=False, indent=2, sort_keys=True)+'\n',
                    encoding='utf-8', newline='\n')


def verificar_fuentes(incluir_documentos=True):
    config = configuracion()
    entradas = [(RAIZ / config['rutas']['fuentes'] / e['archivo'], e) for e in config['fuentes'] + config['diccionarios']]
    if incluir_documentos:
        entradas += [(RAIZ / '02_DOCUMENTACION' / e['archivo'], e) for e in config['documentos']]
    resultado = []
    for ruta, entrada in entradas:
        intacto = ruta.is_file() and sha256(ruta) == entrada['sha256']
        resultado.append({'archivo': ruta.relative_to(RAIZ).as_posix(), 'intacto': intacto})
    if not all(f['intacto'] for f in resultado):
        raise ValueError('Faltan fuentes o cambiaron sus hashes: '+str([f['archivo'] for f in resultado if not f['intacto']]))
    return resultado


def inventariar():
    """Registra todos los archivos del proyecto; omite únicamente metadatos de Git."""
    config = configuracion()
    destino = RAIZ / config['rutas']['inventario']
    origenes = {config['rutas']['fuentes']+'/'+e['archivo']: e['nombre_original'] for e in config['fuentes'] + config['diccionarios']}
    origenes.update({'02_DOCUMENTACION/'+e['archivo']: e['nombre_original'] for e in config['documentos']})
    rutas = sorted(p for p in RAIZ.rglob('*') if p.is_file() and '.git' not in p.relative_to(RAIZ).parts)
    if destino not in rutas:
        rutas.append(destino)
        rutas.sort()
    filas = []
    for ruta in rutas:
        relativa = ruta.relative_to(RAIZ).as_posix()
        autorreferencia = ruta == destino
        filas.append({'NUMERO': len(filas)+1, 'RUTA': relativa, 'NOMBRE_ORIGINAL': origenes.get(relativa, ''),
                      'BYTES': '' if autorreferencia else ruta.stat().st_size,
                      'SHA256': '' if autorreferencia else sha256(ruta),
                      'CLASE': relativa.split('/')[0], 'CONTROL': 'AUTORREFERENCIA' if autorreferencia else 'SHA256'})
    with destino.open('w', encoding='utf-8-sig', newline='') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]), lineterminator='\n')
        escritor.writeheader()
        escritor.writerows(filas)
    return {'archivos_inventariados': len(filas), 'inventario': destino.relative_to(RAIZ).as_posix()}


def ejecutar_pruebas(requeridas=True):
    ruta = RAIZ/'03_PROCESOS_ETL/05_PRUEBAS/01_PRUEBAS_MAPEO.py'
    if not ruta.is_file():
        if requeridas:
            raise ValueError('Las pruebas son locales y no se distribuyen en GitHub; la suite no está disponible.')
        informe = {'pruebas': None, 'correcto': None, 'estado': 'no_distribuidas',
                   'detalle': 'Sin suite local; se mantienen versiones, hashes y comparación del mapeo aprobado.'}
        guardar_json(RAIZ/configuracion()['rutas']['validaciones']/'02_PRUEBAS_MAPEO.json', informe)
        return informe
    # discovery omite nombres que comienzan en dígito; cargar el módulo numerado explícitamente.
    modulo = import_module('05_PRUEBAS.01_PRUEBAS_MAPEO')
    conjunto = unittest.defaultTestLoader.loadTestsFromModule(modulo)
    if conjunto.countTestCases() == 0:
        raise ValueError('La suite no contiene pruebas; no se acepta una ejecución vacía.')
    resultado = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(conjunto)
    informe = {'pruebas': resultado.testsRun, 'fallos': len(resultado.failures),
               'errores': len(resultado.errors), 'correcto': resultado.wasSuccessful()}
    if not resultado.wasSuccessful():
        informe['detalle'] = [texto for _, texto in resultado.failures + resultado.errors]
    guardar_json(RAIZ/configuracion()['rutas']['validaciones']/'02_PRUEBAS_MAPEO.json', informe)
    if not resultado.wasSuccessful():
        raise ValueError(str(informe))
    return informe


def validar_referencia(hashes, resumen, referencia):
    """Rechaza resultados distintos de la referencia aprobada, antes de publicarlos."""
    if not referencia or not referencia.get('archivos_mapeo_sha256'):
        raise ValueError('Falta la referencia aprobada; no se acepta una reproducción sin comparación.')
    if hashes != referencia['archivos_mapeo_sha256']:
        raise ValueError('El mapeo no coincide con los hashes aprobados; se conservan los resultados anteriores.')
    for campo in ('variables_mapeadas', 'variables_sin_etiqueta'):
        if resumen.get(campo) != referencia.get(campo):
            raise ValueError(f'El conteo {campo} difiere de la referencia aprobada.')
    if resumen.get('carga_ejecutada') is not False or resumen.get('constraints_creados') is not False:
        raise ValueError('La reproducción de mapeo no puede incluir cargas ni constraints.')


def reproducir():
    """Ejecuta verificaciones y dos mapeos; compara SHA-256 antes de guardar resultados."""
    config = configuracion()
    validaciones = RAIZ / config['rutas']['validaciones']
    fuentes = verificar_fuentes()
    entorno = import_module('03_VERIFICAR_ENTORNO').verificar()
    guardar_json(validaciones/'01_ENTORNO_ESPOL.json', entorno)
    if not entorno['correcto']:
        raise ValueError('El entorno no coincide con las versiones fijadas.')
    subprocess.run([sys.executable, '-m', 'pip', 'check'], check=True)
    pruebas = ejecutar_pruebas(requeridas=False)
    etl = import_module('01_ETL_FUENTES')
    with tempfile.TemporaryDirectory(prefix='espol_reproduccion_') as temporal:
        primera, segunda = Path(temporal)/'uno', Path(temporal)/'dos'
        resumen = etl.generar_mapeo_endi(RAIZ, salida=primera)
        etl.generar_mapeo_endi(RAIZ, salida=segunda)
        hashes = {p.name: sha256(p) for p in sorted(primera.iterdir())}
        if hashes != {p.name: sha256(p) for p in sorted(segunda.iterdir())}:
            raise ValueError('Los dos mapeos produjeron archivos diferentes.')
        validar_referencia(hashes, resumen, config.get('resultado_referencia'))
        destino = RAIZ / config['rutas']['mapeo']
        destino.mkdir(parents=True, exist_ok=True)
        for archivo in primera.iterdir():
            (destino/archivo.name).write_bytes(archivo.read_bytes())
    ruta_informe = validaciones/'03_REPRODUCIBILIDAD.json'
    informe = json.loads(ruta_informe.read_text(encoding='utf-8')) if ruta_informe.exists() else {'ejecuciones': {}}
    informe['ejecuciones'][sys.platform] = {
        'python': sys.version.split()[0], 'archivos_mapeo_sha256': hashes,
        'dos_ejecuciones_identicas': True, 'fuentes_originales_intactas': len(fuentes),
        'coincide_con_referencia_aprobada': True,
        'variables_mapeadas': resumen['variables_mapeadas'], 'pruebas_correctas': pruebas['pruebas'],
        'carga_sql_ejecutada': False, 'constraints_creados': False,
    }
    comparaciones = [e['archivos_mapeo_sha256'] for e in informe['ejecuciones'].values()]
    informe['coincidencia_entre_plataformas'] = all(h == comparaciones[0] for h in comparaciones) if len(comparaciones)>1 else None
    guardar_json(ruta_informe, informe)
    if informe['coincidencia_entre_plataformas'] is False:
        raise ValueError('Los resultados locales y del contenedor no coinciden; revisar el informe.')
    return informe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accion', choices=['inventariar', 'verificar-fuentes', 'pruebas', 'reproducir', 'ejecutar'])
    parser.add_argument('--sobrescribir-fuentes', action='store_true', help='Reemplaza exclusivamente las seis tablas fuente en research_lab.endi.')
    argumentos = parser.parse_args()
    accion = argumentos.accion
    if argumentos.sobrescribir_fuentes and accion != 'ejecutar':
        parser.error('--sobrescribir-fuentes solo corresponde a ejecutar.')
    if accion == 'ejecutar':
        if not argumentos.sobrescribir_fuentes:
            parser.error('ejecutar requiere --sobrescribir-fuentes; para no escribir SQL, usar reproducir.')
        print('1/3 Verificando fuentes, versiones, pruebas y mapeo reproducible...', flush=True)
        reproducir()
        config = configuracion()
        print('2/3 Mapeo aprobado. Reemplazando las seis tablas en research_lab.endi...', flush=True)
        resultado = import_module('01_ETL_FUENTES').recargar_fuentes_postgresql(
            RAIZ, esquema=config['postgresql']['esquema'], sobrescribir=True, solicitar_clave=True,
        )
        guardar_json(RAIZ/config['rutas']['validaciones']/'12_RECARGA_POSTGRESQL.json', resultado)
        print('3/3 Recarga confirmada: filas, tipos y nulos verificados.', flush=True)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        inventariar()
        return
    acciones = {'inventariar': inventariar, 'verificar-fuentes': verificar_fuentes,
                'pruebas': ejecutar_pruebas, 'reproducir': reproducir}
    print(json.dumps(acciones[accion](), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
