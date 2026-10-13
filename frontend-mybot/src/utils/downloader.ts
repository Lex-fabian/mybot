import { ref } from 'vue'

export interface DownloadProgress {
  percent: number
  downloadedMb: string
  totalMb: string
}

export const isDownloading = ref(false)
export const downloadPercent = ref(0)
export const downloadDetail = ref('')
export const isCompleted = ref(false)

const ESTIMATED_SIZE_BYTES = 142 * 1024 * 1024 // ~140 MB

/**
 * Descarga el instalador mediante Blob y ReadableStream reportando el porcentaje en tiempo real.
 * Si se pulsa en el App Bar o en el Hero, ambos botones reflejan el avance sincronizado.
 */
export async function iniciarDescargaGlobal(
  onProgress?: (p: DownloadProgress) => void
): Promise<void> {
  if (isDownloading.value) return
  isDownloading.value = true
  downloadPercent.value = 0
  downloadDetail.value = 'Conectando con el servidor...'
  isCompleted.value = false

  const fileUrl = '/downloads/MyBot_v1.2_Instalador.exe'
  const fileName = 'MyBot_v1.2_Instalador.exe'

  try {
    const res = await fetch(fileUrl)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    const contentLength = res.headers.get('content-length')
    let totalBytes = contentLength ? parseInt(contentLength, 10) : 0
    if (isNaN(totalBytes) || totalBytes <= 0) {
      totalBytes = ESTIMATED_SIZE_BYTES
    }
    const totalMb = (totalBytes / (1024 * 1024)).toFixed(1)

    let blob: Blob

    if (res.body) {
      const reader = res.body.getReader()
      const chunks: Uint8Array[] = []
      let receivedBytes = 0

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        if (value) {
          chunks.push(value)
          receivedBytes += value.length
          const pct = Math.min(99, Math.round((receivedBytes / totalBytes) * 100))
          downloadPercent.value = pct
          const mbNow = (receivedBytes / (1024 * 1024)).toFixed(1)
          downloadDetail.value = `${pct}% • ${mbNow} MB de ${totalMb} MB`
          if (onProgress) {
            onProgress({ percent: pct, downloadedMb: mbNow, totalMb })
          }
        }
      }
      blob = new Blob(chunks as BlobPart[], { type: 'application/octet-stream' })
      downloadPercent.value = 100
      downloadDetail.value = `100% • ${totalMb} MB de ${totalMb} MB`
      if (onProgress) {
        onProgress({ percent: 100, downloadedMb: totalMb, totalMb })
      }
    } else {
      blob = await res.blob()
      downloadPercent.value = 100
      if (onProgress) {
        onProgress({ percent: 100, downloadedMb: totalMb, totalMb })
      }
    }

    // Disparar la descarga nativa mediante Blob URL
    const blobUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = fileName
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()

    isCompleted.value = true
    downloadDetail.value = '✓ ¡Descarga lista! Guardando en tu equipo...'

    setTimeout(() => {
      window.URL.revokeObjectURL(blobUrl)
      if (link.parentNode) {
        link.parentNode.removeChild(link)
      }
      isDownloading.value = false
      isCompleted.value = false
      downloadPercent.value = 0
    }, 3500)
  } catch (err) {
    console.warn('Error en descarga Blob, usando enlace directo de respaldo:', err)
    downloadPercent.value = 100
    isCompleted.value = true
    const fallbackLink = document.createElement('a')
    fallbackLink.href = fileUrl
    fallbackLink.download = fileName
    fallbackLink.style.display = 'none'
    document.body.appendChild(fallbackLink)
    fallbackLink.click()
    setTimeout(() => {
      if (fallbackLink.parentNode) {
        fallbackLink.parentNode.removeChild(fallbackLink)
      }
      isDownloading.value = false
      isCompleted.value = false
      downloadPercent.value = 0
    }, 2500)
  }
}

export const descargarInstaladorBlob = iniciarDescargaGlobal
