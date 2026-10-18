"""Configura la visibilidad de columnas del diagrama ER en un workspace DBeaver."""

import argparse
import json
import os
from pathlib import Path
import tempfile


CLAVE = b'erd.attr.visibility='
ARCHIVO = Path('.metadata/.plugins/org.eclipse.core.runtime/.settings/org.jkiss.dbeaver.ui.editors.erd.prefs')


def configurar(workspace, visibilidad='KEYS', verificar=False):
    """Cambia solo la preferencia ER; conserva las demás líneas y no toca conexiones."""
    if visibilidad not in ('ALL', 'KEYS', 'PRIMARY', 'NONE'):
        raise ValueError('Visibilidad no admitida por DBeaver.')
    ruta = Path(workspace).expanduser().resolve()/ARCHIVO
    if not ruta.is_file():
        raise FileNotFoundError(f'No existe la preferencia ER de este workspace: {ruta}')
    original = ruta.read_bytes()
    lineas = original.splitlines(keepends=True)
    encontradas = [l for l in lineas if l.startswith(CLAVE)]
    anterior = encontradas[-1][len(CLAVE):].strip().decode('ascii') if encontradas else None
    if not verificar:
        salto = b'\r\n' if b'\r\n' in original else b'\n'
        nuevas = [CLAVE+visibilidad.encode('ascii')+salto if l.startswith(CLAVE) else l for l in lineas]
        if not encontradas:
            if nuevas and not nuevas[-1].endswith((b'\r', b'\n')):
                nuevas[-1] += salto
            nuevas.append(CLAVE+visibilidad.encode('ascii')+salto)
        contenido = b''.join(nuevas)
        if contenido != original:
            with tempfile.NamedTemporaryFile(dir=ruta.parent, delete=False, suffix='.tmp') as temporal:
                temporal.write(contenido)
                nombre_temporal = Path(temporal.name)
            try:
                os.replace(nombre_temporal, ruta)
            finally:
                nombre_temporal.unlink(missing_ok=True)
    actual = [l[len(CLAVE):].strip().decode('ascii') for l in ruta.read_bytes().splitlines() if l.startswith(CLAVE)]
    if not actual or (not verificar and any(v != visibilidad for v in actual)):
        raise ValueError('No se pudo comprobar la preferencia guardada.')
    return {'archivo': str(ruta), 'anterior': anterior, 'actual': actual[-1],
            'solo_lectura': verificar, 'verificado_en_archivo': True,
            'aplicacion_visual': 'Reiniciar DBeaver y abrir de nuevo el diagrama; no cerrar consultas sin guardar.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, help='Workspace DBeaver; por defecto APPDATA/DBeaverData/workspace6.')
    parser.add_argument('--visibilidad', choices=('KEYS', 'ALL', 'PRIMARY', 'NONE'), default='KEYS')
    parser.add_argument('--verificar', action='store_true', help='Lee la configuración sin cambiarla.')
    args = parser.parse_args()
    workspace = args.workspace
    if workspace is None:
        if not os.environ.get('APPDATA'):
            parser.error('En este sistema debe indicar --workspace; se configura el cliente del anfitrión, no PostgreSQL.')
        workspace = Path(os.environ['APPDATA'])/'DBeaverData/workspace6'
    print(json.dumps(configurar(workspace, args.visibilidad, args.verificar), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
