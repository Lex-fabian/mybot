<template>
  <footer class="footer">
    <div class="container footer-container">
      <div class="footer-left">
        <div class="footer-brand">
          <img src="/icono.png" alt="MyBot" class="footer-icon" />
          <span class="footer-name">MyBot</span>
          <span class="footer-badge">v1.1</span>
        </div>
        <p class="footer-desc">
          Software libre y ligero para lectura de voz e interactividad en transmisiones de TikTok Live.
        </p>
        <div class="footer-author">
          <span>Desarrollado por <strong>i.am.lex</strong></span>
          <span class="footer-dot">•</span>
          <a href="https://web-lex.vercel.app/" target="_blank" rel="noopener" class="footer-link">Sitio Web</a>
          <span class="footer-dot">•</span>
          <a href="https://www.tiktok.com/@l.am.lex_?is_from_webapp=1&sender_device=pc" target="_blank" rel="noopener" class="footer-link">TikTok</a>
          <span class="footer-dot">•</span>
          <a href="https://www.instagram.com/l.am.lex_/" target="_blank" rel="noopener" class="footer-link">Instagram</a>
        </div>
      </div>

      <div class="footer-right">
        <span class="copyright">© 2026 MyBot v1.0 • Desarrollado por <strong>i.am.lex</strong></span>
        <span class="disclaimer">
          TikTok es una marca registrada de ByteDance Ltd. MyBot es un proyecto independiente desarrollado para la comunidad.
        </span>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  padding: 40px 0;
  background: #FFFFFF;
  border-top: 1px solid var(--ios-border);
}

.footer-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.footer-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.footer-icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
}

.footer-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--ios-blue);
}

.footer-badge {
  font-size: 10px;
  font-weight: 700;
  color: var(--ios-blue);
  background: var(--ios-blue-light);
  padding: 1px 6px;
  border-radius: var(--radius-pill);
}

.footer-desc {
  font-size: 12px;
  color: var(--ios-text-secondary);
}

.footer-author {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--ios-text-primary);
  margin-top: 4px;
  flex-wrap: wrap;
}

.footer-dot {
  color: var(--ios-text-muted);
  opacity: 0.5;
}

.footer-link {
  color: var(--ios-blue);
  text-decoration: none;
  font-weight: 600;
  transition: opacity var(--transition);
}

.footer-link:hover {
  text-decoration: underline;
  opacity: 0.8;
}

.footer-right {
  display: flex;
  flex-direction: column;
  text-align: right;
  gap: 4px;
}

.copyright {
  font-size: 12px;
  font-weight: 600;
  color: var(--ios-text-secondary);
}

.disclaimer {
  font-size: 11px;
  color: var(--ios-text-muted);
  max-width: 480px;
}

@media (max-width: 768px) {
  .footer-right {
    text-align: left;
  }
}
</style>
