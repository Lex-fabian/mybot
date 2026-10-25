"""
=============================================================================
 MyBot - Backend Asíncrono para Desktop App (HTTP + WebSockets)
=============================================================================
 Maneja la conexión con TikTok Live, cola de voz prioritaria, Edge TTS,
 SAPI5 de Windows, parada instantánea de audio y filtros anti-spam,
 comunicándose en tiempo real con la interfaz de la aplicación.
=============================================================================
"""

import asyncio
import hashlib
import json
import logging
import os
import queue
import re
import secrets
import shutil
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import uuid
from collections import deque

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from aiohttp import web

# La libreria de TikTokLive se carga de forma diferida (ver _cargar_tiktoklive):
# arrastra protobuf, httpx y otros modulos pesados que retrasaban varios segundos
# la apertura de la ventana, y solo se necesitan al conectar con un directo.
TikTokLiveClient = None
CommentEvent = ConnectEvent = DisconnectEvent = GiftEvent = None
JoinEvent = None
AgeRestrictedError = SignAPIError = UserNotFoundError = None
UserOfflineError = WebcastBlockedError = FailedResolveUserId = None
_tiktoklive_cargado = False


def _cargar_tiktoklive() -> None:
    """Importa TikTokLive la primera vez que se necesita (al conectar)."""
    global TikTokLiveClient, CommentEvent, ConnectEvent, DisconnectEvent
    global GiftEvent, JoinEvent, AgeRestrictedError, SignAPIError
    global UserNotFoundError, UserOfflineError, WebcastBlockedError
    global FailedResolveUserId, _tiktoklive_cargado

    if _tiktoklive_cargado:
        return

    from TikTokLive import TikTokLiveClient as cliente_cls
    from TikTokLive.client.errors import AgeRestrictedError as err_edad
    from TikTokLive.client.errors import SignAPIError as err_firma
    from TikTokLive.client.errors import UserNotFoundError as err_usuario
    from TikTokLive.client.errors import UserOfflineError as err_offline
    from TikTokLive.client.errors import WebcastBlockedError as err_bloqueo
    from TikTokLive.client.web.routes.fetch_user_unique_id import FailedResolveUserId as err_resolver
    from TikTokLive.events import CommentEvent as evento_comentario
    from TikTokLive.events import ConnectEvent as evento_conectar
    from TikTokLive.events import DisconnectEvent as evento_desconectar
    from TikTokLive.events import GiftEvent as evento_regalo

    try:
        from TikTokLive.events import JoinEvent as evento_unirse
    except ImportError:
        evento_unirse = None

    TikTokLiveClient = cliente_cls
    CommentEvent, ConnectEvent = evento_comentario, evento_conectar
    DisconnectEvent, GiftEvent = evento_desconectar, evento_regalo
    JoinEvent = evento_unirse
    AgeRestrictedError, SignAPIError = err_edad, err_firma
    UserNotFoundError, UserOfflineError = err_usuario, err_offline
    WebcastBlockedError, FailedResolveUserId = err_bloqueo, err_resolver
    _tiktoklive_cargado = True


import audio_assets
import tts_voces

if getattr(sys, "frozen", False):
    # Empaquetado con PyInstaller: los recursos viven junto al ejecutable, no en
    # el directorio temporal (_MEIPASS), que se borra al cerrar la aplicación.
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WEB_DIR = os.path.join(BASE_DIR, "web")
PORT = 58421

# Token de sesión: la interfaz lo recibe inyectado en index.html y lo envía al
# abrir el WebSocket. Sin él, cualquier página web visitada por el usuario podría
# conectarse al servidor local (WebSocket no aplica la política de mismo origen).
SESSION_TOKEN = secrets.token_urlsafe(32)
HOSTS_PERMITIDOS = {
    f"127.0.0.1:{PORT}",
    f"localhost:{PORT}",
    f"[::1]:{PORT}",
}
ORIGENES_PERMITIDOS = {
    f"http://127.0.0.1:{PORT}",
    f"http://localhost:{PORT}",
    f"http://[::1]:{PORT}",
}

MAX_WS_MSG = 64 * 1024
MAX_CONFIG_BYTES = 512 * 1024
MAX_UPDATE_BYTES = 300 * 1024 * 1024
MAX_COMENTARIOS_VISTOS = 5000
MAX_USUARIOS_BIENVENIDA = 5000
MAX_TEXTO_VOZ = 1000
_CONFIG_LOCK = threading.Lock()


def _es_directorio_escribible(directorio: str) -> bool:
    try:
        os.makedirs(directorio, exist_ok=True)
        prueba = os.path.join(directorio, f".escritura_{os.getpid()}")
        with open(prueba, "w", encoding="utf-8") as f:
            f.write("1")
        os.remove(prueba)
        return True
    except OSError:
        return False


def _resolver_carpeta_datos() -> str:
    r"""Carpeta raíz escribible para datos del usuario (config, voces, descargas).
    Si BASE_DIR es escribible (ej. desarrollo o portable), se usa BASE_DIR.
    Si BASE_DIR es de solo lectura (ej. Program Files), se usa %LOCALAPPDATA%\MyBot."""
    if _es_directorio_escribible(BASE_DIR):
        return BASE_DIR
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.path.expanduser("~")
    carpeta = os.path.join(base, "MyBot")
    try:
        os.makedirs(carpeta, exist_ok=True)
        return carpeta
    except OSError:
        return BASE_DIR


DATA_DIR = _resolver_carpeta_datos()


def _resolver_archivo_config() -> str:
    local = os.path.join(BASE_DIR, "config.json")
    if os.path.exists(local) and _es_directorio_escribible(BASE_DIR):
        return local
    return os.path.join(DATA_DIR, "config.json")


CONFIG_FILE = _resolver_archivo_config()
DESCARGAS_DIR = os.path.join(DATA_DIR, "assets", "descargas_audio")

APP_VERSION = "1.3.3"
# La interfaz se sirve desde disco y WebView2 conserva su caché entre
# ejecuciones. Este sufijo cambia en cada arranque para que el index.html y los
# assets se vuelvan a pedir en lugar de reutilizar una versión antigua.
ASSET_VERSION = f"{APP_VERSION}-{secrets.token_hex(4)}"
USER_AGENT = f"MyBot-Desktop-App/{APP_VERSION}"
UPDATE_URL = "https://mybot-79861.web.app/version.json"

# Voces Neurales Edge TTS
VOICES_EDGE = [
    ("🇦🇷 Tomas - Hombre (Argentina)", "es-AR-TomasNeural"),
    ("🇦🇷 Elena - Mujer (Argentina)", "es-AR-ElenaNeural"),
    ("🇪🇸 Alvaro - Hombre (España)", "es-ES-AlvaroNeural"),
    ("🇪🇸 Elvira - Mujer (España)", "es-ES-ElviraNeural"),
    ("🇪🇸 Ximena - Mujer (España)", "es-ES-XimenaNeural"),
    ("🇲🇽 Jorge - Hombre (México)", "es-MX-JorgeNeural"),
    ("🇲🇽 Dalia - Mujer (México)", "es-MX-DaliaNeural"),
    ("🇲🇽 Beatriz - Mujer (México)", "es-MX-BeatrizNeural"),
    ("🇲🇽 Candela - Mujer (México)", "es-MX-CandelaNeural"),
    ("🇲🇽 Carlota - Mujer (México)", "es-MX-CarlotaNeural"),
    ("🇲🇽 Gerardo - Hombre (México)", "es-MX-GerardoNeural"),
    ("🇲🇽 Larissa - Mujer (México)", "es-MX-LarissaNeural"),
    ("🇲🇽 Luciano - Hombre (México)", "es-MX-LucianoNeural"),
    ("🇲🇽 Marina - Mujer (México)", "es-MX-MarinaNeural"),
    ("🇲🇽 Nuria - Mujer (México)", "es-MX-NuriaNeural"),
    ("🇲🇽 Pelayo - Hombre (México)", "es-MX-PelayoNeural"),
    ("🇨🇴 Salome - Mujer (Colombia)", "es-CO-SalomeNeural"),
    ("🇨🇴 Gonzalo - Hombre (Colombia)", "es-CO-GonzaloNeural"),
    ("🇨🇱 Catalina - Mujer (Chile)", "es-CL-CatalinaNeural"),
    ("🇨🇱 Lorenzo - Hombre (Chile)", "es-CL-LorenzoNeural"),
    ("🇵🇪 Camila - Mujer (Perú)", "es-PE-CamilaNeural"),
    ("🇵🇪 Alex - Hombre (Perú)", "es-PE-AlexNeural"),
    ("🇺🇸 Alonso - Hombre (EE. UU.)", "es-US-AlonsoNeural"),
    ("🇺🇸 Paloma - Mujer (EE. UU.)", "es-US-PalomaNeural"),
    ("🇻🇪 Paola - Mujer (Venezuela)", "es-VE-PaolaNeural"),
    ("🇻🇪 Sebastian - Hombre (Venezuela)", "es-VE-SebastianNeural"),
    ("🇪🇨 Andrea - Mujer (Ecuador)", "es-EC-AndreaNeural"),
    ("🇪🇨 Luis - Hombre (Ecuador)", "es-EC-LuisNeural"),
    ("🇧🇴 Sofia - Mujer (Bolivia)", "es-BO-SofiaNeural"),
    ("🇧🇴 Marcelo - Hombre (Bolivia)", "es-BO-MarceloNeural"),
    ("🇺🇾 Valentina - Mujer (Uruguay)", "es-UY-ValentinaNeural"),
    ("🇺🇾 Mateo - Hombre (Uruguay)", "es-UY-MateoNeural"),
    ("🇩🇴 Ramona - Mujer (Rep. Dominicana)", "es-DO-RamonaNeural"),
    ("🇩🇴 Emilio - Hombre (Rep. Dominicana)", "es-DO-EmilioNeural"),
    ("🇨🇷 Juan - Hombre (Costa Rica)", "es-CR-JuanNeural"),
    ("🇨🇷 Maria - Mujer (Costa Rica)", "es-CR-MariaNeural"),
    ("🌐 Brian - Multilingüe", "en-US-BrianMultilingualNeural"),
    ("🌐 Emma - Multilingüe", "en-US-EmmaMultilingualNeural"),
]

BOT_PRESETS = {
    "👤 Natural / Neutro": {"tono": 0, "vel": 0, "desc": "Voz cristalina equilibrada sin alteraciones."},
    "🤖 MyBot Androide": {"tono": -12, "vel": 10, "desc": "Cadencia tecnológica y timbre sintético futurista."},
    "🐿️ Ardilla Divertida": {"tono": 45, "vel": 25, "desc": "Voz aguda con efecto de helio ultra dinámico."},
    "🎙️ Locutor Profesional": {"tono": -25, "vel": -5, "desc": "Tono grave, profundo y ritmo relajado de radio."},
    "⚡ Streamer Rápido": {"tono": 12, "vel": 38, "desc": "Velocidad acelerada ideal para directos con mucho tráfico."},
    "👾 Gamer Sintético": {"tono": 28, "vel": -10, "desc": "Modulación de voz estilo videojuego retro."},
    "📻 Loquendo Clásico": {"tono": 0, "vel": 5, "desc": "Cadencia nostálgica tradicional de sintetizador."},
}


def _normalizar_texto_voz(texto: str) -> str:
    """Normaliza para comparar voces: sin emojis, sin signos y en minúsculas."""
    return re.sub(r"[^0-9a-záéíóúüñ ]+", "", (texto or "").lower()).strip()


def resolver_voz_edge(nombre_o_id: str):
    if not nombre_o_id:
        return VOICES_EDGE[0][0], VOICES_EDGE[0][1]
    for nom, vid in VOICES_EDGE:
        if nom == nombre_o_id or vid == nombre_o_id:
            return nom, vid

    objetivo = _normalizar_texto_voz(nombre_o_id)
    if objetivo:
        for nom, vid in VOICES_EDGE:
            if objetivo == _normalizar_texto_voz(nom) or objetivo == _normalizar_texto_voz(vid):
                return nom, vid
        for nom, vid in VOICES_EDGE:
            if objetivo in f"{_normalizar_texto_voz(nom)} {_normalizar_texto_voz(vid)}":
                return nom, vid
    return VOICES_EDGE[0][0], VOICES_EDGE[0][1]


def obtener_voces_sapi5():
    lista = []
    vistos = set()
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass
    try:
        import win32com.client

        try:
            s = win32com.client.Dispatch("SAPI.SpVoice")
            for v in s.GetVoices():
                desc = v.GetDescription()
                v_id = str(v.Id)
                desc_low = desc.lower()
                limpio = re.sub(r"^Microsoft\s+", "", desc)
                limpio = re.sub(r"\s+Desktop(\s*-\s*)", " - ", limpio).strip()
                if "spain" in desc_low or "españa" in desc_low or "es-es" in desc_low:
                    limpio = f"🇪🇸 {limpio}"
                elif "argentina" in desc_low or "es-ar" in desc_low:
                    limpio = f"🇦🇷 {limpio}"
                elif "mexico" in desc_low or "méxico" in desc_low or "es-mx" in desc_low:
                    limpio = f"🇲🇽 {limpio}"
                lista.append((limpio, v_id))
                vistos.add(limpio.lower())
        except Exception:
            pass

        try:
            cp = win32com.client.Dispatch("SAPI.SpObjectTokenCategory")
            cp.SetId(r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices")
            for t in cp.EnumerateTokens():
                desc = t.GetDescription()
                v_id = str(t.Id)
                desc_low = desc.lower()
                limpio = re.sub(r"^Microsoft\s+", "", desc)
                limpio = re.sub(r"\s+Desktop(\s*-\s*)", " - ", limpio).strip()
                if "spain" in desc_low or "españa" in desc_low or "es-es" in desc_low:
                    limpio = f"🇪🇸 {limpio}"
                elif "argentina" in desc_low or "es-ar" in desc_low:
                    limpio = f"🇦🇷 {limpio}"
                elif "mexico" in desc_low or "méxico" in desc_low or "es-mx" in desc_low:
                    limpio = f"🇲🇽 {limpio}"
                if limpio.lower() not in vistos:
                    lista.append((limpio, v_id))
                    vistos.add(limpio.lower())
        except Exception:
            pass
    except Exception:
        pass

    if not lista:
        try:
            import pyttsx3
            engine = pyttsx3.init(driverName="sapi5")
            voices = engine.getProperty("voices")
            for v in voices:
                nombre = v.name
                nombre_limpio = re.sub(r"^Microsoft\s+", "", nombre)
                nombre_limpio = re.sub(r"\s+Desktop(\s*-\s*)", " - ", nombre_limpio).strip()
                nom_low = nombre.lower()
                if "spain" in nom_low or "españa" in nom_low or "es-es" in nom_low:
                    nombre_limpio = f"🇪🇸 {nombre_limpio}"
                elif "argentina" in nom_low or "es-ar" in nom_low:
                    nombre_limpio = f"🇦🇷 {nombre_limpio}"
                lista.append((nombre_limpio, v.id))
            engine.stop()
        except Exception:
            pass

    return lista or [("Voz por defecto del sistema", "")]


# =============================================================================
# VOCES NEURONALES OFFLINE (PIPER) — CATÁLOGO DESCARGABLE
# =============================================================================
# La lista de voces y la descarga viven en tts_voces.py, compartido con la GUI
# clásica, para no mantener dos catálogos distintos.
BASE_PIPER_DIR = os.path.join(BASE_DIR, "assets", "voices")
PIPER_DIR = os.path.join(DATA_DIR, "assets", "voices")
VOZ_CATALOGO_PIPER = tts_voces.CATALOGO


def _archivo_modelo_piper(voz_id: str) -> str:
    return tts_voces.archivo_modelo(PIPER_DIR, voz_id, fallback_dir=BASE_PIPER_DIR)


def voz_piper_instalada(voz_id: str) -> bool:
    return tts_voces.instalada(PIPER_DIR, voz_id, fallback_dir=BASE_PIPER_DIR)


def url_modelo_piper(entrada: dict) -> str:
    """URL oficial (.onnx) de un modelo del catálogo."""
    return tts_voces.url_modelo(entrada)


def catalogo_voces_piper() -> list:
    """Catálogo completo con el estado de instalación de cada voz."""
    return tts_voces.catalogo(PIPER_DIR, fallback_dir=BASE_PIPER_DIR)


def obtener_voces_piper():
    """Voces Piper INSTALADAS, en el orden del catálogo: [(etiqueta, id), ...]."""
    return tts_voces.instaladas(PIPER_DIR, fallback_dir=BASE_PIPER_DIR)


def limpiar_nombre_usuario_tiktok(texto: str) -> str:
    if not texto:
        return ""
    t = texto.strip()
    match = re.search(r"tiktok\.com/@([a-zA-Z0-9_\.\-]+)", t)
    if match:
        return match.group(1)
    t = re.sub(r"^https?://[^\/]+/", "", t)
    t = t.strip("/").strip().lstrip("@").strip()
    t = re.sub(r"/live.*$", "", t)
    return t


def limpiar_nombre_para_voz(nombre: str) -> str:
    """Limpia nombres de usuario de TikTok para una locución rápida y natural sin deletrear números infinitos."""
    if not nombre:
        return "Usuario"
    n = nombre.strip()
    # Si es un nombre autogenerado tipo user1948291481 o tiktok_user_1234
    if re.match(r"^(?:user|tiktok_user)?\d{5,}$", n, re.IGNORECASE):
        return "Usuario"
    # Eliminar emojis y caracteres decorativos raros
    n = re.sub(r"[\U00010000-\U0010ffff]", "", n)
    n = re.sub(r"[^\w\sáéíóúüñÁÉÍÓÚÜÑ]", " ", n)
    # Si termina en una ristra de dígitos largos (ej. Carlos_837492), recortar dígitos para ahorrar tiempo
    n = re.sub(r"[\s_]+\d{4,}$", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n if len(n) >= 2 else "Usuario"


def normalizar_comentario(comentario: str, filtrar_links: bool = True, compactar_emojis: bool = True) -> str:
    if not comentario:
        return ""
    c = str(comentario).strip()[:1000]
    c = re.sub(r"[\x00-\x1f\x7f-\x9f\u200b-\u200f\ufeff]", "", c)
    if filtrar_links:
        c = re.sub(r"(https?://\S+|www\.\S+|\b[a-zA-Z0-9.\-_]+(?:\.com|\.org|\.net|\.io|\.me|\.gg|\.xyz)\b\S*)", "[enlace]", c, flags=re.IGNORECASE)
    c = re.sub(r"(.)\1{3,}", r"\1\1", c)
    if compactar_emojis:
        c = re.sub(r"([\U00010000-\U0010ffff])\1{2,}", r"\1\1", c)
    # Cota de memoria: el texto completo se guarda en el anti-repetición.
    return c.strip()[:500]


def _version_mayor(remota: str, local: str) -> bool:
    """Compara versiones tipo 1.3.0 frente a 1.2.10. Ignora textos como 'v'."""
    def partes(v: str):
        limpio = re.sub(r"[^\d.]", "", str(v or ""))
        return [int(p) for p in limpio.split(".") if p != ""] or [0]

    a, b = partes(remota), partes(local)
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else 0
        y = b[i] if i < len(b) else 0
        if x != y:
            return x > y
    return False


def mensaje_error_conexion(exc: Exception) -> str:
    try:
        _cargar_tiktoklive()
    except Exception:  # noqa: BLE001
        return str(exc)

    if isinstance(exc, UserOfflineError):
        return "El usuario no está en directo en este momento."
    if isinstance(exc, UserNotFoundError):
        return "No se encontró el usuario (o no tiene directos habilitados)."
    if isinstance(exc, AgeRestrictedError):
        return "El directo es para mayores de edad (+18)."
    if isinstance(exc, WebcastBlockedError):
        return "TikTok bloqueó temporalmente la conexión. Intenta en unos minutos."
    if isinstance(exc, SignAPIError):
        return f"Error en la firma de TikTok ({getattr(exc, 'reason', exc)})."
    if isinstance(exc, FailedResolveUserId):
        return "No se pudo resolver el ID del usuario en TikTok."
    return str(exc)


def mensaje_error_tts(exc: Exception) -> str:
    """Traduce errores del motor de voz a mensajes claros para el usuario."""
    texto = str(exc)
    if "403" in texto or "Invalid response status" in texto:
        return ("El servicio de voces Edge TTS rechazó la conexión (error 403). "
                "Comprueba tu conexión a Internet o usa voces SAPI5 (Windows).")
    if "Speech synthesis" in texto or "No audio was received" in texto:
        return "La voz seleccionada no está disponible. Prueba con otra voz Edge TTS."
    return texto


def _url_de_actualizacion_oficial(partes) -> bool:
    """Comprueba host y ruta del proyecto, no solo el dominio."""
    host = (partes.hostname or "").lower()
    ruta = partes.path or ""
    if host == "mybot-79861.web.app":
        return True
    if host == "storage.googleapis.com":
        return ruta.startswith("/mybot-79861.firebasestorage.app/")
    if host == "firebasestorage.googleapis.com":
        return "mybot-79861.firebasestorage.app" in ruta
    return False


def validar_url_actualizacion(url: str):
    """Solo permite HTTPS del proyecto oficial y un nombre de .exe seguro."""
    texto = str(url or "").strip()
    partes = urllib.parse.urlparse(texto)
    if partes.scheme.lower() != "https" or not _url_de_actualizacion_oficial(partes):
        raise ValueError("La actualización no procede de un servidor oficial por HTTPS.")
    nombre = urllib.parse.unquote(os.path.basename(partes.path or ""))
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,120}\.exe", nombre, re.IGNORECASE):
        raise ValueError("El nombre del instalador no es válido.")
    return texto, nombre


def _firma_autentica(ruta: str) -> bool:
    """Valida la firma Authenticode con WinVerifyTrust (sin lanzar PowerShell)."""
    if not sys.platform.startswith("win") or not os.path.isfile(ruta):
        return False
    try:
        import ctypes
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", ctypes.c_ubyte * 8),
            ]

        class WINTRUST_FILE_INFO(ctypes.Structure):
            _fields_ = [
                ("cbStruct", wintypes.DWORD),
                ("pcwszFilePath", wintypes.LPCWSTR),
                ("hFile", wintypes.HANDLE),
                ("pgKnownSubject", ctypes.POINTER(GUID)),
            ]

        class WINTRUST_DATA(ctypes.Structure):
            _fields_ = [
                ("cbStruct", wintypes.DWORD),
                ("pPolicyCallbackData", ctypes.c_void_p),
                ("pSIPClientData", ctypes.c_void_p),
                ("dwUIChoice", wintypes.DWORD),
                ("fdwRevocationChecks", wintypes.DWORD),
                ("dwUnionChoice", wintypes.DWORD),
                ("pFile", ctypes.POINTER(WINTRUST_FILE_INFO)),
                ("dwStateAction", wintypes.DWORD),
                ("hWVTStateData", wintypes.HANDLE),
                ("pwszURLReference", wintypes.LPWSTR),
                ("dwProvFlags", wintypes.DWORD),
                ("dwUIContext", wintypes.DWORD),
                ("pSignatureSettings", ctypes.c_void_p),
            ]

        accion = GUID(
            0x00AAC56B, 0xCD44, 0x11D0,
            (ctypes.c_ubyte * 8)(0x8C, 0xC2, 0x00, 0xC0, 0x4F, 0xC2, 0x95, 0xEE),
        )
        archivo = WINTRUST_FILE_INFO()
        archivo.cbStruct = ctypes.sizeof(WINTRUST_FILE_INFO)
        archivo.pcwszFilePath = os.path.abspath(ruta)

        datos = WINTRUST_DATA()
        datos.cbStruct = ctypes.sizeof(WINTRUST_DATA)
        datos.dwUIChoice = 2           # WTD_UI_NONE
        datos.fdwRevocationChecks = 0  # WTD_REVOKE_NONE
        datos.dwUnionChoice = 1        # WTD_CHOICE_FILE
        datos.pFile = ctypes.pointer(archivo)
        datos.dwStateAction = 0        # WTD_STATEACTION_IGNORE
        datos.dwProvFlags = 0x1000     # WTD_CACHE_ONLY_URL_RETRIEVAL

        resultado = ctypes.windll.wintrust.WinVerifyTrust(
            ctypes.c_void_p(0), ctypes.byref(accion), ctypes.byref(datos)
        )
        return resultado == 0
    except Exception:
        return False


def _sha256_archivo(ruta: str) -> str:
    digest = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest().upper()


def _consumir_futuro(futuro) -> None:
    """Recoge la excepción de un envío WebSocket para no acumular avisos."""
    try:
        futuro.exception()
    except BaseException:
        pass


def enviar_tecla_multimedia(vk: int) -> bool:
    """Envía una tecla multimedia con SendInput.

    Las teclas multimedia son teclas extendidas (prefijo E0). keybd_event sin
    KEYEVENTF_EXTENDEDKEY no las entrega correctamente a YouTube Music/Spotify,
    que es la causa de que "siguiente", "anterior" y "pausa" no hicieran nada.
    """
    if not sys.platform.startswith("win"):
        return False
    try:
        import ctypes
        from ctypes import wintypes

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t),
            ]

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t),
            ]

        class _EntradaUnion(ctypes.Union):
            _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

        class INPUT(ctypes.Structure):
            _anonymous_ = ("u",)
            _fields_ = [("type", wintypes.DWORD), ("u", _EntradaUnion)]

        INPUT_KEYBOARD = 1
        KEYEVENTF_EXTENDEDKEY = 0x0001
        KEYEVENTF_KEYUP = 0x0002

        scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
        entradas = (INPUT * 2)()
        for indice, flags in ((0, KEYEVENTF_EXTENDEDKEY),
                              (1, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP)):
            entradas[indice].type = INPUT_KEYBOARD
            entradas[indice].ki.wVk = vk
            entradas[indice].ki.wScan = scan
            entradas[indice].ki.dwFlags = flags
            entradas[indice].ki.time = 0
            entradas[indice].ki.dwExtraInfo = 0

        enviados = ctypes.windll.user32.SendInput(
            2, ctypes.byref(entradas), ctypes.sizeof(INPUT)
        )
        return enviados == 2
    except Exception:
        return False


# =============================================================================
# VALIDACIÓN DE LA CONFIGURACIÓN
# =============================================================================
# La configuración llega tanto de config.json como de la interfaz. Se valida
# siempre contra este esquema: evita valores de tipo incorrecto (que rompían el
# hilo de voz), límites absurdos y claves arbitrarias inyectadas por WebSocket.
CONFIG_DEFECTOS = {
    "usuario": "@l.am.lex_",
    "motor": "piper",
    "voz_nombre": VOZ_CATALOGO_PIPER[0]["etiqueta"],
    "voz_id": VOZ_CATALOGO_PIPER[0]["id"],
    "tono": 0,
    "velocidad": 0,
    "volumen": 100,
    "leer_nombre": True,
    "formato_usuario": "{usuario} dice: {mensaje}",
    "donaciones_activas": True,
    "esperar_racha": True,
    "min_diamantes": 1,
    "leer_donacion": True,
    "tpl_donacion": "¡Muchas gracias a {usuario} por enviar {cantidad} {regalo}!",
    "sonido_activo": True,
    "tipo_sonido": "Campana (Suave)",
    "ruta_sonido_custom": "",
    "baneadas": "ejemplo1,ejemplo2,ejemplo3",
    "max_caracteres": 65,
    "max_cola": 4,
    "filtrar_links": True,
    "compactar_emojis": True,
    "auto_reconnect": True,
    "usar_gtts": True,
    "bienvenidas_activas": True,
    "leer_bienvenida": False,
    "mostrar_bienvenida_chat": True,
    "tpl_bienvenida": "¡Bienvenido {usuario} al directo!",
    "cooldown_bienvenida": 10,
    "anti_repeticion_bienvenida": True,
    "ignorar_comentarios_repetidos": True,
    "tiempo_anti_repeticion": 45,
    "accion_multimedia_activa": False,
    "tipo_accion_multimedia": "next",
    "min_diamantes_multimedia": 1,
    "aceleracion_dinamica": True,
    "ttl_comentarios_cola": 20,
    "limpiar_nombres_usuarios": True,
}

CONFIG_BOOL = {
    "leer_nombre", "donaciones_activas", "esperar_racha", "leer_donacion",
    "sonido_activo", "filtrar_links", "compactar_emojis", "auto_reconnect",
    "usar_gtts", "bienvenidas_activas", "leer_bienvenida",
    "mostrar_bienvenida_chat", "anti_repeticion_bienvenida",
    "ignorar_comentarios_repetidos", "accion_multimedia_activa",
    "aceleracion_dinamica", "limpiar_nombres_usuarios",
}
CONFIG_INT = {
    "tono": (-50, 50),
    "velocidad": (-50, 100),
    "volumen": (0, 100),
    "min_diamantes": (0, 1_000_000),
    "max_caracteres": (10, 500),
    "max_cola": (1, 100),
    "cooldown_bienvenida": (0, 3600),
    "tiempo_anti_repeticion": (0, 3600),
    "min_diamantes_multimedia": (0, 1_000_000),
    "ttl_comentarios_cola": (1, 600),
}
CONFIG_TEXTO = {
    "usuario": 120,
    "voz_nombre": 200,
    "voz_id": 120,
    "formato_usuario": 300,
    "tpl_donacion": 300,
    "tipo_sonido": 200,
    "ruta_sonido_custom": 500,
    "baneadas": 2000,
    "tpl_bienvenida": 300,
}
CONFIG_ENUM = {
    "motor": {"piper", "sapi5", "edge"},
    "tipo_accion_multimedia": {"next", "prev", "play_pause"},
}


def sanear_config(crudo, base=None) -> dict:
    """Devuelve solo claves conocidas, con el tipo y los límites correctos."""
    limpio = {}
    if not isinstance(crudo, dict):
        return limpio
    referencia = base if base is not None else CONFIG_DEFECTOS

    for clave, valor in crudo.items():
        if clave not in referencia:
            continue
        defecto = referencia[clave]

        if clave in CONFIG_BOOL:
            if isinstance(valor, bool):
                limpio[clave] = valor
            elif isinstance(valor, (int, float)):
                limpio[clave] = bool(valor)
            elif isinstance(valor, str):
                limpio[clave] = valor.strip().lower() in ("1", "true", "si", "sí", "on")
            continue

        if clave in CONFIG_INT:
            if isinstance(valor, bool):
                continue
            try:
                numero = int(valor)
            except (TypeError, ValueError):
                continue
            minimo, maximo = CONFIG_INT[clave]
            limpio[clave] = max(minimo, min(maximo, numero))
            continue

        if clave in CONFIG_ENUM:
            texto = str(valor or "").strip()
            limpio[clave] = texto if texto in CONFIG_ENUM[clave] else defecto
            continue

        if clave in CONFIG_TEXTO:
            texto = valor if isinstance(valor, str) else str(valor)
            if clave == "usuario":
                texto = texto.strip()[:CONFIG_TEXTO[clave]]
            else:
                texto = texto[:CONFIG_TEXTO[clave]]
            limpio[clave] = texto
            continue

        if isinstance(valor, type(defecto)):
            limpio[clave] = valor

    return limpio


# =============================================================================
# SERVICIO PRINCIPAL DE MYBOT
# =============================================================================
class MyBotService:
    def __init__(self, loop):
        self.loop = loop
        self.sonidos_predeterminados = audio_assets.generar_sonidos_predeterminados()
        self.voces_sapi5 = obtener_voces_sapi5()
        self.cfg = self._cargar_configuracion()
        self._patron_baneadas = self._compilar_patron_baneadas()

        # Colas de voz
        self.cola_voz = queue.PriorityQueue()
        self._cola_lock = threading.Lock()
        self.ws_clients = set()

        # TikTok Client
        self.cliente = None
        self.hilo_cliente = None
        self._debe_correr = False
        self._sapi_engine = None
        self._sapi_voice = None
        self._edge_disponible = True
        self._piper_voz = None
        self._piper_modelo = None

        # Métricas
        self.total_comentarios = 0
        self.total_donaciones = 0
        self.total_diamantes = 0

        # Aviso único de respaldo de voz (evita saturar el chat)
        self._aviso_respaldo_tts = False

        # Control de bienvenidas y anti-repetición. El orden permite expulsar a
        # los usuarios más antiguos: en directos muy largos este conjunto crecía
        # sin límite (fuga de memoria).
        self._usuarios_bienvenida = set()
        self._usuarios_bienvenida_orden = deque()
        self._ultimo_saludo_tiempo = 0.0
        self._comentarios_vistos = {}
        self._ultimo_cleanup_comentarios = 0.0
        # Control de actualización in-app sin navegador
        self._descarga_activa = False
        self._comprobando_actualizacion = False
        self._instalador_listo = ""
        self._instalador_hash = ""
        self._instalador_dir = ""
        # Control de descarga de voces neuronales y clips
        self._descarga_voz_activa = False
        self._generando_clip = False

        # Iniciar hilo de voz
        threading.Thread(target=self._hilo_tts, daemon=True).start()

    def _cargar_configuracion(self):
        # Piper es el motor recomendado. Su modelo no viene en el instalador:
        # si aún no está descargado, la propia app guía al usuario para bajarlo.
        motor_def = CONFIG_DEFECTOS["motor"]
        voz_nom_def = CONFIG_DEFECTOS["voz_nombre"]
        voz_id_def = CONFIG_DEFECTOS["voz_id"]
        defaults = dict(CONFIG_DEFECTOS)

        if os.path.exists(CONFIG_FILE):
            try:
                if os.path.getsize(CONFIG_FILE) > MAX_CONFIG_BYTES:
                    raise ValueError("config.json demasiado grande")
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    contenido = f.read().strip()
                    if contenido:
                        defaults.update(sanear_config(json.loads(contenido), defaults))
            except Exception as e:
                print(f"[MyBot] config.json no válido, se usan valores seguros: {e}")

        if defaults.get("motor") not in ("piper", "sapi5", "edge"):
            defaults["motor"] = motor_def

        if defaults.get("motor") == "piper":
            # Solo corregimos el voz_id si no existe en el catálogo. Si existe pero
            # aún no está descargado, se respeta (la app pedirá descargarlo).
            ids_catalogo = {v["id"] for v in VOZ_CATALOGO_PIPER}
            if defaults.get("voz_id") not in ids_catalogo:
                defaults["voz_nombre"], defaults["voz_id"] = voz_nom_def, voz_id_def

        if defaults.get("motor") == "edge":
            v_nom, v_id = resolver_voz_edge(defaults.get("voz_nombre") or defaults.get("voz_id"))
            defaults["voz_nombre"] = v_nom
            defaults["voz_id"] = v_id

        return defaults

    def _guardar_configuracion(self):
        """Escritura atómica: un corte de luz no deja config.json a medias."""
        try:
            carpeta = os.path.dirname(CONFIG_FILE)
            if carpeta:
                os.makedirs(carpeta, exist_ok=True)
            temporal = f"{CONFIG_FILE}.{os.getpid()}.tmp"
            with _CONFIG_LOCK:
                with open(temporal, "w", encoding="utf-8") as f:
                    json.dump(sanear_config(self.cfg), f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temporal, CONFIG_FILE)
        except Exception as e:
            print(f"[MyBot] Error guardando config: {e}")

    def _resolver_sonido(self, tipo_s: str) -> str:
        """Busca la ruta del sonido de forma tolerante (ignora emojis y mayúsculas)."""
        if not tipo_s:
            return ""

        directo = self.sonidos_predeterminados.get(tipo_s)
        if directo:
            return directo

        def _norm(t: str) -> str:
            return re.sub(r"[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ/ ]+", "", t or "").strip().lower()

        objetivo = _norm(tipo_s)
        if not objetivo:
            return ""
        for etiqueta, ruta in self.sonidos_predeterminados.items():
            if _norm(etiqueta) == objetivo:
                return ruta
        for etiqueta, ruta in self.sonidos_predeterminados.items():
            etiqueta_norm = _norm(etiqueta)
            if objetivo in etiqueta_norm or etiqueta_norm in objetivo:
                return ruta
        return ""

    def emit_ws(self, msg_type: str, data: dict):
        """Emite mensaje a todos los clientes WebSocket conectados."""
        if not self.ws_clients:
            return
        try:
            payload = json.dumps({"type": msg_type, "data": data})
        except (TypeError, ValueError):
            return
        for ws in list(self.ws_clients):
            if ws.closed:
                self.ws_clients.discard(ws)
                continue
            try:
                futuro = asyncio.run_coroutine_threadsafe(ws.send_str(payload), self.loop)
                # Consumir la excepción evita acumular futuros con error si el
                # cliente se cierra a mitad de un envío.
                futuro.add_done_callback(_consumir_futuro)
            except RuntimeError:
                # El bucle ya se detuvo durante el cierre de la aplicación.
                return

    def conectar_tiktok(self, usuario_raw: str):
        if self.hilo_cliente and self.hilo_cliente.is_alive():
            if not self._debe_correr:
                self.hilo_cliente.join(timeout=1.2)
            if self.hilo_cliente and self.hilo_cliente.is_alive():
                self.emit_ws("toast", {"message": "Ya hay una conexión activa o en proceso"})
                return

        usuario_limpio = limpiar_nombre_usuario_tiktok(str(usuario_raw or "")[:500])
        usuario_limpio = usuario_limpio[:100]
        if not usuario_limpio:
            self.emit_ws("toast", {"message": "Usuario de TikTok inválido"})
            return

        # Reiniciar registros de bienvenida y anti-repetición para el nuevo directo
        self._usuarios_bienvenida.clear()
        self._comentarios_vistos.clear()

        self.cfg["usuario"] = f"@{usuario_limpio}"
        self._guardar_configuracion()
        self._debe_correr = True

        self.emit_ws("estado", {"text": f"Conectando a @{usuario_limpio}...", "status": "amber"})
        self.emit_ws("sis", {"message": f"Conectando al directo de @{usuario_limpio}..."})

        self.hilo_cliente = threading.Thread(target=self._hilo_cliente_loop, args=(usuario_limpio,), daemon=True)
        self.hilo_cliente.start()

    def desconectar_tiktok(self):
        self.emit_ws("sis", {"message": "Desconectando del directo..."})
        self._debe_correr = False
        cliente = self.cliente
        self.cliente = None
        if cliente is not None:
            try:
                loop = getattr(cliente, "_asyncio_loop", None)
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(cliente.disconnect(), loop)
                else:
                    asyncio.run(cliente.disconnect())
            except Exception:
                pass
        self.emit_ws("estado", {"text": "Desconectado", "status": "gray"})

    def _limpiar_comentarios_vistos(self, ahora: float):
        """Limpia comentarios antiguos de la memoria para evitar consumo continuo."""
        if self._ultimo_cleanup_comentarios + 30 > ahora:
            return
        self._ultimo_cleanup_comentarios = ahora
        limite = int(self.cfg.get("tiempo_anti_repeticion", 45) or 0) * 2
        self._comentarios_vistos = {
            k: t for k, t in self._comentarios_vistos.items()
            if ahora - t < limite
        }
        self._limitar_comentarios_vistos()

    def _limitar_comentarios_vistos(self):
        """Cota dura: un flood de comentarios no puede hacer crecer el diccionario sin fin."""
        sobrantes = len(self._comentarios_vistos) - MAX_COMENTARIOS_VISTOS
        if sobrantes <= 0:
            return
        for clave in list(self._comentarios_vistos)[:sobrantes]:
            self._comentarios_vistos.pop(clave, None)

    def _ya_saludado(self, uid: str) -> bool:
        """Anti-repetición de bienvenidas con límite FIFO (evita fuga de memoria)."""
        if uid in self._usuarios_bienvenida:
            return True
        self._usuarios_bienvenida.add(uid)
        self._usuarios_bienvenida_orden.append(uid)
        while len(self._usuarios_bienvenida_orden) > MAX_USUARIOS_BIENVENIDA:
            viejo = self._usuarios_bienvenida_orden.popleft()
            self._usuarios_bienvenida.discard(viejo)
        return False

    def _hilo_cliente_loop(self, usuario: str):
        reintentos = 0
        max_reintentos = 15

        # TikTokLive se importa aqui (no al arrancar) para que la ventana abra rapido.
        self.emit_ws("tts_estado", {"state": "cargando", "detail": "Preparando el motor de TikTok..."})
        try:
            _cargar_tiktoklive()
        except Exception as e:  # noqa: BLE001
            self.emit_ws("estado", {"text": "Error al cargar TikTokLive", "status": "red"})
            self.emit_ws("err", {"message": f"No se pudo cargar la libreria de TikTokLive: {e}"})
            self._debe_correr = False
            return

        while self._debe_correr:
            try:
                cliente = TikTokLiveClient(unique_id=usuario)
                self.cliente = cliente
                logging.getLogger("TikTokLive").setLevel(logging.ERROR)

                @cliente.on(ConnectEvent)
                async def _al_conectar(event: ConnectEvent):
                    nonlocal reintentos
                    reintentos = 0  # una conexión correcta reinicia el contador
                    self.emit_ws("sis", {"message": f"CONECTADO con éxito a @{event.unique_id}"})
                    self.emit_ws("estado", {"text": f"Conectado a @{event.unique_id}", "status": "green"})

                @cliente.on(DisconnectEvent)
                async def _al_desconectar(event: DisconnectEvent):
                    if self._debe_correr:
                        self.emit_ws("sis", {"message": "TikTok reportó desconexión del directo."})

                if JoinEvent is not None:
                    @cliente.on(JoinEvent)
                    async def _al_unirse(event: JoinEvent):
                        if not self.cfg.get("bienvenidas_activas", True):
                            return

                        nombre = getattr(event.user, "nickname", None) or getattr(event.user, "unique_id", "Usuario")
                        uid = getattr(event.user, "unique_id", "") or nombre

                        # Mostrar en el chat en vivo si está habilitado
                        if self.cfg.get("mostrar_bienvenida_chat", True):
                            self.emit_ws("join", {"user": nombre, "unique_id": uid})

                        # Leer bienvenida por voz si está activa
                        if not self.cfg.get("leer_bienvenida", False):
                            return

                        ahora = time.time()
                        # Evitar saludar a la misma persona más de una vez en el directo
                        if (self.cfg.get("anti_repeticion_bienvenida", True)
                                and uid in self._usuarios_bienvenida):
                            return

                        # Cooldown entre bienvenidas de voz para no saturar
                        cooldown = max(3, int(self.cfg.get("cooldown_bienvenida", 10)))
                        if ahora - self._ultimo_saludo_tiempo < cooldown:
                            return

                        # Si la cola ya tiene varios mensajes (>= 2), descartar bienvenida (baja prioridad)
                        if self.cola_voz.qsize() >= 2:
                            return

                        tpl = self.cfg.get("tpl_bienvenida", "¡Bienvenido {usuario} al directo!")
                        texto_voz = re.sub(r"\{usuario\}", lambda _: nombre, tpl)

                        # Solo se marca como saludado cuando realmente se encola.
                        if self.cfg.get("anti_repeticion_bienvenida", True):
                            self._ya_saludado(uid)
                        self._ultimo_saludo_tiempo = ahora
                        self._encolar_voz(prioridad=3, texto=texto_voz)

                @cliente.on(CommentEvent)
                async def _al_comentario(event: CommentEvent):
                    nombre = getattr(event.user, "nickname", None) or getattr(event.user, "unique_id", "Usuario")
                    comentario = normalizar_comentario(
                        event.comment or "",
                        self.cfg.get("filtrar_links", True),
                        self.cfg.get("compactar_emojis", True)
                    )

                    if not self._comentario_valido(comentario):
                        return

                    # Filtro anti-repetición de comentarios ya leídos
                    if self.cfg.get("ignorar_comentarios_repetidos", True):
                        ahora = time.time()
                        self._limpiar_comentarios_vistos(ahora)

                        com_norm = _normalizar_texto_voz(comentario)
                        clave_usuario = f"{nombre.lower()}::{com_norm}"
                        clave_global = f"msg::{com_norm}"

                        ultimo_u = self._comentarios_vistos.get(clave_usuario, 0)
                        ultimo_g = self._comentarios_vistos.get(clave_global, 0)
                        t_limite = int(self.cfg.get("tiempo_anti_repeticion", 45))

                        # Si el mismo usuario repite en < t_limite o varios repiten la misma frase corta en < 15s
                        if (ahora - ultimo_u < t_limite) or (len(com_norm) >= 4 and ahora - ultimo_g < 15):
                            # Se muestra en el chat marcado como repetido, pero no se satura la voz
                            self.emit_ws("com", {"user": nombre, "comment": comentario, "repetido": True})
                            return

                        self._comentarios_vistos[clave_usuario] = ahora
                        self._comentarios_vistos[clave_global] = ahora
                        self._limitar_comentarios_vistos()

                    self.total_comentarios += 1
                    self.emit_ws("com", {"user": nombre, "comment": comentario, "repetido": False})
                    self.emit_ws("stats", {
                        "comments": self.total_comentarios,
                        "gifts": self.total_donaciones,
                        "diamonds": self.total_diamantes
                    })

                    max_c = int(self.cfg.get("max_caracteres", 65))
                    comentario_voz = comentario if len(comentario) <= max_c else f"{comentario[:max_c].rstrip()}..."
                    nombre_para_voz = limpiar_nombre_para_voz(nombre) if self.cfg.get("limpiar_nombres_usuarios", True) else nombre

                    if self.cfg.get("leer_nombre", True):
                        fmt = self.cfg.get("formato_usuario", "{usuario} dice: {mensaje}")
                        vals = {"usuario": nombre_para_voz, "mensaje": comentario_voz}
                        texto_voz = re.sub(r"\{(usuario|mensaje)\}", lambda m: vals.get(m.group(1), m.group(0)), fmt)
                    else:
                        texto_voz = comentario_voz

                    self._encolar_voz(prioridad=2, texto=texto_voz)

                @cliente.on(GiftEvent)
                async def _al_regalo(event: GiftEvent):
                    if not self.cfg.get("donaciones_activas", True):
                        return
                    if self.cfg.get("esperar_racha", True) and getattr(event, "streaking", False):
                        return

                    nombre = getattr(event.user, "nickname", None) or getattr(event.user, "unique_id", "Usuario")
                    regalo = getattr(getattr(event, "gift", None), "name", "Regalo") or "Regalo"
                    diamantes_u = getattr(getattr(event, "gift", None), "diamond_count", 1) or 1
                    cantidad = getattr(event, "repeat_count", 1) or 1
                    total_dia = diamantes_u * cantidad

                    if total_dia < self.cfg.get("min_diamantes", 1):
                        return

                    self.total_donaciones += 1
                    self.total_diamantes += total_dia
                    self.emit_ws("don", {"user": nombre, "gift": regalo, "count": cantidad, "diamonds": total_dia})
                    self.emit_ws("stats", {
                        "comments": self.total_comentarios,
                        "gifts": self.total_donaciones,
                        "diamonds": self.total_diamantes
                    })

                    # Control multimedia / Acción interactiva (YouTube Music / Spotify)
                    if self.cfg.get("accion_multimedia_activa", False):
                        min_dia_media = int(self.cfg.get("min_diamantes_multimedia", 1) or 1)
                        if total_dia >= min_dia_media:
                            tipo_accion = self.cfg.get("tipo_accion_multimedia", "next")
                            self.ejecutar_accion_multimedia(tipo_accion, nombre)

                    # Secuencia de donación: primero sonido de alerta si está activo, y después voz
                    texto_don = ""
                    if self.cfg.get("leer_donacion", True):
                        tpl = self.cfg.get("tpl_donacion", "¡Muchas gracias a {usuario} por enviar {cantidad} {regalo}!")
                        vals = {
                            "usuario": nombre,
                            "regalo": regalo,
                            "cantidad": str(cantidad),
                            "diamantes": str(total_dia),
                        }
                        texto_don = re.sub(r"\{(usuario|regalo|cantidad|diamantes)\}", lambda m: vals.get(m.group(1), m.group(0)), tpl)

                    def _ejecutar_audio_donacion(txt=texto_don):
                        if self.cfg.get("sonido_activo", True):
                            tipo_s = self.cfg.get("tipo_sonido", "Campana (Suave)")
                            snd_path = self._resolver_sonido(tipo_s)
                            audio_assets.reproducir_sonido_alerta_sincrono(snd_path, volumen=int(self.cfg.get("volumen", 100) or 100))
                            time.sleep(0.12)
                        if txt and self.cfg.get("leer_donacion", True):
                            self._encolar_voz(prioridad=1, texto=txt)

                    threading.Thread(target=_ejecutar_audio_donacion, daemon=True).start()

                cliente.run()

            except Exception as exc:
                if not self._debe_correr:
                    break
                err_m = mensaje_error_conexion(exc)
                self.emit_ws("err", {"message": f"Desconexión: {err_m}"})

            if not self._debe_correr:
                break

            if self.cfg.get("auto_reconnect", True):
                reintentos += 1
                if reintentos > max_reintentos:
                    self.emit_ws("err", {"message": "Límite de reconexiones alcanzado."})
                    break
                pausa = min(3 + reintentos * 2, 15)
                self.emit_ws("sis", {"message": f"Reconectando automáticamente en {pausa}s (intento {reintentos}/{max_reintentos})..."})
                self.emit_ws("estado", {"text": f"Reconectando ({reintentos})...", "status": "amber"})

                for _ in range(pausa * 2):
                    if not self._debe_correr:
                        break
                    time.sleep(0.5)
            else:
                break

        self.cliente = None
        self._debe_correr = False
        self.emit_ws("estado", {"text": "Desconectado", "status": "gray"})

    def _compilar_patron_baneadas(self):
        """Precompila un único patrón Regex unificado para filtrado O(1) ultra rápido."""
        raw = str(self.cfg.get("baneadas", "") or "")
        palabras = [re.escape(p.strip().lower()) for p in raw.split(",") if p.strip()]
        if not palabras:
            return None
        patron_str = r"(?:\b|_)(?:" + "|".join(palabras[:500]) + r")(?:\b|_)"
        try:
            return re.compile(patron_str, re.IGNORECASE)
        except Exception:
            return None

    def _comentario_valido(self, comentario: str) -> bool:
        if not comentario:
            return False
        if self._patron_baneadas is not None:
            if self._patron_baneadas.search(comentario):
                return False
        return True

    def _encolar_voz(self, prioridad: int, texto: str):
        texto = str(texto or "").strip()
        if not texto:
            return
        max_q = int(self.cfg.get("max_cola", 4) or 4)
        with self._cola_lock:
            if self.cola_voz.qsize() >= max_q and prioridad >= 2:
                return
            self.cola_voz.put((prioridad, time.time(), texto[:MAX_TEXTO_VOZ]))
            tamano = self.cola_voz.qsize()
        self.emit_ws("queue", {"count": tamano})

    def silenciar_inmediato(self):
        audio_assets.detener_todo_el_audio()
        if self._sapi_engine:
            try:
                self._sapi_engine.stop()
            except Exception:
                pass
        if self._sapi_voice:
            try:
                # 2 = SVSFPurgeBeforeSpeak en SAPI nativo: detiene la síntesis actual de inmediato
                self._sapi_voice.Speak("", 2)
            except Exception:
                pass
        with self._cola_lock:
            with self.cola_voz.mutex:
                self.cola_voz.queue.clear()
        self.emit_ws("queue", {"count": 0})
        self.emit_ws("tts_estado", {"state": "listo", "detail": "Audio silenciado de inmediato."})
        self.emit_ws("sis", {"message": "Audio silenciado de inmediato y cola vaciada."})

    def ejecutar_accion_multimedia(self, accion: str, usuario: str = ""):
        """Envía comandos multimedia nativos de Windows a YouTube Music / Spotify."""
        mapeo = {
            "next": (0xB0, "Siguiente canción ⏭️"),
            "prev": (0xB1, "Canción anterior ⏮️"),
            "play_pause": (0xB3, "Pausa / Reproducir ⏯️"),
        }
        info = mapeo.get(accion)
        if not info:
            return
        vk, etiqueta = info
        if enviar_tecla_multimedia(vk):
            msg = f"🎵 [YouTube Music] {etiqueta}" + (f" por donación de {usuario}" if usuario else "")
            self.emit_ws("sis", {"message": msg})
            self.emit_ws("toast", {"message": msg})
        else:
            self.emit_ws("toast", {
                "message": "Windows no permitió enviar la tecla multimedia. "
                           "Reproduce música en YouTube Music o Spotify y vuelve a probar."
            })

    # ------------------------------------------------------------------ VOCES
    def descargar_modelo_voz(self, voz_id: str):
        """Descarga una voz neuronal offline (Piper) desde la propia aplicación."""
        entrada = next((v for v in VOZ_CATALOGO_PIPER if v["id"] == voz_id), None)
        if not entrada or not entrada.get("ruta"):
            self.emit_ws("toast", {"message": "Esa voz no se puede descargar."})
            return
        if self._descarga_voz_activa:
            self.emit_ws("toast", {"message": "Ya hay una descarga de voz en curso."})
            return
        self._descarga_voz_activa = True
        try:
            threading.Thread(target=self._hilo_descarga_voz, args=(entrada,), daemon=True).start()
        except RuntimeError:
            self._descarga_voz_activa = False

    def _hilo_descarga_voz(self, entrada: dict):
        voz_id = entrada["id"]
        etiqueta = entrada["etiqueta"]

        def _progreso(percent, mb, total_mb, velocidad):
            self.emit_ws("voice_download", {
                "id": voz_id, "state": "downloading", "percent": percent,
                "mb": mb, "total_mb": total_mb, "speed": f"{velocidad:.1f} MB/s",
                "message": f"Descargando {etiqueta}...",
            })

        try:
            self.emit_ws("sis", {"message": f"⬇️ Descargando voz {etiqueta} (~{entrada['mb']:.0f} MB)..."})
            _progreso(0, 0, float(entrada.get("mb") or 0), 0.0)

            ruta = tts_voces.descargar(voz_id, PIPER_DIR, progreso=_progreso)
            tam_mb = round(os.path.getsize(ruta) / 1048576, 1)

            self.emit_ws("voice_download", {
                "id": voz_id, "state": "done", "percent": 100,
                "mb": tam_mb, "total_mb": tam_mb, "speed": "",
                "message": f"{etiqueta} lista para usar.",
            })
            self.emit_ws("sis", {"message": f"✅ Voz neuronal instalada: {etiqueta}"})
            self.emit_ws("toast", {"message": f"Voz descargada: {etiqueta}"})
            self.emit_ws("catalogo_piper", {"catalogo": catalogo_voces_piper()})
        except Exception as e:  # noqa: BLE001
            self.emit_ws("voice_download", {
                "id": voz_id, "state": "error", "percent": 0, "mb": 0, "total_mb": 0,
                "speed": "", "message": f"No se pudo descargar la voz: {e}",
            })
            self.emit_ws("toast", {"message": "Error al descargar la voz. Comprueba tu conexión."})
        finally:
            self._descarga_voz_activa = False

    # ------------------------------------------------------------------ ACTUALIZACIONES
    def comprobar_actualizacion(self, manual: bool = False):
        """Consulta version.json desde Python.

        Se hace aqui y no en el navegador porque la aplicacion se sirve desde
        127.0.0.1, de modo que la peticion a mybot-79861.web.app es de otro origen
        y el navegador la bloquearia por CORS (Firebase Hosting no envia
        Access-Control-Allow-Origin). Python no tiene esa restriccion.
        """

        if self._comprobando_actualizacion:
            return

        def _worker():
            try:
                url = f"{UPDATE_URL}?t={int(time.time())}"
                peticion = urllib.request.Request(
                    url,
                    headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"},
                )
                with urllib.request.urlopen(peticion, timeout=15) as respuesta:
                    datos = json.loads(respuesta.read().decode("utf-8"))

                remota = str(datos.get("version", "") or "")
                if _version_mayor(remota, APP_VERSION):
                    payload = dict(datos)
                    payload["manual"] = manual
                    self.emit_ws("nueva_version", payload)
                else:
                    self.emit_ws("sin_actualizacion", {"version": APP_VERSION, "manual": manual})
            except Exception as e:  # noqa: BLE001
                self.emit_ws("error_actualizacion", {"error": str(e), "manual": manual})
            finally:
                self._comprobando_actualizacion = False

        self._comprobando_actualizacion = True
        try:
            threading.Thread(target=_worker, daemon=True).start()
        except RuntimeError:
            self._comprobando_actualizacion = False

    def descargar_actualizacion(self, url: str, sha256_esperado: str = ""):
        """Descarga el instalador de actualización dentro de la app (sin navegador) y
        verifica su firma SHA-256 antes de permitir la instalación."""
        if getattr(self, "_descarga_activa", False):
            self.emit_ws("toast", {"message": "Ya hay una descarga de actualización en curso."})
            return

        try:
            url, filename = validar_url_actualizacion(url)
            sha_esperado = str(sha256_esperado or "").strip().upper()
            if not re.fullmatch(r"[0-9A-F]{64}", sha_esperado):
                raise ValueError(
                    "La actualización no incluye una firma SHA-256 válida. "
                    "No se descargará por seguridad."
                )
        except ValueError as e:
            self.emit_ws("update_error", {"error": str(e)})
            self.emit_ws("toast", {"message": str(e)})
            return

        # Se marca antes de crear el hilo: dos clics rápidos no pueden lanzar
        # dos descargas simultáneas del mismo instalador.
        self._descarga_activa = True

        def _hilo_descarga():
            self._instalador_listo = ""
            self._instalador_hash = ""
            self._instalador_dir = ""
            destino = ""

            try:
                self.emit_ws("update_progress", {
                    "percent": 0,
                    "downloaded_mb": 0,
                    "total_mb": 0,
                    "speed": "Conectando...",
                    "state": "starting"
                })

                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=45) as resp:
                    # Un redirect no puede sacarnos del proyecto oficial.
                    if not _url_de_actualizacion_oficial(urllib.parse.urlparse(resp.geturl())):
                        raise RuntimeError("La descarga redirigió a un servidor no oficial.")

                    total_bytes = int(resp.headers.get("Content-Length", 0) or 0)
                    if total_bytes > MAX_UPDATE_BYTES:
                        raise RuntimeError("El instalador remoto es demasiado grande.")
                    total_mb = round(total_bytes / (1024 * 1024), 1) if total_bytes else 0
                    descargados = 0
                    t_inicio = time.time()
                    t_ultimo_envio = 0

                    carpeta = tempfile.mkdtemp(prefix="mybot_update_")
                    self._instalador_dir = carpeta
                    destino = os.path.join(carpeta, filename)

                    with open(destino, "wb") as f_out:
                        while True:
                            chunk = resp.read(128 * 1024)  # 128 KB
                            if not chunk:
                                break
                            descargados += len(chunk)
                            if descargados > MAX_UPDATE_BYTES:
                                raise RuntimeError("El instalador remoto supera el tamaño permitido.")
                            f_out.write(chunk)

                            ahora = time.time()
                            if ahora - t_ultimo_envio >= 0.25 or descargados == total_bytes:
                                t_ultimo_envio = ahora
                                transcurrido = max(0.001, ahora - t_inicio)
                                velocidad_mb = (descargados / (1024 * 1024)) / transcurrido
                                pct = int((descargados / total_bytes * 100)) if total_bytes else 50
                                mb_down = round(descargados / (1024 * 1024), 1)

                                self.emit_ws("update_progress", {
                                    "percent": pct,
                                    "downloaded_mb": mb_down,
                                    "total_mb": total_mb,
                                    "speed": f"{velocidad_mb:.1f} MB/s",
                                    "state": "downloading"
                                })

                # Verificación de integridad obligatoria: no se permite instalar un
                # archivo que no coincida con el hash publicado en version.json.
                calculado = _sha256_archivo(destino)
                if calculado != sha_esperado:
                    raise RuntimeError(
                        "El archivo descargado no coincide con la firma SHA-256 publicada. "
                        "Se ha descartado por seguridad."
                    )
                self._instalador_hash = sha_esperado
                self._instalador_listo = destino
                self.emit_ws("sis", {"message": "🔒 Firma SHA-256 verificada correctamente."})
                self.emit_ws("update_ready", {
                    "installer_path": destino,
                    "message": "¡Descarga completada con éxito!"
                })
                self.emit_ws("toast", {"message": "✓ Actualización lista. Pulsa 'Iniciar Instalador'."})
            except Exception as e:
                try:
                    if destino and os.path.exists(destino):
                        os.remove(destino)
                except OSError:
                    pass
                self._instalador_listo = ""
                self._instalador_hash = ""
                self.emit_ws("update_error", {"error": str(e)})
                self.emit_ws("toast", {"message": f"Error descargando actualización: {e}"})
            finally:
                self._descarga_activa = False

        try:
            threading.Thread(target=_hilo_descarga, daemon=True).start()
        except RuntimeError:
            self._descarga_activa = False

    def ejecutar_instalador(self, ruta: str = ""):
        """Ejecuta únicamente el instalador descargado y verificado por esta app."""
        destino = getattr(self, "_instalador_listo", "")
        if not destino or not os.path.isfile(destino):
            self.emit_ws("toast", {"message": "El archivo del instalador no existe o aún no se ha descargado."})
            return False

        # La ruta que llega desde JavaScript no se usa nunca para ejecutar algo
        # distinto del archivo que la propia app descargó y verificó.
        if ruta and os.path.abspath(str(ruta)) != os.path.abspath(destino):
            self.emit_ws("toast", {"message": "Ruta de instalador no permitida."})
            return False
        if not destino.lower().endswith(".exe"):
            self.emit_ws("toast", {"message": "El archivo de actualización no es un ejecutable."})
            return False

        try:
            if _sha256_archivo(destino) != self._instalador_hash:
                self.emit_ws("toast", {"message": "El instalador cambió después de la descarga. Se cancela."})
                return False

            # Si esta versión de MyBot ya está firmada, exigimos que la actualización
            # también lo esté. Así una actualización manipulada no puede ejecutarse.
            if getattr(sys, "frozen", False) and _firma_autentica(sys.executable):
                if not _firma_autentica(destino):
                    self.emit_ws("toast", {
                        "message": "El instalador no tiene una firma digital válida. Se cancela."
                    })
                    return False

            os.startfile(destino)
            self.emit_ws("toast", {"message": "🚀 Lanzando asistente de instalación..."})
            self.emit_ws("sis", {"message": f"[Actualización] Instalador ejecutado: {os.path.basename(destino)}"})
            # El instalador necesita reemplazar MyBot.exe y los archivos de _internal,
            # que estan bloqueados mientras la aplicacion sigue abierta. Se avisa a la
            # interfaz para que cierre la aplicacion en cuanto el asistente arranque.
            self.emit_ws("app_cerrando", {"delay_ms": 2500})
            return True
        except Exception as e:
            self.emit_ws("toast", {"message": f"No se pudo ejecutar el instalador: {e}"})
            return False

    def _hilo_tts(self):
        while True:
            item = self.cola_voz.get()
            if item is None:
                break

            prioridad, tiempo_encolado, texto = item
            ahora = time.time()
            ttl = int(self.cfg.get("ttl_comentarios_cola", 20) or 20)

            # TTL Anti-Lag: si un comentario lleva más de ttl segundos esperando, se descarta para mantener tiempo real
            if prioridad >= 2 and (ahora - tiempo_encolado > ttl):
                self.emit_ws("sis", {
                    "message": "⚡ Comentario antiguo descartado para mantener el directo en tiempo real."
                })
                self.cola_voz.task_done()
                self.emit_ws("queue", {"count": self.cola_voz.qsize()})
                continue

            cfg = dict(self.cfg)
            # Aceleración dinámica anti-lag si la cola se acumula
            if self.cfg.get("aceleracion_dinamica", True) and self.cola_voz.qsize() >= 2:
                vel_actual = int(cfg.get("velocidad", 0) or 0)
                cfg["velocidad"] = min(100, vel_actual + 20)

            try:
                respaldo_usado = False
                motor_actual = cfg.get("motor", "piper")

                if motor_actual == "sapi5":
                    self._hablar_sapi5(texto, cfg)

                elif motor_actual == "piper":
                    try:
                        self._hablar_piper(texto, cfg)
                    except Exception:  # noqa: BLE001
                        # El modelo .onnx no está descargado o falló el motor offline:
                        # no dejamos el directo mudo, pasamos a otra voz.
                        self._avisar_una_vez(
                            "La voz neuronal offline no está descargada. Ve a «Voz & Presets» y "
                            "pulsa «Descargar» para instalarla. Mientras tanto se usa otra voz.",
                            "Voz offline no descargada: usando voz alternativa.",
                        )
                        respaldo_usado = self._hablar_voz_alternativa(texto)

                elif self._edge_disponible:
                    try:
                        self._hablar_edge(texto, cfg)
                    except Exception:  # noqa: BLE001
                        # Edge TTS no responde (p. ej. error 403 del servicio):
                        # pasamos a una voz alternativa de forma permanente.
                        self._edge_disponible = False
                        self._avisar_una_vez(
                            "Edge TTS no disponible (error 403). Usando voz alternativa automáticamente.",
                            "Edge TTS bloqueado: usando voz alternativa.",
                        )
                        respaldo_usado = self._hablar_voz_alternativa(texto)

                else:
                    # Edge TTS ya falló antes: usamos directamente la voz alternativa.
                    respaldo_usado = self._hablar_voz_alternativa(texto)

                if respaldo_usado:
                    self.emit_ws("tts_estado", {
                        "state": "listo",
                        "detail": "Leído con voz alternativa (Edge TTS no disponible)."
                    })
                else:
                    self.emit_ws("tts_estado", {"state": "listo", "detail": "Voz lista para nuevos comentarios."})
            except Exception as e:
                self.emit_ws("tts_estado", {"state": "fallando", "detail": mensaje_error_tts(e)})
            finally:
                self.cola_voz.task_done()
                self.emit_ws("queue", {"count": self.cola_voz.qsize()})

    def _avisar_una_vez(self, mensaje: str, resumen: str = "Voz alternativa activada."):
        """Muestra un aviso en el chat solo la primera vez (evita saturar)."""
        if not self._aviso_respaldo_tts:
            self._aviso_respaldo_tts = True
            self.emit_ws("sis", {"message": mensaje})
            self.emit_ws("toast", {"message": resumen})

    @staticmethod
    def _idioma_gtts(cfg: dict) -> str:
        """Deduce el idioma para gTTS a partir de la voz elegida (p. ej. es-AR -> es)."""
        voz = str(cfg.get("voz_id") or cfg.get("voz_nombre") or "")
        match = re.match(r"^([a-zA-Z]{2})[-_]", voz)
        if match:
            return match.group(1).lower()
        return "es"

    def _generar_mp3_gtts(self, texto: str) -> str:
        """Genera un MP3 con la voz de Google (gTTS) y devuelve su ruta temporal."""
        from gtts import gTTS

        ruta_temp = os.path.join(tempfile.gettempdir(), f"mybot_gtts_{uuid.uuid4().hex[:8]}.mp3")
        gTTS(texto, lang=self._idioma_gtts(self.cfg), slow=False).save(ruta_temp)
        return ruta_temp

    def _hablar_gtts(self, texto: str, cfg: dict):
        """Habla con la voz de Google (gTTS). Requiere conexión a Internet."""
        ruta_temp = ""
        try:
            self.emit_ws("tts_estado", {"state": "cargando", "detail": "Generando voz alternativa (Google)..."})
            ruta_temp = self._generar_mp3_gtts(texto)
            self.emit_ws("tts_estado", {"state": "reproduciendo", "detail": "Hablando (voz alternativa)..."})
            audio_assets.reproducir_mp3_tts(ruta_temp, volumen=int(cfg.get("volumen", 100) or 100))
        finally:
            if ruta_temp and os.path.exists(ruta_temp):
                try:
                    os.remove(ruta_temp)
                except OSError:
                    pass

    def _es_modelo_piper(self, modelo: str) -> bool:
        return bool(modelo) and tts_voces.instalada(PIPER_DIR, modelo)

    def _modelo_piper(self, cfg: dict) -> str:
        """Devuelve un modelo Piper válido (el configurado o el primero disponible)."""
        modelo = str(cfg.get("voz_id") or "")
        if modelo == "es_AR-mateo-hombre" or self._es_modelo_piper(modelo):
            return modelo
        voces = obtener_voces_piper()
        return voces[0][1] if voces else ""

    def _sintetizar_piper(self, texto: str, cfg: dict) -> str:
        """Sintetiza un WAV con Piper (voz neuronal OFFLINE) en memoria y devuelve su ruta temporal.
        Aplica cambio de tono en RAM evitando dobles lecturas/escrituras en disco."""
        import io
        import wave

        modelo = self._modelo_piper(cfg)
        if not modelo:
            raise RuntimeError("No hay ningún modelo de voz Piper instalado.")

        es_mateo = (modelo == "es_AR-mateo-hombre")
        modelo_onnx = "es_AR-daniela-high" if es_mateo else modelo

        if self._piper_voz is None or self._piper_modelo != modelo_onnx:
            self.emit_ws("tts_estado", {"state": "cargando", "detail": "Cargando voz neuronal offline..."})
            from piper import PiperVoice

            self._piper_voz = None
            self._piper_modelo = None
            ruta_onnx = _archivo_modelo_piper(modelo_onnx)
            self._piper_voz = PiperVoice.load(ruta_onnx)
            self._piper_modelo = modelo_onnx

        mem_wav = io.BytesIO()
        with wave.open(mem_wav, "wb") as wav_file:
            sint = self._sintesis_piper(cfg)
            if sint is not None:
                try:
                    self._piper_voz.synthesize_wav(texto, wav_file, syn_config=sint)
                except TypeError:
                    self._piper_voz.synthesize_wav(texto, wav_file)
            else:
                self._piper_voz.synthesize_wav(texto, wav_file)

        datos_wav = mem_wav.getvalue()
        factor = self._factor_tono(cfg)
        if abs(factor - 1.0) > 0.01:
            datos_wav = self._cambiar_tono_wav_bytes(datos_wav, factor)

        ruta_salida = os.path.join(tempfile.gettempdir(), f"mybot_piper_{uuid.uuid4().hex[:8]}.wav")
        with open(ruta_salida, "wb") as f_out:
            f_out.write(datos_wav)
        return ruta_salida

    def _hablar_piper(self, texto: str, cfg: dict):
        """Habla con una voz neuronal OFFLINE (Piper). No requiere Internet."""
        ruta_wav = ""
        try:
            ruta_wav = self._sintetizar_piper(texto, cfg)
            self.emit_ws("tts_estado", {"state": "reproduciendo", "detail": "Hablando (voz neuronal offline)..."})
            audio_assets.reproducir_wav_tts(ruta_wav)
        finally:
            if ruta_wav and os.path.exists(ruta_wav):
                try:
                    os.remove(ruta_wav)
                except OSError:
                    pass

    def _generar_clip_audio(self, texto: str) -> str:
        """Genera un clip de audio con el motor de voz ACTIVO (Piper/Edge/gTTS) y devuelve su ruta.
        Antes se usaba siempre Edge TTS, por lo que la descarga fallaba con el error 403."""
        motor = str(self.cfg.get("motor", "piper") or "piper")

        piper = lambda t: self._sintetizar_piper(t, self.cfg)  # noqa: E731

        candidatos = {}
        if motor == "piper" or (motor == "sapi5" and obtener_voces_piper()):
            candidatos["Piper (offline)"] = piper
        if motor == "edge":
            candidatos["Edge TTS"] = self._generar_mp3_edge
        if self.cfg.get("usar_gtts", True):
            candidatos["Google (gTTS)"] = self._generar_mp3_gtts
        candidatos.setdefault("Edge TTS", self._generar_mp3_edge)
        candidatos.setdefault("Piper (offline)", piper)

        ultimo_error = None
        for etiqueta, generar in candidatos.items():
            try:
                return generar(texto)
            except Exception as exc:  # noqa: BLE001
                ultimo_error = exc
                self.emit_ws("sis", {"message": f"Motor {etiqueta} no disponible ({exc}). Probando otro."})

        raise RuntimeError(f"Ningún motor de voz disponible ({ultimo_error}).")

    @staticmethod
    def _factor_tono(cfg: dict) -> float:
        """Convierte el ajuste de 'tono' (-50..50) en un factor de frecuencia (>1 = más agudo)."""
        tono = int(cfg.get("tono", 0) or 0)
        modelo = str(cfg.get("voz_id") or "")
        if modelo == "es_AR-mateo-hombre":
            tono -= 28  # Modula Daniela hacia frecuencia masculina
        return max(0.5, min(2.0, 1.0 + tono / 100.0))

    @staticmethod
    def _ssml_tono(texto: str, cfg: dict) -> str:
        """Devuelve SSML con cambio de tono para SAPI5 (vacío si el tono es 0)."""
        tono = int(cfg.get("tono", 0) or 0)
        if not tono:
            return ""
        seguro = (
            texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        return f'<prosody pitch="{tono:+d}%">{seguro}</prosody>'

    def _sintesis_piper(self, cfg: dict):
        """Configuración de Piper (compensa velocidad y luego el cambio de tono)."""
        try:
            from piper import SynthesisConfig
        except Exception:  # noqa: BLE001
            return None

        velocidad = int(cfg.get("velocidad", 0) or 0)
        volumen = int(cfg.get("volumen", 100) or 100)
        factor = self._factor_tono(cfg)
        # Piper alarga la síntesis por 'factor'; después el cambio de tono la acorta.
        length_scale = max(0.25, min(4.0, factor / (1.0 + velocidad / 100.0)))
        modelo = str(cfg.get("voz_id") or "")
        # En Sharvard (es_ES), speaker 1 es la voz femenina española
        speaker_id = 1 if modelo == "es_ES-sharvard-medium" else None
        try:
            return SynthesisConfig(speaker_id=speaker_id, length_scale=length_scale, volume=volumen / 100.0)
        except TypeError:
            try:
                return SynthesisConfig(length_scale=length_scale)
            except Exception:  # noqa: BLE001
                return None
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _cambiar_tono_wav_bytes(datos_in: bytes, factor: float) -> bytes:
        """Sube/baja el tono remuestreando el WAV en RAM usando float32 para máximo rendimiento."""
        import io
        import wave
        import numpy as np

        if not datos_in:
            return datos_in

        with wave.open(io.BytesIO(datos_in), "rb") as entrada:
            params = entrada.getparams()
            datos = np.frombuffer(entrada.readframes(entrada.getnframes()), dtype=np.int16)

        if datos.size == 0:
            return datos_in

        nuevo_tam = max(1, int(round(datos.size / factor)))
        indices = np.linspace(0, datos.size - 1, nuevo_tam)
        muestras = np.interp(indices, np.arange(datos.size), datos.astype(np.float32))
        muestras = np.clip(muestras, -32768, 32767).astype(np.int16)

        out_io = io.BytesIO()
        with wave.open(out_io, "wb") as salida:
            salida.setparams(params)
            salida.writeframes(muestras.tobytes())
        return out_io.getvalue()

    @staticmethod
    def _cambiar_tono_wav(ruta_in: str, ruta_out: str, factor: float) -> None:
        """Compatibilidad con scripts externos."""
        with open(ruta_in, "rb") as f_in:
            datos_out = MyBotService._cambiar_tono_wav_bytes(f_in.read(), factor)
        with open(ruta_out, "wb") as f_out:
            f_out.write(datos_out)

    def _hablar_voz_alternativa(self, texto: str) -> bool:
        """Voz de reemplazo cuando Edge TTS no está disponible. Prioriza la voz
        neuronal offline argentina (Piper) y, si falla, gTTS y la voz local."""
        if obtener_voces_piper():
            try:
                self._hablar_piper(texto, self.cfg)
                return True
            except Exception as exc:  # noqa: BLE001
                self.emit_ws("sis", {
                    "message": f"Voz neuronal offline no disponible ({exc}). Probando otra alternativa."
                })

        if self.cfg.get("usar_gtts", True):
            try:
                self._hablar_gtts(texto, self.cfg)
                return True
            except Exception as exc:  # noqa: BLE001
                self.emit_ws("sis", {
                    "message": f"Voz alternativa online no disponible ({exc}). Usando voz local de Windows."
                })

        self._hablar_sapi5(texto, self._cfg_respaldo())
        return True

    def _generar_mp3_edge(self, texto: str) -> str:
        """Genera un MP3 con Edge TTS usando la configuración actual y devuelve su ruta temporal."""
        import edge_tts

        cfg = self.cfg
        voz_id = cfg.get("voz_id") or "es-AR-TomasNeural"
        tono = cfg.get("tono", 0)
        vel = cfg.get("velocidad", 0)
        vol = cfg.get("volumen", 100)

        rate_str = f"{vel:+d}%"
        pitch_str = f"{tono:+d}Hz"
        vol_str = f"{vol:+d}%" if vol != 100 else "+0%"

        ruta_temp = os.path.join(tempfile.gettempdir(), f"mybot_edge_{uuid.uuid4().hex[:8]}.mp3")

        async def _generar():
            com = edge_tts.Communicate(texto, voz_id, rate=rate_str, pitch=pitch_str, volume=vol_str)
            await com.save(ruta_temp)

        if self.loop and self.loop.is_running():
            futuro = asyncio.run_coroutine_threadsafe(_generar(), self.loop)
            futuro.result(timeout=25)
        else:
            asyncio.run(_generar())
        return ruta_temp

    def _hablar_edge(self, texto: str, cfg: dict):
        voz_nombre = cfg.get("voz_nombre") or cfg.get("voz_id") or "voz"
        ruta_temp = ""
        try:
            self.emit_ws("tts_estado", {"state": "cargando", "detail": f"Descargando voz ({voz_nombre})..."})
            ruta_temp = self._generar_mp3_edge(texto)
            self.emit_ws("tts_estado", {"state": "reproduciendo", "detail": f"Reproduciendo voz ({voz_nombre})..."})
            audio_assets.reproducir_mp3_tts(ruta_temp)
        finally:
            if ruta_temp and os.path.exists(ruta_temp):
                try:
                    os.remove(ruta_temp)
                except OSError:
                    pass

    def descargar_voz(self, texto: str):
        """Genera un clip de voz con el motor activo y lo guarda en assets/descargas_audio."""
        texto = (texto or "").strip()[:1000] or "Prueba de voz en directo."
        if self._generando_clip:
            self.emit_ws("toast", {"message": "Ya se está generando un clip de voz."})
            return
        self._generando_clip = True

        def _worker():
            ruta_temp = ""
            try:
                self.emit_ws("toast", {"message": "Generando clip de voz..."})
                self.emit_ws("tts_estado", {"state": "cargando", "detail": "Generando clip de voz para descargar..."})
                ruta_temp = self._generar_clip_audio(texto)
                destino_dir = DESCARGAS_DIR
                os.makedirs(destino_dir, exist_ok=True)
                extension = os.path.splitext(ruta_temp)[1].lower() or ".mp3"
                nombre = time.strftime("mybot_%Y%m%d_%H%M%S") + extension
                destino = os.path.join(destino_dir, nombre)
                with open(ruta_temp, "rb") as src, open(destino, "wb") as dst:
                    dst.write(src.read())
                self.emit_ws("toast", {"message": f"Clip guardado como {nombre}"})
                self.emit_ws("tts_estado", {"state": "listo", "detail": f"Clip guardado en assets/descargas_audio/{nombre}"})
            except Exception as e:
                self.emit_ws("toast", {"message": f"Error al descargar voz: {mensaje_error_tts(e)}"})
                self.emit_ws("tts_estado", {"state": "fallando", "detail": mensaje_error_tts(e)})
            finally:
                self._generando_clip = False
                if ruta_temp and os.path.exists(ruta_temp):
                    try:
                        os.remove(ruta_temp)
                    except OSError:
                        pass

        try:
            threading.Thread(target=_worker, daemon=True).start()
        except RuntimeError:
            self._generando_clip = False

    def _voz_sapi5_es(self) -> str:
        """Devuelve el id de una voz SAPI5 en español si existe (para el respaldo)."""
        for nom, vid in self.voces_sapi5:
            bajo = f"{nom} {vid}".lower()
            if "spanish" in bajo or "españa" in bajo or "es-es" in bajo or "es-ar" in bajo or "es-mx" in bajo:
                return vid
        return ""

    def _cfg_respaldo(self) -> dict:
        """Copia la configuración usando una voz SAPI5 válida para el respaldo local."""
        cfg = dict(self.cfg)
        cfg["voz_id"] = self._voz_sapi5_es()
        return cfg

    def _hablar_sapi5(self, texto: str, cfg: dict):
        """Habla con la voz local de Windows: primero la API nativa SAPI (win32com),
        y si no está disponible, el motor pyttsx3."""
        voz_id = cfg.get("voz_id", "")
        voz_sapi = bool(voz_id) and ("HKEY" in voz_id or voz_id.startswith("{"))
        if not voz_sapi:
            # Si la voz configurada es de Edge (o no es válida), elegimos una voz SAPI5 en español.
            voz_id = self._voz_sapi5_es() or ""
            voz_sapi = bool(voz_id)
        volumen = int(cfg.get("volumen", 100) or 100)
        velocidad = int(cfg.get("velocidad", 0) or 0)

        # 1) API nativa de Windows (SAPI.SpVoice): la opción más fiable y audible.
        try:
            import pythoncom
            import win32com.client

            pythoncom.CoInitialize()
            if self._sapi_voice is None:
                self._sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")

            voice = self._sapi_voice
            if voz_sapi:
                try:
                    asignada = False
                    for v in voice.GetVoices():
                        if voz_id.lower() in str(v.Id).lower():
                            voice.Voice = v
                            asignada = True
                            break
                    if not asignada and "speech_onecore" in voz_id.lower():
                        cp = win32com.client.Dispatch("SAPI.SpObjectTokenCategory")
                        cp.SetId(r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices")
                        for t in cp.EnumerateTokens():
                            if voz_id.lower() in str(t.Id).lower():
                                voice.Voice = t
                                break
                except Exception:
                    pass

            try:
                voice.Rate = max(-10, min(10, int(velocidad / 8)))
                voice.Volume = max(0, min(100, volumen))
            except Exception:
                pass

            self.emit_ws("tts_estado", {"state": "reproduciendo", "detail": "Hablando (voz local de Windows)..."})
            ssml = self._ssml_tono(texto, cfg)
            if ssml:
                voice.Speak(ssml, 8)  # 8 = SVSFIsXML (permite <prosody pitch=...>)
            else:
                voice.Speak(texto, 0)  # 0 = reproducción síncrona
            return
        except Exception as e:  # noqa: BLE001
            self.emit_ws("sis", {"message": f"API SAPI nativa no disponible ({e}); usando pyttsx3."})

        # 2) Respaldo con pyttsx3.
        import pyttsx3

        if self._sapi_engine is None:
            self._sapi_engine = pyttsx3.init(driverName="sapi5")
        engine = self._sapi_engine
        if voz_sapi:
            try:
                engine.setProperty("voice", voz_id)
            except Exception:
                pass
        rate_sapi = int(165 * (1.0 + (velocidad / 100.0)))
        engine.setProperty("rate", max(80, min(350, rate_sapi)))
        engine.setProperty("volume", max(0.0, min(1.0, volumen / 100.0)))
        self.emit_ws("tts_estado", {"state": "reproduciendo", "detail": "Hablando (pyttsx3)..."})
        engine.say(texto)
        engine.runAndWait()


# =============================================================================
# MANEJADORES HTTP Y WEBSOCKET (AIOHTTP)
# =============================================================================
service = None

# CSP mínima: no interfiere con pywebview, pero impide incrustar la app en un
# iframe y bloquear el uso de plugins/objetos.
CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self' ws://127.0.0.1:* ws://localhost:* ws://[::1]:*; "
    "frame-ancestors 'none'; "
    "object-src 'none'; "
    "base-uri 'self'"
)


def _host_valido(request) -> bool:
    """Bloquea DNS rebinding: el Host debe ser el del servidor local."""
    host = (request.headers.get("Host") or "").strip().lower()
    return host in HOSTS_PERMITIDOS


def _origen_valido(request) -> bool:
    """Los navegadores envían Origin al abrir un WebSocket: debe ser local."""
    origen = (request.headers.get("Origin") or "").strip().lower()
    return not origen or origen in ORIGENES_PERMITIDOS


@web.middleware
async def seguridad_middleware(request, handler):
    if not _host_valido(request):
        return web.Response(status=403, text="Forbidden")
    respuesta = await handler(request)
    respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
    respuesta.headers.setdefault("X-Frame-Options", "DENY")
    respuesta.headers.setdefault("Referrer-Policy", "no-referrer")
    respuesta.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    respuesta.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    respuesta.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    respuesta.headers.setdefault("Content-Security-Policy", CSP)
    respuesta.headers.setdefault("Cache-Control", "no-cache")
    return respuesta


async def health_handler(request):
    return web.json_response({"app": "mybot", "version": APP_VERSION})


async def ws_handler(request):
    if not _origen_valido(request):
        return web.Response(status=403, text="Origen no permitido")
    token = request.query.get("token", "")
    if not token or not secrets.compare_digest(token, SESSION_TOKEN):
        return web.Response(status=403, text="Token de sesión no válido")

    ws = web.WebSocketResponse(max_msg_size=MAX_WS_MSG, heartbeat=30)
    await ws.prepare(request)
    service.ws_clients.add(ws)

    # Enviar estado inicial completo
    init_data = {
        "version": APP_VERSION,
        "config": service.cfg,
        "voices_edge": VOICES_EDGE,
        "voices_sapi5": service.voces_sapi5,
        "voices_piper": obtener_voces_piper(),
        "catalogo_piper": catalogo_voces_piper(),
        "presets": BOT_PRESETS,
        "sounds": list(service.sonidos_predeterminados.keys()),
    }
    await ws.send_str(json.dumps({"type": "init", "data": init_data}))

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except (TypeError, ValueError):
                    continue
                if not isinstance(data, dict):
                    continue
                action = data.get("action")

                if action == "connect":
                    service.conectar_tiktok(str(data.get("user", ""))[:200])

                elif action == "disconnect":
                    service.desconectar_tiktok()

                elif action == "mute":
                    service.silenciar_inmediato()

                elif action == "test_voice":
                    txt = str(data.get("text", "Prueba de voz en directo."))[:500]
                    service._encolar_voz(prioridad=1, texto=txt)

                elif action == "download_voice":
                    service.descargar_voz(str(data.get("text", ""))[:1000])

                elif action == "test_donation":
                    tpl = service.cfg.get("tpl_donacion", "¡Muchas gracias a {usuario} por enviar {cantidad} {regalo}!")
                    txt = tpl.replace("{usuario}", "Carlos").replace("{regalo}", "Rosa").replace("{cantidad}", "5").replace("{diamantes}", "5")

                    def _ejecutar_test_donacion(texto=txt):
                        if service.cfg.get("sonido_activo", True):
                            tipo_s = service.cfg.get("tipo_sonido", "Campana (Suave)")
                            snd_path = service._resolver_sonido(tipo_s)
                            audio_assets.reproducir_sonido_alerta_sincrono(snd_path, volumen=int(service.cfg.get("volumen", 100) or 100))
                            time.sleep(0.12)
                        if service.cfg.get("leer_donacion", True):
                            service._encolar_voz(prioridad=1, texto=texto)

                    threading.Thread(target=_ejecutar_test_donacion, daemon=True).start()

                elif action == "test_welcome":
                    user_test = str(data.get("user", "Alex"))[:80]
                    service.emit_ws("join", {"user": user_test, "unique_id": f"@{user_test.lower()}"})
                    tpl = str(data.get("template") or service.cfg.get("tpl_bienvenida", "¡Bienvenido {usuario} al directo!"))
                    txt = tpl.replace("{usuario}", user_test)
                    service._encolar_voz(prioridad=1, texto=txt)

                elif action == "test_media":
                    media_act = str(data.get("media_action", "next"))
                    if media_act in ("next", "prev", "play_pause"):
                        service.ejecutar_accion_multimedia(media_act, "Prueba Manual")

                elif action == "save_config":
                    new_cfg = sanear_config(data.get("config", {}), service.cfg)
                    service.cfg.update(new_cfg)
                    service._patron_baneadas = service._compilar_patron_baneadas()
                    service._aviso_respaldo_tts = False
                    service._edge_disponible = True
                    if service.cfg.get("motor") == "sapi5":
                        # Resolvemos el id real de la voz local seleccionada.
                        nom = service.cfg.get("voz_nombre", "")
                        for n, vid in service.voces_sapi5:
                            if n == nom:
                                service.cfg["voz_id"] = vid
                                break
                    elif service.cfg.get("motor") == "piper":
                        nom = service.cfg.get("voz_nombre", "")
                        # Se busca en el catálogo completo: la voz puede estar aún sin descargar.
                        for v in catalogo_voces_piper():
                            if v["etiqueta"] == nom:
                                service.cfg["voz_id"] = v["id"]
                                break
                    else:
                        v_nom, v_id = resolver_voz_edge(service.cfg.get("voz_nombre"))
                        service.cfg["voz_nombre"] = v_nom
                        service.cfg["voz_id"] = v_id
                    service._guardar_configuracion()
                    await ws.send_str(json.dumps({"type": "toast", "data": {"message": "Configuración guardada"}}))

                elif action == "download_update":
                    url = str(data.get("url", ""))[:1000]
                    service.descargar_actualizacion(url, str(data.get("sha256", "") or "")[:128])

                elif action == "check_update":
                    service.comprobar_actualizacion(bool(data.get("manual", False)))

                elif action == "download_voice_model":
                    service.descargar_modelo_voz(str(data.get("id", "") or "")[:100])

                elif action == "launch_installer":
                    service.ejecutar_instalador(str(data.get("path", ""))[:500])

    finally:
        service.ws_clients.discard(ws)

    return ws


async def index_handler(request):
    """Sirve la interfaz inyectando el token de sesión de esta ejecución."""
    try:
        with open(os.path.join(WEB_DIR, "index.html"), "r", encoding="utf-8") as f:
            html = f.read()
    except OSError:
        return web.Response(status=500, text="No se pudo cargar la interfaz.")
    html = html.replace("__MYBOT_TOKEN__", SESSION_TOKEN)
    html = html.replace("__MYBOT_VERSION__", ASSET_VERSION)
    return web.Response(
        text=html,
        content_type="text/html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


def limpiar_temporales_antiguos():
    """Limpia restos antiguos sin tocar los archivos de otra instancia en curso."""
    temp_dir = tempfile.gettempdir()
    ahora = time.time()
    try:
        for nombre in os.listdir(temp_dir):
            ruta = os.path.join(temp_dir, nombre)
            try:
                edad = ahora - os.path.getmtime(ruta)
                if nombre.startswith("mybot_update_") and os.path.isdir(ruta):
                    if edad > 24 * 3600:
                        shutil.rmtree(ruta, ignore_errors=True)
                elif nombre.startswith("mybot_") and nombre.lower().endswith((".mp3", ".wav")):
                    # Antes se borraba todo al arrancar, incluido el audio que otra
                    # instancia acababa de generar. Ahora solo pasadas 6 horas.
                    if edad > 6 * 3600:
                        os.remove(ruta)
            except OSError:
                pass
    except OSError:
        pass

    # Descargas de voces interrumpidas (.parcial) que ya nadie va a reanudar.
    try:
        for nombre in os.listdir(PIPER_DIR):
            if nombre.endswith(".parcial"):
                ruta = os.path.join(PIPER_DIR, nombre)
                try:
                    if time.time() - os.path.getmtime(ruta) > 24 * 3600:
                        os.remove(ruta)
                except OSError:
                    pass
    except OSError:
        pass


_loop_servidor = None
_runner = None
_site = None


def servidor_activo(puerto: int = PORT) -> bool:
    """Comprueba que el puerto lo ocupa MyBot (no otro programa cualquiera)."""
    import http.client

    conexion = http.client.HTTPConnection("127.0.0.1", puerto, timeout=0.6)
    try:
        conexion.request("GET", "/api/health")
        respuesta = conexion.getresponse()
        if respuesta.status != 200:
            return False
        datos = json.loads(respuesta.read(4096).decode("utf-8", "replace"))
        return datos.get("app") == "mybot"
    except Exception:
        return False
    finally:
        conexion.close()


def detener_servidor():
    """Cierra los WebSocket y detiene el bucle de eventos desde otro hilo."""
    global _loop_servidor
    loop = _loop_servidor
    if loop is None or not loop.is_running():
        return

    async def _cerrar():
        if service is not None:
            for ws in list(service.ws_clients):
                try:
                    await ws.close(code=1001, message=b"")
                except Exception:
                    pass
            service.ws_clients.clear()
            try:
                service.cola_voz.put(None)
            except Exception:
                pass
        loop.stop()

    try:
        # Se espera brevemente al cierre ordenado: evita el traceback de
        # ConnectionResetError que aparecía al destruir la ventana WebView2.
        futuro = asyncio.run_coroutine_threadsafe(_cerrar(), loop)
        futuro.result(timeout=2.5)
    except Exception:
        try:
            loop.call_soon_threadsafe(loop.stop)
        except Exception:
            pass


def iniciar_servidor(bloquear: bool = True):
    """Arranca el servidor HTTP/WebSocket en 127.0.0.1.

    bloquear=True (por defecto) mantiene el hilo actual en el bucle de eventos,
    que es lo que espera 'python mybot_backend.py'. La aplicación de escritorio
    (mybot_app.py) lo llama en un hilo con bloquear=False.
    """
    global service, _loop_servidor, _runner, _site
    limpiar_temporales_antiguos()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _excepcion_asyncio(loop_actual, contexto):
        # Al cerrar WebView2 se resetea una conexión HTTP; no es un fallo real.
        if isinstance(contexto.get("exception"), ConnectionResetError):
            return
        loop_actual.default_exception_handler(contexto)

    loop.set_exception_handler(_excepcion_asyncio)
    service = MyBotService(loop)
    _loop_servidor = loop

    app = web.Application(middlewares=[seguridad_middleware])
    app.router.add_get("/", index_handler)
    app.router.add_get("/index.html", index_handler)
    app.router.add_get("/api/health", health_handler)
    app.router.add_get("/ws", ws_handler)
    app.router.add_static("/", WEB_DIR)

    _runner = web.AppRunner(app, access_log=None)
    loop.run_until_complete(_runner.setup())
    _site = web.TCPSite(_runner, "127.0.0.1", PORT)
    loop.run_until_complete(_site.start())

    print(f"[MyBot Server] Servidor activo en http://127.0.0.1:{PORT}")
    sys.stdout.flush()

    if not bloquear:
        return loop

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _loop_servidor = None
        try:
            if _site is not None:
                loop.run_until_complete(_site.stop())
            if _runner is not None:
                loop.run_until_complete(_runner.cleanup())
        except Exception:
            pass
        finally:
            _site = None
            _runner = None
            loop.close()


if __name__ == "__main__":
    iniciar_servidor()
