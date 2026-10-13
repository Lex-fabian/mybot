<script setup lang="ts">
import LogoParticleCanvas from './LogoParticleCanvas.vue'
import {
  isDownloading as descargando,
  downloadPercent as progreso,
  downloadDetail as detalleDescarga,
  isCompleted as completado,
  iniciarDescargaGlobal as iniciarDescarga
} from '../utils/downloader'
import { APP_VERSION_NAME } from '../version'

defineEmits<{
  (e: 'open-binance'): void
}>()

function handleDescarga() {
  iniciarDescarga()
}
</script>

<template>
  <section class="hero-section">
    <div class="container hero-container">
      
      <!-- LOGO DE PUNTOS ANIMADOS EN EL INICIO -->
      <LogoParticleCanvas />

      <!-- HEADER INTRO -->
      <div class="hero-badge-wrapper">
        <span class="badge badge-celeste">
          <span>MyBot {{ APP_VERSION_NAME }} • Desarrollado por i.am.lex</span>
        </span>
      </div>

      <h1 class="hero-title">
        La voz de tu directo en <span class="text-gradient">TikTok Live</span>
      </h1>

      <p class="hero-subtitle">
        Lectura de comentarios y alertas de regalos en tiempo real con voces neurales ultra realistas. Rápido, ligero y elegante.
      </p>

      <!-- BOTONES DE ACCIÓN -->
      <div class="hero-cta-group" id="descarga">
        <button
          type="button"
          class="btn btn-primary btn-lg btn-download-interactive"
          :class="{ 'btn-loading': descargando, 'btn-done': completado }"
          :disabled="descargando"
          @click="handleDescarga"
        >
          <i v-if="!descargando && !completado" class="fa-brands fa-windows" style="font-size: 18px;"></i>
          <i v-else-if="descargando" class="fa-solid fa-spinner fa-spin" style="font-size: 18px;"></i>
          <i v-else class="fa-solid fa-check" style="font-size: 18px;"></i>

          <div class="download-btn-text">
            <span v-if="!descargando && !completado">Descargar Instalador para Windows</span>
            <span v-else-if="descargando">Descargando MyBot... {{ progreso }}%</span>
            <span v-else>¡Descarga finalizada!</span>
            <small v-if="descargando || completado" class="download-subtext">{{ detalleDescarga }}</small>
          </div>

          <!-- Barra de progreso visual in-button -->
          <div v-if="descargando" class="btn-progress-bar" :style="{ width: progreso + '%' }"></div>
        </button>

        <button class="btn btn-binance btn-lg" @click="$emit('open-binance')">
          <i class="fa-solid fa-heart"></i>
          <span>Donar</span>
        </button>
      </div>

      <div class="hero-specs-row">
        <span class="spec-item">Windows 10 / 11 (64-bit)</span>
      </div>

      <!-- MOCKUP VISUAL DE LA APP DESKTOP -->
      <div class="app-mockup-wrapper">
        <div class="app-mockup-window">
          <div class="mockup-titlebar">
            <div class="traffic-lights">
              <span class="light red"></span>
              <span class="light yellow"></span>
              <span class="light green"></span>
            </div>
            <span class="mockup-title">MyBot {{ APP_VERSION_NAME }} — Lector de Comentarios y Donaciones</span>
            <span class="mockup-badge"><i class="fa-solid fa-circle" style="font-size: 8px;"></i> Conectado a @streamer</span>
          </div>

          <div class="mockup-body">
            <div class="mockup-chat-feed">
              <div class="mockup-bubble system">
                <i class="fa-solid fa-circle-check text-green"></i>
                <span>Conectado al directo en tiempo real.</span>
              </div>
              <div class="mockup-bubble user">
                <span class="bubble-name"><i class="fa-solid fa-comment"></i> Andrea_21:</span>
                <span class="bubble-msg">¡Hola streamer! Saludos desde México, me encanta tu directo</span>
              </div>
              <div class="mockup-bubble donation">
                <span class="don-icon"><i class="fa-solid fa-gift"></i></span>
                <div class="don-info">
                  <strong>Carlos_Gamer</strong> envió 10x Rosa (10 diamantes)
                </div>
              </div>
              <div class="mockup-bubble user">
                <span class="bubble-name"><i class="fa-solid fa-comment"></i> Lucas_Arg:</span>
                <span class="bubble-msg">¿Qué juego vas a probar después? ¡Saludos!</span>
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
  padding: 32px 0 44px;
  text-align: center;
}

.hero-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-badge-wrapper {
  margin-bottom: 12px;
}

.hero-title {
  font-size: 34px;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.2;
  color: var(--ios-text-primary);
  max-width: 720px;
  margin-bottom: 12px;
}

.text-gradient {
  background: linear-gradient(135deg, #007AFF 0%, #38BDF8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-subtitle {
  font-size: 14px;
  font-weight: 400;
  color: var(--ios-text-secondary);
  max-width: 580px;
  line-height: 1.5;
  margin-bottom: 22px;
}

.hero-cta-group {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.hero-specs-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--ios-text-muted);
  margin-bottom: 28px;
}

.spec-dot {
  opacity: 0.4;
}

/* MOCKUP DE VENTANA iOS */
.app-mockup-wrapper {
  width: 100%;
  max-width: 760px;
  perspective: 1000px;
}

.app-mockup-window {
  background: #FFFFFF;
  border: 1px solid var(--ios-border);
  border-radius: var(--radius-lg);
  box-shadow: 0 24px 60px -12px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  text-align: left;
  transform: translateY(0);
  transition: transform var(--transition);
}

.app-mockup-window:hover {
  transform: translateY(-4px);
}

.mockup-titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  background: #F1F4F9;
  border-bottom: 1px solid var(--ios-border);
}

.traffic-lights {
  display: flex;
  gap: 8px;
}

.light {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.light.red { background: #FF5F56; }
.light.yellow { background: #FFBD2E; }
.light.green { background: #27C93F; }

.mockup-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--ios-text-secondary);
}

.mockup-badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--ios-green);
  background: var(--ios-green-light);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}

.mockup-body {
  padding: 20px;
  background: #FAFBFD;
}

.mockup-chat-feed {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mockup-bubble {
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 13px;
  max-width: 88%;
}

.mockup-bubble.system {
  align-self: center;
  background: #EEF2F6;
  color: var(--ios-text-secondary);
  font-size: 12px;
  border-radius: var(--radius-pill);
  padding: 5px 14px;
}

.mockup-bubble.user {
  background: #FFFFFF;
  border: 1px solid var(--ios-border);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.bubble-name {
  font-size: 11px;
  font-weight: 700;
  color: var(--ios-blue);
}

.bubble-msg {
  color: var(--ios-text-primary);
}

.mockup-bubble.donation {
  align-self: center;
  width: 95%;
  background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
  border: 1px solid #FCD34D;
  color: #78350F;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 2px 10px rgba(245, 158, 11, 0.15);
}

.don-icon {
  font-size: 20px;
}

/* BOTÓN DE DESCARGA INTERACTIVO BLOB */
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
  .hero-title {
    font-size: 36px;
  }
  .hero-subtitle {
    font-size: 16px;
  }
}
</style>
