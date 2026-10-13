<script setup lang="ts">
import { ref } from 'vue'
import Navbar from './components/Navbar.vue'
import HeroSection from './components/HeroSection.vue'
import Features from './components/Features.vue'
import UserGuide from './components/UserGuide.vue'
import SupportAndCreator from './components/SupportAndCreator.vue'
import Footer from './components/Footer.vue'

const showBinanceModal = ref(false)

function scrollToDonations() {
  const el = document.getElementById('donar')
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  } else {
    showBinanceModal.value = true
  }
}
</script>

<template>
  <div class="landing-page">
    <Navbar @open-binance="scrollToDonations" />
    <main>
      <HeroSection @open-binance="scrollToDonations" />
      <Features />
      <UserGuide />
      <SupportAndCreator />
    </main>
    <Footer />
  </div>
</template>

<style scoped>
.landing-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
}
</style>
