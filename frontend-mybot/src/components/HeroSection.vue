<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import {
  isDownloading as descargando,
  downloadPercent as progreso,
  downloadDetail as detalleDescarga,
  isCompleted as completado,
  iniciarDescargaGlobal as iniciarDescarga
} from '../utils/downloader'
import { APP_VERSION_NAME } from '../version'
import LogoParticleCanvas from './LogoParticleCanvas.vue'

defineEmits<{
  (e: 'open-binance'): void
}>()

function handleDescarga() {
  iniciarDescarga()
}

// ============================================================================
// SIMULACIÓN INTERACTIVA Y ANIMADA DE LA INTERFAZ LIMPIA DE MYBOT
// ============================================================================
type DemoTab = 'tabChat' | 'tabVoice' | 'tabDonations' | 'tabCommunity' | 'tabFilters'

interface ChatItem {
  id: number
  type: 'system' | 'user' | 'welcome' | 'donation'
  user?: string
  text?: string
  gift?: string
  count?: number
  diamonds?: number
  speaking?: boolean
}

const activeTab = ref<DemoTab>('tabChat')
const typedUser = ref('')
const isConnected = ref(false)
const isConnecting = ref(false)
const btnPulse = ref(false)
const chatItems = ref<ChatItem[]>([
  { id: 1, type: 'system', text: 'Conéctate y empieza a interactuar' }
])
const ttsStatus = ref<{ mode: 'idle' | 'sound' | 'voice'; text: string }>({
  mode: 'idle',
  text: ''
})
const userInteracted = ref(false)
const demoStepLabel = ref('1. Escribe tu usuario de TikTok')

let timers: number[] = []

function clearTimers() {
  timers.forEach(t => window.clearTimeout(t))
  timers = []
}

function schedule(fn: () => void, delay: number) {
  const id = window.setTimeout(fn, delay)
  timers.push(id)
}

function selectTabManual(tab: DemoTab) {
  userInteracted.value = true
  activeTab.value = tab
}

function runDemoCycle() {
  clearTimers()
  if (userInteracted.value) return

  // Reinicio al estado inicial
  activeTab.value = 'tabChat'
  typedUser.value = ''
  isConnected.value = false
  isConnecting.value = false
  btnPulse.value = false
  ttsStatus.value = { mode: 'idle', text: '' }
  chatItems.value = [
    { id: 1, type: 'system', text: 'Conéctate y empieza a interactuar' }
  ]
  demoStepLabel.value = '1. Ingresa tu usuario sin arroba'

  const targetUsername = 'l.am.lex_'
  // Escribir usuario letra por letra
  targetUsername.split('').forEach((char, idx) => {
    schedule(() => {
      typedUser.value += char
    }, 500 + idx * 110)
  })

  // Pulsar botón Conectar
  schedule(() => {
    demoStepLabel.value = '2. Pulsa Conectar para enlazar el directo'
    btnPulse.value = true
    isConnecting.value = true
  }, 1750)

  // Conectado en vivo
  schedule(() => {
    btnPulse.value = false
    isConnecting.value = false
    isConnected.value = true
    demoStepLabel.value = '3. Escucha comentarios y alertas en tiempo real'
    chatItems.value = [
      { id: 2, type: 'system', text: 'Conectado al directo de l.am.lex_' }
    ]
  }, 2400)

  // Comentario 1: Andrea_21
  schedule(() => {
    chatItems.value.push({
      id: 3,
      type: 'user',
      user: 'Andrea_21',
      text: '¡Hola streamer! Saludos desde México, me encanta tu directo',
      speaking: true
    })
    ttsStatus.value = {
      mode: 'voice',
      text: 'Andrea_21 dice: ¡Hola streamer! Saludos desde México...'
    }
  }, 3300)

  // Entrada de espectador (Bienvenida)
  schedule(() => {
    chatItems.value.forEach(i => (i.speaking = false))
    ttsStatus.value = { mode: 'idle', text: '' }
    chatItems.value.push({
      id: 4,
      type: 'welcome',
      user: 'Mateo_Pro'
    })
  }, 5600)

  // Donación: Primero suena la alerta, después habla la voz
  schedule(() => {
    chatItems.value.push({
      id: 5,
      type: 'donation',
      user: 'Carlos_Gamer',
      gift: 'Rosa',
      count: 10,
      diamonds: 10,
      speaking: true
    })
    ttsStatus.value = {
      mode: 'sound',
      text: 'Sonando alerta: Monedas / Donación...'
    }
  }, 6600)

  // Después del sonido de alerta, habla el agradecimiento
  schedule(() => {
    ttsStatus.value = {
      mode: 'voice',
      text: '¡Muchas gracias a Carlos_Gamer por enviar 10 Rosa!'
    }
  }, 7800)

  // Comentario 2: Lucas_Arg
  schedule(() => {
    chatItems.value.forEach(i => (i.speaking = false))
    chatItems.value.push({
      id: 6,
      type: 'user',
      user: 'Lucas_Arg',
      text: '¿Qué juego vas a probar después? ¡Saludos!',
      speaking: true
    })
    ttsStatus.value = {
      mode: 'voice',
      text: 'Lucas_Arg dice: ¿Qué juego vas a probar después?...'
    }
  }, 9800)

  // Mostrar pestaña Ajustes de Voz
  schedule(() => {
    if (userInteracted.value) return
    ttsStatus.value = { mode: 'idle', text: '' }
    activeTab.value = 'tabVoice'
    demoStepLabel.value = '4. Personaliza motor neuronal offline, tono y velocidad'
  }, 12200)

  // Mostrar pestaña Donaciones
  schedule(() => {
    if (userInteracted.value) return
    activeTab.value = 'tabDonations'
    demoStepLabel.value = '5. Configura alertas de regalos, plantillas fijas y música'
  }, 15500)

  // Reiniciar ciclo
  schedule(() => {
    if (!userInteracted.value) {
      runDemoCycle()
    }
  }, 19000)
}

onMounted(() => {
  runDemoCycle()
})

onUnmounted(() => {
  clearTimers()
})
</script>

<template>
  <section class="hero-section">
    <div class="container hero-container">
      
      <!-- FILA HERO DE 2 COLUMNAS CON MAYOR ALTURA -->
      <div class="hero-split-row">
        <div class="hero-left-col">
          <LogoParticleCanvas />
        </div>

        <div class="hero-right-col">
          <h1 class="hero-title">
            Un amigo para ti y tu <span class="text-gradient">comunidad</span>
          </h1>

          <!-- BOTÓN DESCARGAR MYBOT CON ÍCONO DE WINDOWS -->
          <div class="hero-cta-group" id="descarga">
            <button
              type="button"
              class="btn btn-primary btn-lg btn-download-interactive"
              :class="{ 'btn-loading': descargando, 'btn-done': completado }"
              :disabled="descargando"
              @click="handleDescarga"
            >
              <i v-if="!descargando && !completado" class="fa-brands fa-windows" style="font-size: 19px;"></i>
              <i v-else-if="descargando" class="fa-solid fa-spinner fa-spin" style="font-size: 19px;"></i>
              <i v-else class="fa-solid fa-check" style="font-size: 19px;"></i>

              <div class="download-btn-text">
                <span v-if="!descargando && !completado">Descargar MyBot</span>
                <span v-else-if="descargando">Descargando MyBot... {{ progreso }}%</span>
                <span v-else>¡Descarga finalizada!</span>
                <small v-if="descargando || completado" class="download-subtext">{{ detalleDescarga }}</small>
              </div>

              <!-- Barra de progreso visual in-button -->
              <div v-if="descargando" class="btn-progress-bar" :style="{ width: progreso + '%' }"></div>
            </button>
          </div>

          <div class="hero-specs-row">
            <span class="spec-item">Windows 10 / 11 (64-bit)</span>
          </div>
        </div>
      </div>

      <!-- DEMO INTERACTIVA Y ANIMADA DE LA NUEVA INTERFAZ LIMPIA DE MYBOT -->
      <div class="app-showcase-wrapper">
        <div class="showcase-step-indicator">
          <span class="step-pulse-dot"></span>
          <span>{{ demoStepLabel }}</span>
          <button
            v-if="userInteracted"
            type="button"
            class="btn-resume-demo"
            @click="userInteracted = false; runDemoCycle()"
          >
            Reanudar animación
          </button>
        </div>

        <div class="clean-app-window">
          <!-- CABECERA PLANA SIN TARJETA (SÓLO LÍNEA INFERIOR) -->
          <div class="clean-header-bar">
            <div class="clean-top-brand">
              <div class="clean-brand-left">
                <img src="/icono.png" alt="MyBot" class="clean-app-icon" />
                <span class="clean-brand-name">MyBot</span>
                <span class="clean-version-text">{{ APP_VERSION_NAME }}</span>
              </div>

              <div
                class="clean-status-pill"
                :class="{
                  'is-connected': isConnected,
                  'is-connecting': isConnecting
                }"
              >
                <span class="clean-status-dot"></span>
                <span>
                  {{ isConnected ? `En Vivo: ${typedUser}` : (isConnecting ? 'Conectando...' : 'Desconectado') }}
                </span>
              </div>
            </div>

            <div class="clean-connection-row">
              <div class="clean-user-field">
                <label>Usuario de TikTok</label>
                <div class="clean-input-box" :class="{ 'is-typing': typedUser.length > 0 && !isConnected }">
                  <span>{{ typedUser || 'l.am.lex_' }}</span>
                  <span v-if="!isConnected" class="typing-caret"></span>
                </div>
              </div>
              <button
                type="button"
                class="clean-connect-btn"
                :class="{
                  'is-disconnect': isConnected,
                  'is-pulsing': btnPulse
                }"
                @click="isConnected = !isConnected"
              >
                {{ isConnected ? 'Desconectar' : 'Conectar' }}
              </button>
            </div>
          </div>

          <!-- BARRA DE PESTAÑAS LIMPIA (TEXTO NEGRO, ACTIVO AZUL CON LÍNEA DEBAJO, SIN ÍCONOS) -->
          <div class="clean-tabs-nav">
            <button
              type="button"
              class="clean-tab-btn"
              :class="{ active: activeTab === 'tabChat' }"
              @click="selectTabManual('tabChat')"
            >
              Chat en Vivo
            </button>
            <button
              type="button"
              class="clean-tab-btn"
              :class="{ active: activeTab === 'tabVoice' }"
              @click="selectTabManual('tabVoice')"
            >
              Ajustes de Voz
            </button>
            <button
              type="button"
              class="clean-tab-btn"
              :class="{ active: activeTab === 'tabDonations' }"
              @click="selectTabManual('tabDonations')"
            >
              Donaciones
            </button>
            <button
              type="button"
              class="clean-tab-btn"
              :class="{ active: activeTab === 'tabCommunity' }"
              @click="selectTabManual('tabCommunity')"
            >
              Bienvenidas
            </button>
            <button
              type="button"
              class="clean-tab-btn"
              :class="{ active: activeTab === 'tabFilters' }"
              @click="selectTabManual('tabFilters')"
            >
              Filtros & Opciones
            </button>
          </div>

          <!-- CONTENIDO DE PESTAÑAS CON ALTURA FIJA Y SCROLL INTERNO -->
          <div class="clean-tab-content">
            
            <!-- PESTAÑA 1: CHAT EN VIVO -->
            <div v-if="activeTab === 'tabChat'" class="clean-chat-pane">
              <div class="clean-chat-feed">
                <transition-group name="chat-pop">
                  <div
                    v-for="item in chatItems"
                    :key="item.id"
                    class="clean-chat-item"
                    :class="[`type-${item.type}`, { 'is-speaking': item.speaking }]"
                  >
                    <template v-if="item.type === 'system'">
                      <span>{{ item.text }}</span>
                    </template>

                    <template v-else-if="item.type === 'user'">
                      <div class="clean-bubble-head">
                        <span class="clean-bubble-user">{{ item.user }}</span>
                        <span v-if="item.speaking" class="voice-mini-wave">
                          <i></i><i></i><i></i>
                        </span>
                      </div>
                      <span class="clean-bubble-text">{{ item.text }}</span>
                    </template>

                    <template v-else-if="item.type === 'welcome'">
                      <span class="clean-welcome-text">
                        <strong>{{ item.user }}</strong> se unió al directo
                      </span>
                    </template>

                    <template v-else-if="item.type === 'donation'">
                      <div class="clean-donation-row">
                        <div class="clean-don-body">
                          <span class="clean-don-title">¡Regalo Recibido!</span>
                          <span class="clean-don-desc">
                            <strong>{{ item.user }}</strong> envió {{ item.count }}x {{ item.gift }} ({{ item.diamonds }} diamantes)
                          </span>
                        </div>
                        <span v-if="item.speaking" class="voice-mini-wave gold">
                          <i></i><i></i><i></i>
                        </span>
                      </div>
                    </template>
                  </div>
                </transition-group>
              </div>

              <!-- INDICADOR DINÁMICO DE VOZ / SONIDO EN TIEMPO REAL -->
              <transition name="fade-fast">
                <div v-if="ttsStatus.mode !== 'idle'" class="clean-tts-live-bar" :class="`mode-${ttsStatus.mode}`">
                  <div class="equalizer-bars">
                    <span></span><span></span><span></span><span></span>
                  </div>
                  <span class="tts-live-text">{{ ttsStatus.text }}</span>
                </div>
              </transition>

              <!-- BARRA INFERIOR CON ÚNICO BOTÓN MINIMALISTA DE SEPARAR -->
              <div class="clean-chat-toolbar">
                <button type="button" class="clean-popout-icon-btn" title="Separar chat en ventana independiente">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                  </svg>
                </button>
              </div>
            </div>

            <!-- PESTAÑA 2: AJUSTES DE VOZ -->
            <div v-else-if="activeTab === 'tabVoice'" class="clean-settings-pane">
              <div class="clean-3col-row">
                <div class="clean-field">
                  <label>Motor</label>
                  <div class="clean-select-mock">Piper</div>
                </div>
                <div class="clean-field">
                  <label>Voz</label>
                  <div class="clean-select-mock">Daniela - Mujer (Arg)</div>
                </div>
                <div class="clean-field">
                  <label>Ajuste Vocal</label>
                  <div class="clean-select-mock">Natural / Neutro</div>
                </div>
              </div>

              <div class="clean-sliders-box">
                <div class="clean-slider-item">
                  <div class="clean-slider-top">
                    <span>Tono de Voz</span>
                    <span class="clean-badge-val">0 Hz</span>
                  </div>
                  <div class="clean-track"><div class="clean-fill" style="width: 50%"></div><div class="clean-thumb" style="left: 50%"></div></div>
                </div>

                <div class="clean-slider-item">
                  <div class="clean-slider-top">
                    <span>Velocidad</span>
                    <span class="clean-badge-val">+10%</span>
                  </div>
                  <div class="clean-track"><div class="clean-fill" style="width: 60%"></div><div class="clean-thumb" style="left: 60%"></div></div>
                </div>

                <div class="clean-slider-item">
                  <div class="clean-slider-top">
                    <span>Volumen</span>
                    <span class="clean-badge-val">100%</span>
                  </div>
                  <div class="clean-track"><div class="clean-fill" style="width: 100%"></div><div class="clean-thumb" style="left: 100%"></div></div>
                </div>
              </div>

              <div class="clean-lined-section">
                <div class="clean-switch-line">
                  <span>Leer nombre de usuario</span>
                  <span class="clean-toggle on"></span>
                </div>
                <div class="clean-field">
                  <label>Plantilla de lectura</label>
                  <div class="clean-input-mock">{usuario} dice: {mensaje}</div>
                </div>
              </div>

              <div class="clean-test-row">
                <div class="clean-input-mock flex-1">¡Hola! Soy MyBot, tu asistente de voz para TikTok Live.</div>
                <button type="button" class="clean-btn-primary">Probar</button>
              </div>
            </div>

            <!-- PESTAÑA 3: DONACIONES -->
            <div v-else-if="activeTab === 'tabDonations'" class="clean-settings-pane">
              <div class="clean-2col-switches">
                <div class="clean-switch-box">
                  <span>Activar avisos de regalos</span>
                  <span class="clean-toggle on"></span>
                </div>
                <div class="clean-switch-box">
                  <span>Avisar solo al finalizar combo / racha</span>
                  <span class="clean-toggle on"></span>
                </div>
              </div>

              <div class="clean-field">
                <label>Mínimo de diamantes para alertar</label>
                <div class="clean-stepper-row">
                  <span class="clean-step-btn">-</span>
                  <span class="clean-step-val">1</span>
                  <span class="clean-step-btn">+</span>
                  <span class="clean-step-unit">diamante(s)</span>
                </div>
              </div>

              <div class="clean-top-line-section">
                <div class="clean-switch-line">
                  <span>Agradecimiento por voz</span>
                  <span class="clean-toggle on"></span>
                </div>
                <div class="clean-field">
                  <label>Plantilla de donación</label>
                  <div class="clean-input-mock">¡Muchas gracias a</div>
                  <div class="clean-fixed-badges">
                    <span class="c-badge">{usuario}</span>
                    <span class="c-sep">por enviar</span>
                    <span class="c-badge">{cantidad}</span>
                    <span class="c-badge">{regalo}</span>
                  </div>
                </div>
              </div>

              <div class="clean-top-line-section">
                <div class="clean-sound-row">
                  <div class="clean-switch-box compact">
                    <span>Sonido de alerta</span>
                    <span class="clean-toggle on"></span>
                  </div>
                  <div class="clean-select-mock flex-1">Monedas / Donación</div>
                  <button type="button" class="clean-play-btn">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="#FFFFFF">
                      <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <!-- PESTAÑA 4: BIENVENIDAS -->
            <div v-else-if="activeTab === 'tabCommunity'" class="clean-settings-pane">
              <div class="clean-2col-switches">
                <div class="clean-switch-box">
                  <span>Activar detección de entradas</span>
                  <span class="clean-toggle on"></span>
                </div>
                <div class="clean-switch-box">
                  <span>Mostrar entrada en el chat</span>
                  <span class="clean-toggle on"></span>
                </div>
              </div>
              <div class="clean-field">
                <label>Plantilla de saludo</label>
                <div class="clean-input-mock">¡Bienvenido {usuario} al directo!</div>
              </div>
              <div class="clean-test-row">
                <div class="clean-input-mock flex-1">Alex</div>
                <button type="button" class="clean-btn-primary">Probar</button>
              </div>
            </div>

            <!-- PESTAÑA 5: FILTROS & OPCIONES -->
            <div v-else class="clean-settings-pane">
              <div class="clean-2col-switches">
                <div class="clean-switch-box">
                  <span>Filtrar enlaces y spam</span>
                  <span class="clean-toggle on"></span>
                </div>
                <div class="clean-switch-box">
                  <span>Ignorar comentarios repetidos</span>
                  <span class="clean-toggle on"></span>
                </div>
              </div>
              <div class="clean-field">
                <label>Palabras bloqueadas (separadas por coma)</label>
                <div class="clean-input-mock">spam, enlace, insulto</div>
              </div>
            </div>

          </div>
        </div>
      </div>

    </div>
  </section>
</template>

<style scoped>
.hero-section {
  padding: 68px 0 84px;
  text-align: center;
}

.hero-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* PORTADA DE 2 COLUMNAS CON MAYOR ALTO Y PRESENCIA */
.hero-split-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 48px;
  width: 100%;
  max-width: 900px;
  min-height: 310px;
  margin: 16px auto 54px;
}

.hero-left-col {
  flex: 0 0 280px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-right-col {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
}

.hero-right-col .hero-title {
  font-size: 42px;
  font-weight: 800;
  letter-spacing: -0.025em;
  line-height: 1.15;
  color: var(--ios-text-primary);
  margin-bottom: 24px;
  text-align: left;
}

.text-gradient {
  background: linear-gradient(135deg, #007AFF 0%, #38BDF8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-right-col .hero-cta-group {
  margin-bottom: 14px;
  display: flex;
  justify-content: flex-start;
}

.hero-right-col .hero-specs-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--ios-text-muted);
  justify-content: flex-start;
}

/* ============================================================================
   VENTANA DEMO ANIMADA CON LA NUEVA INTERFAZ LIMPIA DE MYBOT
   ============================================================================ */
.app-showcase-wrapper {
  width: 100%;
  max-width: 500px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.showcase-step-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  align-self: center;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #E2E8F0;
  border-radius: 999px;
  padding: 5px 14px;
  font-size: 12px;
  font-weight: 600;
  color: #334155;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}

.step-pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #007AFF;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
  animation: pulseDot 1.6s infinite;
}

@keyframes pulseDot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.25); opacity: 0.7; }
}

.btn-resume-demo {
  background: #EFF6FF;
  color: #007AFF;
  border: none;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.clean-app-window {
  background: #F5F6F8;
  border: 1px solid #DCE1E9;
  border-radius: 10px;
  box-shadow: 0 24px 60px -14px rgba(15, 23, 42, 0.14), 0 0 0 1px rgba(15, 23, 42, 0.04);
  padding: 10px 12px 12px;
  text-align: left;
  font-size: 11.5px;
  color: #1E293B;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Cabecera plana sin tarjeta */
.clean-header-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 2px 10px;
  border-bottom: 1px solid #E2E8F0;
}

.clean-top-brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.clean-brand-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.clean-app-icon {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0, 122, 255, 0.2);
}

.clean-brand-name {
  font-size: 15px;
  font-weight: 700;
  color: #007AFF;
}

.clean-version-text {
  font-size: 10.5px;
  font-weight: 500;
  color: #64748B;
}

.clean-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 600;
  background: #F1F5F9;
  color: #64748B;
  transition: all 0.25s ease;
}

.clean-status-pill.is-connecting {
  background: #FEF3C7;
  color: #D97706;
}

.clean-status-pill.is-connected {
  background: #DCFCE7;
  color: #15803D;
}

.clean-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

/* Fila de conexión */
.clean-connection-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.clean-user-field {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.clean-user-field label {
  font-size: 10.5px;
  font-weight: 600;
  color: #64748B;
}

.clean-input-box {
  height: 30px;
  background: #FFFFFF;
  border: 1px solid #CBD5E1;
  border-radius: 6px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  font-size: 11.5px;
  color: #0F172A;
  transition: border-color 0.2s;
}

.clean-input-box.is-typing {
  border-color: #007AFF;
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.12);
}

.typing-caret {
  display: inline-block;
  width: 1.5px;
  height: 13px;
  background: #007AFF;
  margin-left: 2px;
  animation: blinkCaret 0.8s infinite;
}

@keyframes blinkCaret {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.clean-connect-btn {
  height: 30px;
  padding: 0 14px;
  border-radius: 6px;
  border: none;
  background: #007AFF;
  color: #FFFFFF;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.clean-connect-btn.is-pulsing {
  transform: scale(0.95);
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.28);
}

.clean-connect-btn.is-disconnect {
  background: #EF4444;
}

/* Barra de pestañas limpia */
.clean-tabs-nav {
  display: flex;
  border-bottom: 2px solid #E2E8F0;
  gap: 2px;
  overflow-x: auto;
}

.clean-tab-btn {
  flex: 1 0 auto;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 7px 8px;
  font-size: 11px;
  font-weight: 600;
  color: #000000;
  cursor: pointer;
  margin-bottom: -2px;
  transition: color 0.18s, border-color 0.18s;
  white-space: nowrap;
}

.clean-tab-btn.active {
  color: #007AFF;
  border-bottom-color: #007AFF;
}

/* Contenedor de contenido */
.clean-tab-content {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  height: 290px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.clean-chat-pane {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.clean-chat-feed {
  flex: 1;
  padding: 10px 12px;
  background: #FAFBFD;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.clean-chat-item {
  font-size: 11.5px;
  border-radius: 6px;
  transition: all 0.25s ease;
}

.clean-chat-item.type-system {
  align-self: center;
  background: #EEF2F6;
  color: #64748B;
  font-size: 10.5px;
  padding: 4px 12px;
  border-radius: 999px;
}

.clean-chat-item.type-user {
  align-self: flex-start;
  max-width: 90%;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  padding: 6px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.clean-chat-item.type-user.is-speaking {
  border-color: #38BDF8;
  box-shadow: 0 2px 8px rgba(56, 189, 248, 0.14);
}

.clean-bubble-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.clean-bubble-user {
  font-size: 10.5px;
  font-weight: 700;
  color: #007AFF;
}

.clean-bubble-text {
  color: #1E293B;
}

.clean-chat-item.type-welcome {
  align-self: center;
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
  color: #166534;
  font-size: 11px;
  padding: 4px 12px;
  border-radius: 999px;
}

.clean-chat-item.type-donation {
  align-self: center;
  width: 96%;
  background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
  border: 1px solid #FCD34D;
  padding: 7px 11px;
  color: #78350F;
}

.clean-donation-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.clean-don-body {
  display: flex;
  flex-direction: column;
}

.clean-don-title {
  font-size: 10px;
  font-weight: 700;
  color: #B45309;
  text-transform: uppercase;
}

.clean-don-desc {
  font-size: 11.5px;
}

/* Ondas de voz animadas */
.voice-mini-wave {
  display: inline-flex;
  align-items: flex-end;
  gap: 2px;
  height: 11px;
}

.voice-mini-wave i {
  width: 2.5px;
  background: #007AFF;
  border-radius: 2px;
  animation: waveBounce 0.6s infinite ease-in-out;
}

.voice-mini-wave.gold i {
  background: #D97706;
}

.voice-mini-wave i:nth-child(1) { height: 5px; animation-delay: 0s; }
.voice-mini-wave i:nth-child(2) { height: 10px; animation-delay: 0.15s; }
.voice-mini-wave i:nth-child(3) { height: 6px; animation-delay: 0.3s; }

@keyframes waveBounce {
  0%, 100% { transform: scaleY(0.45); }
  50% { transform: scaleY(1.1); }
}

/* Barra activa de lectura TTS */
.clean-tts-live-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  font-size: 10.5px;
  font-weight: 600;
  background: #EFF6FF;
  color: #1D4ED8;
  border-top: 1px solid #BFDBFE;
}

.clean-tts-live-bar.mode-sound {
  background: #FEF3C7;
  color: #B45309;
  border-top-color: #FDE68A;
}

.equalizer-bars {
  display: inline-flex;
  align-items: flex-end;
  gap: 2px;
  height: 12px;
}

.equalizer-bars span {
  width: 2.5px;
  background: currentColor;
  border-radius: 2px;
  animation: waveBounce 0.55s infinite ease-in-out;
}

.equalizer-bars span:nth-child(1) { height: 6px; animation-delay: 0s; }
.equalizer-bars span:nth-child(2) { height: 11px; animation-delay: 0.12s; }
.equalizer-bars span:nth-child(3) { height: 8px; animation-delay: 0.24s; }
.equalizer-bars span:nth-child(4) { height: 10px; animation-delay: 0.36s; }

.tts-live-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Barra inferior de chat con icono cuadrado minimalista */
.clean-chat-toolbar {
  display: flex;
  justify-content: flex-end;
  padding: 5px 10px;
  background: #FFFFFF;
  border-top: 1px solid #E2E8F0;
}

.clean-popout-icon-btn {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid #CBD5E1;
  border-radius: 4px;
  color: #64748B;
  cursor: pointer;
}

/* Paneles de configuración (Voz, Donaciones, etc.) */
.clean-settings-pane {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  height: 100%;
}

.clean-3col-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 6px;
}

.clean-field {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.clean-field label {
  font-size: 10.5px;
  font-weight: 600;
  color: #64748B;
}

.clean-select-mock,
.clean-input-mock {
  height: 28px;
  padding: 0 8px;
  background: #F1F5F9;
  border: 1px solid #CBD5E1;
  border-radius: 5px;
  display: flex;
  align-items: center;
  font-size: 11px;
  color: #1E293B;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.clean-sliders-box {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.clean-slider-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.clean-slider-top {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 600;
}

.clean-badge-val {
  font-size: 10px;
  color: #007AFF;
  background: #EFF6FF;
  padding: 1px 6px;
  border-radius: 999px;
}

.clean-track {
  position: relative;
  height: 5px;
  background: #E2E8F0;
  border-radius: 999px;
}

.clean-fill {
  height: 100%;
  background: #007AFF;
  border-radius: 999px;
}

.clean-thumb {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 12px;
  background: #FFFFFF;
  border: 2px solid #007AFF;
  border-radius: 50%;
}

.clean-lined-section {
  border-top: 1px solid #E2E8F0;
  border-bottom: 1px solid #E2E8F0;
  padding: 8px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.clean-top-line-section {
  border-top: 1px solid #E2E8F0;
  padding-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.clean-switch-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.clean-toggle {
  width: 32px;
  height: 18px;
  background: #CBD5E1;
  border-radius: 999px;
  position: relative;
  display: inline-block;
}

.clean-toggle.on {
  background: #22C55E;
}

.clean-toggle::after {
  content: "";
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  background: #FFFFFF;
  border-radius: 50%;
  transition: transform 0.2s;
}

.clean-toggle.on::after {
  transform: translateX(14px);
}

.clean-test-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.flex-1 {
  flex: 1;
}

.clean-btn-primary {
  height: 28px;
  padding: 0 12px;
  background: #007AFF;
  color: #FFFFFF;
  border: none;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 600;
}

.clean-2col-switches {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.clean-switch-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  padding: 6px 8px;
  border: 1px solid #E2E8F0;
  border-radius: 5px;
  font-size: 10.5px;
  font-weight: 600;
}

.clean-stepper-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.clean-step-btn {
  width: 24px;
  height: 24px;
  background: #F1F5F9;
  border: 1px solid #CBD5E1;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #007AFF;
}

.clean-step-val {
  width: 48px;
  height: 24px;
  background: #FFFFFF;
  border: 1px solid #CBD5E1;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.clean-step-unit {
  font-size: 10.5px;
  color: #64748B;
}

.clean-fixed-badges {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 6px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 4px;
  margin-top: 2px;
}

.c-badge {
  background: #E2E8F0;
  color: #1E293B;
  font-weight: 700;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
}

.c-sep {
  font-size: 10px;
  color: #64748B;
}

.clean-sound-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.clean-play-btn {
  width: 28px;
  height: 28px;
  background: #007AFF;
  border: none;
  border-radius: 5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* Animaciones de transición de burbujas */
.chat-pop-enter-active {
  transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
}
.chat-pop-enter-from {
  opacity: 0;
  transform: translateY(8px) scale(0.97);
}

/* BOTÓN DE DESCARGA INTERACTIVO */
.btn-download-interactive {
  position: relative;
  overflow: hidden;
  min-width: 290px;
  min-height: 52px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  transition: all 0.3s ease;
}

.download-btn-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
  line-height: 1.25;
}

.download-subtext {
  font-size: 11px;
  font-weight: 500;
  opacity: 0.92;
  margin-top: 2px;
  color: #E0F2FE;
}

.btn-progress-bar {
  position: absolute;
  left: 0;
  bottom: 0;
  height: 4px;
  background: #38BDF8;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.9);
  transition: width 0.15s ease-out;
}

.btn-loading {
  background: #0284C7 !important;
  cursor: wait;
}

.btn-done {
  background: #10B981 !important;
  box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4) !important;
}

@media (max-width: 768px) {
  .hero-section {
    padding: 40px 0 56px;
  }

  .hero-split-row {
    flex-direction: column;
    text-align: center;
    gap: 24px;
    min-height: auto;
  }

  .hero-right-col {
    align-items: center;
    text-align: center;
  }

  .hero-right-col .hero-title {
    text-align: center;
    font-size: 30px;
  }

  .hero-right-col .hero-cta-group,
  .hero-right-col .hero-specs-row {
    justify-content: center;
  }
}
</style>
