<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { APP_VERSION_NAME } from '../version'
import { auth, loginWithGoogle, logoutFirebase, onAuthStateChanged, type User } from '../utils/firebase'

defineEmits<{
  (e: 'open-binance'): void
}>()

const currentUser = ref<User | null>(null)
const isLoggingIn = ref(false)
const showUserMenu = ref(false)
let syncInterval: number | null = null

async function sincronizarConAppEscritorio(user: User | null) {
  if (!user) return
  const payload = {
    uid: user.uid,
    email: user.email || '',
    displayName: user.displayName || user.email?.split('@')[0] || 'Usuario',
    photoURL: user.photoURL || ''
  }
  try {
    await fetch('http://127.0.0.1:58421/api/auth/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
  } catch {
    // App de escritorio cerrada; se ignora silenciosamente
  }
}

onMounted(() => {
  onAuthStateChanged(auth, (user) => {
    currentUser.value = user
    if (user) {
      sincronizarConAppEscritorio(user)
    }
  })

  syncInterval = window.setInterval(() => {
    if (currentUser.value) {
      sincronizarConAppEscritorio(currentUser.value)
    }
  }, 4000)
})

onUnmounted(() => {
  if (syncInterval) {
    clearInterval(syncInterval)
  }
})

async function handleLogin() {
  if (isLoggingIn.value) return
  isLoggingIn.value = true
  try {
    await loginWithGoogle()
  } catch (err: any) {
    if (err?.code !== 'auth/popup-closed-by-user') {
      console.error('Error al iniciar sesión:', err)
      alert('No se pudo iniciar sesión con Google. Por favor, intenta nuevamente.')
    }
  } finally {
    isLoggingIn.value = false
  }
}

async function handleLogout() {
  try {
    await logoutFirebase()
    showUserMenu.value = false
  } catch (err) {
    console.error('Error al cerrar sesión:', err)
  }
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
        <!-- Usuario Autenticado -->
        <div v-if="currentUser" class="user-profile-wrapper">
          <button 
            type="button" 
            class="user-profile-btn" 
            @click="showUserMenu = !showUserMenu"
            :title="currentUser.email || currentUser.displayName || 'Mi Perfil'"
          >
            <img 
              v-if="currentUser.photoURL" 
              :src="currentUser.photoURL" 
              alt="Avatar" 
              class="user-avatar" 
              referrerpolicy="no-referrer"
            />
            <span v-else class="user-avatar-placeholder">
              <i class="fa-solid fa-user"></i>
            </span>
            <span class="user-display-name">{{ currentUser.displayName?.split(' ')[0] || 'Usuario' }}</span>
            <i class="fa-solid fa-chevron-down caret-icon" :class="{ rotate: showUserMenu }"></i>
          </button>

          <!-- Dropdown Menú -->
          <div v-if="showUserMenu" class="user-dropdown-menu">
            <div class="dropdown-header">
              <span class="dropdown-name">{{ currentUser.displayName || 'Usuario MyBot' }}</span>
              <span class="dropdown-email">{{ currentUser.email }}</span>
            </div>
            <div class="dropdown-divider"></div>
            <button type="button" class="dropdown-item logout-item" @click="handleLogout">
              <i class="fa-solid fa-arrow-right-from-bracket"></i>
              <span>Cerrar Sesión</span>
            </button>
          </div>
        </div>

        <!-- Usuario No Autenticado -->
        <button
          v-else
          type="button"
          class="btn btn-primary btn-sm btn-login"
          :disabled="isLoggingIn"
          @click="handleLogin"
        >
          <i v-if="isLoggingIn" class="fa-solid fa-circle-notch fa-spin"></i>
          <i v-else class="fa-brands fa-google"></i>
          <span>{{ isLoggingIn ? 'Iniciando...' : 'Iniciar Sesión' }}</span>
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
  position: relative;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 13px;
  border-radius: var(--radius-pill);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-login {
  background: #0f172a;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
  font-weight: 600;
}

.btn-login:hover {
  background: #1e293b;
  transform: translateY(-1px);
}

/* User profile */
.user-profile-wrapper {
  position: relative;
}

.user-profile-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px 4px 5px;
  background: #f1f5f9;
  border: 1px solid var(--ios-border);
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: all var(--transition);
  color: var(--ios-text-primary);
  font-size: 13px;
  font-weight: 600;
}

.user-profile-btn:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
}

.user-avatar-placeholder {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--ios-blue);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.user-display-name {
  max-width: 110px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.caret-icon {
  font-size: 10px;
  color: var(--ios-text-secondary);
  transition: transform 0.2s ease;
}

.caret-icon.rotate {
  transform: rotate(180deg);
}

/* Dropdown */
.user-dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 210px;
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid var(--ios-border);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
  padding: 8px;
  z-index: 100;
  animation: fadeInDown 0.18s ease-out;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
  }
}

.dropdown-header {
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dropdown-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--ios-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-email {
  font-size: 11px;
  color: var(--ios-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-divider {
  height: 1px;
  background: var(--ios-border);
  margin: 6px 0;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  font-size: 12.5px;
  font-weight: 500;
  border: none;
  background: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.logout-item {
  color: #ef4444;
}

.logout-item:hover {
  background: #fef2f2;
}

@media (max-width: 768px) {
  .nav-links {
    display: none;
  }
}
</style>
