# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller - Empaquetado de la aplicacion de escritorio de MyBot.

Genera un unico ejecutable a partir de mybot_app.py, que arranca el servidor
local (HTTP + WebSocket) y abre la interfaz con el WebView2 del sistema.

La interfaz (web/), los sonidos (assets/sounds) y los iconos NO se incrustan en
el ejecutable: installer.iss los copia junto a el. Asi se pueden actualizar sin
recompilar y los modelos de voz neuronales se descargan bajo demanda desde la
propia aplicacion, en lugar de viajar dentro del instalador.
"""
import os

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    "audio_assets",
    "tts_voces",
    "webview",
    "webview.platforms.edgechromium",
    "clr_loader",
    "pythonnet",
    "win32com",
    "win32com.client",
    "pythoncom",
    "pywintypes",
]

for pkg in ["TikTokLive", "TikTokLiveProto", "edge_tts", "pyttsx3", "piper",
            "onnxruntime", "numpy", "gtts", "webview"]:
    tmp_ret = collect_all(pkg)
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]

a = Analysis(
    ["mybot_app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Dependencias innecesarias y suites de pruebas
        "tkinter",
        "PIL",
        "PIL.ImageTk",
        "pytest",
        "unittest",
        "numpy.testing",
        "scipy",
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

icon_path = "assets/icono.ico" if os.path.exists("assets/icono.ico") else None
# Los metadatos de version reducen los falsos positivos de antivirus/SmartScreen.
version_path = "version_info.txt" if os.path.exists("version_info.txt") else None

# MYBOT_CONSOLE=1 genera una version con consola para diagnosticar errores de
# arranque (el ejecutable distribuible se compila sin consola).
con_consola = os.environ.get("MYBOT_CONSOLE") == "1"

# Se empaqueta en modo "onedir" (carpeta) y no "onefile" (un solo .exe): el modo
# onefile descomprime todo el contenido en una carpeta temporal en cada arranque,
# lo que anadia ~20 segundos al inicio. En onedir la aplicacion abre en segundos.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MyBot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=con_consola,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
    version=version_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MyBot",
)
