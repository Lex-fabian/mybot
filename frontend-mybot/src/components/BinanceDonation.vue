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
  <section class="binance-section" id="donar">
    <div class="container">
      <div class="binance-card card">
        <h2 class="binance-title">Apoyar el Proyecto</h2>
        <p class="binance-subtitle">
          Donaciones voluntarias a través de Binance Pay para apoyar el desarrollo continuo de MyBot.
        </p>

        <div class="binance-content">
          <div class="qr-wrapper">
            <img src="/binance-qr.svg" alt="Binance QR" class="qr-img" />
          </div>

          <div class="pay-info">
            <div class="alias-tag">
              <span>Usuario:</span>
              <strong>{{ binanceAlias }}</strong>
            </div>

            <div class="copy-row">
              <span class="uid-label">UID:</span>
              <input type="text" :value="binancePayId" readonly class="uid-input" />
              <button class="btn btn-binance btn-sm" @click="copyToClipboard">
                {{ copied ? '✓ Copiado' : 'Copiar UID' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.binance-section {
  padding: 40px 0 60px;
}

.binance-card {
  max-width: 580px;
  margin: 0 auto;
  padding: 36px 32px;
  text-align: center;
  background: #FFFFFF;
  border: 1px solid var(--ios-border);
}

.binance-title {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--ios-text-primary);
  margin-bottom: 8px;
}

.binance-subtitle {
  font-size: 14px;
  color: var(--ios-text-secondary);
  margin-bottom: 28px;
  line-height: 1.5;
}

.binance-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.qr-wrapper {
  background: #FFFFFF;
  padding: 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--ios-border);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
}

.qr-img {
  width: 160px;
  height: 160px;
  display: block;
}

.pay-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.alias-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #8A6500;
  background: #FEF9E7;
  padding: 4px 12px;
  border-radius: var(--radius-pill);
}

.copy-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  max-width: 380px;
}

.uid-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--ios-text-secondary);
}

.uid-input {
  flex: 1;
  background: #F8FAFC;
  border: 1px solid var(--ios-border);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  font-size: 14px;
  font-weight: 700;
  text-align: center;
  color: var(--ios-text-primary);
  outline: none;
}

.btn-binance {
  padding: 8px 16px;
  font-size: 13px;
  white-space: nowrap;
}
</style>
