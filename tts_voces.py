"""
=============================================================================
 MyBot — Catálogo y descarga de voces neuronales offline (Piper)
=============================================================================
 Fuente única de verdad para las voces neuronales: qué voces existen, cuáles
 están ya instaladas y cómo descargarlas. Lo usan tanto el servidor de la
 aplicación (mybot_backend) como cualquier otro consumidor, para no duplicar
 la lista.

 Los modelos .onnx NO se empaquetan en el instalador (ahorran ~270 MB): se
 descargan desde la app, desde el repositorio oficial rhasspy/piper-voices.
=============================================================================
"""

import os
import time
import urllib.request

USER_AGENT = "MyBot-Desktop-App/1.3.0"
PIPER_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es"
BLOQUE = 256 * 1024

# 'ruta' es la ruta dentro del repositorio; 'ruta': None => no descargable (alias).
CATALOGO = [
    {"id": "es_AR-daniela-high", "etiqueta": "🇦🇷 Daniela - Mujer (Argentina)",
     "ruta": "es_AR/daniela/high", "calidad": "Alta", "mb": 108.9},
    {"id": "es_AR-mateo-hombre", "etiqueta": "🇦🇷 Mateo - Hombre (Argentina)",
     "ruta": None, "calidad": "Alta · se obtiene modulando a Daniela", "mb": 0.0},
    {"id": "es_ES-carlfm-x_low", "etiqueta": "🇪🇸 Carlfm - Hombre (España)",
     "ruta": "es_ES/carlfm/x_low", "calidad": "Básica (la más ligera)", "mb": 26.8},
    {"id": "es_ES-davefx-medium", "etiqueta": "🇪🇸 Davefx - Hombre (España)",
     "ruta": "es_ES/davefx/medium", "calidad": "Media", "mb": 60.3},
    {"id": "es_ES-sharvard-medium", "etiqueta": "🇪🇸 Sharvard - Mujer (España)",
     "ruta": "es_ES/sharvard/medium", "calidad": "Media", "mb": 73.2},
    {"id": "es_ES-mls_10246-low", "etiqueta": "🇪🇸 MLS 10246 - Voz (España)",
     "ruta": "es_ES/mls_10246/low", "calidad": "Básica", "mb": 60.2},
    {"id": "es_ES-mls_9972-low", "etiqueta": "🇪🇸 MLS 9972 - Voz (España)",
     "ruta": "es_ES/mls_9972/low", "calidad": "Básica", "mb": 60.2},
    {"id": "es_MX-ald-medium", "etiqueta": "🇲🇽 Ald - Voz (México)",
     "ruta": "es_MX/ald/medium", "calidad": "Media", "mb": 60.3},
    {"id": "es_MX-ald-x_low", "etiqueta": "🇲🇽 Ald - Voz (México, ligera)",
     "ruta": "es_MX/ald/x_low", "calidad": "Básica (la más ligera)", "mb": 20.0},
    {"id": "es_MX-claude-high", "etiqueta": "🇲🇽 Claude - Voz (México)",
     "ruta": "es_MX/claude/high", "calidad": "Alta", "mb": 60.2},
]

ALIAS = {"es_AR-mateo-hombre": "es_AR-daniela-high"}


def entrada(voz_id: str):
    """Devuelve la entrada del catálogo de una voz (o None)."""
    return next((v for v in CATALOGO if v["id"] == voz_id), None)


def archivo_modelo(directorio: str, voz_id: str) -> str:
    return os.path.join(directorio, f"{voz_id}.onnx")


def instalada(directorio: str, voz_id: str) -> bool:
    return bool(voz_id) and os.path.exists(archivo_modelo(directorio, voz_id))


def url_modelo(voz: dict) -> str:
    return f"{PIPER_BASE_URL}/{voz['ruta']}/{voz['id']}.onnx"


def catalogo(directorio: str) -> list:
    """Catálogo completo con el estado de instalación de cada voz."""
    resultado = []
    for v in CATALOGO:
        descargable = v.get("ruta") is not None
        base = ALIAS.get(v["id"], v["id"])
        resultado.append({
            "id": v["id"],
            "etiqueta": v["etiqueta"],
            "calidad": v["calidad"],
            "mb": v["mb"],
            "descargable": descargable,
            "instalada": instalada(directorio, base),
        })

    # Modelos añadidos a mano por el usuario que no estén en el catálogo
    conocidos = {v["id"] for v in CATALOGO}
    if os.path.isdir(directorio):
        for nombre in sorted(os.listdir(directorio)):
            if nombre.endswith(".onnx") and nombre[:-5] not in conocidos:
                resultado.append({
                    "id": nombre[:-5], "etiqueta": f"🎧 {nombre[:-5]} (personalizada)",
                    "calidad": "Modelo local", "mb": 0.0,
                    "descargable": False, "instalada": True,
                })
    return resultado


def instaladas(directorio: str) -> list:
    """Voces instaladas en el orden del catálogo: [(etiqueta, id), ...]."""
    return [(v["etiqueta"], v["id"]) for v in catalogo(directorio) if v["instalada"]]


def esta_descargable(voz_id: str) -> bool:
    v = entrada(voz_id)
    return bool(v and v.get("ruta"))


def descargar(voz_id: str, directorio: str, progreso=None, cancelado=None) -> str:
    """Descarga el modelo .onnx y su .onnx.json. Devuelve la ruta del .onnx.

    'progreso(percent, mb, total_mb, velocidad_mb_s)' se invoca periódicamente.
    'cancelado()' permite abortar la descarga a mitad.
    """
    voz = entrada(voz_id)
    if not voz or not voz.get("ruta"):
        raise ValueError("Esa voz no se puede descargar.")

    os.makedirs(directorio, exist_ok=True)
    origen = url_modelo(voz)
    destino = archivo_modelo(directorio, voz_id)
    total = int(float(voz.get("mb") or 0) * 1048576) or 1

    _descargar_archivo(origen, destino, 0, total, progreso, cancelado)
    tam = os.path.getsize(destino)
    _descargar_archivo(origen + ".json", destino + ".json", tam, int(tam * 1.05), progreso, cancelado)
    return destino


def _descargar_archivo(url, destino, base_bytes, total_bytes, progreso, cancelado):
    parcial = destino + ".parcial"
    peticion = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(peticion, timeout=60) as respuesta, open(parcial, "wb") as salida:
            descargado = base_bytes
            inicio = time.time()
            ultimo_aviso = 0.0
            total = max(total_bytes, 1)

            while True:
                if cancelado and cancelado():
                    raise RuntimeError("Descarga cancelada.")
                bloque = respuesta.read(BLOQUE)
                if not bloque:
                    break
                salida.write(bloque)
                descargado += len(bloque)

                if progreso:
                    ahora = time.time()
                    if ahora - ultimo_aviso >= 0.3:
                        ultimo_aviso = ahora
                        transcurrido = max(0.001, ahora - inicio)
                        progreso(
                            min(99, int(descargado * 100 / total)),
                            round(descargado / 1048576, 1),
                            round(total / 1048576, 1),
                            (descargado - base_bytes) / transcurrido / 1048576,
                        )
        os.replace(parcial, destino)
    except Exception:
        # Solo se descarta el archivo incompleto: una voz ya instalada no se toca.
        try:
            os.remove(parcial)
        except OSError:
            pass
        raise
