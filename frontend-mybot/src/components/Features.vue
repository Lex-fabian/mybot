<template>
  <section class="features-section" id="caracteristicas">
    <div class="container">
      <div class="section-header">
        <h2 class="section-title">Características Principales</h2>
        <p class="section-subtitle">
          Herramientas diseñadas para transmisiones de TikTok Live fluidas y sin saturación.
        </p>
      </div>

      <div class="features-grid">
        <div class="feature-item">
          <h3 class="feature-title">Voces Neurales Ultra Realistas</h3>
          <p class="feature-desc">
            Integración con Edge TTS y SAPI5 local. Acentos en español de múltiples países sin demoras ni límites.
          </p>
        </div>

        <div class="feature-item">
          <h3 class="feature-title">Alertas de Regalos y Rachas</h3>
          <p class="feature-desc">
            Agradece donaciones con audio y voz personalizada. Filtra combos masivos para evitar saturar tu directo.
          </p>
        </div>

        <div class="feature-item">
          <h3 class="feature-title">Filtros Anti-Spam en Vivo</h3>
          <p class="feature-desc">
            Oculta links sospechosos, compacta cadenas repetidas de emojis y filtra palabras baneadas al instante.
          </p>
        </div>

        <div class="feature-item">
          <h3 class="feature-title">Parada Instantánea</h3>
          <p class="feature-desc">
            Silencia la voz al instante y limpia la cola de lectura con un solo clic para tener control total.
          </p>
        </div>

        <div class="feature-item">
          <h3 class="feature-title">Modulación y Presets</h3>
          <p class="feature-desc">
            Ajusta tono, velocidad y volumen en tiempo real, o activa perfiles rápidos como Robot, Locutor o Gamer.
          </p>
        </div>

        <div class="feature-item">
          <h3 class="feature-title">Actualizaciones Integradas</h3>
          <p class="feature-desc">
            Detección automática de nuevas mejoras con descarga directa del instalador optimizado.
          </p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.features-section {
  padding: 64px 0 72px;
  background: #FFFFFF;
  border-top: 1px solid var(--ios-border);
  border-bottom: 1px solid var(--ios-border);
}

.section-header {
  text-align: center;
  max-width: 620px;
  margin: 0 auto 48px;
}

.section-title {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--ios-text-primary);
  margin-bottom: 8px;
}

.section-subtitle {
  font-size: 15px;
  color: var(--ios-text-secondary);
  line-height: 1.5;
}

/* GRID LIMPIO Y SIN ICONOS */
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.feature-item {
  display: flex;
  flex-direction: column;
  padding: 24px 22px;
  background: #F8FAFD;
  border: 1px solid var(--ios-border);
  border-radius: var(--radius-md);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.feature-item:hover {
  transform: translateY(-2px);
  border-color: #CBD5E1;
  background: #FFFFFF;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
}

.feature-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--ios-text-primary);
  margin-bottom: 6px;
  letter-spacing: -0.01em;
}

.feature-desc {
  font-size: 13.5px;
  color: var(--ios-text-secondary);
  line-height: 1.55;
}

@media (max-width: 900px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 32px 24px;
  }
}

@media (max-width: 600px) {
  .features-grid {
    grid-template-columns: 1fr;
    gap: 28px;
  }
  .features-section {
    padding: 48px 0;
  }
  .section-header {
    margin-bottom: 36px;
  }
}
</style>
