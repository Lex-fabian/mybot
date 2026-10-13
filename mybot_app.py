"""
=============================================================================
 MyBot - Aplicacion de escritorio (Windows)
=============================================================================
 Un unico ejecutable que:

   1. Arranca el servidor local HTTP + WebSocket (mybot_backend).
   2. Abre una ventana nativa con el motor WebView2 del sistema (Edge/Chromium
      ya presente en Windows 10/11) y muestra la interfaz de 'web/'.

 No requiere Electron ni Node.js: la interfaz se renderiza con el WebView2
 que Windows ya incluye, de modo que no se duplica el motor de navegador ni
 se anaden ~200 MB de runtime.
=============================================================================
"""

import json
import os
import sys
import tempfile
import threading
import time
import webbrowser

import webview

import audio_assets
import mybot_backend as backend

APP_NOMBRE = "MyBot"
URL_LOCAL = f"http://127.0.0.1:{backend.PORT}"
ANCHO, ALTO = 880, 940
ANCHO_MIN, ALTO_MIN = 760, 820


def _preparar_salidas_de_texto():
    """Redirige stdout/stderr a un archivo de registro.

    El ejecutable se compila sin consola, por lo que sys.stdout y sys.stderr son
    None y cualquier print() del programa fallaria con AttributeError. Se envian a
    'mybot.log' para conservar los diagnosticos.
    """
    if sys.stdout is not None and sys.stderr is not None:
        return

    destino = None
    for carpeta in (backend.BASE_DIR, tempfile.gettempdir()):
        try:
            ruta = os.path.join(carpeta, "mybot.log")
            destino = open(ruta, "a", encoding="utf-8", errors="replace")
            break
        except OSError:
            continue

    if destino is None:
        destino = open(os.devnull, "w", encoding="utf-8")

    if sys.stdout is None:
        sys.stdout = destino
    if sys.stderr is None:
        sys.stderr = destino


_preparar_salidas_de_texto()


def _configurar_proceso_windows():
    """DPI awareness y AppUserModelID para un icono propio en la barra de tareas."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("mybot.tiktoklive.tts.desktop")
    except Exception:
        pass
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


class ApiPuente:
    """API expuesta a JavaScript como window.pywebview.api.*"""

    def open_external(self, url: str) -> bool:
        """Abre un enlace http(s) en el navegador predeterminado del sistema."""
        destino = str(url or "").strip()
        if destino.startswith(("http://", "https://")):
            webbrowser.open(destino)
            return True
        return False

    def version_app(self) -> str:
        return backend.APP_VERSION

    def ruta_descargas(self) -> str:
        return os.path.join(backend.BASE_DIR, "assets", "descargas_audio")


def _esperar_servidor(timeout: float = 30.0) -> bool:
    limite = time.time() + timeout
    while time.time() < limite:
        if backend.servidor_activo():
            return True
        time.sleep(0.15)
    return False


def _ruta_icono() -> str:
    icono = os.path.join(backend.BASE_DIR, "assets", "icono.ico")
    return icono if os.path.exists(icono) else ""


def _autoprueba(ventana) -> None:
    """--selftest: comprueba que la interfaz carga y cierra.

    El ejecutable se compila sin consola, así que el resultado se guarda en
    'mybot_selftest.json' junto al programa (además de imprimirse si hay consola).
    """
    time.sleep(6)
    resultado = {}
    try:
        resultado["titulo"] = ventana.evaluate_js("document.title")
        resultado["motor"] = ventana.evaluate_js(
            "document.getElementById('selectEngine')"
            " ? document.getElementById('selectEngine').value : 'AUSENTE'"
        )
        resultado["opciones_voz"] = ventana.evaluate_js(
            "document.getElementById('selectVoice')"
            " ? document.getElementById('selectVoice').options.length : -1"
        )
        resultado["websocket"] = ventana.evaluate_js(
            "document.getElementById('connStatusText')"
            " ? document.getElementById('connStatusText').textContent : 'AUSENTE'"
        )
        resultado["puente_js"] = ventana.evaluate_js(
            "(window.pywebview && window.pywebview.api) ? 'disponible' : 'AUSENTE'"
        )
    except Exception as exc:  # noqa: BLE001
        resultado["error"] = str(exc)
    finally:
        try:
            with open(os.path.join(backend.BASE_DIR, "mybot_selftest.json"), "w", encoding="utf-8") as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
        except OSError:
            pass
        print("AUTOTEST " + json.dumps(resultado, ensure_ascii=False))
        sys.stdout.flush()
        ventana.destroy()


def _carpeta_datos_app() -> str:
    """Carpeta de datos del usuario (perfil de WebView2, registros, etc.)."""
    base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    carpeta = os.path.join(base, "MyBot")
    try:
        os.makedirs(carpeta, exist_ok=True)
        return carpeta
    except OSError:
        return tempfile.gettempdir()


def _iniciar_ventana(ventana, funcion=None):
    """Arranca el bucle de la interfaz con el WebView2 del sistema.

    Se usa un perfil persistente (private_mode=False): crear un perfil temporal
    en cada arranque obligaba a WebView2 a inicializarse desde cero y anadia
    varios segundos a la apertura de la ventana.
    """
    parametros = {
        "gui": "edgechromium",
        "icon": _ruta_icono(),
        "private_mode": False,
        "storage_path": _carpeta_datos_app(),
    }
    if funcion is not None:
        webview.start(funcion, **parametros)
    else:
        webview.start(**parametros)


def main() -> int:
    _configurar_proceso_windows()

    # Si ya hay una instancia escuchando (por ejemplo la app abierta dos veces),
    # se reutiliza su servidor en lugar de fallar al ocupar el puerto.
    if _esperar_servidor(timeout=0.6):
        print(f"[MyBot] Reutilizando la instancia activa en {URL_LOCAL}")
    else:
        threading.Thread(target=backend.iniciar_servidor, daemon=True).start()
        if not _esperar_servidor():
            webview.create_window(
                APP_NOMBRE,
                html=(
                    "<body style='font-family:Segoe UI;padding:32px'>"
                    "<h2>No se pudo iniciar MyBot</h2>"
                    "<p>El servidor interno no respondio en el puerto "
                    f"{backend.PORT}.</p></body>"
                ),
                width=520,
                height=280,
            )
            webview.start()
            return 1

    ventana = webview.create_window(
        f"{APP_NOMBRE} - TikTok Live TTS & Donaciones Pro",
        URL_LOCAL,
        width=ANCHO,
        height=ALTO,
        min_size=(ANCHO_MIN, ALTO_MIN),
        js_api=ApiPuente(),
        background_color="#F2F4F8",
        text_select=False,
    )

    if "--selftest" in sys.argv:
        _iniciar_ventana(ventana, lambda: _autoprueba(ventana))
    else:
        _iniciar_ventana(ventana)

    # Cierre ordenado: corta el audio en curso y detiene el bucle del servidor.
    audio_assets.detener_todo_el_audio()
    backend.detener_servidor()
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:  # noqa: BLE001
        pass
    # WebView2 y pythonnet mantienen hilos nativos propios que impiden el cierre
    # normal del interprete: tras liberar audio y servidor se fuerza la salida
    # para no dejar procesos MyBot en segundo plano ocupando el puerto local.
    os._exit(0)


if __name__ == "__main__":
    sys.exit(main())
