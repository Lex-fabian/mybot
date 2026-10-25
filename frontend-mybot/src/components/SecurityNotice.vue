<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { APP_VERSION, INSTALLER_SHA256 } from '../version'

const storageKey = `mybot-security-notice-${APP_VERSION}`
const visible = ref(true)

onMounted(() => {
  try {
    if (localStorage.getItem(storageKey) === 'hidden') {
      visible.value = false
    }
  } catch {
    /* almacenamiento no disponible */
  }
})

function dismiss() {
  visible.value = false
  try {
    localStorage.setItem(storageKey, 'hidden')
  } catch {
    /* almacenamiento no disponible */
  }
}
</script>

<template>
  <section v-if="visible" class="security-notice-section" aria-label="Aviso de seguridad de Windows">
    <div class="container">
      <div class="security-notice" role="note">
        <div class="notice-icon" aria-hidden="true">
          <i class="fa-solid fa-shield-halved"></i>
        </div>

        <div class="notice-content">
          <p class="notice-kicker">Aviso de seguridad · Windows 10 / 11</p>
          <h2 class="notice-title">Windows puede mostrar «Software desconocido»</h2>

          <p class="notice-text">
            Con la última actualización, Windows SmartScreen puede mostrar una alerta de
            <strong>«Software desconocido»</strong>. Es normal en aplicaciones de desarrolladores
            independientes sin firma digital: Windows no reconoce la nueva versión de inmediato.
          </p>

          <p class="notice-text">
            MyBot sigue siendo seguro: no modifica archivos del sistema, no instala servicios y solo
            procesa los comentarios y regalos del directo. Ya enviamos el archivo a Microsoft para su
            revisión.
          </p>

          <div class="notice-actions">
            <details class="notice-details">
              <summary>Ver instrucciones</summary>
              <ol>
                <li>
                  Si aparece <strong>«Windows protegió tu PC»</strong>, pulsa
                  <strong>Más información</strong> y luego <strong>Ejecutar de todas formas</strong>.
                </li>
                <li>
                  Si tu PC tiene <strong>Smart App Control</strong> activado y no aparece esa opción,
                  no desactives la seguridad: Smart App Control bloquea aplicaciones sin firma.
                  Espera la revisión de Microsoft o usa una versión firmada.
                </li>
              </ol>
              <p class="notice-hash">
                SHA-256 del instalador:
                <code>{{ INSTALLER_SHA256 }}</code>
              </p>
            </details>

            <button type="button" class="notice-dismiss" @click="dismiss">
              Ocultar aviso
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.security-notice-section {
  padding: 18px 0 0;
}

.security-notice {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 18px 20px;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-left: 4px solid #D97706;
  border-radius: 14px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
}

.notice-icon {
  flex: 0 0 auto;
  width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #FFF7ED;
  color: #B45309;
  font-size: 17px;
}

.notice-content {
  min-width: 0;
}

.notice-kicker {
  margin: 0 0 3px;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #B45309;
}

.notice-title {
  margin: 0 0 6px;
  font-size: 16px;
  line-height: 1.35;
  font-weight: 700;
  color: #0F172A;
}

.notice-text {
  margin: 0 0 6px;
  font-size: 13.5px;
  line-height: 1.55;
  color: #475569;
}

.notice-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.notice-details {
  font-size: 13px;
  color: #475569;
}

.notice-details summary {
  cursor: pointer;
  font-weight: 600;
  color: #007AFF;
  list-style: none;
}

.notice-details summary::-webkit-details-marker {
  display: none;
}

.notice-details summary::after {
  content: " +";
  font-weight: 700;
}

.notice-details[open] summary::after {
  content: " −";
}

.notice-details ol {
  margin: 8px 0 8px 18px;
  padding: 0;
  line-height: 1.55;
}

.notice-details li + li {
  margin-top: 4px;
}

.notice-hash {
  margin: 8px 0 0;
  font-size: 10.5px;
  line-height: 1.5;
  color: #64748B;
  word-break: break-all;
}

.notice-hash code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 10px;
  color: #475569;
}

.notice-dismiss {
  border: 1px solid #E2E8F0;
  background: #FFFFFF;
  color: #64748B;
  border-radius: 9999px;
  padding: 5px 11px;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
}

.notice-dismiss:hover {
  background: #F8FAFC;
  color: #334155;
}

@media (max-width: 600px) {
  .security-notice {
    padding: 16px;
    gap: 12px;
  }

  .notice-icon {
    width: 34px;
    height: 34px;
    font-size: 15px;
  }

  .notice-title {
    font-size: 15px;
  }
}
</style>
