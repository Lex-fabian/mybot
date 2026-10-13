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
export const APP_VERSION = '1.3.0'
export const APP_VERSION_NAME = 'v1.3'

/** Nombre del archivo publicado en frontend-mybot/public/downloads. */
export const INSTALLER_FILE = `MyBot_${APP_VERSION_NAME}_Instalador.exe`
export const INSTALLER_URL = `/downloads/${INSTALLER_FILE}`

/** Tamano aproximado en MB, usado solo si el servidor no envia Content-Length. */
export const INSTALLER_SIZE_MB = 69.1
