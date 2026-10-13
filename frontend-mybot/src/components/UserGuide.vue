<template>
  <section class="guide-section" id="guia">
    <div class="container">
      <div class="guide-header">
        <h2 class="guide-title">Guía de Configuración y Uso</h2>
        <p class="guide-subtitle">Aprende a conectar tu cuenta de TikTok y sacarle el máximo provecho a cada módulo.</p>
      </div>

      <div class="steps-flow">
        <!-- PASO 1 -->
        <div class="step-node">
          <div class="step-badge-wrap">
            <div class="step-num">1</div>
            <div class="step-line"></div>
          </div>
          <div class="step-body">
            <h3 class="step-title">Conectar con TikTok Live</h3>
            <p class="step-desc">
              Inicia tu transmisión en TikTok desde tu móvil o PC. Luego, en MyBot, ingresa tu <strong>@usuario</strong> o el enlace de tu live y haz clic en <strong>Conectar</strong>. El indicador cambiará a conectado cuando esté sincronizado.
            </p>
          </div>
        </div>

        <!-- PASO 2 -->
        <div class="step-node">
          <div class="step-badge-wrap">
            <div class="step-num">2</div>
            <div class="step-line"></div>
          </div>
          <div class="step-body">
            <h3 class="step-title">Configurar la Voz Neural</h3>
            <p class="step-desc">
              En la pestaña <strong>Voz</strong>, selecciona <em>Edge TTS</em> para voces humanas ultra realistas. Elige el país y locutor deseado (México, España, etc.) y ajusta la velocidad, tono y volumen de lectura.
            </p>
          </div>
        </div>

        <!-- PASO 3 -->
        <div class="step-node">
          <div class="step-badge-wrap">
            <div class="step-num">3</div>
            <div class="step-line"></div>
          </div>
          <div class="step-body">
            <h3 class="step-title">Alertas de Regalos</h3>
            <p class="step-desc">
              En la pestaña <strong>Donaciones</strong>, define el mínimo de diamantes para leer regalos. Activa <em>"Esperar fin de racha"</em> para que el bot anuncie el combo final en vez de saturar con cada rosa individual.
            </p>
          </div>
        </div>

        <!-- PASO 4 -->
        <div class="step-node last">
          <div class="step-badge-wrap">
            <div class="step-num">4</div>
          </div>
          <div class="step-body">
            <h3 class="step-title">Filtros y Control Total</h3>
            <p class="step-desc">
              En la pestaña <strong>Filtros</strong>, activa la compactación de emojis y bloqueo de enlaces. Usa el botón superior <strong>⏹️ Detener Audio</strong> para cortar la voz al instante si necesitas silencio inmediato.
            </p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.guide-section {
  padding: 64px 0 72px;
  background: var(--ios-bg);
  border-bottom: 1px solid var(--ios-border);
}

.guide-header {
  text-align: center;
  max-width: 620px;
  margin: 0 auto 48px;
}

.guide-title {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--ios-text-primary);
  margin-bottom: 8px;
}

.guide-subtitle {
  font-size: 15px;
  color: var(--ios-text-secondary);
  line-height: 1.5;
}

/* FLUJO DE PASOS LIMPIO Y MONOCROMÁTICO */
.steps-flow {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  position: relative;
}

.step-node {
  display: flex;
  flex-direction: column;
}

.step-badge-wrap {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  position: relative;
}

.step-num {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: var(--ios-text-primary);
  background: #FFFFFF;
  border: 1.5px solid var(--ios-border);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
  z-index: 2;
  transition: transform 0.2s ease, border-color 0.2s ease, background-color 0.2s ease;
}

.step-node:hover .step-num {
  transform: scale(1.08);
  border-color: var(--ios-text-secondary);
  background: #F8FAFC;
}

.step-line {
  flex: 1;
  height: 1px;
  background: var(--ios-border);
  margin-left: 12px;
}

.step-node.last .step-line {
  display: none;
}

.step-body {
  padding-right: 12px;
}

.step-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--ios-text-primary);
  margin-bottom: 8px;
  letter-spacing: -0.01em;
}

.step-desc {
  font-size: 13px;
  color: var(--ios-text-secondary);
  line-height: 1.6;
}

.step-desc strong {
  color: var(--ios-text-primary);
  font-weight: 600;
}

.step-desc em {
  font-style: normal;
  color: var(--ios-text-primary);
  font-weight: 600;
}

@media (max-width: 900px) {
  .steps-flow {
    grid-template-columns: repeat(2, 1fr);
    gap: 36px 24px;
  }
  .step-line {
    display: none;
  }
}

@media (max-width: 550px) {
  .steps-flow {
    grid-template-columns: 1fr;
    gap: 28px;
  }
  .guide-section {
    padding: 48px 0;
  }
  .guide-header {
    margin-bottom: 36px;
  }
}
</style>
