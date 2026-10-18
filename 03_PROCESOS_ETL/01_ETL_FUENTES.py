import pandas as pd
import pyreadr
from scipy.stats import kurtosis, skew
from sqlalchemy import URL, create_engine
from pathlib import Path
import argparse
import json
import os
from importlib import import_module

mapeo = import_module('02_MAPEO_POSTGRESQL')

class ETL_ENDI:
    def __init__(self, db_user=None, db_password=None, db_name=None, db_host=None, db_port=None):
        config = json.loads((Path(__file__).resolve().parents[1] / '05_CONFIGURACIONES/01_PROYECTO.json').read_text(encoding='utf-8'))['postgresql']
        self.engine = create_engine(URL.create(
            'postgresql+psycopg', username=db_user or os.environ.get('PGUSER', config['usuario']),
            password=db_password if db_password is not None else os.environ.get('PGPASSWORD'),
            host=db_host or os.environ.get('PGHOST', config['host']),
            port=int(db_port or os.environ.get('PGPORT', config['puerto'])),
            database=db_name or os.environ.get('PGDATABASE', config['base']),
        ))
    
    def leer_rds(self, ruta_archivo):
        """Lee un único objeto RDS sin cambiar códigos ni tipos de origen."""
        objetos = mapeo.leer_fuente(ruta_archivo)
        if len(objetos) != 1:
            raise ValueError('La fuente contiene varios objetos; utilizar leer_fuente y mapear cada objeto.')
        return next(iter(objetos.values()))
    
    def exploratorio(self, df):
        """Generar resumen estadístico de un DataFrame en Pandas."""
        resumen = pd.DataFrame({
            "Variable": df.columns,
            "Tipo": df.dtypes,
            "Minimo": df.min(numeric_only=True),
            "Maximo": df.max(numeric_only=True),
            "Rango": df.max(numeric_only=True) - df.min(numeric_only=True),
            "Promedio": df.mean(numeric_only=True).round(2),
            "Mediana": df.median(numeric_only=True),
            "Moda": df.mode().iloc[0],
            "Desviacion_Estandar": df.std(numeric_only=True).round(2),
            "Coeficiente_Asimetria": df.apply(lambda x: skew(x.dropna()) if x.dtype.kind in 'biufc' else None),
            "Curtosis": df.apply(lambda x: kurtosis(x.dropna()) if x.dtype.kind in 'biufc' else None),
        })
        return resumen
    
    def almacenamiento_postgresql(self, df, table_name, schema='endi', declaraciones=None, margen=10):
        """Mapea cada variable antes de crear una tabla nueva; nunca reemplaza tablas."""
        return mapeo.almacenar_dataframe(df, self.engine, table_name, schema, declaraciones, margen)
    
    def lectura_diccionario(self, file_path, sheets):
        """Leer múltiples pestañas de un archivo Excel y concatenarlas."""
        dataframes_diccionarios = []
        for sheet in sheets:
            df = pd.read_excel(file_path, sheet_name=sheet, usecols=[0, 1])  # Solo leer columnas Variable y Etiqueta
            df.columns = ['Variable', 'Etiqueta']  # Renombrar columnas
            df = df.dropna()  # Eliminar filas vacías
            dataframes_diccionarios.append(df)
        endi_diccionarios = pd.concat(dataframes_diccionarios, ignore_index=True).drop_duplicates()
        return endi_diccionarios
    
    def buscar_variable(self, diccionario_df, variable):
        """Buscar una variable en el diccionario y devolverla en formato tabular vertical."""
        resultado = diccionario_df[diccionario_df["Variable"] == variable]
        if not resultado.empty:
            return resultado.melt(id_vars="Variable", var_name="Campo", value_name="Valor")
        else:
            return f"No se encontraron resultados para la variable '{variable}'."


def generar_mapeo_endi(raiz, margen=None, declaraciones=None, salida=None):
    """Mapea las seis fuentes y exporta metadatos, sin abrir conexiones PostgreSQL."""
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.schema import CreateTable

    raiz = Path(raiz)
    config = json.loads((raiz / '05_CONFIGURACIONES/01_PROYECTO.json').read_text(encoding='utf-8'))
    margen = config['margen_varchar'] if margen is None else margen
    fuente = raiz / config['rutas']['fuentes']
    salida = Path(salida) if salida is not None else raiz / config['rutas']['mapeo']
    archivos = config['fuentes']
    esperados = {f['archivo'] for f in archivos}
    encontrados = {p.name for p in fuente.glob('*.rds')}
    if encontrados != esperados:
        raise ValueError(f'Fuentes distintas del manifiesto. Faltantes: {sorted(esperados-encontrados)}; adicionales: {sorted(encontrados-esperados)}.')
    etiquetas = {}
    for entrada in config['diccionarios']:
        libro = fuente / entrada['archivo']
        for hoja, diccionario in pd.read_excel(libro, sheet_name=None).items():
            diccionario.columns = diccionario.columns.str.strip()
            tabla = 'f3_desarrollo_inf' if hoja == 'f3_desarrollo_infantil' else hoja
            etiquetas[tabla] = dict(zip(diccionario['Variable'].str.strip(), diccionario['Etiqueta']))

    declaraciones = declaraciones or {}
    nombres = {entrada['tabla'] for entrada in archivos}
    if set(declaraciones) - nombres:
        raise ValueError('El archivo de declaraciones contiene tablas desconocidas.')
    mapeos, tablas, sentencias = [], [], []
    import hashlib
    for entrada in config['fuentes'] + config['diccionarios']:
        archivo = fuente / entrada['archivo']
        if hashlib.sha256(archivo.read_bytes()).hexdigest() != entrada['sha256']:
            raise ValueError(f'{archivo.name}: SHA-256 distinto del origen; revisar antes de mapear.')
    for entrada in archivos:
        archivo = fuente / entrada['archivo']
        nombre = entrada['tabla']
        objetos = mapeo.leer_fuente(archivo)
        if len(objetos) != 1:
            raise ValueError(f'{archivo.name}: número de objetos distinto de uno; revisar cobertura.')
        objeto, original = next(iter(objetos.items()))
        normalizado, tipos, columnas = mapeo.mapear_dataframe(original, declaraciones.get(nombre), margen)
        if len(normalizado) != len(original):
            raise ValueError(f'{nombre}: el mapeo alteró el número de filas.')
        for variable in columnas:
            clave_etiqueta = config.get('aliases_etiquetas', {}).get(nombre, {}).get(variable['variable'], variable['variable'])
            variable.update({'tabla': nombre, 'archivo': archivo.name, 'objeto': objeto,
                             'variable_diccionario': clave_etiqueta,
                             'etiqueta': etiquetas.get(nombre, {}).get(clave_etiqueta, ''),
                             'registros': len(original)})
        mapeos.extend(columnas)
        tablas.append({'tabla': nombre, 'archivo': archivo.name, 'registros': len(original),
                       'variables': len(original.columns)})
        tabla = mapeo.definir_tabla(nombre, config['postgresql']['esquema'], tipos)
        sentencias.append(str(CreateTable(tabla).compile(dialect=postgresql.dialect())).strip() + ';')

    resumen = {'etapa': 'MAPEO_PREVIO', 'margen_varchar': margen, 'tablas': tablas,
               'variables_mapeadas': len(mapeos), 'variables_sin_etiqueta': sum(not bool(v['etiqueta']) for v in mapeos),
               'tipos_sql': pd.Series([v['tipo_sql'] for v in mapeos]).value_counts().to_dict(),
               'carga_ejecutada': False, 'constraints_creados': False}
    salida.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(mapeos).to_csv(salida / '01_MAPEO_VARIABLES.csv', index=False, encoding='utf-8-sig', lineterminator='\n')
    (salida / '02_RESUMEN_MAPEO.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    # El SQL es un artefacto de revisión: se genera, pero no se ejecuta.
    (salida / '03_TIPOS_POSTGRESQL.sql').write_text(
        '-- PROPUESTA DE TIPOS. Sin carga, PK, FK, UNIQUE ni CHECK. No ejecutado.\n\n' + '\n\n'.join(sentencias) + '\n',
        encoding='utf-8', newline='\n',
    )
    return resumen


def recargar_fuentes_postgresql(raiz, *, esquema='endi', sobrescribir=False, solicitar_clave=False):
    """Remapea las seis fuentes y las sustituye juntas; solo confirma tras validarlas."""
    import hashlib
    from getpass import getpass
    raiz = Path(raiz)
    config = json.loads((raiz/'05_CONFIGURACIONES/01_PROYECTO.json').read_text(encoding='utf-8'))
    if not sobrescribir:
        raise ValueError('Debe solicitarse explícitamente la sobrescritura de tablas fuente.')
    if esquema != config['postgresql']['esquema']:
        raise ValueError('El esquema no coincide con el destino confirmado del manifiesto.')
    fuentes = {}
    for entrada in config['fuentes']:
        archivo = raiz/config['rutas']['fuentes']/entrada['archivo']
        if hashlib.sha256(archivo.read_bytes()).hexdigest() != entrada['sha256']:
            raise ValueError(f'{archivo.name}: la fuente cambió antes de la carga.')
        objetos = mapeo.leer_fuente(archivo)
        if len(objetos) != 1:
            raise ValueError(f'{archivo.name}: se esperaba un único objeto tabular.')
        fuentes[entrada['tabla']] = mapeo.mapear_dataframe(next(iter(objetos.values())), margen=config['margen_varchar'])
    clave = None
    modelo = import_module('05_MODELO_RELACIONAL')
    modelo.generar_sql(raiz, esquema)
    if solicitar_clave and not os.environ.get('PGPASSWORD') and not os.environ.get('PGPASSFILE'):
        clave = getpass(f"Clave PostgreSQL para {os.environ.get('PGUSER', config['postgresql']['usuario'])}: ")
    motor = ETL_ENDI(db_password=clave).engine
    try:
        with motor.begin() as conexion:
            base = conexion.exec_driver_sql('SELECT current_database()').scalar_one()
            if base != config['postgresql']['base']:
                raise ValueError('La base conectada no coincide con research_lab; no se reemplaza ninguna tabla.')
            version = conexion.exec_driver_sql('SHOW server_version').scalar_one()
            tablas = mapeo.recargar_tablas(conexion, esquema, fuentes, sobrescribir=True)
            relaciones = modelo.aplicar_modelo(conexion, esquema)
            diccionario = import_module('07_DICCIONARIO_VARIABLES').cargar_diccionario(raiz, conexion, esquema)
        return {'base': base, 'esquema': esquema, 'tablas': tablas,
                'version_postgresql': version,
                'recarga_confirmada': True, 'constraints_creados': True,
                'modelo_relacional': relaciones,
                'diccionario': diccionario,
                'otras_tablas_modificadas': False}
    finally:
        motor.dispose()


def main():
    parser = argparse.ArgumentParser(description='Mapeo completo ENDI previo a cualquier carga o constraint.')
    parser.add_argument('--margen-varchar', type=int)
    parser.add_argument('--declaraciones', type=Path, help='JSON opcional {tabla: {variable: tipo o especificación}}.')
    parser.add_argument('--salida', type=Path, help='Directorio de metadatos; no contiene registros fuente.')
    argumentos = parser.parse_args()
    declaraciones = json.loads(argumentos.declaraciones.read_text(encoding='utf-8')) if argumentos.declaraciones else None
    resumen = generar_mapeo_endi(Path(__file__).resolve().parents[1], argumentos.margen_varchar,
                               declaraciones, argumentos.salida)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
