/**
 * Version de MyBot mostrada en el sitio. Fuente unica de verdad.
 *
 * Antes estaba escrita a mano en el pie, la barra de navegacion, la portada, el
 * titulo de la pagina y el descargador, y se habian quedado en versiones
 * distintas (v1.0, v1.1 y v1.2). Al publicar una version nueva solo hay que
 * cambiar los valores de este archivo.
 *
 * Mantener sincronizado con:
 *   - mybot_backend.py               -> APP_VERSION
 *   - web/app.js                     -> VERSION_ACTUAL
 *   - installer.iss                  -> MyAppVersion
 *   - frontend-mybot/public/version.json
 *   - frontend-mybot/index.html      -> <title> y meta description
 */
export const APP_VERSION = '1.3.3'
export const APP_VERSION_NAME = 'v1.3.3'

/** SHA-256 y tamano exactos del instalador publicado en Storage. */
export const INSTALLER_SHA256 = '20B5DDCFBA8996272E59C3D019C17014018AB37D40A729ECA01A714B60073342'
export const INSTALLER_SIZE_BYTES = 36614120

/**
 * Los instaladores se publican en Cloud Storage for Firebase y no en Hosting.
 * Motivo: con 69 MB por archivo, servirlos desde Hosting consume la cuota de
 * transferencia del sitio entero (10 GB/mes), de modo que un pico de descargas
 * afectaria a la propia pagina. En Storage la cuota es independiente y el
 * binario deja de viajar en cada compilacion y despliegue del sitio.
 *
 * El bucket tiene lectura publica solo en la carpeta 'instaladores'
 * (ver frontend-mybot/storage.rules).
 */
export const STORAGE_BUCKET = 'mybot-79861.firebasestorage.app'
export const INSTALLER_FOLDER = 'instaladores'

/** Nombre del archivo publicado en el bucket. */
export const INSTALLER_FILE = `MyBot_${APP_VERSION_NAME}_Instalador.exe`
export const INSTALLER_URL = `https://storage.googleapis.com/${STORAGE_BUCKET}/${INSTALLER_FOLDER}/${INSTALLER_FILE}`

/** Tamano aproximado en MB, usado solo si el servidor no envia Content-Length. */
export const INSTALLER_SIZE_MB = 34.9
