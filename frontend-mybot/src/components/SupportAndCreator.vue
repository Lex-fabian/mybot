<script setup lang="ts">
import { ref } from 'vue'

const binancePayId = ref('1175466526')
const binanceAlias = ref('lexfabian')
const copied = ref(false)

function copyToClipboard() {
  navigator.clipboard.writeText(binancePayId.value).then(() => {
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  })
}
</script>

<template>
  <section class="support-section" id="donar">
    <div class="container">
      <div class="support-container-clean">
        
        <!-- COLUMNA 1: APID / BINANCE PAY -->
        <div class="support-block">
          <div class="block-tag gold">
            <i class="fa-solid fa-heart"></i>
            <span>Apoyar el Proyecto</span>
          </div>

          <h3 class="block-title">Binance Pay</h3>

          <div class="binance-content">
            <a
              href="https://app.binance.com/payment/secpay?uid=1175466526"
              target="_blank"
              rel="noopener"
              class="qr-wrapper"
              title="Escanear con Binance o hacer clic para abrir"
            >
              <img src="/binance-qr.svg" alt="Binance QR" class="qr-image" />
            </a>

            <div class="binance-info">
              <div class="user-pill">
                <span class="user-label">Usuario:</span>
                <strong class="user-name">{{ binanceAlias }}</strong>
              </div>

              <div class="uid-copy-row">
                <div class="uid-field-wrap">
                  <span class="uid-label">UID</span>
                  <span class="uid-number">{{ binancePayId }}</span>
                </div>
                <button
                  class="btn-copy"
                  :class="{ copied }"
                  @click="copyToClipboard"
                  title="Copiar UID de Binance"
                >
                  <i :class="copied ? 'fa-solid fa-check' : 'fa-solid fa-copy'"></i>
                  <span>{{ copied ? '¡Copiado!' : 'Copiar' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- SEPARADOR VERTICAL SUTIL -->
        <div class="support-divider"></div>

        <!-- COLUMNA 2: CREADOR OFICIAL -->
        <div class="support-block" id="desarrollador">
          <div class="block-tag blue">
            <i class="fa-solid fa-code"></i>
            <span>Creador Oficial</span>
          </div>

          <h3 class="block-title">i.am.lex</h3>

          <p class="creator-desc">
            Desarrollo de bots inteligentes y herramientas de streaming de alto rendimiento.
          </p>

          <div class="creator-links">
            <a
              href="https://discord.gg/q9HsEkCHyN"
              target="_blank"
              rel="noopener"
              class="creator-link-row discord"
            >
              <div class="link-icon-box discord">
                <i class="fa-brands fa-discord"></i>
              </div>
              <div class="link-meta">
                <span class="link-title">Comunidad Discord</span>
                <span class="link-sub">Noticias, updates y sugerencias</span>
              </div>
              <i class="fa-solid fa-arrow-up-right-from-square link-arrow"></i>
            </a>

            <a
              href="https://web-lex.vercel.app/"
              target="_blank"
              rel="noopener"
              class="creator-link-row"
            >
              <div class="link-icon-box blue">
                <i class="fa-solid fa-globe"></i>
              </div>
              <div class="link-meta">
                <span class="link-title">Sitio Web</span>
                <span class="link-sub">web-lex.vercel.app</span>
              </div>
              <i class="fa-solid fa-arrow-up-right-from-square link-arrow"></i>
            </a>

            <a
              href="https://www.tiktok.com/@l.am.lex_?is_from_webapp=1&sender_device=pc"
              target="_blank"
              rel="noopener"
              class="creator-link-row tiktok"
            >
              <div class="link-icon-box black">
                <i class="fa-brands fa-tiktok"></i>
              </div>
              <div class="link-meta">
                <span class="link-title">TikTok</span>
                <span class="link-sub">@l.am.lex_</span>
              </div>
              <i class="fa-solid fa-arrow-up-right-from-square link-arrow"></i>
            </a>

            <a
              href="https://www.instagram.com/l.am.lex_/"
              target="_blank"
              rel="noopener"
              class="creator-link-row instagram"
            >
              <div class="link-icon-box pink">
                <i class="fa-brands fa-instagram"></i>
              </div>
              <div class="link-meta">
                <span class="link-title">Instagram</span>
                <span class="link-sub">@l.am.lex_</span>
              </div>
              <i class="fa-solid fa-arrow-up-right-from-square link-arrow"></i>
            </a>
          </div>
        </div>

      </div>
    </div>
  </section>
</template>

<style scoped>
.support-section {
  padding: 64px 0 80px;
  background: #FFFFFF;
}

.support-container-clean {
  display: grid;
  grid-template-columns: 1fr auto 1.15fr;
  align-items: start;
  gap: 48px;
  background: #FFFFFF;
  border: 1px solid var(--ios-border);
  border-radius: var(--radius-xl);
  padding: 40px 48px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
}

.support-divider {
  width: 1px;
  align-self: stretch;
  background: var(--ios-border);
}

.support-block {
  display: flex;
  flex-direction: column;
}

.block-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 700;
  width: fit-content;
  margin-bottom: 12px;
}

.block-tag.gold {
  background: #FEF9E7;
  color: #B45309;
}

.block-tag.blue {
  background: #EBF5FF;
  color: #007AFF;
}

.block-title {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--ios-text-primary);
  margin-bottom: 16px;
}

/* BINANCE CONTENT */
.binance-content {
  display: flex;
  align-items: center;
  gap: 24px;
}

.qr-wrapper {
  flex-shrink: 0;
  display: inline-block;
  background: #FFFFFF;
  padding: 10px;
  border-radius: 16px;
  border: 1px solid #E2E8F0;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.qr-wrapper:hover {
  transform: scale(1.03);
  box-shadow: 0 8px 24px rgba(240, 185, 11, 0.2);
}

.qr-image {
  width: 120px;
  height: 120px;
  display: block;
}

.binance-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

.user-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  padding: 6px 14px;
  border-radius: var(--radius-pill);
  font-size: 13px;
  width: fit-content;
}

.user-label {
  color: var(--ios-text-muted);
}

.user-name {
  color: #0F172A;
  font-weight: 700;
}

.uid-copy-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.uid-field-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #F8FAFC;
  border: 1px solid #CBD5E1;
  padding: 8px 14px;
  border-radius: 12px;
  flex: 1;
}

.uid-label {
  font-size: 10px;
  font-weight: 800;
  color: #D97706;
  background: #FEF3C7;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.05em;
}

.uid-number {
  font-family: monospace;
  font-size: 14px;
  font-weight: 700;
  color: #0F172A;
}

.btn-copy {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #F0B90B;
  color: #0F172A;
  font-size: 13px;
  font-weight: 700;
  border: none;
  padding: 10px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.btn-copy:hover {
  background: #E2AD07;
  transform: translateY(-1px);
}

.btn-copy.copied {
  background: #10B981;
  color: #FFFFFF;
}

/* CREADOR OFICIAL */
.creator-desc {
  font-size: 14px;
  color: var(--ios-text-secondary);
  line-height: 1.55;
  margin-bottom: 20px;
}

.creator-links {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.creator-link-row {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  padding: 10px 16px;
  border-radius: 14px;
  text-decoration: none;
  transition: all 0.2s ease;
}

.creator-link-row:hover {
  background: #FFFFFF;
  border-color: #007AFF;
  transform: translateX(3px);
  box-shadow: 0 4px 14px rgba(0, 122, 255, 0.08);
}

.creator-link-row.tiktok:hover {
  border-color: #000000;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
}

.creator-link-row.instagram:hover {
  border-color: #E1306C;
  box-shadow: 0 4px 14px rgba(225, 48, 108, 0.1);
}

.creator-link-row.discord:hover {
  border-color: #5865F2;
  box-shadow: 0 4px 14px rgba(88, 101, 242, 0.15);
}

/* CARD DE APOYO DISCORD (retirada: el acceso a Discord ya esta en la columna del creador) */
.link-icon-box {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.link-icon-box.discord {
  background: #5865F2;
  color: #FFFFFF;
}

.link-icon-box.blue {
  background: #EBF5FF;
  color: #007AFF;
}

.link-icon-box.black {
  background: #000000;
  color: #FFFFFF;
}

.link-icon-box.pink {
  background: linear-gradient(135deg, #833AB4, #FD1D1D, #FCB045);
  color: #FFFFFF;
}

.link-meta {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.link-title {
  font-size: 13.5px;
  font-weight: 700;
  color: #0F172A;
}

.link-sub {
  font-size: 12px;
  color: var(--ios-text-muted);
}

.link-arrow {
  font-size: 12px;
  color: #94A3B8;
  transition: transform 0.2s ease, color 0.2s ease;
}

.creator-link-row:hover .link-arrow {
  color: #0F172A;
  transform: translate(2px, -2px);
}

@media (max-width: 900px) {
  .support-container-clean {
    grid-template-columns: 1fr;
    gap: 36px;
    padding: 32px 24px;
  }
  .support-divider {
    display: none;
  }
  .binance-content {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
