<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import rawPoints from './logoPoints.json'

const canvasRef = ref<HTMLCanvasElement | null>(null)
let animationId = 0

interface Particle {
  baseX: number
  baseY: number
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  color: string
  alpha: number
  phase: number
}

const particles: Particle[] = []
const mouse = { x: -9999, y: -9999, radius: 75, active: false }

const colors = [
  '#38BDF8', // Sky 400
  '#22D3EE', // Cyan 400
  '#007AFF', // Apple iOS Blue
  '#67E8F9', // Cyan 300
  '#E0F2FE', // Ice White
]

function initParticles(width: number, height: number) {
  particles.length = 0
  
  // Calculate scale and centering based on canvas size
  const scale = Math.min(width, height) / 400
  const offsetX = (width - 400 * scale) / 2
  const offsetY = (height - 400 * scale) / 2

  for (let i = 0; i < rawPoints.length; i++) {
    const [ptX, ptY] = rawPoints[i]
    const targetX = offsetX + ptX * scale
    const targetY = offsetY + ptY * scale

    // Particles start spread out or gently dispersed
    const angle = Math.random() * Math.PI * 2
    const dist = 50 + Math.random() * 120

    particles.push({
      baseX: targetX,
      baseY: targetY,
      x: targetX + Math.cos(angle) * dist,
      y: targetY + Math.sin(angle) * dist,
      vx: (Math.random() - 0.5) * 2,
      vy: (Math.random() - 0.5) * 2,
      radius: Math.random() > 0.85 ? 2.6 : Math.random() > 0.4 ? 1.8 : 1.2,
      color: colors[Math.floor(Math.random() * colors.length)],
      alpha: 0.6 + Math.random() * 0.4,
      phase: Math.random() * Math.PI * 2
    })
  }
}

function handleMouseMove(e: MouseEvent) {
  if (!canvasRef.value) return
  const rect = canvasRef.value.getBoundingClientRect()
  mouse.x = e.clientX - rect.left
  mouse.y = e.clientY - rect.top
  mouse.active = true
}

function handleMouseLeave() {
  mouse.x = -9999
  mouse.y = -9999
  mouse.active = false
}

function handleTouchMove(e: TouchEvent) {
  if (!canvasRef.value || !e.touches[0]) return
  const rect = canvasRef.value.getBoundingClientRect()
  mouse.x = e.touches[0].clientX - rect.left
  mouse.y = e.touches[0].clientY - rect.top
  mouse.active = true
}

function render() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const width = canvas.width
  const height = canvas.height
  const time = performance.now() * 0.002

  // Clear with transparent subtle backdrop
  ctx.clearRect(0, 0, width, height)

  // Energy pulse position moving in a loop across indices
  const pulseCenter = (performance.now() * 0.15) % particles.length

  for (let i = 0; i < particles.length; i++) {
    const p = particles[i]

    // Breathing motion around base position
    const breatheX = Math.sin(time + p.phase) * 1.5
    const breatheY = Math.cos(time + p.phase * 1.2) * 1.5
    const targetX = p.baseX + breatheX
    const targetY = p.baseY + breatheY

    // Mouse repulsion physics
    const dx = p.x - mouse.x
    const dy = p.y - mouse.y
    const distance = Math.sqrt(dx * dx + dy * dy)

    if (distance < mouse.radius && mouse.active) {
      const force = (1 - distance / mouse.radius) * 8
      const angle = Math.atan2(dy, dx)
      p.vx += Math.cos(angle) * force
      p.vy += Math.sin(angle) * force
    }

    // Spring force back to target
    const springX = (targetX - p.x) * 0.08
    const springY = (targetY - p.y) * 0.08

    p.vx = (p.vx + springX) * 0.82
    p.vy = (p.vy + springY) * 0.82

    p.x += p.vx
    p.y += p.vy

    // Energy pulse brightness boost
    const distToPulse = Math.abs(i - pulseCenter)
    const isPulseNear = distToPulse < 35 || distToPulse > particles.length - 35
    const pulseBoost = isPulseNear ? 1.6 : 1.0

    // Draw particle
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.radius * pulseBoost, 0, Math.PI * 2)
    ctx.fillStyle = p.color
    ctx.globalAlpha = Math.min(1, p.alpha * (isPulseNear ? 1 : 0.85))
    
    if (isPulseNear || p.radius > 2.0) {
      ctx.shadowBlur = 10
      ctx.shadowColor = '#38BDF8'
    } else {
      ctx.shadowBlur = 0
    }
    
    ctx.fill()
  }

  // Draw delicate constellation threads between close neighbors
  ctx.shadowBlur = 0
  const connectDist = 18
  for (let i = 0; i < particles.length; i += 2) {
    for (let j = i + 1; j < Math.min(i + 8, particles.length); j++) {
      const p1 = particles[i]
      const p2 = particles[j]
      const d = Math.hypot(p1.x - p2.x, p1.y - p2.y)
      if (d < connectDist) {
        ctx.beginPath()
        ctx.moveTo(p1.x, p1.y)
        ctx.lineTo(p2.x, p2.y)
        ctx.strokeStyle = '#38BDF8'
        ctx.globalAlpha = (1 - d / connectDist) * 0.28
        ctx.lineWidth = 0.8
        ctx.stroke()
      }
    }
  }

  ctx.globalAlpha = 1
  animationId = requestAnimationFrame(render)
}

function handleResize() {
  const canvas = canvasRef.value
  if (!canvas) return
  const container = canvas.parentElement
  if (!container) return

  const size = Math.min(container.clientWidth, 400)
  canvas.width = size
  canvas.height = size
  initParticles(size, size)
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
  animationId = requestAnimationFrame(render)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  cancelAnimationFrame(animationId)
})
</script>

<template>
  <div class="logo-canvas-container">
    <div class="canvas-ambient-glow"></div>
    <canvas
      ref="canvasRef"
      class="logo-canvas"
      @mousemove="handleMouseMove"
      @mouseleave="handleMouseLeave"
      @touchmove="handleTouchMove"
      @touchend="handleMouseLeave"
    ></canvas>
  </div>
</template>

<style scoped>
.logo-canvas-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 280px;
  margin: 0 auto;
}

.canvas-ambient-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 210px;
  height: 210px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.12) 0%, rgba(0, 122, 255, 0.04) 50%, transparent 70%);
  pointer-events: none;
  filter: blur(20px);
  z-index: 0;
}

.logo-canvas {
  position: relative;
  z-index: 1;
  display: block;
  cursor: default;
  background: transparent;
  user-select: none;
  touch-action: none;
  filter: drop-shadow(0 8px 20px rgba(0, 122, 255, 0.15));
}
</style>
