"""
=============================================================================
 MyBot - Gestor de Sonidos de Alerta y Reproductor de Audio Robusto Windows
=============================================================================
 Genera tonos de alerta limpios en formato WAV puro (sin dependencias externas)
 y proporciona funciones seguras para reproducir WAV y MP3 en Windows con soporte
 para cancelación y parada de audio instantánea.
=============================================================================
"""

import ctypes
import math
import os
import struct
import threading
import time
import uuid
import wave

import sys

def _es_directorio_escribible(carpeta: str) -> bool:
    try:
        os.makedirs(carpeta, exist_ok=True)
        prueba = os.path.join(carpeta, f".test_{os.getpid()}")
        with open(prueba, "w", encoding="utf-8") as f:
            f.write("1")
        os.remove(prueba)
        return True
    except OSError:
        return False


def obtener_dir_sonidos() -> str:
    """Obtiene la ruta absoluta de assets/sounds. Si la carpeta del programa es de
    solo lectura (p. ej. Program Files), redirige la escritura a LocalAppData."""
    candidatos = []
    if getattr(sys, "frozen", False):
        meipass_sounds = os.path.join(getattr(sys, "_MEIPASS", ""), "assets", "sounds")
        if os.path.exists(meipass_sounds):
            candidatos.append(meipass_sounds)
        exe_sounds = os.path.join(os.path.dirname(sys.executable), "assets", "sounds")
        if os.path.exists(exe_sounds):
            candidatos.append(exe_sounds)
    source_sounds = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sounds")
    candidatos.append(source_sounds)

    for c in candidatos:
        if os.path.exists(c) and _es_directorio_escribible(c):
            return c

    user_sounds = os.path.join(
        os.environ.get("LOCALAPPDATA") or tempfile.gettempdir(), "MyBot", "assets", "sounds"
    )
    try:
        os.makedirs(user_sounds, exist_ok=True)
        return user_sounds
    except OSError:
        return source_sounds

SOUNDS_DIR = obtener_dir_sonidos()

# Bloqueo y registro de alias MCI activos para parada instantánea.
# Hay dos señales separadas: una alerta de donación no debe cancelar la voz que
# se está reproduciendo, ni al revés.
_mci_lock = threading.Lock()
_active_mci_aliases = set()
_abort_tts = threading.Event()
_abort_alertas = threading.Event()
# Limita los hilos MCI simultáneos: una ráfaga de regalos ya no crea decenas.
_alerta_sem = threading.BoundedSemaphore(2)


def _asegurar_directorio():
    s_dir = obtener_dir_sonidos()
    if not os.path.exists(s_dir):
        os.makedirs(s_dir, exist_ok=True)


def _crear_wav_senoidal(ruta_archivo, frecuencias, duracion=0.5, tasa_muestreo=44100, volumen=0.6):
    """
    Crea un archivo WAV puro de alta calidad con síntesis aditiva y envolvente suave.
    frecuencias: lista de tuplas (frecuencia_hz, peso) o lista de frecuencias.
    """
    _asegurar_directorio()
    num_muestras = int(tasa_muestreo * duracion)
    datos = bytearray()

    if isinstance(frecuencias[0], (int, float)):
        frecuencias = [(f, 1.0 / len(frecuencias)) for f in frecuencias]

    for i in range(num_muestras):
        t = float(i) / tasa_muestreo
        # Envolvente: ataque rápido de 15ms y decaimiento exponencial natural
        ataque = min(1.0, t / 0.015)
        decaimiento = math.exp(-3.5 * (t / duracion))
        envolvente = ataque * decaimiento

        muestra = 0.0
        for f, peso in frecuencias:
            muestra += peso * math.sin(2.0 * math.pi * f * t)

        val = int(muestra * envolvente * volumen * 32767.0)
        val = max(-32768, min(32767, val))
        datos.extend(struct.pack("<h", val))

    with wave.open(ruta_archivo, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(tasa_muestreo)
        wf.writeframes(datos)


def generar_sonidos_predeterminados():
    """Genera y cataloga los tonos predeterminados y sonidos virales de la comunidad."""
    s_dir = obtener_dir_sonidos()
    _asegurar_directorio()

    # Síntesis local de tonos clásicos si no existen
    tonos_sintetizados = {
        "campana.wav": ([(880, 0.6), (1760, 0.4)], 0.7),
        "monedas.wav": ([(987.77, 0.5), (1318.51, 0.5)], 0.45),
        "ding.wav": ([(1046.50, 0.7), (2093.00, 0.3)], 0.6),
    }

    for archivo, (freqs, dur) in tonos_sintetizados.items():
        ruta = os.path.join(s_dir, archivo)
        if not os.path.exists(ruta):
            try:
                _crear_wav_senoidal(ruta, freqs, duracion=dur, volumen=0.65)
            except Exception as e:
                print(f"[AudioAssets] Error creando {archivo}: {e}")

    # Catálogo ordenado de sonidos disponibles
    catalogo = {}

    sonidos_lista = [
        ("📣 Faaa! (Meme)", "faaa.mp3"),
        ("📣 Faaa! Largo / Épico", "faaa_alt.mp3"),
        ("🎙️ Auron - ¡¿Pero qué ha pasao?!", "auron_pero_que_ha_pasao.mp3"),
        ("🤬 Auron - ¡Cállese señora!", "auron_callese.mp3"),
        ("🛸 Auron - ¡Abduzcan!", "auron_abduzcan.mp3"),
        ("🥚 Auron - ¡Calvooooo!", "auron_calvo.mp3"),
        ("😨 Auron - ¡Tengo miedo!", "auron_tengo_miedo.mp3"),
        ("⏰ Auron - ¡Alarma!", "auron_alarma.mp3"),
        ("🔥 CR7 - ¡Siuuu!", "siuuu.mp3"),
        ("🗿 Bruh (Meme)", "bruh.mp3"),
        ("🌸 Anime Wow", "wow.mp3"),
        ("🔔 Campana (Suave)", "campana.wav"),
        ("💰 Monedas / Donación", "monedas.wav"),
        ("✨ Ding Brillante", "ding.wav"),
    ]

    carpetas_busqueda = [s_dir]
    if getattr(sys, "frozen", False):
        exe_s = os.path.join(os.path.dirname(sys.executable), "assets", "sounds")
        if exe_s not in carpetas_busqueda and os.path.exists(exe_s):
            carpetas_busqueda.append(exe_s)
    src_s = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sounds")
    if src_s not in carpetas_busqueda and os.path.exists(src_s):
        carpetas_busqueda.append(src_s)

    for etiqueta, nombre_arch in sonidos_lista:
        for carpeta in carpetas_busqueda:
            p = os.path.join(carpeta, nombre_arch)
            if os.path.exists(p):
                catalogo[etiqueta] = p
                break

    # Fallback si por algún motivo la carpeta de sonidos no tiene los archivos
    if not catalogo:
        catalogo = {
            "🔔 Campana (Suave)": os.path.join(s_dir, "campana.wav"),
            "💰 Monedas / Donación": os.path.join(s_dir, "monedas.wav"),
            "✨ Ding Brillante": os.path.join(s_dir, "ding.wav"),
        }

    return catalogo


def obtener_ruta_corta(ruta: str) -> str:
    """Convierte una ruta a formato corto 8.3 de Windows para total compatibilidad con MCI."""
    try:
        buffer = ctypes.create_unicode_buffer(500)
        ret = ctypes.windll.kernel32.GetShortPathNameW(ruta, buffer, 500)
        if ret > 0:
            return buffer.value
    except Exception:
        pass
    return ruta


def detener_todo_el_audio():
    """
    Detiene inmediatamente cualquier reproducción de audio activa en Windows:
    1. Detiene todos los alias MCI en reproducción y los cierra.
    2. Detiene cualquier sonido WAV emitido por winsound.
    3. Señaliza al reproductor para no continuar con audios en espera.
    """
    _abort_tts.set()
    _abort_alertas.set()

    # Detener winsound
    try:
        import winsound
        winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        pass

    # Detener MCI
    mci = ctypes.windll.winmm.mciSendStringW
    with _mci_lock:
        aliases_to_close = list(_active_mci_aliases)
        _active_mci_aliases.clear()

    for alias in aliases_to_close:
        try:
            mci(f"stop {alias}", None, 0, None)
            mci(f"close {alias}", None, 0, None)
        except Exception:
            pass



def reproducir_sonido_alerta_sincrono(ruta_archivo: str, volumen: int = 100):
    """
    Reproduce un sonido de alerta de forma síncrona (bloquea hasta que termine).
    Garantiza que la alerta suene completa antes de que comience el agradecimiento por voz.
    """
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return

    _abort_alertas.clear()
    ext = os.path.splitext(ruta_archivo)[1].lower()
    if ext == ".wav":
        try:
            import winsound
            winsound.PlaySound(ruta_archivo, winsound.SND_FILENAME)
            return
        except Exception as e:
            print(f"[AudioAssets] Error winsound alerta sincrona: {e}")

    try:
        _reproducir_mci(ruta_archivo, True, _abort_alertas, volumen=volumen)
    except Exception as e:
        print(f"[AudioAssets] Error MCI alerta sincrona: {e}")


def reproducir_sonido_alerta(ruta_archivo: str, volumen: int = 100):
    """
    Reproduce un sonido de alerta en segundo plano sin interrumpir la voz ni la UI.
    Soporta WAV nativamente mediante winsound y MP3 mediante MCI seguro.
    """
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return

    _abort_alertas.clear()
    ext = os.path.splitext(ruta_archivo)[1].lower()
    if ext == ".wav":
        try:
            import winsound
            winsound.PlaySound(ruta_archivo, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return
        except Exception as e:
            print(f"[AudioAssets] Error winsound: {e}")

    # Fallback para MP3 u otros formatos con MCI (esperar=True en hilo daemon para que suene completo)
    if not _alerta_sem.acquire(blocking=False):
        # Demasiadas alertas solapadas: se descarta esta para no crear hilos sin fin.
        return

    def _reproducir_alerta():
        try:
            _reproducir_mci(ruta_archivo, True, _abort_alertas, volumen=volumen)
        finally:
            _alerta_sem.release()

    threading.Thread(target=_reproducir_alerta, daemon=True).start()


def _reproducir_mci(ruta: str, esperar: bool = True, aborto: threading.Event = None, volumen: int = 100):
    """
    Reproduce un archivo de audio con MCI asegurando alias único, registro
    para detención inmediata y cierre garantizado.
    """
    if not os.path.exists(ruta):
        return

    aborto = aborto or _abort_tts
    alias = f"mci_{uuid.uuid4().hex[:8]}"
    ruta_segura = obtener_ruta_corta(ruta)
    mci = ctypes.windll.winmm.mciSendStringW

    with _mci_lock:
        _active_mci_aliases.add(alias)

    try:
        # Abrir el archivo con alias único
        cmd_open = f'open "{ruta_segura}" type mpegvideo alias {alias}'
        res_open = mci(cmd_open, None, 0, None)
        if res_open != 0:
            res_open = mci(f'open "{ruta_segura}" alias {alias}', None, 0, None)
        if res_open != 0:
            return

        if aborto.is_set():
            return

        if volumen is not None:
            vol_val = max(0, min(1000, int(volumen * 10)))
            mci(f"setaudio {alias} volume to {vol_val}", None, 0, None)

        cmd_play = f"play {alias}"
        mci(cmd_play, None, 0, None)

        if esperar:
            buf = ctypes.create_unicode_buffer(128)
            inicio = time.monotonic()
            while not aborto.is_set():
                mci(f"status {alias} mode", buf, 128, None)
                modo = buf.value.lower()
                if modo not in ("playing", "seeking", ""):
                    break
                # Una alerta/clip nunca dura minutos: si MCI no responde, el hilo
                # no debe quedarse vivo para siempre.
                if time.monotonic() - inicio > 120:
                    break
                time.sleep(0.04)
    except Exception as e:
        print(f"[AudioAssets] Error reproduciendo MCI: {e}")
    finally:
        with _mci_lock:
            _active_mci_aliases.discard(alias)
        try:
            mci(f"stop {alias}", None, 0, None)
            mci(f"close {alias}", None, 0, None)
        except Exception:
            pass


def reproducir_mp3_tts(ruta: str, volumen: int = 100):
    """
    Reproduce de forma segura un archivo generado por TTS (para el hilo de voz).
    Si se solicita detener el audio, finaliza de inmediato.
    """
    _abort_tts.clear()
    _reproducir_mci(ruta, esperar=True, aborto=_abort_tts, volumen=volumen)


def reproducir_wav_tts(ruta: str):
    """
    Reproduce un WAV generado por TTS de forma síncrona (bloquea hasta terminar),
    permitiendo la parada instantánea mediante winsound.SND_PURGE.
    """
    if not ruta or not os.path.exists(ruta):
        return

    _abort_tts.clear()
    try:
        import winsound

        winsound.PlaySound(ruta, winsound.SND_FILENAME)
        return
    except Exception as e:
        print(f"[AudioAssets] Error winsound (wav tts): {e}")

    _reproducir_mci(ruta, esperar=True, aborto=_abort_tts)
