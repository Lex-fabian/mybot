<script setup lang="ts">
import { APP_VERSION_NAME } from '../version'

defineEmits<{
  (e: 'open-binance'): void
}>()

function handleLogin() {
  alert('El panel de inicio de sesión de MyBot estará disponible muy pronto.')
}
</script>

<template>
  <header class="navbar">
    <div class="container nav-container">
      <a href="#" class="brand">
        <img src="/icono.png" alt="MyBot" class="brand-icon" />
        <div class="brand-text">
          <span class="brand-title">MyBot</span>
          <span class="brand-badge">{{ APP_VERSION_NAME }}</span>
        </div>
      </a>

      <nav class="nav-links">
        <a href="#caracteristicas" class="nav-link">Características</a>
        <a href="#guia" class="nav-link">Guía de Uso</a>
        <a href="#donar" class="nav-link" @click.prevent="$emit('open-binance')">Donaciones & Creador</a>
      </nav>

      <div class="nav-actions">
        <button
          type="button"
          class="btn btn-primary btn-sm btn-login"
          @click="handleLogin"
        >
          <i class="fa-solid fa-user"></i>
          <span>Iniciar Sesión</span>
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--ios-border);
  padding: 12px 0;
}

.nav-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.brand-icon {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  box-shadow: 0 4px 10px rgba(0, 122, 255, 0.2);
}

.brand-text {
  display: flex;
  align-items: center;
  gap: 8px;
}

.brand-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--ios-blue);
  letter-spacing: -0.01em;
}

.brand-badge {
  font-size: 10px;
  font-weight: 700;
  color: var(--ios-blue);
  background: var(--ios-blue-light);
  padding: 2px 7px;
  border-radius: var(--radius-pill);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 24px;
}

.nav-link {
  font-size: 14px;
  font-weight: 500;
  color: var(--ios-text-secondary);
  text-decoration: none;
  transition: color var(--transition);
}

.nav-link:hover {
  color: var(--ios-blue);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 13px;
}

.btn-nav-download {
  position: relative;
  overflow: hidden;
  min-width: 150px;
  justify-content: center;
  transition: all var(--transition);
}

.btn-nav-text {
  position: relative;
  z-index: 2;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.nav-progress-fill {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.35);
  transition: width 0.15s ease-out;
  z-index: 1;
}

.btn-nav-download.btn-done {
  background: var(--ios-green) !important;
}

@media (max-width: 768px) {
  .nav-links {
    display: none;
  }
}
</style>
