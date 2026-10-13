/**
 * ============================================================================
 *  MyBot — Puente seguro entre la interfaz (web/) y el proceso principal
 * ============================================================================
 *  Expone una API mínima en `window.electronAPI`. Sin este archivo, el
 *  frontend no encontraba `window.electronAPI` y los enlaces externos
 *  terminaban abriéndose dentro de la propia aplicación.
 * ============================================================================
 */

const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  /** Abre una URL http(s) en el navegador predeterminado del sistema. */
  openExternal: (url) => ipcRenderer.invoke("open-external", String(url)),
});
