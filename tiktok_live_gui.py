"""
=============================================================================
 MyBot - TikTok Live Lector de Comentarios y Donaciones con Voz (TTS Pro)
=============================================================================
 Interfaz UX/UI moderna inspirada en iOS (Light Theme: Blanco y Celeste),
 con icono de app personalizado, tamaño mínimo fijo garantizado,
 botones estilizados y espaciados ergonómicamente, parada instantánea de audio,
 filtros inteligentes anti-spam y soporte completo para voces Edge y SAPI5.
=============================================================================
"""

import asyncio
import json
import logging
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from PIL import Image, ImageDraw, ImageTk

import tts_voces

# Configuración específica para Windows: DPI Awareness y AppUserModelID para icono propio
if sys.platform.startswith("win"):
    try:
        import ctypes
        # Desvincular el proceso de python.exe en la barra de tareas de Windows
        myappid = "mybot.v10.app"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

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

from TikTokLive import TikTokLiveClient
from TikTokLive.client.errors import (
    AgeRestrictedError,
    SignAPIError,
    UserNotFoundError,
    UserOfflineError,
    WebcastBlockedError,
)
from TikTokLive.client.web.routes.fetch_user_unique_id import FailedResolveUserId
from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent, GiftEvent, JoinEvent

import audio_assets

# =============================================================================
# CONSTANTES DE IDENTIDAD & CONFIGURACIÓN
# =============================================================================
APP_NAME = "MyBot"
APP_SUBTITLE = "Lector de Comentarios y Donaciones Pro"
APP_VERSION = "v1.2"
CURRENT_VERSION = "1.2.0"
UPDATE_URL = "https://mybot-79861.web.app/version.json"

if getattr(sys, "frozen", False):
    ASSETS_DIR = os.path.join(getattr(sys, "_MEIPASS", ""), "assets")
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def obtener_ruta_config() -> str:
    """Devuelve la ruta persistente de config.json asegurando permisos de escritura en Windows."""
    local_cfg = os.path.join(BASE_DIR, "config.json")
    try:
        if os.path.exists(local_cfg):
            with open(local_cfg, "a+", encoding="utf-8"):
                pass
            return local_cfg
        test_file = os.path.join(BASE_DIR, f".write_test_{os.getpid()}")
        with open(test_file, "w") as f:
            f.write("1")
        if os.path.exists(test_file):
            os.remove(test_file)
        return local_cfg
    except Exception:
        pass

    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    dir_appdata = os.path.join(appdata, "MyBot")
    try:
        os.makedirs(dir_appdata, exist_ok=True)
        return os.path.join(dir_appdata, "config.json")
    except Exception:
        return local_cfg

CONFIG_FILE = obtener_ruta_config()
ICON_JPG = os.path.join(ASSETS_DIR, "icono.jpg")
ICON_ICO = os.path.join(ASSETS_DIR, "icono.ico")
ICON_PNG = os.path.join(ASSETS_DIR, "icono.png")

# Dimensiones mínimas fijas inalterables
MIN_WIDTH = 750
MIN_HEIGHT = 860

# =============================================================================
# CATÁLOGO DE VOCES
# =============================================================================
VOICES_EDGE = [
    # 🇦🇷 Argentina
    ("🇦🇷 Tomas - Hombre (Argentina)", "es-AR-TomasNeural"),
    ("🇦🇷 Elena - Mujer (Argentina)", "es-AR-ElenaNeural"),
    # 🇪🇸 España
    ("🇪🇸 Alvaro - Hombre (España)", "es-ES-AlvaroNeural"),
    ("🇪🇸 Elvira - Mujer (España)", "es-ES-ElviraNeural"),
    ("🇪🇸 Ximena - Mujer (España)", "es-ES-XimenaNeural"),
    # 🇲🇽 México
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
    # 🇨🇴 Colombia
    ("🇨🇴 Salome - Mujer (Colombia)", "es-CO-SalomeNeural"),
    ("🇨🇴 Gonzalo - Hombre (Colombia)", "es-CO-GonzaloNeural"),
    # 🇨🇱 Chile
    ("🇨🇱 Catalina - Mujer (Chile)", "es-CL-CatalinaNeural"),
    ("🇨🇱 Lorenzo - Hombre (Chile)", "es-CL-LorenzoNeural"),
    # 🇵🇪 Perú
    ("🇵🇪 Camila - Mujer (Perú)", "es-PE-CamilaNeural"),
    ("🇵🇪 Alex - Hombre (Perú)", "es-PE-AlexNeural"),
    # 🇺🇸 Estados Unidos (Latino)
    ("🇺🇸 Alonso - Hombre (EE. UU.)", "es-US-AlonsoNeural"),
    ("🇺🇸 Paloma - Mujer (EE. UU.)", "es-US-PalomaNeural"),
    # 🇻🇪 Venezuela
    ("🇻🇪 Paola - Mujer (Venezuela)", "es-VE-PaolaNeural"),
    ("🇻🇪 Sebastian - Hombre (Venezuela)", "es-VE-SebastianNeural"),
    # Otros países hispanohablantes
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
    # Voces Multilingües
    ("🌐 Brian - Multilingüe", "en-US-BrianMultilingualNeural"),
    ("🌐 Emma - Multilingüe", "en-US-EmmaMultilingualNeural"),
]

def _normalizar_texto_voz(texto: str) -> str:
    """Normaliza para comparar voces: sin emojis, sin signos y en minúsculas."""
    return re.sub(r"[^0-9a-záéíóúüñ ]+", "", (texto or "").lower()).strip()


def resolver_voz_edge(nombre_o_id: str):
    """Resuelve nombre e ID de forma tolerante a banderas, mayúsculas o prefijos."""
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


def _obtener_piper_dir() -> str:
    """Ubicación de los modelos de voz Piper (junto al exe si está empaquetado)."""
    if getattr(sys, "frozen", False):
        externo = os.path.join(os.path.dirname(sys.executable), "assets", "voices")
        if os.path.isdir(externo):
            return externo
    return os.path.join(ASSETS_DIR, "voices")


# Voces neuronales offline (Piper): catálogo compartido con el backend (tts_voces.py)
PIPER_DIR = _obtener_piper_dir()


def obtener_voces_piper():
    """Voces Piper INSTALADAS: [(etiqueta, id), ...]."""
    return tts_voces.instaladas(PIPER_DIR)


def catalogo_voces_piper():
    """Catálogo completo con el estado de instalación de cada voz."""
    return tts_voces.catalogo(PIPER_DIR)

# Presets de Bots preconfigurados (nombre -> {tono, velocidad, descripcion})
BOT_PRESETS = {
    "👤 Natural / Neutro": {"tono": 0, "vel": 0, "desc": "Voz cristalina equilibrada sin alteraciones."},
    "🤖 MyBot Androide": {"tono": -12, "vel": 10, "desc": "Cadencia tecnológica y timbre sintético futurista."},
    "🐿️ Ardilla Divertida": {"tono": 45, "vel": 25, "desc": "Voz aguda con efecto de helio ultra dinámico."},
    "🎙️ Locutor Profesional": {"tono": -25, "vel": -5, "desc": "Tono grave, profundo y ritmo relajado de radio."},
    "⚡ Streamer Rápido": {"tono": 12, "vel": 38, "desc": "Velocidad acelerada ideal para directos con mucho tráfico."},
    "👾 Gamer Sintético": {"tono": 28, "vel": -10, "desc": "Modulación de voz estilo videojuego retro."},
    "📻 Loquendo Clásico": {"tono": 0, "vel": 5, "desc": "Cadencia nostálgica tradicional de sintetizador."},
}

def obtener_voces_sapi5():
    """Detecta de forma segura todas las voces SAPI5 instaladas en Windows."""
    try:
        import pyttsx3
        engine = pyttsx3.init(driverName="sapi5")
        voices = engine.getProperty("voices")
        lista = []
        for v in voices:
            nombre = v.name
            nombre_limpio = nombre.replace("Microsoft ", "").replace(" Desktop - ", " (").replace(" Desktop", "")
            if "(" in nombre_limpio and not nombre_limpio.endswith(")"):
                nombre_limpio += ")"

            nom_low = nombre.lower()
            if "spain" in nom_low or "españa" in nom_low or "es-es" in nom_low:
                nombre_limpio = f"🇪🇸 {nombre_limpio}"
            elif "argentina" in nom_low or "es-ar" in nom_low:
                nombre_limpio = f"🇦🇷 {nombre_limpio}"
            elif "mexico" in nom_low or "méxico" in nom_low or "es-mx" in nom_low:
                nombre_limpio = f"🇲🇽 {nombre_limpio}"
            lista.append((nombre_limpio, v.id))
        engine.stop()
        return lista
    except Exception:
        return [("Voz por defecto del sistema", "")]

def limpiar_nombre_usuario_tiktok(texto: str) -> str:
    """Extrae el usuario limpio si pegan una URL como https://www.tiktok.com/@fulano/live o @fulano."""
    if not texto:
        return ""
    t = texto.strip()
    match = re.search(r"tiktok\.com/@([a-zA-Z0-9_\.\-]+)", t)
    if match:
        return match.group(1)
    t = re.sub(r"^https?://[^\/]+/", "", t)
    t = t.strip("/").strip()
    t = t.lstrip("@").strip()
    t = re.sub(r"/live.*$", "", t)
    return t

def obtener_nombre_usuario(user) -> str:
    """Extrae el nombre del usuario de TikTok de la forma más natural y correcta."""
    if not user:
        return "Usuario"

    nombre = getattr(user, "nickname", None)
    if not nombre or not str(nombre).strip():
        nombre = getattr(user, "display_id", None)
    if not nombre or not str(nombre).strip():
        nombre = getattr(user, "unique_id", None)
    if not nombre or not str(nombre).strip():
        return "Usuario"

    nombre = str(nombre).strip()
    nombre = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", nombre)
    nombre = re.sub(r"(.)\1{3,}", r"\1\1", nombre).strip()

    if not nombre:
        nombre = getattr(user, "display_id", "Usuario") or "Usuario"

    if len(nombre) > 24:
        nombre = nombre[:24].strip()

    return nombre

def normalizar_comentario(comentario: str) -> str:
    """Limpia caracteres de control, enmascara URLs de spam y compacta repeticiones de emojis."""
    if not comentario:
        return ""
    c = comentario.strip()
    c = re.sub(r"[\x00-\x1f\x7f-\x9f\u200b-\u200f\ufeff]", "", c)
    # Enmascarar URLs para evitar lectura de links de spam
    c = re.sub(r"(https?://\S+|www\.\S+|\b[a-zA-Z0-9.\-_]+(?:\.com|\.org|\.net|\.io|\.me|\.gg|\.xyz)\b\S*)", "[enlace]", c, flags=re.IGNORECASE)
    # Reducir repetición exagerada de caracteres
    c = re.sub(r"(.)\1{3,}", r"\1\1", c)
    # Compactar emojis repetidos
    c = re.sub(r"([\U00010000-\U0010ffff])\1{2,}", r"\1\1", c)
    return c.strip()

def mensaje_error_conexion(exc: Exception) -> str:
    """Convierte excepciones de TikTokLive en mensajes claros y amigables."""
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


# =============================================================================
# CLASE PRINCIPAL: MyBot
# =============================================================================
class MyBotApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_NAME} {APP_VERSION} - {APP_SUBTITLE}")

        # Dimensiones iniciales y LÍMITE MÍNIMO FIJO INALTERABLE
        self.root.geometry(f"{MIN_WIDTH}x{MIN_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)

        # Generación de tonos de alerta predeterminados
        self.sonidos_predeterminados = audio_assets.generar_sonidos_predeterminados()

        # Detección de voces del sistema
        self.voces_sapi5 = obtener_voces_sapi5()
        self.voces_piper = obtener_voces_piper()
        self.catalogo_piper = catalogo_voces_piper()
        self._descargando_voz = False

        # Configuración persistente
        self.cfg = self._cargar_configuracion()
        self.ultima_info_version = None

        # Colas de comunicación
        self.cola_voz: queue.PriorityQueue = queue.PriorityQueue()
        self.cola_ui: queue.Queue = queue.Queue()

        # Control de hilos y conexión
        self.cliente = None
        self.hilo_cliente = None
        self._debe_correr = False
        self._sapi_engine = None
        self._sapi_voice = None
        self._piper_voz = None
        self._piper_modelo = None
        self._edge_disponible = True
        self._aviso_respaldo_tts = False
        self._usuarios_saludados = set()
        self._ultimo_saludo_tiempo = 0

        # Métricas de la sesión
        self.total_comentarios = 0
        self.total_donaciones = 0
        self.total_diamantes = 0

        # Cargar y configurar icono de la app
        self._configurar_icono_app()

        # Estilo iOS Blanco y Celeste
        self._aplicar_tema_ios()
        self._construir_ui()
        self._actualizar_cfg()

        # Hilo permanente de voz TTS
        threading.Thread(target=self._hilo_tts, daemon=True).start()

        # Actualización de UI periódica
        self.root.after(80, self._procesar_cola_ui)
        self.root.protocol("WM_DELETE_WINDOW", self._al_cerrar)

        # Comprobación de actualizaciones en segundo plano a los 3 segundos
        self.root.after(3000, lambda: self._comprobar_actualizacion(silencioso=True))

        self._log_sistema(f"✨ {APP_NAME} {APP_VERSION} listo para el directo. Configura tu voz y pulsa 'Conectar'.")

    # ------------------------------------------------------------------ ICONO
    def _configurar_icono_app(self):
        """Carga el icono de assets/icono.jpg y configura la ventana de Tkinter."""
        self.header_icon_photo = None
        ruta_ico = os.path.abspath(ICON_ICO)
        ruta_jpg = os.path.abspath(ICON_JPG)
        ruta_png = os.path.abspath(ICON_PNG)

        try:
            # 1. Asegurar icono ICO para Tkinter con ruta absoluta
            if os.path.exists(ruta_ico):
                try:
                    self.root.iconbitmap(default=ruta_ico)
                except Exception:
                    try:
                        self.root.iconbitmap(ruta_ico)
                    except Exception:
                        pass

            # 2. Cargar imagen con Pillow para iconphoto y avatar del header
            ruta_img = ruta_jpg if os.path.exists(ruta_jpg) else (ruta_png if os.path.exists(ruta_png) else None)
            if ruta_img and os.path.exists(ruta_img):
                img_pil = Image.open(ruta_img).convert("RGBA")

                # Icono de barra de tareas / ventana
                img_taskbar = img_pil.resize((64, 64), Image.Resampling.LANCZOS)
                self.photo_taskbar = ImageTk.PhotoImage(img_taskbar)
                self.root.iconphoto(True, self.photo_taskbar)

                # Avatar squircle estilo iOS (48x48 con esquinas redondeadas)
                size_h = (48, 48)
                img_header = img_pil.resize(size_h, Image.Resampling.LANCZOS)
                mask = Image.new("L", size_h, 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle([(0, 0), size_h], radius=11, fill=255)

                img_rounded = Image.new("RGBA", size_h, (0, 0, 0, 0))
                img_rounded.paste(img_header, (0, 0), mask=mask)
                self.header_icon_photo = ImageTk.PhotoImage(img_rounded)

            # 3. Forzado directo Win32 de WM_SETICON en el HWND para eliminar el icono de Python
            if sys.platform.startswith("win") and os.path.exists(ruta_ico):
                def _forzar_hicon_windows():
                    try:
                        import ctypes
                        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                        if not hwnd:
                            hwnd = self.root.winfo_id()
                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x00000010
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon_big = ctypes.windll.user32.LoadImageW(None, ruta_ico, IMAGE_ICON, 64, 64, LR_LOADFROMFILE)
                        hicon_small = ctypes.windll.user32.LoadImageW(None, ruta_ico, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
                        if hicon_big:
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
                        if hicon_small:
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
                    except Exception as e:
                        print(f"[Icono] Error forzando HICON: {e}")

                self.root.after(120, _forzar_hicon_windows)

        except Exception as e:
            print(f"[Icono] Error configurando icono: {e}")

    # ------------------------------------------------------------------ TEMA iOS
    def _aplicar_tema_ios(self):
        """
        Paleta de diseño iOS Light Theme refinada:
        - Fondo: Gris suave iOS (#F2F4F8 / System Grouped Background)
        - Tarjetas: Blanco puro (#FFFFFF) con bordes ultra nítidos (#E2E8F0)
        - Acentos: Celeste Apple (#007AFF / #0284C7), Celeste suave (#E0F2FE)
        - Alertas: Verde (#34C759), Ámbar (#FF9500), Rojo (#FF3B30)
        """
        self.c_bg = "#F2F4F8"
        self.c_card = "#FFFFFF"
        self.c_card_border = "#E2E8F0"
        self.c_primary = "#007AFF"          # Celeste iOS dinámico
        self.c_primary_hover = "#0062CC"
        self.c_primary_light = "#E0F2FE"    # Celeste fondo suave
        self.c_primary_dark = "#0369A1"
        self.c_danger = "#FF3B30"           # Rojo iOS
        self.c_danger_hover = "#D70015"
        self.c_danger_light = "#FEE2E2"
        self.c_success = "#34C759"          # Verde iOS
        self.c_success_light = "#DCFCE7"
        self.c_warning = "#FF9500"          # Ámbar iOS
        self.c_warning_light = "#FEF3C7"
        self.c_text = "#0F172A"             # Texto oscuro nítido
        self.c_text_muted = "#64748B"       # Texto secundario suave
        self.c_input_bg = "#F8FAFC"
        self.c_input_border = "#CBD5E1"

        self.root.configure(bg=self.c_bg)

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        # Configuración general TTK
        self.style.configure(".", background=self.c_bg, foreground=self.c_text, font=("Segoe UI", 9))
        self.style.configure("TFrame", background=self.c_bg)
        self.style.configure("Card.TFrame", background=self.c_card, relief="flat", borderwidth=0)
        self.style.configure("TLabel", background=self.c_bg, foreground=self.c_text)
        self.style.configure("Card.TLabel", background=self.c_card, foreground=self.c_text, font=("Segoe UI", 9))
        self.style.configure("CardBold.TLabel", background=self.c_card, foreground=self.c_text, font=("Segoe UI", 9, "bold"))
        self.style.configure("CardMuted.TLabel", background=self.c_card, foreground=self.c_text_muted, font=("Segoe UI", 8))
        self.style.configure("Header.TLabel", background=self.c_card, foreground=self.c_primary, font=("Segoe UI", 12, "bold"))

        # Pestañas (Segmented Control iOS Look)
        self.style.configure("TNotebook", background=self.c_bg, borderwidth=0)
        self.style.configure(
            "TNotebook.Tab",
            background="#E2E8F0",
            foreground="#475569",
            padding=(18, 8),
            font=("Segoe UI", 9, "bold")
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", self.c_card), ("active", "#CBD5E1")],
            foreground=[("selected", self.c_primary), ("active", self.c_text)]
        )

        # LabelFrame estilo Card iOS
        self.style.configure(
            "TLabelframe",
            background=self.c_card,
            bordercolor=self.c_card_border,
            relief="solid",
            borderwidth=1
        )
        self.style.configure(
            "TLabelframe.Label",
            background=self.c_card,
            foreground=self.c_primary_dark,
            font=("Segoe UI", 9, "bold")
        )

        # Botones estilo iOS con padding y separación ergonómica
        self.style.configure("TButton", background="#E2E8F0", foreground=self.c_text, borderwidth=0, padding=(12, 7))
        self.style.map("TButton",
                       background=[("active", "#CBD5E1"), ("disabled", "#F1F5F9")],
                       foreground=[("disabled", "#94A3B8")])

        # Botón primario Celeste iOS
        self.style.configure(
            "Primary.TButton",
            background=self.c_primary,
            foreground="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            padding=(16, 7)
        )
        self.style.map(
            "Primary.TButton",
            background=[("active", self.c_primary_hover), ("disabled", "#93C5FD")],
            foreground=[("disabled", "#EFF6FF")]
        )

        # Botón peligro Rojo iOS
        self.style.configure(
            "Danger.TButton",
            background=self.c_danger,
            foreground="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            padding=(16, 7)
        )
        self.style.map(
            "Danger.TButton",
            background=[("active", self.c_danger_hover), ("disabled", "#FCA5A5")]
        )

        # Botón secundario Celeste Suave
        self.style.configure(
            "SoftCeleste.TButton",
            background=self.c_primary_light,
            foreground=self.c_primary_dark,
            font=("Segoe UI", 9, "bold"),
            padding=(12, 6)
        )
        self.style.map(
            "SoftCeleste.TButton",
            background=[("active", "#BAE6FD")]
        )

        # Checkbutton & Scales
        self.style.configure("TCheckbutton", background=self.c_card, foreground=self.c_text)
        self.style.map("TCheckbutton", background=[("active", self.c_card)])
        self.style.configure("TScale", background=self.c_card, troughcolor="#E2E8F0")

    # ------------------------------------------------------------------ UI
    def _construir_ui(self):
        contenedor = ttk.Frame(self.root, padding=12)
        contenedor.pack(fill="both", expand=True)

        # 1. HEADER BRANDING DE MYBOT CON ICONO OFICIAL
        f_header = tk.Frame(contenedor, bg=self.c_card, highlightthickness=1,
                            highlightbackground=self.c_card_border, padx=14, pady=10)
        f_header.pack(fill="x", pady=(0, 10))

        if self.header_icon_photo:
            lbl_logo = tk.Label(f_header, image=self.header_icon_photo, bg=self.c_card)
            lbl_logo.pack(side="left", padx=(0, 12))
        else:
            lbl_logo = tk.Label(f_header, text="🤖", font=("Segoe UI Emoji", 22), bg=self.c_card)
            lbl_logo.pack(side="left", padx=(0, 10))

        f_titles = tk.Frame(f_header, bg=self.c_card)
        f_titles.pack(side="left")

        lbl_title = tk.Label(
            f_titles, text=APP_NAME, font=("Segoe UI", 14, "bold"),
            fg=self.c_primary, bg=self.c_card
        )
        lbl_title.pack(anchor="w")

        lbl_subtitle = tk.Label(
            f_titles, text=f"{APP_SUBTITLE} • {APP_VERSION}", font=("Segoe UI", 8),
            fg=self.c_text_muted, bg=self.c_card
        )
        lbl_subtitle.pack(anchor="w")

        # Indicador superior de estado de voz
        self.lbl_tts_status_top = tk.Label(
            f_header, text="🎙️ Voz: ● Lista", bg=self.c_primary_light, fg=self.c_primary_dark,
            font=("Segoe UI", 8, "bold"), padx=12, pady=5
        )
        self.lbl_tts_status_top.pack(side="right")

        # Botón de búsqueda de actualización
        self.btn_update = ttk.Button(
            f_header, text="🔄 Actualizaciones", style="SoftCeleste.TButton",
            command=lambda: self._comprobar_actualizacion(silencioso=False)
        )
        self.btn_update.pack(side="right", padx=(0, 8))

        # Banner de actualización (oculto por defecto)
        self.f_update_banner = tk.Frame(
            contenedor, bg="#FEF3C7", highlightthickness=1, highlightbackground="#F59E0B", padx=12, pady=8
        )
        self.lbl_update_txt = tk.Label(
            self.f_update_banner, text="", bg="#FEF3C7", fg="#92400E", font=("Segoe UI", 9, "bold")
        )
        self.lbl_update_txt.pack(side="left")

        self.btn_update_download = ttk.Button(
            self.f_update_banner, text="🚀 Descargar", style="Primary.TButton",
            command=self._abrir_url_descarga
        )
        self.btn_update_download.pack(side="right", padx=(8, 0))

        ttk.Button(
            self.f_update_banner, text="✕", width=3,
            command=self.f_update_banner.pack_forget
        ).pack(side="right")

        # 2. BARRA DE CONEXIÓN RÁPIDA (Card iOS con espaciado ergonómico)
        f_top = tk.Frame(contenedor, bg=self.c_card, highlightthickness=1,
                         highlightbackground=self.c_card_border, padx=14, pady=12)
        f_top.pack(fill="x", pady=(0, 10))

        tk.Label(f_top, text="Usuario o Link:", bg=self.c_card, fg=self.c_text,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.var_usuario = tk.StringVar(value=self.cfg.get("usuario", "@l.am.lex_"))
        self.var_usuario.trace_add("write", lambda *_: self._actualizar_cfg())
        self.ent_user = tk.Entry(
            f_top, textvariable=self.var_usuario, bg=self.c_input_bg, fg=self.c_text,
            insertbackground=self.c_primary, relief="flat", highlightthickness=1,
            highlightbackground=self.c_input_border, highlightcolor=self.c_primary,
            font=("Segoe UI", 10)
        )
        self.ent_user.grid(row=0, column=1, sticky="we", padx=(0, 12), ipady=3)
        self.ent_user.bind("<FocusOut>", lambda e: self._actualizar_cfg())
        f_top.columnconfigure(1, weight=1)

        self.btn_conectar = ttk.Button(f_top, text="Conectar", style="Primary.TButton", command=self._conectar)
        self.btn_conectar.grid(row=0, column=2, padx=(0, 8))

        self.btn_desconectar = ttk.Button(f_top, text="Desconectar", style="Danger.TButton",
                                          command=self._desconectar, state="disabled")
        self.btn_desconectar.grid(row=0, column=3)

        # Chips de estado y métricas (Pills estilo iOS con separación generosa)
        f_pills = tk.Frame(f_top, bg=self.c_card)
        f_pills.grid(row=1, column=0, columnspan=4, sticky="we", pady=(12, 0))

        self.lbl_indicador = tk.Label(
            f_pills, text="● Desconectado", bg="#F1F5F9", fg=self.c_text_muted,
            font=("Segoe UI", 8, "bold"), padx=12, pady=4
        )
        self.lbl_indicador.pack(side="left")

        # Métricas individuales estilo iOS pills
        f_metrics_right = tk.Frame(f_pills, bg=self.c_card)
        f_metrics_right.pack(side="right")

        self.lbl_comentarios = tk.Label(
            f_metrics_right, text="💬 0 comentarios", bg=self.c_primary_light, fg=self.c_primary_dark,
            font=("Segoe UI", 8, "bold"), padx=10, pady=4
        )
        self.lbl_comentarios.pack(side="left", padx=4)

        self.lbl_donaciones = tk.Label(
            f_metrics_right, text="🎁 0 regalos", bg=self.c_warning_light, fg="#B45309",
            font=("Segoe UI", 8, "bold"), padx=10, pady=4
        )
        self.lbl_donaciones.pack(side="left", padx=4)

        self.lbl_diamantes = tk.Label(
            f_metrics_right, text="💎 0 diamantes", bg="#F3E8FF", fg="#6B21A8",
            font=("Segoe UI", 8, "bold"), padx=10, pady=4
        )
        self.lbl_diamantes.pack(side="left", padx=4)

        # 3. PESTAÑAS (Notebook Segmented)
        self.notebook = ttk.Notebook(contenedor)
        self.notebook.pack(fill="both", expand=True)

        # Pestaña 1: Directo & Chat
        self.tab_chat = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_chat, text="  💬 Chat en Vivo  ")
        self._construir_tab_chat(self.tab_chat)

        # Pestaña 2: Voz & Bots
        self.tab_voz = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_voz, text="  🎙️ Voz & Presets  ")
        self._construir_tab_voz(self.tab_voz)

        # Pestaña 3: Donaciones & Regalos
        self.tab_donaciones = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_donaciones, text="  🎁 Donaciones  ")
        self._construir_tab_donaciones(self.tab_donaciones)

        # Pestaña 4: Bienvenidas & Saludos
        self.tab_bienvenida = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_bienvenida, text="  👋 Bienvenidas  ")
        self._construir_tab_bienvenida(self.tab_bienvenida)

        # Pestaña 5: Filtros & Seguridad
        self.tab_filtros = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_filtros, text="  🛡️ Filtros & Opciones  ")
        self._construir_tab_filtros(self.tab_filtros)

        # 4. PIE DE VENTANA / CRÉDITOS Y ENLACES OFICIALES
        f_footer = tk.Frame(contenedor, bg=self.c_bg)
        f_footer.pack(fill="x", pady=(8, 0))

        lbl_dev = tk.Label(
            f_footer, text="Desarrollado por i.am.lex • MyBot v1.2",
            bg=self.c_bg, fg=self.c_text_muted, font=("Segoe UI", 8)
        )
        lbl_dev.pack(side="left")

        f_links = tk.Frame(f_footer, bg=self.c_bg)
        f_links.pack(side="right")

        def _crear_link(parent, texto, url):
            lbl = tk.Label(parent, text=texto, bg=self.c_bg, fg=self.c_primary,
                           font=("Segoe UI", 8), cursor="hand2")
            lbl.pack(side="left", padx=6)
            lbl.bind("<Button-1>", lambda e: webbrowser.open(url))
            lbl.bind("<Enter>", lambda e: lbl.configure(font=("Segoe UI", 8, "underline")))
            lbl.bind("<Leave>", lambda e: lbl.configure(font=("Segoe UI", 8)))
            return lbl

        _crear_link(f_links, "🌐 Web Oficial", "https://mybot-79861.web.app")
        _crear_link(f_links, "🎵 TikTok", "https://www.tiktok.com/@l.am.lex_?is_from_webapp=1&sender_device=pc")
        _crear_link(f_links, "📷 Instagram", "https://www.instagram.com/l.am.lex_/")
        _crear_link(f_links, "💼 Desarrollador", "https://web-lex.vercel.app/")

    def _construir_tab_chat(self, tab):
        # Visor de chat blanco y nítido
        f_log = tk.Frame(tab, bg=self.c_card, highlightthickness=1,
                         highlightbackground=self.c_card_border, padx=8, pady=8)
        f_log.pack(fill="both", expand=True)

        self.txt_chat = tk.Text(
            f_log, wrap="word", bg="#FFFFFF", fg=self.c_text,
            insertbackground=self.c_primary, relief="flat", font=("Segoe UI", 9),
            state="disabled", padx=10, pady=10
        )
        # Tags de colores tipo iOS
        self.txt_chat.tag_configure("sis", foreground=self.c_text_muted, font=("Segoe UI", 8, "italic"))
        self.txt_chat.tag_configure("err", foreground=self.c_danger, font=("Segoe UI", 9, "bold"))
        self.txt_chat.tag_configure("user", foreground=self.c_primary, font=("Segoe UI", 9, "bold"))
        self.txt_chat.tag_configure("com", foreground=self.c_text, font=("Segoe UI", 9))
        self.txt_chat.tag_configure("don_badge", foreground="#D97706", font=("Segoe UI", 9, "bold"))
        self.txt_chat.tag_configure("don_txt", foreground="#92400E", font=("Segoe UI", 9, "bold"))

        sb = ttk.Scrollbar(f_log, command=self.txt_chat.yview)
        self.txt_chat.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt_chat.pack(side="left", fill="both", expand=True)

        # Controles inferiores del chat con espaciado amplio
        f_controles = tk.Frame(tab, bg=self.c_bg)
        f_controles.pack(fill="x", pady=(10, 2))

        ttk.Button(f_controles, text="🗑️ Limpiar chat", command=self._limpiar_chat).pack(side="left")
        ttk.Button(
            f_controles, text="⏹️ Silenciar / Parar Audio Inmediato",
            style="Danger.TButton", command=self._vaciar_cola_audio
        ).pack(side="left", padx=10)

        self.lbl_estado_cola = tk.Label(
            f_controles, text="Cola de voz: 0", bg="#E2E8F0", fg=self.c_text,
            font=("Segoe UI", 8, "bold"), padx=10, pady=4
        )
        self.lbl_estado_cola.pack(side="right")

    def _construir_tab_voz(self, tab):
        # 1. TARJETA PRINCIPAL: Configuración de Voz y Modulación
        f_card_voz = ttk.LabelFrame(tab, text="  🎙️ Motor de Voz y Modulación  ", padding=14)
        f_card_voz.pack(fill="x", pady=(0, 10))

        # Fila 0: Motor y Preset en 2 columnas elegantes
        f_row0 = tk.Frame(f_card_voz, bg=self.c_card)
        f_row0.pack(fill="x", pady=(0, 8))

        f_col_motor = tk.Frame(f_row0, bg=self.c_card)
        f_col_motor.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Label(f_col_motor, text="Motor de voz:", style="CardBold.TLabel").pack(anchor="w", pady=(0, 3))
        self.var_motor = tk.StringVar(value=self.cfg.get("motor", "piper"))
        cmb_motor = ttk.Combobox(f_col_motor, textvariable=self.var_motor, values=["piper", "sapi5"],
                                 state="readonly")
        cmb_motor.pack(fill="x")
        cmb_motor.bind("<<ComboboxSelected>>", self._al_cambiar_motor)

        f_col_preset = tk.Frame(f_row0, bg=self.c_card)
        f_col_preset.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ttk.Label(f_col_preset, text="Preset de Bot:", style="CardBold.TLabel").pack(anchor="w", pady=(0, 3))
        self.var_preset = tk.StringVar(value="👤 Natural / Neutro")
        cmb_preset = ttk.Combobox(f_col_preset, textvariable=self.var_preset, values=list(BOT_PRESETS.keys()),
                                  state="readonly")
        cmb_preset.pack(fill="x")
        cmb_preset.bind("<<ComboboxSelected>>", self._al_seleccionar_preset)

        # Fila 1: Selector de Voz principal amplia
        f_row1 = tk.Frame(f_card_voz, bg=self.c_card)
        f_row1.pack(fill="x", pady=(0, 4))
        ttk.Label(f_row1, text="Voz principal neural:", style="CardBold.TLabel").pack(anchor="w", pady=(0, 3))
        self.var_voz = tk.StringVar(value=self.cfg.get("voz_nombre", VOICES_EDGE[0][0]))
        self.cmb_voz = ttk.Combobox(f_row1, textvariable=self.var_voz, state="readonly")
        self.cmb_voz.pack(fill="x")
        self.cmb_voz.bind("<<ComboboxSelected>>", lambda e: self._al_seleccionar_voz())
        self._actualizar_opciones_voces()

        # Fila 1b: Descarga de la voz neuronal (los modelos NO vienen en el instalador)
        f_descarga = tk.Frame(f_card_voz, bg=self.c_card)
        f_descarga.pack(fill="x", pady=(6, 2))
        self.btn_descargar_voz = ttk.Button(f_descarga, text="⬇️ Descargar voz seleccionada",
                                            command=self._descargar_voz_seleccionada)
        self.btn_descargar_voz.pack(side="left")
        self.lbl_voz_estado = ttk.Label(f_descarga, text="", style="CardMuted.TLabel")
        self.lbl_voz_estado.pack(side="left", padx=(10, 0))
        self._actualizar_estado_voz()

        # Fila 2: Descripción sutil del preset
        self.lbl_preset_desc = ttk.Label(f_card_voz, text=BOT_PRESETS["👤 Natural / Neutro"]["desc"],
                                         style="CardMuted.TLabel")
        self.lbl_preset_desc.pack(anchor="w", pady=(0, 10))

        # Fila 3: Sliders de modulación con badges alineados
        f_sliders = tk.Frame(f_card_voz, bg=self.c_card)
        f_sliders.pack(fill="x", pady=(0, 10))
        f_sliders.columnconfigure(1, weight=1)

        # Tono
        ttk.Label(f_sliders, text="Tono:", style="CardBold.TLabel").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 8))
        self.var_tono = tk.IntVar(value=self.cfg.get("tono", 0))
        scl_tono = ttk.Scale(f_sliders, from_=-50, to=50, variable=self.var_tono,
                             command=lambda _: self._al_mover_slider("tono"))
        scl_tono.grid(row=0, column=1, sticky="we", pady=4, padx=4)
        self.lbl_tono = tk.Label(f_sliders, text=f"{self.var_tono.get():+d} Hz", bg=self.c_primary_light,
                                 fg=self.c_primary_dark, font=("Segoe UI", 8, "bold"), width=9, padx=4, pady=2)
        self.lbl_tono.grid(row=0, column=2, sticky="e", pady=4, padx=(8, 0))

        # Velocidad
        ttk.Label(f_sliders, text="Velocidad:", style="CardBold.TLabel").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 8))
        self.var_vel = tk.IntVar(value=self.cfg.get("velocidad", 0))
        scl_vel = ttk.Scale(f_sliders, from_=-50, to=100, variable=self.var_vel,
                            command=lambda _: self._al_mover_slider("vel"))
        scl_vel.grid(row=1, column=1, sticky="we", pady=4, padx=4)
        self.lbl_vel = tk.Label(f_sliders, text=f"{self.var_vel.get():+d}%", bg=self.c_primary_light,
                                fg=self.c_primary_dark, font=("Segoe UI", 8, "bold"), width=9, padx=4, pady=2)
        self.lbl_vel.grid(row=1, column=2, sticky="e", pady=4, padx=(8, 0))

        # Volumen
        ttk.Label(f_sliders, text="Volumen:", style="CardBold.TLabel").grid(row=2, column=0, sticky="w", pady=4, padx=(0, 8))
        self.var_vol = tk.IntVar(value=self.cfg.get("volumen", 100))
        scl_vol = ttk.Scale(f_sliders, from_=10, to=100, variable=self.var_vol,
                            command=lambda _: self._al_mover_slider("vol"))
        scl_vol.grid(row=2, column=1, sticky="we", pady=4, padx=4)
        self.lbl_vol = tk.Label(f_sliders, text=f"{self.var_vol.get()}%", bg=self.c_primary_light,
                                fg=self.c_primary_dark, font=("Segoe UI", 8, "bold"), width=9, padx=4, pady=2)
        self.lbl_vol.grid(row=2, column=2, sticky="e", pady=4, padx=(8, 0))

        # Fila 4: Formato de usuario
        f_user_opt = tk.Frame(f_card_voz, bg=self.c_card)
        f_user_opt.pack(fill="x", pady=(4, 0))

        self.var_leer_nombre = tk.BooleanVar(value=self.cfg.get("leer_nombre", True))
        ttk.Checkbutton(f_user_opt, text="Leer nombre del usuario en los comentarios",
                        variable=self.var_leer_nombre, command=self._actualizar_cfg).pack(anchor="w")

        f_fmt = tk.Frame(f_user_opt, bg=self.c_card)
        f_fmt.pack(fill="x", pady=(6, 0))
        ttk.Label(f_fmt, text="Formato de lectura:", style="CardMuted.TLabel").pack(side="left", padx=(0, 8))
        self.var_formato_usuario = tk.StringVar(value=self.cfg.get("formato_usuario", "{usuario} dice: {mensaje}"))
        self.var_formato_usuario.trace_add("write", lambda *_: self._actualizar_cfg())
        ent_fmt = tk.Entry(f_fmt, textvariable=self.var_formato_usuario, bg=self.c_input_bg, fg=self.c_text,
                           insertbackground=self.c_primary, relief="flat", highlightthickness=1,
                           highlightbackground=self.c_input_border, highlightcolor=self.c_primary,
                           font=("Segoe UI", 9))
        ent_fmt.pack(side="left", fill="x", expand=True, ipady=3)
        ent_fmt.bind("<FocusOut>", lambda e: self._actualizar_cfg())

        # 2. TARJETA SECUNDARIA: Prueba Rápida y Descarga de Audio
        f_card_test = ttk.LabelFrame(tab, text="  🔊 Prueba Rápida y Exportación de Audio  ", padding=14)
        f_card_test.pack(fill="x")

        f_test_row1 = tk.Frame(f_card_test, bg=self.c_card)
        f_test_row1.pack(fill="x", pady=(0, 8))

        self.var_texto_test = tk.StringVar(value="¡Hola! Soy MyBot, tu asistente de voz en directo.")
        tk.Entry(f_test_row1, textvariable=self.var_texto_test, bg=self.c_input_bg, fg=self.c_text,
                 insertbackground=self.c_primary, relief="flat", highlightthickness=1,
                 highlightbackground=self.c_input_border, highlightcolor=self.c_primary,
                 font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)

        ttk.Button(f_test_row1, text="🔊 Probar Voz", style="Primary.TButton", command=self._probar_voz).pack(side="left", padx=(0, 6))
        ttk.Button(f_test_row1, text="💾 Guardar MP3", style="SoftCeleste.TButton", command=self._descargar_audio_prueba).pack(side="left", padx=(0, 6))
        ttk.Button(f_test_row1, text="📁 Carpeta", command=self._abrir_carpeta_descargas).pack(side="left")

        f_test_row2 = tk.Frame(f_card_test, bg=self.c_card)
        f_test_row2.pack(fill="x")

        self.lbl_badge_estado = tk.Label(
            f_test_row2, text="● Estado: Listo", bg=self.c_primary_light, fg=self.c_primary_dark,
            font=("Segoe UI", 8, "bold"), padx=12, pady=4, relief="flat"
        )
        self.lbl_badge_estado.pack(side="left")

        self.lbl_detalle_estado = tk.Label(
            f_test_row2, text="Voz lista para usar en el directo.", bg=self.c_card, fg=self.c_text_muted,
            font=("Segoe UI", 8)
        )
        self.lbl_detalle_estado.pack(side="left", padx=10)

    def _construir_tab_donaciones(self, tab):
        # 1. TARJETA: Reglas y Lectura de Donaciones
        f_box_rules = ttk.LabelFrame(tab, text="  🎁 Reglas de Donaciones y Lectura de Regalos  ", padding=14)
        f_box_rules.pack(fill="x", pady=(0, 10))

        self.var_donaciones_activas = tk.BooleanVar(value=self.cfg.get("donaciones_activas", True))
        ttk.Checkbutton(f_box_rules, text="Activar avisos de donaciones y regalos en vivo",
                        variable=self.var_donaciones_activas, command=self._actualizar_cfg).pack(anchor="w", pady=(0, 6))

        self.var_esperar_racha = tk.BooleanVar(value=self.cfg.get("esperar_racha", True))
        ttk.Checkbutton(f_box_rules, text="Avisar solo al terminar combo / racha (evita repetir en ráfagas de rosas)",
                        variable=self.var_esperar_racha, command=self._actualizar_cfg).pack(anchor="w", pady=(0, 8))

        f_min_dia = tk.Frame(f_box_rules, bg=self.c_card)
        f_min_dia.pack(fill="x", pady=(0, 10))
        ttk.Label(f_min_dia, text="Mínimo de diamantes para alertar:", style="CardBold.TLabel").pack(side="left", padx=(0, 8))
        self.var_min_diamantes = tk.IntVar(value=self.cfg.get("min_diamantes", 1))
        self.var_min_diamantes.trace_add("write", lambda *_: self._actualizar_cfg())
        ttk.Spinbox(f_min_dia, from_=1, to=10000, textvariable=self.var_min_diamantes, width=8,
                    command=self._actualizar_cfg).pack(side="left")

        # Mensaje de agradecimiento
        self.var_leer_donacion = tk.BooleanVar(value=self.cfg.get("leer_donacion", True))
        ttk.Checkbutton(f_box_rules, text="Leer agradecimiento por voz en el directo",
                        variable=self.var_leer_donacion, command=self._actualizar_cfg).pack(anchor="w", pady=(4, 6))

        f_tpl = tk.Frame(f_box_rules, bg=self.c_card)
        f_tpl.pack(fill="x", pady=(0, 4))
        ttk.Label(f_tpl, text="Plantilla:", style="CardBold.TLabel").pack(side="left", padx=(0, 8))
        self.var_tpl_donacion = tk.StringVar(
            value=self.cfg.get("tpl_donacion", "¡Muchas gracias a {usuario} por enviar {cantidad} {regalo}!"))
        self.var_tpl_donacion.trace_add("write", lambda *_: self._actualizar_cfg())
        ent_tpl = tk.Entry(f_tpl, textvariable=self.var_tpl_donacion, bg=self.c_input_bg, fg=self.c_text,
                           insertbackground=self.c_primary, relief="flat", highlightthickness=1,
                           highlightbackground=self.c_input_border, highlightcolor=self.c_primary,
                           font=("Segoe UI", 9))
        ent_tpl.pack(side="left", fill="x", expand=True, ipady=3)
        ent_tpl.bind("<FocusOut>", lambda e: self._actualizar_cfg())

        ttk.Label(f_box_rules, text="Variables disponibles: {usuario}, {regalo}, {cantidad}, {diamantes}",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(2, 0))

        # 2. TARJETA: Efectos de Sonido
        f_box_sound = ttk.LabelFrame(tab, text="  🔔 Efectos de Sonido de Donación  ", padding=14)
        f_box_sound.pack(fill="x")

        self.var_sonido_activo = tk.BooleanVar(value=self.cfg.get("sonido_activo", True))
        ttk.Checkbutton(f_box_sound, text="Reproducir efecto de sonido al recibir donación",
                        variable=self.var_sonido_activo, command=self._actualizar_cfg).pack(anchor="w", pady=(0, 8))

        f_snd_sel = tk.Frame(f_box_sound, bg=self.c_card)
        f_snd_sel.pack(fill="x", pady=(0, 6))

        ttk.Label(f_snd_sel, text="Tono o Meme:", style="CardBold.TLabel").pack(side="left", padx=(0, 8))
        opciones_sonido = list(self.sonidos_predeterminados.keys()) + ["Personalizado..."]
        sonido_actual = self.cfg.get("tipo_sonido", opciones_sonido[0])
        if sonido_actual not in opciones_sonido:
            sonido_actual = opciones_sonido[0]
        self.var_tipo_sonido = tk.StringVar(value=sonido_actual)
        self.var_tipo_sonido.trace_add("write", lambda *_: self._actualizar_cfg())
        self.cmb_snd = ttk.Combobox(f_snd_sel, textvariable=self.var_tipo_sonido, values=opciones_sonido,
                                    state="readonly", width=33)
        self.cmb_snd.pack(side="left", padx=(0, 8))
        self.cmb_snd.bind("<<ComboboxSelected>>", self._al_cambiar_sonido)

        self.var_ruta_sonido = tk.StringVar(value=self.cfg.get("ruta_sonido_custom", ""))
        self.var_ruta_sonido.trace_add("write", lambda *_: self._actualizar_cfg())
        self.btn_examinar_snd = ttk.Button(f_snd_sel, text="📁 Examinar...", command=self._examinar_sonido)
        if self.var_tipo_sonido.get() == "Personalizado...":
            self.btn_examinar_snd.pack(side="left", padx=(0, 8))

        ttk.Button(f_snd_sel, text="🔔 Probar Alerta",
                   style="SoftCeleste.TButton", command=self._probar_alerta_donacion).pack(side="right")

        lbl_snd_hint = ttk.Label(
            f_box_sound,
            text="✨ Sonidos listos: ¡Faaa!, AuronPlay (¿Pero qué ha pasao?, Abduzcan, Calvo), Siuuu (CR7), Bruh, Wow y Campanas.",
            style="CardMuted.TLabel"
        )
        lbl_snd_hint.pack(anchor="w", pady=(2, 0))

        # 3. TARJETA: Control Multimedia (YouTube Music / Spotify)
        f_box_media = ttk.LabelFrame(tab, text="  🎵 Control Multimedia (YouTube Music / Spotify)  ", padding=14)
        f_box_media.pack(fill="x", pady=(10, 0))

        self.var_media_activa = tk.BooleanVar(value=self.cfg.get("media_action_activa", False))
        ttk.Checkbutton(f_box_media, text="Cambiar de canción automáticamente al recibir donación",
                        variable=self.var_media_activa, command=self._actualizar_cfg).pack(anchor="w", pady=(0, 8))

        f_media_opts = tk.Frame(f_box_media, bg=self.c_card)
        f_media_opts.pack(fill="x", pady=(0, 6))

        ttk.Label(f_media_opts, text="Acción en YouTube Music:", style="CardBold.TLabel").pack(side="left", padx=(0, 6))
        self.acciones_media_nombres = ["⏭️ Siguiente canción", "⏮️ Canción anterior", "⏯️ Pausar / Reanudar"]
        self.acciones_media_map = {
            "next": self.acciones_media_nombres[0],
            "prev": self.acciones_media_nombres[1],
            "play_pause": self.acciones_media_nombres[2],
        }
        val_act = self.acciones_media_map.get(self.cfg.get("media_tipo_accion", "next"), self.acciones_media_nombres[0])
        self.var_media_accion = tk.StringVar(value=val_act)
        self.var_media_accion.trace_add("write", lambda *_: self._actualizar_cfg())
        cmb_act = ttk.Combobox(f_media_opts, textvariable=self.var_media_accion, values=self.acciones_media_nombres,
                               state="readonly", width=22)
        cmb_act.pack(side="left", padx=(0, 12))

        ttk.Label(f_media_opts, text="Mínimo diamantes:", style="CardBold.TLabel").pack(side="left", padx=(0, 6))
        self.var_media_min_dia = tk.IntVar(value=self.cfg.get("media_min_diamantes", 1))
        self.var_media_min_dia.trace_add("write", lambda *_: self._actualizar_cfg())
        ttk.Spinbox(f_media_opts, from_=1, to=1000, textvariable=self.var_media_min_dia, width=6,
                    command=self._actualizar_cfg).pack(side="left")

        f_media_btns = tk.Frame(f_box_media, bg=self.c_card)
        f_media_btns.pack(fill="x", pady=(6, 0))
        ttk.Button(f_media_btns, text="⏭️ Probar Siguiente Canción",
                   command=lambda: self._ejecutar_accion_multimedia("next", "Prueba")).pack(side="left", padx=(0, 8))
        ttk.Button(f_media_btns, text="⏮️ Probar Canción Anterior",
                   command=lambda: self._ejecutar_accion_multimedia("prev", "Prueba")).pack(side="left")

    def _construir_tab_bienvenida(self, tab):
        # TARJETA: Bienvenidas y Saludos al Entrar al Live
        f_box = ttk.LabelFrame(tab, text="  👋 Saludar a Espectadores que Entran al Directo  ", padding=14)
        f_box.pack(fill="x", pady=(0, 10))

        self.var_bienvenidas_activas = tk.BooleanVar(value=self.cfg.get("bienvenidas_activas", True))
        ttk.Checkbutton(f_box, text="Activar detección de personas que entran al live",
                        variable=self.var_bienvenidas_activas, command=self._actualizar_cfg).pack(anchor="w", pady=(0, 6))

        self.var_mostrar_bienvenida_chat = tk.BooleanVar(value=self.cfg.get("mostrar_bienvenida_chat", True))
        ttk.Checkbutton(f_box, text="Mostrar aviso en el chat en vivo (burbuja 👋)",
                        variable=self.var_mostrar_bienvenida_chat, command=self._actualizar_cfg).pack(anchor="w", pady=(0, 6))

        self.var_leer_bienvenida = tk.BooleanVar(value=self.cfg.get("leer_bienvenida", False))
        ttk.Checkbutton(f_box, text="Saludar por voz alta (TTS) cuando alguien entra",
                        variable=self.var_leer_bienvenida, command=self._actualizar_cfg).pack(anchor="w", pady=(0, 6))

        self.var_anti_repeticion_bienvenida = tk.BooleanVar(value=self.cfg.get("anti_repeticion_bienvenida", True))
        ttk.Checkbutton(f_box, text="No repetir saludo al mismo espectador durante la sesión",
                        variable=self.var_anti_repeticion_bienvenida, command=self._actualizar_cfg).pack(anchor="w", pady=(0, 10))

        f_tpl = tk.Frame(f_box, bg=self.c_card)
        f_tpl.pack(fill="x", pady=(0, 6))
        ttk.Label(f_tpl, text="Plantilla de saludo:", style="CardBold.TLabel").pack(side="left", padx=(0, 8))
        self.var_tpl_bienvenida = tk.StringVar(value=self.cfg.get("tpl_bienvenida", "¡Bienvenido {usuario} al directo!"))
        self.var_tpl_bienvenida.trace_add("write", lambda *_: self._actualizar_cfg())
        ent_tpl = tk.Entry(f_tpl, textvariable=self.var_tpl_bienvenida, bg=self.c_input_bg, fg=self.c_text,
                           insertbackground=self.c_primary, relief="flat", highlightthickness=1,
                           highlightbackground=self.c_input_border, highlightcolor=self.c_primary,
                           font=("Segoe UI", 9))
        ent_tpl.pack(side="left", fill="x", expand=True, ipady=3)

        f_cd = tk.Frame(f_box, bg=self.c_card)
        f_cd.pack(fill="x", pady=(4, 10))
        ttk.Label(f_cd, text="Intervalo mínimo entre saludos de voz:", style="CardBold.TLabel").pack(side="left", padx=(0, 8))
        self.var_cooldown_bienvenida = tk.IntVar(value=self.cfg.get("cooldown_bienvenida", 10))
        self.var_cooldown_bienvenida.trace_add("write", lambda *_: self._actualizar_cfg())
        ttk.Spinbox(f_cd, from_=3, to=60, textvariable=self.var_cooldown_bienvenida, width=6,
                    command=self._actualizar_cfg).pack(side="left", padx=(0, 6))
        ttk.Label(f_cd, text="segundos (evita saturación en directos concurridos)", style="CardMuted.TLabel").pack(side="left")

        ttk.Button(f_box, text="👋 Probar Saludo de Bienvenida", style="SoftCeleste.TButton",
                   command=self._probar_bienvenida).pack(anchor="w", pady=(6, 0))

    def _construir_tab_filtros(self, tab):
        # 1. TARJETA: Moderación de Comentarios
        f_box_mod = ttk.LabelFrame(tab, text="  🛡️ Moderación de Comentarios en Vivo  ", padding=14)
        f_box_mod.pack(fill="x", pady=(0, 10))

        ttk.Label(f_box_mod, text="Palabras prohibidas (separadas por coma):", style="CardBold.TLabel").pack(anchor="w", pady=(0, 4))
        self.var_baneadas = tk.StringVar(value=self.cfg.get("baneadas", "ejemplo1,ejemplo2,ejemplo3"))
        self.var_baneadas.trace_add("write", lambda *_: self._actualizar_cfg())
        ent_ban = tk.Entry(f_box_mod, textvariable=self.var_baneadas, bg=self.c_input_bg, fg=self.c_text,
                           insertbackground=self.c_primary, relief="flat", highlightthickness=1,
                           highlightbackground=self.c_input_border, highlightcolor=self.c_primary,
                           font=("Segoe UI", 9))
        ent_ban.pack(fill="x", pady=(0, 10), ipady=3)
        ent_ban.bind("<FocusOut>", lambda e: self._actualizar_cfg())

        # Fila horizontal con 2 límites anti-lag
        f_limits = tk.Frame(f_box_mod, bg=self.c_card)
        f_limits.pack(fill="x")

        f_lim1 = tk.Frame(f_limits, bg=self.c_card)
        f_lim1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Label(f_lim1, text="Máx. caracteres por comentario:", style="CardMuted.TLabel").pack(anchor="w", pady=(0, 3))
        self.var_max_caracteres = tk.IntVar(value=self.cfg.get("max_caracteres", 85))
        self.var_max_caracteres.trace_add("write", lambda *_: self._actualizar_cfg())
        ttk.Spinbox(f_lim1, from_=10, to=300, textvariable=self.var_max_caracteres, width=10,
                    command=self._actualizar_cfg).pack(anchor="w")

        f_lim2 = tk.Frame(f_limits, bg=self.c_card)
        f_lim2.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ttk.Label(f_lim2, text="Máx. mensajes en cola (anti-lag):", style="CardMuted.TLabel").pack(anchor="w", pady=(0, 3))
        self.var_max_cola = tk.IntVar(value=self.cfg.get("max_cola", 8))
        self.var_max_cola.trace_add("write", lambda *_: self._actualizar_cfg())
        ttk.Spinbox(f_lim2, from_=3, to=50, textvariable=self.var_max_cola, width=10,
                    command=self._actualizar_cfg).pack(anchor="w")

        # 2. TARJETA: Protección y Conexión Automática
        f_box_prot = ttk.LabelFrame(tab, text="  ⚡ Estabilidad y Filtros Automáticos  ", padding=14)
        f_box_prot.pack(fill="x")

        self.var_filtrar_links = tk.BooleanVar(value=self.cfg.get("filtrar_links", True))
        ttk.Checkbutton(f_box_prot, text="Enmascarar automáticamente enlaces y páginas web sospechosas",
                        variable=self.var_filtrar_links, command=self._actualizar_cfg).pack(anchor="w", pady=(0, 6))

        self.var_compactar_emojis = tk.BooleanVar(value=self.cfg.get("compactar_emojis", True))
        ttk.Checkbutton(f_box_prot, text="Compactar emojis repetitivos (evita lecturas infinitas de emojis)",
                        variable=self.var_compactar_emojis, command=self._actualizar_cfg).pack(anchor="w", pady=(0, 6))

        self.var_auto_reconnect = tk.BooleanVar(value=self.cfg.get("auto_reconnect", True))
        ttk.Checkbutton(f_box_prot, text="Reconectar automáticamente si TikTok Live pierde conexión",
                        variable=self.var_auto_reconnect, command=self._actualizar_cfg).pack(anchor="w")

    # ---------------------------------------------------------- CONFIGURACIÓN
    def _cargar_configuracion(self):
        defaults = {
            "usuario": "@l.am.lex_",
            "motor": "piper",
            "voz_nombre": "🇦🇷 Daniela - Mujer (Argentina, offline)",
            "voz_id": "es_AR-daniela-high",
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
            "media_action_activa": False,
            "media_tipo_accion": "next",
            "media_min_diamantes": 1,
            "bienvenidas_activas": True,
            "mostrar_bienvenida_chat": True,
            "leer_bienvenida": False,
            "anti_repeticion_bienvenida": True,
            "tpl_bienvenida": "¡Bienvenido {usuario} al directo!",
            "cooldown_bienvenida": 10,
            "baneadas": "ejemplo1,ejemplo2,ejemplo3",
            "max_caracteres": 85,
            "max_cola": 8,
            "filtrar_links": True,
            "compactar_emojis": True,
            "auto_reconnect": True,
        }
        ruta_cfg = obtener_ruta_config()
        if not os.path.exists(ruta_cfg):
            c_local = os.path.join(BASE_DIR, "config.json")
            appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
            c_appdata = os.path.join(appdata, "MyBot", "config.json")
            if os.path.exists(c_local):
                ruta_cfg = c_local
            elif os.path.exists(c_appdata):
                ruta_cfg = c_appdata

        if os.path.exists(ruta_cfg):
            try:
                with open(ruta_cfg, "r", encoding="utf-8") as f:
                    contenido = f.read().strip()
                    if contenido:
                        c = json.loads(contenido)
                        defaults.update(c)
            except Exception as e:
                print(f"[{APP_NAME}] Error leyendo config {ruta_cfg}: {e}")

        if defaults.get("motor") not in ["sapi5", "piper"] or defaults.get("motor") == "edge":
            defaults["motor"] = "piper"
            defaults["voz_nombre"] = "🇦🇷 Daniela - Mujer (Argentina, offline)"
            defaults["voz_id"] = "es_AR-daniela-high"

        return defaults

    def _guardar_configuracion(self):
        ruta_cfg = obtener_ruta_config()
        try:
            os.makedirs(os.path.dirname(ruta_cfg), exist_ok=True)
            with open(ruta_cfg, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[{APP_NAME}] Error guardando config en {ruta_cfg}: {e}")

    def _actualizar_cfg(self, *_):
        try:
            tono = self.var_tono.get()
            vel = self.var_vel.get()
            vol = self.var_vol.get()
        except tk.TclError:
            tono, vel, vol = 0, 0, 100

        motor = self.var_motor.get()
        voz_nombre = self.var_voz.get()

        if motor == "sapi5":
            voz_id = next((v_id for n, v_id in self.voces_sapi5 if n == voz_nombre), "")
        elif motor == "piper":
            # Se resuelve contra el catálogo completo: la voz puede estar aún sin descargar.
            voz_id = self._voz_piper_id(voz_nombre)
        else:
            voz_nombre, voz_id = resolver_voz_edge(voz_nombre)

        baneadas_lista = [p.strip().lower() for p in self.var_baneadas.get().split(",") if p.strip()]

        map_act = {"⏭️ Siguiente canción": "next", "⏮️ Canción anterior": "prev", "⏯️ Pausar / Reanudar": "play_pause"}
        txt_accion = self.var_media_accion.get() if hasattr(self, "var_media_accion") else "⏭️ Siguiente canción"
        tipo_accion_multimedia = map_act.get(txt_accion, "next")

        self.cfg = {
            "usuario": self.var_usuario.get().strip(),
            "motor": motor,
            "voz_nombre": voz_nombre,
            "voz_id": voz_id,
            "tono": tono,
            "velocidad": vel,
            "volumen": vol,
            "leer_nombre": bool(self.var_leer_nombre.get()),
            "formato_usuario": self.var_formato_usuario.get(),
            "donaciones_activas": bool(self.var_donaciones_activas.get()),
            "esperar_racha": bool(self.var_esperar_racha.get()),
            "min_diamantes": int(self.var_min_diamantes.get()),
            "leer_donacion": bool(self.var_leer_donacion.get()),
            "tpl_donacion": self.var_tpl_donacion.get(),
            "sonido_activo": bool(self.var_sonido_activo.get()),
            "tipo_sonido": self.var_tipo_sonido.get(),
            "ruta_sonido_custom": self.var_ruta_sonido.get(),
            "media_action_activa": bool(self.var_media_activa.get()) if hasattr(self, "var_media_activa") else False,
            "media_tipo_accion": tipo_accion_multimedia,
            "media_min_diamantes": int(self.var_media_min_dia.get()) if hasattr(self, "var_media_min_dia") else 1,
            "bienvenidas_activas": bool(self.var_bienvenidas_activas.get()) if hasattr(self, "var_bienvenidas_activas") else True,
            "mostrar_bienvenida_chat": bool(self.var_mostrar_bienvenida_chat.get()) if hasattr(self, "var_mostrar_bienvenida_chat") else True,
            "leer_bienvenida": bool(self.var_leer_bienvenida.get()) if hasattr(self, "var_leer_bienvenida") else False,
            "anti_repeticion_bienvenida": bool(self.var_anti_repeticion_bienvenida.get()) if hasattr(self, "var_anti_repeticion_bienvenida") else True,
            "tpl_bienvenida": self.var_tpl_bienvenida.get() if hasattr(self, "var_tpl_bienvenida") else "¡Bienvenido {usuario} al directo!",
            "cooldown_bienvenida": int(self.var_cooldown_bienvenida.get()) if hasattr(self, "var_cooldown_bienvenida") else 10,
            "baneadas": self.var_baneadas.get(),
            "baneadas_lista": baneadas_lista,
            "max_caracteres": int(self.var_max_caracteres.get()),
            "max_cola": int(self.var_max_cola.get()),
            "filtrar_links": bool(self.var_filtrar_links.get()),
            "compactar_emojis": bool(self.var_compactar_emojis.get()),
            "auto_reconnect": bool(self.var_auto_reconnect.get()),
        }

        self.lbl_tono.configure(text=f"{tono:+d} Hz")
        self.lbl_vel.configure(text=f"{vel:+d}%")
        self.lbl_vol.configure(text=f"{vol}%")
        self._guardar_configuracion()

    def _al_mover_slider(self, cual):
        self._actualizar_cfg()

    def _al_cambiar_motor(self, *_):
        self._actualizar_opciones_voces()
        self._actualizar_cfg()

    def _actualizar_opciones_voces(self):
        motor = self.var_motor.get()
        if motor == "sapi5":
            opciones = [v[0] for v in self.voces_sapi5]
        elif motor == "piper":
            # Se listan TODAS las voces del catálogo: las que faltan se marcan
            # como "sin descargar" para que el usuario sepa qué debe descargar.
            opciones = [
                v["etiqueta"] if v["instalada"] else f"{v['etiqueta']} · sin descargar"
                for v in self.catalogo_piper
            ]
        else:
            opciones = [v[0] for v in VOICES_EDGE]

        self.cmb_voz.configure(values=opciones)
        voz_actual = self.var_voz.get()
        if voz_actual not in opciones:
            resuelto = opciones[0] if opciones else ""
            if motor == "piper":
                vid = self._voz_piper_id(voz_actual)
                resuelto = next((o for o in opciones if self._voz_piper_id(o) == vid), resuelto) if vid else resuelto
            elif motor == "edge":
                nom_resuelto, _ = resolver_voz_edge(voz_actual)
                if nom_resuelto in opciones:
                    resuelto = nom_resuelto
            self.var_voz.set(resuelto)

        self._actualizar_estado_voz()

    # ------------------------------------------------- VOCES PIPER (descarga)
    def _voz_piper_id(self, nombre: str) -> str:
        """Convierte la etiqueta mostrada (con o sin sufijo) en el id del catálogo."""
        limpio = (nombre or "").replace(" · sin descargar", "").strip()
        for v in self.catalogo_piper:
            if v["etiqueta"] == limpio or v["id"] == limpio:
                return v["id"]

        def _norm(texto: str) -> str:
            # Ignora emojis, mayúsculas, signos y el sufijo antiguo ", offline".
            sin_extras = re.sub(r"\b(offline|online)\b", "", _normalizar_texto_voz(texto))
            return re.sub(r"\s+", " ", sin_extras).strip()

        objetivo = _norm(limpio)
        if not objetivo:
            return ""

        for v in self.catalogo_piper:
            if objetivo == _norm(v["etiqueta"]):
                return v["id"]

        # Último recurso: coincidencia por prefijo (etiquetas renombradas), la más larga gana.
        if len(objetivo) >= 8:
            candidatos = [
                v for v in self.catalogo_piper
                if objetivo.startswith(_norm(v["etiqueta"])) or _norm(v["etiqueta"]).startswith(objetivo)
            ]
            if candidatos:
                return max(candidatos, key=lambda v: len(v["etiqueta"]))["id"]
        return ""

    def _entrada_voz_piper(self, nombre: str):
        vid = self._voz_piper_id(nombre)
        return next((v for v in self.catalogo_piper if v["id"] == vid), None)

    def _actualizar_estado_voz(self):
        if not hasattr(self, "lbl_voz_estado"):
            return
        if self.var_motor.get() != "piper":
            self.lbl_voz_estado.configure(text="")
            self.btn_descargar_voz.state(["disabled"])
            return

        v = self._entrada_voz_piper(self.var_voz.get())
        if v and v["descargable"] and not v["instalada"]:
            self.lbl_voz_estado.configure(
                text=f"⚠️ No está descargada · {v['mb']:.0f} MB · pulsa «Descargar voz»"
            )
            self.btn_descargar_voz.state(["!disabled"])
        elif v:
            self.lbl_voz_estado.configure(text="✅ Descargada (funciona sin Internet)")
            self.btn_descargar_voz.state(["!disabled"])
        else:
            self.lbl_voz_estado.configure(text="")
            self.btn_descargar_voz.state(["disabled"])

    def _al_seleccionar_voz(self):
        self._actualizar_estado_voz()
        self._actualizar_cfg()

    def _descargar_voz_seleccionada(self):
        v = self._entrada_voz_piper(self.var_voz.get())
        if not v or not v["descargable"]:
            messagebox.showinfo(APP_NAME, "Esa voz no se puede descargar.")
            return
        if self._descargando_voz:
            messagebox.showinfo(APP_NAME, "Ya hay una descarga de voz en curso.")
            return

        self._descargando_voz = True
        self.btn_descargar_voz.state(["disabled"])
        self.lbl_voz_estado.configure(text="⏳ Iniciando descarga...")
        threading.Thread(target=self._hilo_descarga_voz, args=(v,), daemon=True).start()

    def _hilo_descarga_voz(self, voz: dict):
        def _progreso(percent, mb, total_mb, velocidad):
            self.cola_ui.put((
                "voz_descarga",
                f"{percent}% · {mb:.1f}/{total_mb:.1f} MB · {velocidad:.1f} MB/s",
            ))

        try:
            tts_voces.descargar(voz["id"], PIPER_DIR, progreso=_progreso)
            self.cola_ui.put(("voz_descarga_ok", voz["etiqueta"]))
        except Exception as e:
            self.cola_ui.put(("voz_descarga_err", str(e)))
        finally:
            self._descargando_voz = False

    def _refrescar_catalogo_voces(self):
        self.catalogo_piper = catalogo_voces_piper()
        self.voces_piper = obtener_voces_piper()
        self._actualizar_opciones_voces()

    def _al_seleccionar_preset(self, *_):
        nombre_preset = self.var_preset.get()
        if nombre_preset in BOT_PRESETS:
            p = BOT_PRESETS[nombre_preset]
            self.var_tono.set(p["tono"])
            self.var_vel.set(p["vel"])
            self.lbl_preset_desc.configure(text=p["desc"])
            self._actualizar_cfg()

    def _al_cambiar_sonido(self, *_):
        if self.var_tipo_sonido.get() == "Personalizado...":
            self.btn_examinar_snd.pack(side="left", padx=6)
        else:
            self.btn_examinar_snd.pack_forget()
        self._actualizar_cfg()

    def _examinar_sonido(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de sonido",
            filetypes=[("Archivos de audio", "*.wav *.mp3"), ("WAV", "*.wav"), ("MP3", "*.mp3")]
        )
        if ruta:
            self.var_ruta_sonido.set(ruta)
            self._actualizar_cfg()

    def _obtener_ruta_sonido_alerta(self) -> str:
        tipo = self.var_tipo_sonido.get()
        if tipo == "Personalizado...":
            return self.var_ruta_sonido.get()
        return self.sonidos_predeterminados.get(tipo, "")

    # -------------------------------------------------------------- ACCIONES
    def _conectar(self):
        if self.hilo_cliente and self.hilo_cliente.is_alive():
            return

        usuario_raw = self.var_usuario.get()
        usuario_limpio = limpiar_nombre_usuario_tiktok(usuario_raw)
        if not usuario_limpio:
            messagebox.showwarning("Usuario requerido", "Por favor introduce un usuario o link válido de TikTok Live.")
            return

        self.var_usuario.set(f"@{usuario_limpio}")
        self._actualizar_cfg()
        self._debe_correr = True
        self.btn_conectar.configure(state="disabled")
        self.btn_desconectar.configure(state="normal")
        self._actualizar_estado_visual("Conectando...", "amber")
        self._log_sistema(f"Conectando al directo de @{usuario_limpio}...")

        self.hilo_cliente = threading.Thread(target=self._hilo_cliente_loop, args=(usuario_limpio,), daemon=True)
        self.hilo_cliente.start()

    def _desconectar(self):
        self._log_sistema("Desconectando del directo...")
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
        self._actualizar_estado_visual("Desconectado", "gray")
        self.btn_conectar.configure(state="normal")
        self.btn_desconectar.configure(state="disabled")

    def _actualizar_estado_visual(self, texto: str, color_tipo: str):
        color_map = {
            "green": (self.c_success, self.c_success_light),
            "amber": (self.c_warning, self.c_warning_light),
            "red": (self.c_danger, self.c_danger_light),
            "gray": (self.c_text_muted, "#F1F5F9"),
        }
        fg_col, bg_col = color_map.get(color_tipo, (self.c_text_muted, "#F1F5F9"))
        self.lbl_indicador.configure(text=f"● {texto}", fg=fg_col, bg=bg_col)

    # ---------------------------------------------------- CONEXIÓN & RESILIENCIA
    def _hilo_cliente_loop(self, usuario: str):
        """Bucle de conexión con reconexión automática y tolerancia a fallos."""
        reintentos = 0
        max_reintentos = 15

        while self._debe_correr:
            try:
                self.cola_ui.put(("estado", f"Conectando a @{usuario}...", "amber"))
                cliente = TikTokLiveClient(unique_id=usuario)
                self.cliente = cliente
                logging.getLogger("TikTokLive").setLevel(logging.ERROR)

                @cliente.on(ConnectEvent)
                async def _al_conectar(event: ConnectEvent):
                    self.cola_ui.put(("sis", f"✅ CONECTADO con éxito a @{event.unique_id}"))
                    self.cola_ui.put(("estado", f"Conectado a @{event.unique_id}", "green"))

                @cliente.on(DisconnectEvent)
                async def _al_desconectar(event: DisconnectEvent):
                    if self._debe_correr:
                        self.cola_ui.put(("sis", "⚠️ TikTok reportó desconexión del directo."))

                @cliente.on(CommentEvent)
                async def _al_comentario(event: CommentEvent):
                    nombre_usuario = obtener_nombre_usuario(event.user)
                    comentario = normalizar_comentario(event.comment or "")

                    if not self._comentario_valido(comentario):
                        return

                    self.cola_ui.put(("com", nombre_usuario, comentario))

                    if self.cfg.get("leer_nombre", True):
                        fmt = self.cfg.get("formato_usuario", "{usuario} dice: {mensaje}")
                        texto_voz = fmt.replace("{usuario}", nombre_usuario).replace("{mensaje}", comentario)
                    else:
                        texto_voz = comentario

                    self._encolar_voz(prioridad=2, texto=texto_voz)

                @cliente.on(JoinEvent)
                async def _al_unirse(event: JoinEvent):
                    if not self.cfg.get("bienvenidas_activas", True):
                        return
                    nombre_usuario = obtener_nombre_usuario(event.user)
                    ahora = time.time()
                    if self.cfg.get("anti_repeticion_bienvenida", True):
                        if nombre_usuario.lower() in self._usuarios_saludados:
                            return
                        self._usuarios_saludados.add(nombre_usuario.lower())

                    if self.cfg.get("mostrar_bienvenida_chat", True):
                        self.cola_ui.put(("join", nombre_usuario))

                    if self.cfg.get("leer_bienvenida", False):
                        cooldown = max(3, int(self.cfg.get("cooldown_bienvenida", 10)))
                        if ahora - self._ultimo_saludo_tiempo >= cooldown:
                            self._ultimo_saludo_tiempo = ahora
                            tpl = self.cfg.get("tpl_bienvenida", "¡Bienvenido {usuario} al directo!")
                            texto_bienvenida = tpl.replace("{usuario}", nombre_usuario)
                            self._encolar_voz(prioridad=3, texto=texto_bienvenida)

                @cliente.on(GiftEvent)
                async def _al_regalo(event: GiftEvent):
                    if not self.cfg.get("donaciones_activas", True):
                        return

                    if self.cfg.get("esperar_racha", True) and getattr(event, "streaking", False):
                        return

                    nombre_usuario = obtener_nombre_usuario(event.user)
                    regalo_nombre = getattr(getattr(event, "gift", None), "name", "Regalo") or "Regalo"
                    diamantes_unidad = getattr(getattr(event, "gift", None), "diamond_count", 1) or 1
                    cantidad = getattr(event, "repeat_count", 1) or 1
                    total_diamantes = diamantes_unidad * cantidad

                    if total_diamantes < self.cfg.get("min_diamantes", 1):
                        return

                    self.cola_ui.put(("don", nombre_usuario, regalo_nombre, cantidad, total_diamantes))

                    # Control multimedia en YouTube Music / Spotify
                    if self.cfg.get("media_action_activa", False):
                        min_media = int(self.cfg.get("media_min_diamantes", 1) or 1)
                        if total_diamantes >= min_media:
                            tipo_act = self.cfg.get("media_tipo_accion", "next")
                            self._ejecutar_accion_multimedia(tipo_act, f"donación de {nombre_usuario}")

                    if self.cfg.get("sonido_activo", True):
                        ruta_sonido = self._obtener_ruta_sonido_alerta()
                        audio_assets.reproducir_sonido_alerta(ruta_sonido)

                    if self.cfg.get("leer_donacion", True):
                        tpl = self.cfg.get("tpl_donacion", "¡Muchas gracias a {usuario} por enviar {cantidad} {regalo}!")
                        texto_don = (tpl.replace("{usuario}", nombre_usuario)
                                        .replace("{regalo}", regalo_nombre)
                                        .replace("{cantidad}", str(cantidad))
                                        .replace("{diamantes}", str(total_diamantes)))
                        retraso = 1.8 if self.cfg.get("sonido_activo", True) else 0.0
                        def _encolar_con_espera():
                            if retraso > 0:
                                time.sleep(retraso)
                            self._encolar_voz(prioridad=1, texto=texto_don)
                        threading.Thread(target=_encolar_con_espera, daemon=True).start()

                cliente.run()

            except Exception as exc:
                if not self._debe_correr:
                    break
                err_msg = mensaje_error_conexion(exc)
                self.cola_ui.put(("err", f"Desconexión: {err_msg}"))

            if not self._debe_correr:
                break

            if self.cfg.get("auto_reconnect", True):
                reintentos += 1
                if reintentos > max_reintentos:
                    self.cola_ui.put(("err", "Límite de reintentos alcanzado."))
                    break
                pausa = min(3 + reintentos * 2, 15)
                self.cola_ui.put(("sis", f"Reconectando automáticamente en {pausa}s (intento {reintentos}/{max_reintentos})..."))
                self.cola_ui.put(("estado", f"Reconectando ({reintentos})...", "amber"))

                for _ in range(pausa * 2):
                    if not self._debe_correr:
                        break
                    time.sleep(0.5)
            else:
                break

        self.cliente = None
        self._debe_correr = False
        self.cola_ui.put(("fin", None))

    def _comentario_valido(self, comentario: str) -> bool:
        if not comentario or len(comentario) > self.cfg.get("max_caracteres", 85):
            return False
        texto_bajo = comentario.lower()
        for p in self.cfg.get("baneadas_lista", []):
            if p and p in texto_bajo:
                return False
        return True

    def _encolar_voz(self, prioridad: int, texto: str):
        max_q = self.cfg.get("max_cola", 8)
        if self.cola_voz.qsize() >= max_q:
            if prioridad >= 2:
                return
        self.cola_voz.put((prioridad, time.time(), texto))

    # ------------------------------------------------------------------ HILO TTS
    def _hilo_tts(self):
        """Hilo de lectura TTS con procesamiento prioritario y captura de excepciones."""
        while True:
            item = self.cola_voz.get()
            if item is None:
                break

            prioridad, _, texto = item
            cfg = self.cfg

            try:
                respaldo = False
                motor_actual = cfg.get("motor", "piper")

                if motor_actual == "sapi5":
                    self._hablar_sapi5(texto, cfg)
                elif motor_actual == "piper":
                    try:
                        self._hablar_piper(texto, cfg)
                    except Exception:
                        # El modelo .onnx no está descargado o falló el motor offline:
                        # no dejamos el directo mudo, pasamos a otra voz.
                        if not self._aviso_respaldo_tts:
                            self._aviso_respaldo_tts = True
                            self.cola_ui.put(("sis", "⚠️ La voz neuronal offline no está descargada. Selecciónala en «Voz principal neural» y pulsa «Descargar voz»."))
                        self._hablar_voz_alternativa(texto)
                        respaldo = True
                elif self._edge_disponible:
                    try:
                        self._hablar_edge(texto, cfg)
                    except Exception:
                        self._edge_disponible = False
                        if not self._aviso_respaldo_tts:
                            self._aviso_respaldo_tts = True
                            self.cola_ui.put(("sis", "⚠️ Edge TTS no disponible (error 403). Usando voz alternativa argentina automáticamente."))
                        self._hablar_voz_alternativa(texto)
                        respaldo = True
                else:
                    self._hablar_voz_alternativa(texto)
                    respaldo = True

                detalle = (
                    "Leído con voz alternativa (Edge TTS no disponible)."
                    if respaldo else "Voz lista para nuevos comentarios."
                )
                self.cola_ui.put(("tts_estado", "listo", detalle))
            except Exception as e:
                self.cola_ui.put(("tts_estado", "fallando", str(e)))
                self.cola_ui.put(("err", f"❌ Error en síntesis de voz: {e}"))
            finally:
                self.cola_voz.task_done()

    def _hablar_edge(self, texto: str, cfg: dict):
        import edge_tts
        import tempfile
        import uuid

        voz_id = cfg.get("voz_id") or "es-AR-TomasNeural"
        voz_nombre = cfg.get("voz_nombre", voz_id)
        tono = cfg.get("tono", 0)
        vel = cfg.get("velocidad", 0)
        vol = cfg.get("volumen", 100)

        rate_str = f"{vel:+d}%"
        pitch_str = f"{tono:+d}Hz"
        vol_str = f"{vol:+d}%" if vol != 100 else "+0%"

        ruta_temp = os.path.join(tempfile.gettempdir(), f"mybot_tts_{uuid.uuid4().hex[:8]}.mp3")

        async def _generar():
            com = edge_tts.Communicate(texto, voz_id, rate=rate_str, pitch=pitch_str, volume=vol_str)
            await com.save(ruta_temp)

        try:
            self.cola_ui.put(("tts_estado", "cargando", f"Descargando audio ({voz_nombre})..."))
            asyncio.run(_generar())
            self.cola_ui.put(("tts_estado", "reproduciendo", f"Reproduciendo voz ({voz_nombre})..."))
            audio_assets.reproducir_mp3_tts(ruta_temp)
        finally:
            if os.path.exists(ruta_temp):
                try:
                    os.remove(ruta_temp)
                except OSError:
                    pass

    def _voz_sapi5_es(self) -> str:
        """Devuelve el id de una voz SAPI5 en español si existe."""
        for nom, vid in self.voces_sapi5:
            bajo = f"{nom} {vid}".lower()
            if "spanish" in bajo or "españa" in bajo or "es-es" in bajo or "es-ar" in bajo or "es-mx" in bajo:
                return vid
        return ""

    def _cfg_respaldo(self) -> dict:
        """Copia la configuración con una voz SAPI5 válida para el respaldo."""
        cfg = dict(self.cfg)
        cfg["voz_id"] = self._voz_sapi5_es()
        return cfg

    @staticmethod
    def _factor_tono(cfg: dict) -> float:
        """Convierte 'tono' (-50..50) en factor de frecuencia (>1 = más agudo)."""
        tono = int(cfg.get("tono", 0) or 0)
        return max(0.5, min(2.0, 1.0 + tono / 100.0))

    @staticmethod
    def _ssml_tono(texto: str, cfg: dict) -> str:
        """SSML con cambio de tono para SAPI5 (vacío si el tono es 0)."""
        tono = int(cfg.get("tono", 0) or 0)
        if not tono:
            return ""
        seguro = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f'<prosody pitch="{tono:+d}%">{seguro}</prosody>'

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

    def _modelo_piper(self, cfg: dict) -> str:
        modelo = str(cfg.get("voz_id") or "")
        if modelo == "es_AR-mateo-hombre":
            if os.path.exists(os.path.join(PIPER_DIR, "es_AR-daniela-high.onnx")):
                return "es_AR-daniela-high"
        if modelo and os.path.exists(os.path.join(PIPER_DIR, f"{modelo}.onnx")):
            return modelo
        return self.voces_piper[0][1] if self.voces_piper else ""

    def _sintetizar_piper(self, texto: str, cfg: dict) -> str:
        """Sintetiza un WAV con Piper y devuelve su ruta temporal (con el tono ya aplicado)."""
        import tempfile
        import uuid
        import wave

        modelo = self._modelo_piper(cfg)
        if not modelo:
            raise RuntimeError("No hay ningún modelo de voz Piper instalado.")

        if self._piper_voz is None or self._piper_modelo != modelo:
            self.cola_ui.put(("tts_estado", "cargando", "Cargando voz neuronal offline..."))
            from piper import PiperVoice

            self._piper_voz = PiperVoice.load(os.path.join(PIPER_DIR, f"{modelo}.onnx"))
            self._piper_modelo = modelo

        es_mateo = (str(cfg.get("voz_id") or "") == "es_AR-mateo-hombre")
        factor = self._factor_tono(cfg) * (0.80 if es_mateo else 1.0)

        ruta_wav = os.path.join(tempfile.gettempdir(), f"mybot_piper_{uuid.uuid4().hex[:8]}.wav")
        with wave.open(ruta_wav, "wb") as wav_file:
            try:
                from piper import SynthesisConfig

                vel = int(cfg.get("velocidad", 0) or 0)
                length_scale = max(0.25, min(4.0, factor / (1.0 + vel / 100.0)))
                syn = SynthesisConfig(
                    length_scale=length_scale,
                    volume=int(cfg.get("volumen", 100) or 100) / 100.0,
                )
                self._piper_voz.synthesize_wav(texto, wav_file, syn_config=syn)
            except Exception:
                self._piper_voz.synthesize_wav(texto, wav_file)

        if abs(factor - 1.0) > 0.01:
            ruta_tono = os.path.join(tempfile.gettempdir(), f"mybot_piper_tono_{uuid.uuid4().hex[:8]}.wav")
            self._cambiar_tono_wav(ruta_wav, ruta_tono, factor)
            try:
                os.remove(ruta_wav)
            except OSError:
                pass
            return ruta_tono
        return ruta_wav

    def _hablar_piper(self, texto: str, cfg: dict):
        """Voz neuronal OFFLINE (Piper) con control real de tono."""
        ruta_wav = ""
        try:
            ruta_wav = self._sintetizar_piper(texto, cfg)
            self.cola_ui.put(("tts_estado", "reproduciendo", "Hablando (voz neuronal offline)..."))
            audio_assets.reproducir_wav_tts(ruta_wav)
        finally:
            if ruta_wav and os.path.exists(ruta_wav):
                try:
                    os.remove(ruta_wav)
                except OSError:
                    pass

    def _hablar_gtts(self, texto: str, cfg: dict):
        """Voz alternativa de Google (gTTS). Requiere Internet."""
        import tempfile
        import uuid

        from gtts import gTTS

        voz = str(cfg.get("voz_id") or cfg.get("voz_nombre") or "")
        coincidencia = re.match(r"^([a-zA-Z]{2})[-_]", voz)
        idioma = coincidencia.group(1).lower() if coincidencia else "es"

        ruta_temp = os.path.join(tempfile.gettempdir(), f"mybot_gtts_{uuid.uuid4().hex[:8]}.mp3")
        try:
            self.cola_ui.put(("tts_estado", "cargando", "Generando voz alternativa (Google)..."))
            gTTS(texto, lang=idioma, slow=False).save(ruta_temp)
            self.cola_ui.put(("tts_estado", "reproduciendo", "Hablando (voz alternativa)..."))
            audio_assets.reproducir_mp3_tts(ruta_temp)
        finally:
            if os.path.exists(ruta_temp):
                try:
                    os.remove(ruta_temp)
                except OSError:
                    pass

    def _hablar_voz_alternativa(self, texto: str):
        """Respaldo: Piper (offline), luego gTTS y por último la voz local de Windows."""
        if self.voces_piper:
            try:
                self._hablar_piper(texto, self.cfg)
                return
            except Exception as exc:
                self.cola_ui.put(("sis", f"⚠️ Voz neuronal offline no disponible ({exc}). Probando otra alternativa."))
        try:
            self._hablar_gtts(texto, self.cfg)
            return
        except Exception as exc:
            self.cola_ui.put(("sis", f"⚠️ Voz alternativa online no disponible ({exc}). Usando voz local de Windows."))
        self._hablar_sapi5(texto, self._cfg_respaldo())

    def _hablar_sapi5(self, texto: str, cfg: dict):
        """Voz local de Windows: SAPI nativo (win32com) con respaldo pyttsx3."""
        voz_id = cfg.get("voz_id", "")
        voz_sapi = bool(voz_id) and ("HKEY" in voz_id or voz_id.startswith("{"))
        if not voz_sapi:
            voz_id = self._voz_sapi5_es() or ""
            voz_sapi = bool(voz_id)
        volumen = int(cfg.get("volumen", 100) or 100)
        velocidad = int(cfg.get("velocidad", 0) or 0)
        voz_nombre = cfg.get("voz_nombre", "SAPI5")

        try:
            import pythoncom
            import win32com.client

            pythoncom.CoInitialize()
            if self._sapi_voice is None:
                self._sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
            voice = self._sapi_voice
            if voz_sapi:
                try:
                    for v in voice.GetVoices():
                        if voz_id.lower() in str(v.Id).lower():
                            voice.Voice = v
                            break
                except Exception:
                    pass
            try:
                voice.Rate = max(-10, min(10, int(velocidad / 8)))
                voice.Volume = max(0, min(100, volumen))
            except Exception:
                pass

            self.cola_ui.put(("tts_estado", "reproduciendo", f"Hablando (voz local: {voz_nombre})..."))
            ssml = self._ssml_tono(texto, cfg)
            if ssml:
                voice.Speak(ssml, 8)
            else:
                voice.Speak(texto, 0)
            return
        except Exception as e:
            self.cola_ui.put(("sis", f"⚠️ API SAPI nativa no disponible ({e}); usando pyttsx3."))

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
        self.cola_ui.put(("tts_estado", "reproduciendo", f"Hablando SAPI5 ({voz_nombre})..."))
        engine.say(texto)
        engine.runAndWait()

    # ---------------------------------------------------- PRUEBAS & ACCIONES
    def _probar_voz(self):
        texto = self.var_texto_test.get().strip()
        if not texto:
            texto = "Prueba de voz en directo."
        self._actualizar_cfg()
        self._encolar_voz(prioridad=1, texto=texto)

    def _descargar_audio_prueba(self):
        texto = self.var_texto_test.get().strip()
        if not texto:
            texto = "Prueba de voz en directo."
        self._actualizar_cfg()

        carpeta_descargas = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "descargas_audio")
        os.makedirs(carpeta_descargas, exist_ok=True)

        def _hilo_descarga():
            self.cola_ui.put(("tts_estado", "cargando", "Generando y guardando archivo de audio..."))
            try:
                cfg = self.cfg
                motor = cfg.get("motor", "piper")
                voz_id = cfg.get("voz_id", "es-AR-TomasNeural")
                voz_nombre = cfg.get("voz_nombre", "Tomas")

                nom_limpio = "".join(c for c in voz_nombre if c.isalnum() or c in (" ", "_", "-")).strip()
                nom_limpio = nom_limpio.replace(" ", "_")
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                base_archivo = f"MyBot_{nom_limpio}_{timestamp}"

                if motor == "piper":
                    # Voz neuronal offline: es el motor por defecto, antes caía en la voz de Windows.
                    import shutil

                    origen = self._sintetizar_piper(texto, cfg)
                    ruta_salida = os.path.join(carpeta_descargas, base_archivo + os.path.splitext(origen)[1].lower())
                    try:
                        shutil.copyfile(origen, ruta_salida)
                    finally:
                        try:
                            os.remove(origen)
                        except OSError:
                            pass
                elif motor == "edge":
                    import edge_tts
                    tono = cfg.get("tono", 0)
                    vel = cfg.get("velocidad", 0)
                    vol = cfg.get("volumen", 100)
                    rate_str = f"{vel:+d}%"
                    pitch_str = f"{tono:+d}Hz"
                    vol_str = f"{vol:+d}%" if vol != 100 else "+0%"
                    ruta_salida = os.path.join(carpeta_descargas, base_archivo + ".mp3")

                    async def _guardar():
                        com = edge_tts.Communicate(texto, voz_id, rate=rate_str, pitch=pitch_str, volume=vol_str)
                        await com.save(ruta_salida)

                    asyncio.run(_guardar())
                else:
                    import pyttsx3
                    engine = pyttsx3.init(driverName="sapi5")
                    if voz_id:
                        try:
                            engine.setProperty("voice", voz_id)
                        except Exception:
                            pass
                    vel_pct = cfg.get("velocidad", 0)
                    rate_sapi = int(165 * (1.0 + (vel_pct / 100.0)))
                    engine.setProperty("rate", max(80, min(350, rate_sapi)))
                    vol_pct = cfg.get("volumen", 100) / 100.0
                    engine.setProperty("volume", max(0.0, min(1.0, vol_pct)))
                    ruta_salida = os.path.join(carpeta_descargas, base_archivo + ".wav")
                    engine.save_to_file(texto, ruta_salida)
                    engine.runAndWait()

                tam = os.path.getsize(ruta_salida)
                self.cola_ui.put(("tts_estado", "listo", f"Audio guardado: {os.path.basename(ruta_salida)}"))
                self.cola_ui.put(("sis", f"💾 Audio guardado ({tam} bytes): {ruta_salida}"))
            except Exception as e:
                self.cola_ui.put(("tts_estado", "fallando", str(e)))
                self.cola_ui.put(("err", f"❌ Error descargando audio: {e}"))

        threading.Thread(target=_hilo_descarga, daemon=True).start()

    def _abrir_carpeta_descargas(self):
        carpeta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "descargas_audio")
        os.makedirs(carpeta, exist_ok=True)
        try:
            os.startfile(carpeta)
        except Exception as e:
            self._log_error(f"No se pudo abrir la carpeta: {e}")

    def _probar_alerta_donacion(self):
        self._actualizar_cfg()
        tiene_sonido = False
        if self.cfg.get("sonido_activo", True):
            ruta_sonido = self._obtener_ruta_sonido_alerta()
            if ruta_sonido and os.path.exists(ruta_sonido):
                tiene_sonido = True
                audio_assets.reproducir_sonido_alerta(ruta_sonido)

        if self.cfg.get("leer_donacion", True):
            tpl = self.cfg.get("tpl_donacion", "¡Muchas gracias a {usuario} por enviar {cantidad} {regalo}!")
            texto_test = (tpl.replace("{usuario}", "Carlos")
                             .replace("{regalo}", "Rosa")
                             .replace("{cantidad}", "5")
                             .replace("{diamantes}", "5"))
            retraso = 1800 if tiene_sonido else 0
            self.root.after(retraso, lambda: self._encolar_voz(prioridad=1, texto=texto_test))

    def _vaciar_cola_audio(self):
        """Silenciamiento instantáneo: detiene el audio que esté sonando y vacía la cola."""
        audio_assets.detener_todo_el_audio()
        if self._sapi_engine:
            try:
                self._sapi_engine.stop()
            except Exception:
                pass

        with self.cola_voz.mutex:
            self.cola_voz.queue.clear()

        self._actualizar_tts_estado_visual("listo", "Audio silenciado de inmediato.")
        self._log_sistema("🔇 Audio silenciado de inmediato y cola de voz vaciada.")

    # ------------------------------------------------------------- MENSAJES UI
    def _actualizar_tts_estado_visual(self, estado: str, detalle: str = ""):
        if estado == "cargando":
            txt_badge = "⏳ Cargando..."
            bg_badge = self.c_warning_light
            fg_badge = "#B45309"
            txt_top = "🎙️ Voz: ⏳ Cargando..."
            det = detalle or "Descargando voz neural..."
        elif estado == "reproduciendo":
            txt_badge = "🔊 Hablando..."
            bg_badge = self.c_success_light
            fg_badge = "#15803D"
            txt_top = "🎙️ Voz: 🔊 Hablando..."
            det = detalle or "Reproduciendo audio en directo..."
        elif estado == "fallando":
            txt_badge = "❌ Error"
            bg_badge = self.c_danger_light
            fg_badge = self.c_danger
            txt_top = "🎙️ Voz: ❌ Error"
            det = f"Fallo: {detalle}" if detalle else "Error en síntesis de voz."
        else:
            txt_badge = "● Estado: Listo"
            bg_badge = self.c_primary_light
            fg_badge = self.c_primary_dark
            txt_top = "🎙️ Voz: ● Lista"
            det = detalle or "Voz lista para usar en el directo."

        if hasattr(self, "lbl_badge_estado"):
            self.lbl_badge_estado.configure(text=txt_badge, bg=bg_badge, fg=fg_badge)
        if hasattr(self, "lbl_detalle_estado"):
            self.lbl_detalle_estado.configure(text=det)
        if hasattr(self, "lbl_tts_status_top"):
            self.lbl_tts_status_top.configure(text=txt_top, bg=bg_badge, fg=fg_badge)

    def _procesar_cola_ui(self):
        try:
            while True:
                item = self.cola_ui.get_nowait()
                tipo = item[0]

                if tipo == "com":
                    _, usuario, comentario = item
                    self.total_comentarios += 1
                    self._escribir_chat_comentario(usuario, comentario)
                    self._actualizar_metricas()

                elif tipo == "don":
                    _, usuario, regalo, cant, diamantes = item
                    self.total_donaciones += 1
                    self.total_diamantes += diamantes
                    self._escribir_chat_donacion(usuario, regalo, cant, diamantes)
                    self._actualizar_metricas()

                elif tipo == "join":
                    _, usuario = item
                    self._escribir_chat_bienvenida(usuario)

                elif tipo == "sis":
                    self._log_sistema(item[1])

                elif tipo == "err":
                    self._log_error(item[1])

                elif tipo == "estado":
                    self._actualizar_estado_visual(item[1], item[2])

                elif tipo == "tts_estado":
                    estado = item[1]
                    detalle = item[2] if len(item) > 2 else ""
                    self._actualizar_tts_estado_visual(estado, detalle)

                elif tipo == "voz_descarga":
                    self.lbl_voz_estado.configure(text=f"⏳ {item[1]}")

                elif tipo == "voz_descarga_ok":
                    self._refrescar_catalogo_voces()
                    self._log_sistema(f"✅ Voz neuronal instalada: {item[1]}")
                    messagebox.showinfo(APP_NAME, f"Voz descargada correctamente:\n{item[1]}")

                elif tipo == "voz_descarga_err":
                    self._refrescar_catalogo_voces()
                    self._log_error(f"❌ No se pudo descargar la voz: {item[1]}")
                    messagebox.showerror(APP_NAME, f"No se pudo descargar la voz:\n{item[1]}")

                elif tipo == "fin":
                    self.btn_conectar.configure(state="normal")
                    self.btn_desconectar.configure(state="disabled")
                    self._actualizar_estado_visual("Desconectado", "gray")

                elif tipo == "nueva_version":
                    data = item[1]
                    self.ultima_info_version = data
                    v_name = data.get("version_name", data.get("version", "v1.1"))
                    self.lbl_update_txt.configure(
                        text=f"🚀 ¡Nueva versión disponible ({v_name})! Descárgala ahora."
                    )
                    try:
                        self.f_update_banner.pack(fill="x", pady=(0, 10), before=self.notebook)
                    except Exception:
                        self.f_update_banner.pack(fill="x", pady=(0, 10))
                    self._log_sistema(f"🚀 ¡Nueva actualización disponible de MyBot ({v_name})!")

                elif tipo == "version_al_dia":
                    messagebox.showinfo(
                        "MyBot Actualizado",
                        f"¡Tienes la versión más reciente ({APP_VERSION})!\nNo hay nuevas actualizaciones pendientes."
                    )

        except queue.Empty:
            pass

        q_size = self.cola_voz.qsize()
        self.lbl_estado_cola.configure(text=f"Cola de voz: {q_size}")
        self.root.after(80, self._procesar_cola_ui)

    def _comprobar_actualizacion(self, silencioso: bool = True):
        def _hilo():
            import urllib.request
            try:
                req = urllib.request.Request(
                    UPDATE_URL,
                    headers={"User-Agent": f"MyBot/{APP_VERSION} (Windows NT 10.0; Win64)"}
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        rem_v = str(data.get("version", "1.0.0")).strip()
                        def parse_v(v):
                            parts = [int(p) for p in re.sub(r"[^\d.]", "", v).split(".") if p.isdigit()]
                            return tuple(parts) if parts else (1, 0, 0)

                        if parse_v(rem_v) > parse_v(CURRENT_VERSION):
                            self.cola_ui.put(("nueva_version", data))
                        elif not silencioso:
                            self.cola_ui.put(("version_al_dia", data))
            except Exception as e:
                if not silencioso:
                    self.cola_ui.put(("err", f"No se pudo consultar el servidor de actualizaciones: {e}"))

        threading.Thread(target=_hilo, daemon=True).start()

    def _abrir_url_descarga(self):
        import webbrowser
        url = "https://mybot-79861.web.app/downloads/MyBot.exe"
        if self.ultima_info_version and "download_url" in self.ultima_info_version:
            url = self.ultima_info_version["download_url"]
        webbrowser.open(url)

    def _actualizar_metricas(self):
        self.lbl_comentarios.configure(text=f"💬 {self.total_comentarios} comentarios")
        self.lbl_donaciones.configure(text=f"🎁 {self.total_donaciones} regalos")
        self.lbl_diamantes.configure(text=f"💎 {self.total_diamantes} diamantes")

    def _escribir_chat_comentario(self, usuario: str, comentario: str):
        self.txt_chat.configure(state="normal")
        self.txt_chat.insert("end", f"💬 {usuario}: ", "user")
        self.txt_chat.insert("end", f"{comentario}\n", "com")
        self._autoscroll()
        self.txt_chat.configure(state="disabled")

    def _escribir_chat_donacion(self, usuario: str, regalo: str, cant: int, diamantes: int):
        self.txt_chat.configure(state="normal")
        self.txt_chat.insert("end", "🎁 [DONACIÓN] ", "don_badge")
        self.txt_chat.insert("end", f"{usuario} envió {cant}x {regalo} ({diamantes} 💎)\n", "don_txt")
        self._autoscroll()
        self.txt_chat.configure(state="disabled")

    def _escribir_chat_bienvenida(self, usuario: str):
        self.txt_chat.configure(state="normal")
        self.txt_chat.insert("end", "👋 [ENTRADA] ", "user")
        self.txt_chat.insert("end", f"{usuario} se unió al directo.\n", "sis")
        self._autoscroll()
        self.txt_chat.configure(state="disabled")

    def _ejecutar_accion_multimedia(self, accion: str, usuario: str = ""):
        """Simula pulsación de teclas multimedia nativas de Windows para YouTube Music / Spotify."""
        if sys.platform.startswith("win"):
            try:
                import ctypes
                VK_MEDIA_NEXT_TRACK = 0xB0
                VK_MEDIA_PREV_TRACK = 0xB1
                VK_MEDIA_PLAY_PAUSE = 0xB3
                KEYEVENTF_KEYUP = 0x0002

                vk = VK_MEDIA_NEXT_TRACK
                nom_act = "Siguiente canción ⏭️"
                if accion == "prev":
                    vk = VK_MEDIA_PREV_TRACK
                    nom_act = "Canción anterior ⏮️"
                elif accion == "play_pause":
                    vk = VK_MEDIA_PLAY_PAUSE
                    nom_act = "Pausar / Reanudar ⏯️"

                user32 = ctypes.windll.user32
                user32.keybd_event(vk, 0, 0, 0)
                time.sleep(0.04)
                user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

                msg = f"🎵 [YouTube Music] {nom_act}" + (f" activado por {usuario}" if usuario else "")
                self.cola_ui.put(("sis", msg))
            except Exception as e:
                print(f"[Media] Error enviando tecla: {e}")

    def _probar_bienvenida(self):
        usuario = "Alex"
        tpl = self.var_tpl_bienvenida.get() if hasattr(self, "var_tpl_bienvenida") else "¡Bienvenido {usuario} al directo!"
        texto = tpl.replace("{usuario}", usuario)
        self.cola_ui.put(("join", usuario))
        self._encolar_voz(prioridad=2, texto=texto)

    def _log_sistema(self, msg: str):
        self.txt_chat.configure(state="normal")
        self.txt_chat.insert("end", f"› {msg}\n", "sis")
        self._autoscroll()
        self.txt_chat.configure(state="disabled")

    def _log_error(self, msg: str):
        self.txt_chat.configure(state="normal")
        self.txt_chat.insert("end", f"⚠️ {msg}\n", "err")
        self._autoscroll()
        self.txt_chat.configure(state="disabled")

    def _autoscroll(self):
        if self.txt_chat.yview()[1] >= 0.98 or self.txt_chat.yview()[1] == 1.0:
            self.txt_chat.see("end")

    def _limpiar_chat(self):
        self.txt_chat.configure(state="normal")
        self.txt_chat.delete("1.0", "end")
        self.txt_chat.configure(state="disabled")

    # ----------------------------------------------------------------- CIERRE
    def _al_cerrar(self):
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

        audio_assets.detener_todo_el_audio()
        self._guardar_configuracion()
        self.cola_voz.put(None)

        if self._sapi_engine:
            try:
                self._sapi_engine.stop()
            except Exception:
                pass

        self.root.destroy()


# =============================================================================
# ENTRADA PRINCIPAL
# =============================================================================
def main():
    logging.basicConfig(level=logging.ERROR)

    if "--electron" in sys.argv:
        try:
            import subprocess
            base_dir = os.path.dirname(os.path.abspath(__file__))
            cmd = ["npx", "electron", "."]
            subprocess.run(cmd, cwd=base_dir, shell=True)
            return
        except Exception as e:
            print(f"[MyBot] Error iniciando Desktop App Electron: {e}")

    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("mybot.v10.app")
        except Exception:
            pass

    root = tk.Tk()
    app = MyBotApp(root)
    if "--autoclose" in sys.argv:
        root.after(3000, app._al_cerrar)
    root.mainloop()


if __name__ == "__main__":
    main()
