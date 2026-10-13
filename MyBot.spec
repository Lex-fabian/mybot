# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    'audio_assets', 'tts_voces', 'PIL', 'PIL.Image', 'PIL.ImageTk',
    'win32com', 'win32com.client', 'pythoncom', 'pywintypes',
]

for pkg in ['TikTokLive', 'TikTokLiveProto', 'edge_tts', 'pyttsx3', 'PIL',
            'piper', 'onnxruntime', 'numpy', 'gtts']:
    tmp_ret = collect_all(pkg)
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]

# Assets: incluimos todo EXCEPTO los modelos de voz pesados (assets/voices),
# que se instalan junto al ejecutable (installer.iss copia assets\* completo).
if os.path.exists('assets'):
    for raiz, _dirs, archivos in os.walk('assets'):
        if 'voices' in raiz.replace('\\', '/').split('/'):
            continue
        for archivo in archivos:
            datos_origen = os.path.join(raiz, archivo)
            datos_destino = os.path.relpath(raiz, '.')
            datas.append((datos_origen, datos_destino))

a = Analysis(
    ['tiktok_live_gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

icon_path = 'assets/icono.ico' if os.path.exists('assets/icono.ico') else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MyBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
