"""
=============================================================================
 MyBot - Backend Asíncrono para Desktop App (HTTP + WebSockets)
=============================================================================
 Maneja la conexión con TikTok Live, cola de voz prioritaria, Edge TTS,
 SAPI5 de Windows, parada instantánea de audio y filtros anti-spam,
 comunicándose en tiempo real con el frontend de Electron.
=============================================================================
"""

import asyncio
import json
import logging
import os
import queue
import re
import sys
import tempfile
import threading
import time
import uuid

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
from TikTokLive import TikTokLiveClient
from TikTokLive.client.errors import (
    AgeRestrictedError,
    SignAPIError,
    UserNotFoundError,
    UserOfflineError,
    WebcastBlockedError,
)
from TikTokLive.client.web.routes.fetch_user_unique_id import FailedResolveUserId
from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent, GiftEvent
try:
    from TikTokLive.events import JoinEvent
except ImportError:
    JoinEvent = None

import audio_assets
import tts_voces

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
PORT = 58421


def _resolver_archivo_config() -> str:
    """Ruta escribible de config.json. Si el directorio de la app es de solo lectura
    (p. ej. instalada en Program Files), se usa %APPDATA%\\MyBot."""
    local = os.path.join(BASE_DIR, "config.json")
    try:
        if os.path.exists(local):
            with open(local, "r+", encoding="utf-8"):
                return local
        prueba = os.path.join(BASE_DIR, f".escritura_{os.getpid()}")
        with open(prueba, "w", encoding="utf-8") as f:
            f.write("1")
        os.remove(prueba)
        return local
    except OSError:
        pass

    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    carpeta = os.path.join(base, "MyBot")
    try:
        os.makedirs(carpeta, exist_ok=True)
        return os.path.join(carpeta, "config.json")
    except OSError:
        return local


CONFIG_FILE = _resolver_archivo_config()

APP_VERSION = "1.2.0"
USER_AGENT = f"MyBot-Desktop-App/{APP_VERSION}"

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
PIPER_DIR = os.path.join(BASE_DIR, "assets", "voices")
VOZ_CATALOGO_PIPER = tts_voces.CATALOGO


def _archivo_modelo_piper(voz_id: str) -> str:
    return tts_voces.archivo_modelo(PIPER_DIR, voz_id)


def voz_piper_instalada(voz_id: str) -> bool:
    return tts_voces.instalada(PIPER_DIR, voz_id)


def url_modelo_piper(entrada: dict) -> str:
    """URL oficial (.onnx) de un modelo del catálogo."""
    return tts_voces.url_modelo(entrada)


def catalogo_voces_piper() -> list:
    """Catálogo completo con el estado de instalación de cada voz."""
    return tts_voces.catalogo(PIPER_DIR)


def obtener_voces_piper():
    """Voces Piper INSTALADAS, en el orden del catálogo: [(etiqueta, id), ...]."""
    return tts_voces.instaladas(PIPER_DIR)


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
    c = comentario.strip()
    c = re.sub(r"[\x00-\x1f\x7f-\x9f\u200b-\u200f\ufeff]", "", c)
    if filtrar_links:
        c = re.sub(r"(https?://\S+|www\.\S+|\b[a-zA-Z0-9.\-_]+(?:\.com|\.org|\.net|\.io|\.me|\.gg|\.xyz)\b\S*)", "[enlace]", c, flags=re.IGNORECASE)
    c = re.sub(r"(.)\1{3,}", r"\1\1", c)
    if compactar_emojis:
        c = re.sub(r"([\U00010000-\U0010ffff])\1{2,}", r"\1\1", c)
    return c.strip()


def mensaje_error_conexion(exc: Exception) -> str:
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


# =============================================================================
# SERVICIO PRINCIPAL DE MYBOT
# =============================================================================
class MyBotService:
    def __init__(self, loop):
        self.loop = loop
        self.sonidos_predeterminados = audio_assets.generar_sonidos_predeterminados()
        self.voces_sapi5 = obtener_voces_sapi5()
        self.cfg = self._cargar_configuracion()

        # Colas de voz
        self.cola_voz = queue.PriorityQueue()
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

        # Control de bienvenidas y anti-repetición
        self._usuarios_bienvenida = set()
        self._ultimo_saludo_tiempo = 0.0
        self._comentarios_vistos = {}
        self._ultimo_cleanup_comentarios = 0.0
        # Control de actualización in-app sin navegador
        self._descarga_activa = False
        self._instalador_listo = ""
        # Control de descarga de voces neuronales
        self._descarga_voz_activa = False

        # Iniciar hilo de voz
        threading.Thread(target=self._hilo_tts, daemon=True).start()

    def _cargar_configuracion(self):
        # Piper es el motor recomendado. Su modelo no viene en el instalador:
        # si aún no está descargado, la propia app guía al usuario para bajarlo.
        motor_def = "piper"
        voz_nom_def = VOZ_CATALOGO_PIPER[0]["etiqueta"]
        voz_id_def = VOZ_CATALOGO_PIPER[0]["id"]

        defaults = {
            "usuario": "@l.am.lex_",
            "motor": motor_def,
            "voz_nombre": voz_nom_def,
            "voz_id": voz_id_def,
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
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    contenido = f.read().strip()
                    if contenido:
                        c = json.loads(contenido)
                        defaults.update(c)
            except Exception:
                pass

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
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=2)
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
        payload = json.dumps({"type": msg_type, "data": data})
        for ws in list(self.ws_clients):
            if not ws.closed:
                asyncio.run_coroutine_threadsafe(ws.send_str(payload), self.loop)

    def conectar_tiktok(self, usuario_raw: str):
        if self.hilo_cliente and self.hilo_cliente.is_alive():
            if not self._debe_correr:
                self.hilo_cliente.join(timeout=1.2)
            if self.hilo_cliente and self.hilo_cliente.is_alive():
                self.emit_ws("toast", {"message": "Ya hay una conexión activa o en proceso"})
                return

        usuario_limpio = limpiar_nombre_usuario_tiktok(usuario_raw)
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
        limite = int(self.cfg.get("tiempo_anti_repeticion", 45)) * 2
        self._comentarios_vistos = {
            k: t for k, t in self._comentarios_vistos.items()
            if ahora - t < limite
        }

    def _hilo_cliente_loop(self, usuario: str):
        reintentos = 0
        max_reintentos = 15

        while self._debe_correr:
            try:
                cliente = TikTokLiveClient(unique_id=usuario)
                self.cliente = cliente
                logging.getLogger("TikTokLive").setLevel(logging.ERROR)

                @cliente.on(ConnectEvent)
                async def _al_conectar(event: ConnectEvent):
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
                        if self.cfg.get("anti_repeticion_bienvenida", True):
                            if uid in self._usuarios_bienvenida:
                                return
                            self._usuarios_bienvenida.add(uid)

                        # Cooldown entre bienvenidas de voz para no saturar
                        cooldown = max(3, int(self.cfg.get("cooldown_bienvenida", 10)))
                        if ahora - self._ultimo_saludo_tiempo < cooldown:
                            return

                        # Si la cola ya tiene varios mensajes (>= 2), descartar bienvenida (baja prioridad)
                        if self.cola_voz.qsize() >= 2:
                            return

                        tpl = self.cfg.get("tpl_bienvenida", "¡Bienvenido {usuario} al directo!")
                        texto_voz = tpl.replace("{usuario}", nombre)

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
                        texto_voz = fmt.replace("{usuario}", nombre_para_voz).replace("{mensaje}", comentario_voz)
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

                    if self.cfg.get("sonido_activo", True):
                        tipo_s = self.cfg.get("tipo_sonido", "Campana (Suave)")
                        snd_path = self._resolver_sonido(tipo_s)
                        audio_assets.reproducir_sonido_alerta(snd_path)

                    if self.cfg.get("leer_donacion", True):
                        tpl = self.cfg.get("tpl_donacion", "¡Muchas gracias a {usuario} por enviar {cantidad} {regalo}!")
                        texto_don = (tpl.replace("{usuario}", nombre)
                                        .replace("{regalo}", regalo)
                                        .replace("{cantidad}", str(cantidad))
                                        .replace("{diamantes}", str(total_dia)))
                        self._encolar_voz(prioridad=1, texto=texto_don)

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

    def _comentario_valido(self, comentario: str) -> bool:
        if not comentario:
            return False
        texto_bajo = comentario.lower()
        baneadas = [p.strip().lower() for p in self.cfg.get("baneadas", "").split(",") if p.strip()]
        for p in baneadas:
            if p:
                patron = r"(?:\b|_)" + re.escape(p) + r"(?:\b|_)"
                if re.search(patron, texto_bajo):
                    return False
        return True

    def _encolar_voz(self, prioridad: int, texto: str):
        max_q = self.cfg.get("max_cola", 4)
        if self.cola_voz.qsize() >= max_q:
            if prioridad >= 2:
                return
        self.cola_voz.put((prioridad, time.time(), texto))
        self.emit_ws("queue", {"count": self.cola_voz.qsize()})

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
        with self.cola_voz.mutex:
            self.cola_voz.queue.clear()
        self.emit_ws("queue", {"count": 0})
        self.emit_ws("tts_estado", {"state": "listo", "detail": "Audio silenciado de inmediato."})
        self.emit_ws("sis", {"message": "Audio silenciado de inmediato y cola vaciada."})

    def ejecutar_accion_multimedia(self, accion: str, usuario: str = ""):
        """Envía comandos multimedia nativos de Windows a YouTube Music / Spotify."""
        import ctypes
        mapeo = {
            "next": (0xB0, "Siguiente canción ⏭️"),
            "prev": (0xB1, "Canción anterior ⏮️"),
            "play_pause": (0xB3, "Pausa / Reproducir ⏯️"),
        }
        info = mapeo.get(accion)
        if not info:
            return
        vk, etiqueta = info
        try:
            user32 = ctypes.windll.user32
            # Key down + Key up
            user32.keybd_event(vk, 0, 0, 0)
            time.sleep(0.04)
            user32.keybd_event(vk, 0, 2, 0)
            msg = f"🎵 [YouTube Music] {etiqueta}" + (f" por donación de {usuario}" if usuario else "")
            self.emit_ws("sis", {"message": msg})
            self.emit_ws("toast", {"message": msg})
        except Exception as e:
            print(f"[MyBot] Error enviando tecla multimedia: {e}")

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
        threading.Thread(target=self._hilo_descarga_voz, args=(entrada,), daemon=True).start()

    def _hilo_descarga_voz(self, entrada: dict):
        voz_id = entrada["id"]
        etiqueta = entrada["etiqueta"]
        self._descarga_voz_activa = True

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

    def descargar_actualizacion(self, url: str, sha256_esperado: str = ""):
        """Descarga el instalador de actualización dentro de la app (sin navegador) y
        verifica su firma SHA-256 antes de permitir la instalación."""
        if getattr(self, "_descarga_activa", False):
            self.emit_ws("toast", {"message": "Ya hay una descarga de actualización en curso."})
            return

        def _hilo_descarga():
            import hashlib
            import urllib.request

            self._descarga_activa = True
            temp_dir = tempfile.gettempdir()
            filename = url.split("/")[-1].split("?")[0] or "MyBot_v1.2_Instalador.exe"
            destino = os.path.join(temp_dir, filename)
            hash_archivo = hashlib.sha256()

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
                    total_bytes = int(resp.headers.get("Content-Length", 0))
                    total_mb = round(total_bytes / (1024 * 1024), 1) if total_bytes else 0
                    descargados = 0
                    t_inicio = time.time()
                    t_ultimo_envio = 0

                    with open(destino, "wb") as f_out:
                        while True:
                            chunk = resp.read(128 * 1024)  # 128 KB
                            if not chunk:
                                break
                            f_out.write(chunk)
                            hash_archivo.update(chunk)
                            descargados += len(chunk)

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

                # Verificación de integridad: no se permite instalar un archivo que no
                # coincida con el hash publicado en version.json.
                if sha256_esperado:
                    calculado = hash_archivo.hexdigest().upper()
                    if calculado != sha256_esperado.upper():
                        try:
                            os.remove(destino)
                        except OSError:
                            pass
                        raise RuntimeError(
                            "El archivo descargado no coincide con la firma SHA-256 publicada. "
                            "Se ha descartado por seguridad."
                        )
                    self.emit_ws("sis", {"message": "🔒 Firma SHA-256 verificada correctamente."})

                self._instalador_listo = destino
                self.emit_ws("update_ready", {
                    "installer_path": destino,
                    "message": "¡Descarga completada con éxito!"
                })
                self.emit_ws("toast", {"message": "✓ Actualización lista. Pulsa 'Iniciar Instalador'."})
            except Exception as e:
                self.emit_ws("update_error", {"error": str(e)})
                self.emit_ws("toast", {"message": f"Error descargando actualización: {e}"})
            finally:
                self._descarga_activa = False

        hilo = threading.Thread(target=_hilo_descarga, daemon=True)
        hilo.start()

    def ejecutar_instalador(self, ruta: str = ""):
        """Ejecuta el instalador descargado nativamente en Windows sin abrir navegador."""
        destino = ruta or getattr(self, "_instalador_listo", "")
        if not destino or not os.path.exists(destino):
            self.emit_ws("toast", {"message": "El archivo del instalador no existe o aún no se ha descargado."})
            return False

        try:
            os.startfile(destino)
            self.emit_ws("toast", {"message": "🚀 Lanzando asistente de instalación..."})
            self.emit_ws("sis", {"message": f"[Actualización] Instalador ejecutado: {os.path.basename(destino)}"})
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
            audio_assets.reproducir_mp3_tts(ruta_temp)
        finally:
            if ruta_temp and os.path.exists(ruta_temp):
                try:
                    os.remove(ruta_temp)
                except OSError:
                    pass

    def _es_modelo_piper(self, modelo: str) -> bool:
        return bool(modelo) and os.path.exists(os.path.join(PIPER_DIR, f"{modelo}.onnx"))

    def _modelo_piper(self, cfg: dict) -> str:
        """Devuelve un modelo Piper válido (el configurado o el primero disponible)."""
        modelo = str(cfg.get("voz_id") or "")
        if modelo == "es_AR-mateo-hombre" or self._es_modelo_piper(modelo):
            return modelo
        voces = obtener_voces_piper()
        return voces[0][1] if voces else ""

    def _sintetizar_piper(self, texto: str, cfg: dict) -> str:
        """Sintetiza un WAV con Piper (voz neuronal OFFLINE) y devuelve su ruta temporal.
        El archivo ya lleva aplicado el tono, así que sirve tanto para reproducir como para guardar."""
        import wave

        modelo = self._modelo_piper(cfg)
        if not modelo:
            raise RuntimeError("No hay ningún modelo de voz Piper instalado.")

        es_mateo = (modelo == "es_AR-mateo-hombre")
        modelo_onnx = "es_AR-daniela-high" if es_mateo else modelo

        if self._piper_voz is None or self._piper_modelo != modelo_onnx:
            self.emit_ws("tts_estado", {"state": "cargando", "detail": "Cargando voz neuronal offline..."})
            from piper import PiperVoice

            self._piper_voz = PiperVoice.load(os.path.join(PIPER_DIR, f"{modelo_onnx}.onnx"))
            self._piper_modelo = modelo_onnx

        ruta_wav = os.path.join(tempfile.gettempdir(), f"mybot_piper_{uuid.uuid4().hex[:8]}.wav")
        with wave.open(ruta_wav, "wb") as wav_file:
            sint = self._sintesis_piper(cfg)
            if sint is not None:
                try:
                    self._piper_voz.synthesize_wav(texto, wav_file, syn_config=sint)
                except TypeError:
                    self._piper_voz.synthesize_wav(texto, wav_file)
            else:
                self._piper_voz.synthesize_wav(texto, wav_file)

        factor = self._factor_tono(cfg)
        if abs(factor - 1.0) <= 0.01:
            return ruta_wav

        ruta_tono = os.path.join(
            tempfile.gettempdir(), f"mybot_piper_tono_{uuid.uuid4().hex[:8]}.wav"
        )
        try:
            self._cambiar_tono_wav(ruta_wav, ruta_tono, factor)
        except Exception:
            try:
                os.remove(ruta_wav)
            except OSError:
                pass
            raise
        try:
            os.remove(ruta_wav)
        except OSError:
            pass
        return ruta_tono

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
    def _cambiar_tono_wav(ruta_in: str, ruta_out: str, factor: float) -> None:
        """Sube/baja el tono remuestreando el WAV (factor > 1 = más agudo/chillón)."""
        import wave

        import numpy as np

        with wave.open(ruta_in, "rb") as entrada:
            params = entrada.getparams()
            datos = np.frombuffer(entrada.readframes(entrada.getnframes()), dtype=np.int16)

        if datos.size == 0:
            raise RuntimeError("El audio generado está vacío.")

        nuevo_tam = max(1, int(round(datos.size / factor)))
        indices = np.linspace(0, datos.size - 1, nuevo_tam)
        muestras = np.interp(indices, np.arange(datos.size), datos.astype(np.float64))
        muestras = np.clip(muestras, -32768, 32767).astype(np.int16)

        with wave.open(ruta_out, "wb") as salida:
            salida.setparams(params)
            salida.writeframes(muestras.tobytes())

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
        texto = (texto or "").strip() or "Prueba de voz en directo."

        def _worker():
            ruta_temp = ""
            try:
                self.emit_ws("toast", {"message": "Generando clip de voz..."})
                self.emit_ws("tts_estado", {"state": "cargando", "detail": "Generando clip de voz para descargar..."})
                ruta_temp = self._generar_clip_audio(texto)
                destino_dir = os.path.join(BASE_DIR, "assets", "descargas_audio")
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
                if ruta_temp and os.path.exists(ruta_temp):
                    try:
                        os.remove(ruta_temp)
                    except OSError:
                        pass

        threading.Thread(target=_worker, daemon=True).start()

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


async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    service.ws_clients.add(ws)

    # Enviar estado inicial completo
    init_data = {
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
                data = json.loads(msg.data)
                action = data.get("action")

                if action == "connect":
                    service.conectar_tiktok(data.get("user", ""))

                elif action == "disconnect":
                    service.desconectar_tiktok()

                elif action == "mute":
                    service.silenciar_inmediato()

                elif action == "test_voice":
                    txt = data.get("text", "Prueba de voz en directo.")
                    service._encolar_voz(prioridad=1, texto=txt)

                elif action == "download_voice":
                    service.descargar_voz(data.get("text", ""))

                elif action == "test_donation":
                    if service.cfg.get("sonido_activo", True):
                        tipo_s = service.cfg.get("tipo_sonido", "Campana (Suave)")
                        audio_assets.reproducir_sonido_alerta(service._resolver_sonido(tipo_s))
                    tpl = service.cfg.get("tpl_donacion", "¡Muchas gracias a {usuario} por enviar {cantidad} {regalo}!")
                    txt = tpl.replace("{usuario}", "Carlos").replace("{regalo}", "Rosa").replace("{cantidad}", "5").replace("{diamantes}", "5")
                    service._encolar_voz(prioridad=1, texto=txt)

                elif action == "test_welcome":
                    user_test = data.get("user", "Alex")
                    if service.cfg.get("mostrar_bienvenida_chat", True):
                        service.emit_ws("join", {"user": user_test, "unique_id": f"@{user_test.lower()}"})
                    if service.cfg.get("leer_bienvenida", True):
                        tpl = service.cfg.get("tpl_bienvenida", "¡Bienvenido {usuario} al directo!")
                        txt = tpl.replace("{usuario}", user_test)
                        service._encolar_voz(prioridad=3, texto=txt)

                elif action == "test_media":
                    media_act = data.get("media_action", "next")
                    service.ejecutar_accion_multimedia(media_act, "Prueba Manual")

                elif action == "save_config":
                    new_cfg = data.get("config", {})
                    service.cfg.update(new_cfg)
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
                    url = data.get("url", "")
                    service.descargar_actualizacion(url, str(data.get("sha256", "") or ""))

                elif action == "download_voice_model":
                    service.descargar_modelo_voz(str(data.get("id", "") or ""))

                elif action == "launch_installer":
                    ruta = data.get("path", "")
                    service.ejecutar_instalador(ruta)

    finally:
        service.ws_clients.discard(ws)

    return ws


async def index_handler(request):
    return web.FileResponse(os.path.join(WEB_DIR, "index.html"))


def limpiar_temporales_antiguos():
    """Limpia archivos de audio residuales previos en la carpeta temporal de Windows."""
    temp_dir = tempfile.gettempdir()
    try:
        for f in os.listdir(temp_dir):
            if f.startswith("mybot_") and (f.endswith(".mp3") or f.endswith(".wav")):
                try:
                    os.remove(os.path.join(temp_dir, f))
                except OSError:
                    pass
    except Exception:
        pass


def iniciar_servidor():
    global service
    limpiar_temporales_antiguos()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    service = MyBotService(loop)

    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_get("/ws", ws_handler)
    app.router.add_static("/", WEB_DIR)

    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, "127.0.0.1", PORT)
    loop.run_until_complete(site.start())

    print(f"[MyBot Server] Servidor activo en http://127.0.0.1:{PORT}")
    sys.stdout.flush()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    iniciar_servidor()
