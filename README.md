# MyBot v1.3 — Lector de Comentarios y Donaciones TikTok Live

**MyBot v1.0** es una aplicación de escritorio nativa independiente para Windows. Pantalla de inicio de carga y lectura en tiempo real de directos de **TikTok Live**.

Cuenta con soporte para voces neuronales **offline (Piper)** que no dependen de Internet, además de **Edge TTS** (nube, opcional) y las voces del sistema de Windows (**SAPI5 / Loquendo**), presets de modulación de voz, parada instantánea de audio y filtros inteligentes anti-spam.

---

##  Características Principales

- **Aplicación de Escritorio Nativa (WebView2 + Backend Python)**:
  - Un único ejecutable `.exe` que arranca un servidor local (HTTP + WebSocket) y
    abre la interfaz en una **ventana nativa** con el motor **WebView2** de Windows.
  - No requiere Node.js ni Electron: usa el motor Chromium que Windows 10/11 ya
    incluye, por lo que se evita duplicar un navegador completo (~200 MB) y la
    aplicación se mantiene ligera.
  - Ventana de escritorio independiente, sin marcos ni barras de navegador.
- ** Motores de Voz Híbridos**:
  - **Piper (Recomendado, 100% offline)**: Voces neuronales sin Internet y sin el error 403 de Microsoft (Daniela de Argentina, voces de España). Es el motor por defecto.
  - **Edge TTS (Opcional, requiere Internet)**: Voces neurales de la nube de Microsoft en español de múltiples países (Argentina, España, México, Colombia, Chile, Perú, etc.).
  - **SAPI5 (Windows)**: Compatible con voces nativas de Microsoft y voces clásicas instaladas en el sistema (Jorge / Loquendo).
- **⬇ Descarga de Voces desde la App**:
  - Los modelos neuronales **no se incluyen en el instalador** (que pasa de ~340 MB a ~87 MB).
  - En *Voz & Presets* la app indica qué voces **faltan** y las descarga con barra de progreso, velocidad y tamaño antes de empezar.
  - Cada voz se descarga **una sola vez** y después funciona sin Internet.
- ** Presets de Bot Instantáneos**:
  - ` Natural / Neutro`
  - ` MyBot Androide`
  - ` Ardilla Divertida`
  - ` Locutor Profesional`
  - ` Streamer Rápido`
  - ` Gamer Sintético`
  - ` Loquendo Clásico`
- ** Soporte Completo para Donaciones y Regalos**:
  - Detección de combos/rachas (evita spam al recibir ráfagas de rosas).
  - Filtro por mínimo de diamantes para alertar.
  - Efectos de sonido de alerta generados nativamente (Campana suave, Monedas, Ding) o tonos personalizados.
  - Métrica en tiempo real de **comentarios**, **regalos** y **diamantes acumulados**.
- ** Filtros Anti-Spam Inteligentes**:
  - Enmascaramiento automático de URLs y enlaces sospechosos para evitar lecturas de spam o phishing.
  - Compactación de repeticiones masivas de emojis y caracteres.
  - Lista de palabras prohibidas/baneadas personalizables en vivo.
- ** Silenciamiento y Parada Instantánea**:
  - Botón de parada de audio de emergencia que corta de inmediato cualquier sonido en reproducción y limpia la cola de voz.
- ** Reconocimiento Inteligente de URLs**:
  - Acepta tanto el usuario (`@usuario` o `usuario`) como el link completo de la transmisión (`https://www.tiktok.com/@usuario/live`).
- ** Descarga de Audio Integrada**:
  - Permite probar y guardar directamente los clips de voz generados en formato `.mp3`.

---

##  Requisitos e Instalación

### Requisitos:
- **Windows 10 / 11**.
- **Python 3.10 o superior** (TikTokLive 7.x lo requiere). Marca **"Add python.exe to PATH"** al instalarlo.
- **Microsoft Edge WebView2 Runtime**: viene preinstalado en Windows 10 y 11. Si
  faltara, el instalador avisa al terminar y puede descargarse gratis desde
  <https://developer.microsoft.com/microsoft-edge/webview2/>.
- Conexión a Internet.

### Instalación (desde el código fuente):
```bash
# Dependencias de Python (incluye la interfaz pywebview)
pip install -r requirements.txt
```

> **Nota:** `run_mybot.bat` detecta Python y, si faltan dependencias, las instala
> automáticamente en la primera ejecución. Ya no se necesita Node.js.

###  Voces neuronales: descárgalas desde la app

El instalador **no incluye** los modelos de voz (son ~270 MB). Al abrir la app por
primera vez, ve a **Voz & Presets → Voz Principal**: la app marca las voces con la
etiqueta *«sin descargar»* y muestra un botón **Descargar voz** con el tamaño que
ocupa antes de empezar. Al terminar, la voz queda disponible **sin Internet**.

| Voz | País | Peso |
|-----|------|------|
| Daniela (Mujer) | 🇦🇷 Argentina | ~109 MB |
| Mateo (Hombre) | 🇦🇷 Argentina | *(se obtiene modulando a Daniela)* |
| Carlfm (Hombre) | 🇪🇸 España | ~27 MB |
| Davefx (Hombre) | 🇪🇸 España | ~60 MB |
| Sharvard (Mujer) | 🇪🇸 España | ~73 MB |
| MLS 10246 / MLS 9972 | 🇪🇸 España | ~60 MB |
| Ald | 🇲🇽 México | ~20-60 MB |
| Claude | 🇲🇽 México | ~60 MB |

Mientras no haya ninguna voz descargada, MyBot sigue leyendo con los motores de
respaldo (Edge TTS, Google o la voz de Windows) y te avisa en el chat.

---

## 🩺 Solución de Problemas

- **El bot no se oye nada al principio** → Si eliges el motor **Piper** y aún no
  has descargado la voz, ve a *Voz & Presets → Voz Principal*: las voces sin
  descargar aparecen marcadas como *«sin descargar»* y verás el botón
  **⬇️ Descargar voz**. Mientras no la descargues, MyBot lee con una voz de
  respaldo y te lo avisa en el chat.
- **"Voz: Error" y el bot no se escucha** → Si usas **Edge TTS**, el servicio de
  voces de Microsoft puede rechazar la conexión con un error **403** (bloqueo de
  Microsoft, sin conexión a Internet o restricción de red). MyBot detecta el fallo
  y **cambia automáticamente de motor** (Piper → gTTS → voz local de Windows) para
  que el bot siga leyendo los comentarios. Lo más simple es dejar el motor
  **Piper (Neuronal Offline)** en la pestaña *Voz & Presets*: no usa Internet y
  nunca da error 403.
- **El bot habla pero no se oye nada** → Comprueba el **dispositivo de
  reproducción predeterminado** de Windows (icono del altavoz en la barra de
  tareas). Si está seleccionado un dispositivo virtual (por ejemplo
  *Steam Streaming Speakers*), cambia a tus altavoces reales y sube el volumen.
- **No aparece nada al elegir una voz Edge concreta** → Algunas voces del
  catálogo pueden no estar disponibles en el servicio; prueba con otra voz
  (por ejemplo, `es-AR-ElenaNeural` o `es-ES-AlvaroNeural`).
- **El bot no conecta con el directo** → Verifica que el usuario esté
  transmitiendo en directo en ese momento y que el nombre o enlace sea correcto.
- **La ventana no se abre o aparece en blanco** → MyBot necesita el componente
  **Microsoft Edge WebView2 Runtime** (incluido de serie en Windows 10 y 11). Si
  falta, descárgalo gratis en
  <https://developer.microsoft.com/microsoft-edge/webview2/>. El instalador
  comprueba este requisito y avisa si no está presente.
- **Python no encontrado** → Reinstálalo marcando la opción para añadirlo al
  **PATH**, o reinicia el equipo para refrescar las variables de entorno. Solo es
  necesario si ejecutas MyBot desde el código fuente; el instalador ya incluye
  su propio intérprete.

---

## 🎙️ Motores de Voz y el error 403 de Edge

| Motor | Calidad | ¿Necesita Internet? | Notas |
|-------|---------|---------------------|-------|
| **Piper (offline)** ⭐ **Recomendado** | ⭐⭐⭐⭐ Neuronal | **No** | **Daniela (mujer argentina)**, funciona siempre |
| **Edge TTS** | ⭐⭐⭐⭐⭐ Neuronal | Sí | Elena (mujer argentina), Tomás, etc. Puede dar error **403** |
| **SAPI5 (Windows)** | ⭐⭐⭐ Clásica | No | Voces del sistema (Helena, Zira) |
| **gTTS (Google)** | ⭐⭐⭐ Clásica | Sí | Respaldo automático si el resto falla |

**¿Por qué falla Edge TTS con error 403?**
El *catálogo* de voces de Microsoft responde correctamente (HTTPS), pero el
servicio de **síntesis por WebSocket** rechaza la conexión con **403**. No es un
problema del equipo (el reloj, el proxy, el DNS y el TLS son correctos): es un
**bloqueo del propio servicio de Microsoft** (por IP/red o por cambios temporales
del servicio). Por eso MyBot aplica esta cadena automática:

```
Piper (Daniela - Argentina, OFFLINE) ──falla──► Edge TTS (nube Microsoft)
                                                  └──falla──► gTTS (Google) ──falla──► SAPI5 (Windows)
```

Así **siempre** se lee con una voz femenina argentina, aunque Edge esté bloqueado
o no haya Internet. Puedes forzar el motor en **Voz & Presets → Motor de Síntesis**.

---

## 🔒 Aviso "Aplicación no confiable" al descargar

Windows (SmartScreen) muestra *"Windows protegió su PC"* y los navegadores avisan
al descargar cualquier `.exe` **que no esté firmado digitalmente**.

- Lo único que elimina ese aviso de raíz es **firmar el ejecutable con un
  certificado de firma de código** (OV o, preferiblemente, **EV**) de una autoridad
  de confianza (DigiCert, Sectigo, GlobalSign…).
- MyBot ya incluye el pipeline listo para ello:

```bat
REM Compila, firma y genera checksums (requiere signtool.exe del Windows SDK)
tools\build_release.bat -PfxPath .\mi_certificado.pfx -PfxPassword "clave"

REM O con un certificado EV instalado en el almacén de Windows:
tools\build_release.bat -CertThumbprint "AB12CD34..."
```

- Mientras no haya certificado, el script genera **checksums SHA-256**
  (`tools\checksums.json`) y el sitio publica el hash en `version.json` para que
  el usuario pueda verificar la descarga.

---

## 🚀 Despliegue en Firebase Hosting

```bat
REM Compila y despliega el sitio en https://mybot-79861.web.app
tools\deploy_firebase.bat
```

La primera vez pedirá iniciar sesión con tu cuenta de Google.

---

## 📦 Cómo publicar una versión nueva (para que la reciban los usuarios)

La app ya instalada comprueba **`https://mybot-79861.web.app/version.json`** al
arrancar. Si el campo `version` es **mayor** que el de la app, muestra el aviso
"Nueva versión disponible" con el botón de descarga. Para publicar una versión:

1. **Sube la versión en el código** (debe coincidir en todos los sitios):
   - `mybot_backend.py` → `APP_VERSION`
   - `web/app.js` → `VERSION_ACTUAL`
   - `installer.iss` → `MyAppVersion` y `OutputBaseFilename`
   - `frontend-mybot/public/version.json` → `version` y `version_name`
   - `frontend-mybot/src/version.ts` → `APP_VERSION`, `APP_VERSION_NAME` y
     `INSTALLER_SIZE_MB` (la web toma de aquí la versión del pie, la barra de
     navegación, la portada y el nombre del instalador, así que no se
     desincronizan entre sí)
   - `frontend-mybot/index.html` → `<title>` y meta description (son HTML
     estático, no pueden leer el archivo anterior)
2. **Compila el ejecutable y el instalador** (requiere PyInstaller e Inno Setup):
   ```bat
   tools\build_release.bat
   ```
3. **Publica los binarios** ejecutando `tools\publish_downloads.bat`, que copia el
   instalador más reciente a `frontend-mybot\public\downloads\`.
   > Esa carpeta es la **única** copia en disco. La build de Vite la replica en
   > `dist\downloads` solo para el despliegue, y `deploy_firebase.bat` la borra al
   > terminar para no duplicar ~70 MB.
4. **Actualiza `frontend-mybot\public\version.json`** con la nueva `version`,
   `download_url`, `sha256` y `size_bytes` (el script genera `tools\checksums.json`).
   > Desde la 1.3 la app **verifica el SHA-256** del instalador antes de ofrecer la
   > instalación: si no coincide con `version.json`, la descarga se descarta.
5. **Despliega:** `tools\deploy_firebase.bat`

> ⚠️ **Importante:** sube la versión en `version.json` **solo después** de haber
> subido el instalador nuevo. Si no, los usuarios verían un aviso de actualización
> que descargaría el archivo antiguo.

### Voz neuronal offline (Piper)

Los modelos se guardan en `assets/voices/` y se descargan **desde la propia app**
(Voz & Presets → Descargar voz) desde el repositorio oficial
[`rhasspy/piper-voices`](https://huggingface.co/rhasspy/piper-voices). **No** se
empaquetan ni en el EXE ni en el instalador: `installer.iss` copia `assets\*` pero
**excluye** `assets\voices\*`, por lo que el instalador baja a ~87 MB.

Para desarrollo puedes poner un `.onnx` + su `.onnx.json` a mano en `assets/voices/`:
la app los detecta como voz personalizada aunque no estén en el catálogo.

---

## Cómo Iniciar MyBot

### Opción 1: Versión instalada (Recomendado)
Ejecuta el instalador `MyBot_v1.3_Instalador.exe` y abre **MyBot** desde el menú
Inicio o el acceso directo del escritorio. No requiere Python ni Node.js: todo
va empaquetado en el ejecutable.

### Opción 2: Desde el código fuente
```bat
run_mybot.bat
```

### Opción 3: Directamente con Python
```bash
python mybot_app.py              REM Abre la aplicación de escritorio
python mybot_app.py --selftest   REM Autoprueba: abre, verifica la interfaz y cierra
python mybot_backend.py          REM Solo el servidor (http://127.0.0.1:58421)
```

---

## Estructura del Proyecto

```
MyBot/
├── assets/
│   ├── descargas_audio/   # Clips de voz exportados (se crea al exportar)
│   ├── icono.ico          # Icono nativo de Windows
│   ├── icono.png          # Icono en alta resolución
│   ├── sounds/            # Tonos de alerta y memes de donación (.wav / .mp3)
│   └── voices/            # Modelos Piper descargados desde la app (.onnx)
├── web/                   # Interfaz de la aplicación (estilo iOS, Vanilla CSS)
│   ├── index.html         # Vista principal y pantalla de carga
│   ├── app.css            # Sistema de diseño iOS blanco y celeste
│   └── app.js             # Lógica cliente y WebSockets
├── frontend-mybot/        # Landing page (Vue + Vite) que se publica en Firebase
│   └── public/downloads/  # Única copia local de los instaladores publicados
├── tools/                 # Scripts de compilación, firma y despliegue
├── audio_assets.py        # Gestor de audio y parada instantánea
├── config.json            # Configuración persistente del usuario
├── mybot_app.py           # Punto de entrada: servidor + ventana WebView2
├── mybot_backend.py       # Servidor HTTP + WebSockets + TikTokLive + TTS
├── tts_voces.py           # Catálogo y descarga de voces neuronales
├── MyBot.spec             # Receta de PyInstaller (genera la carpeta dist\MyBot)
├── installer.iss          # Receta de Inno Setup (genera el instalador)
├── requirements.txt       # Dependencias de Python
├── run_mybot.bat          # Lanzador desde el código fuente
└── README.md              # Documentación
```

---
*MyBot — Potencia tus transmisiones de TikTok Live con la mejor interacción de voz y una experiencia de escritorio de nivel comercial.*
