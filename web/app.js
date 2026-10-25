/**
 * ============================================================================
 *  MyBot — Lógica del Frontend Web (JavaScript ES6)
 * ============================================================================
 */

(function () {
  "use strict";

  let splashAnimId = null;

  // Estado global de la aplicación
  const state = {
    connected: false,
    authUser: null,
    ws: null,
    config: {},
    voicesEdge: [],
    voicesSapi5: [],
    voicesPiper: [],
    catalogoPiper: [],
    presets: {},
    sounds: [],
    updateInfo: null,
    stats: { comments: 0, gifts: 0, diamonds: 0 }
  };

  // Versión de esta aplicación y servidor de actualizaciones
  let VERSION_ACTUAL = "1.3.3";
  const UPDATE_URL = "https://mybot-79861.web.app/version.json";

  function parsearVersion(v) {
    const partes = String(v || "").replace(/[^\d.]/g, "").split(".").filter(p => p !== "");
    return partes.map(n => parseInt(n, 10) || 0);
  }

  function esVersionMayor(remota, local) {
    const a = parsearVersion(remota);
    const b = parsearVersion(local);
    for (let i = 0; i < Math.max(a.length, b.length); i++) {
      const x = a[i] || 0;
      const y = b[i] || 0;
      if (x > y) return true;
      if (x < y) return false;
    }
    return false;
  }

  // Referencias a elementos del DOM
  const dom = {
    splash: document.getElementById("splashScreen"),
    splashBar: document.getElementById("splashProgressBar"),
    splashStatus: document.getElementById("splashStatusText"),
    
    // Header & Estado
    topTtsStatus: document.getElementById("topTtsStatus"),
    topTtsStatusText: document.getElementById("topTtsStatusText"),
    
    // Conexión
    tiktokUser: document.getElementById("tiktokUser"),
    btnConnect: document.getElementById("btnConnect"),
    btnDisconnect: document.getElementById("btnDisconnect"),
    connStatusPill: document.getElementById("connStatusPill"),
    connStatusText: document.getElementById("connStatusText"),

    // Autenticación Google Firebase
    btnHeaderLogin: document.getElementById("btnHeaderLogin"),
    authUserPill: document.getElementById("authUserPill"),
    authUserAvatar: document.getElementById("authUserAvatar"),
    authUserName: document.getElementById("authUserName"),
    btnHeaderLogout: document.getElementById("btnHeaderLogout"),
    authGateBanner: document.getElementById("authGateBanner"),
    btnAuthGateLogin: document.getElementById("btnAuthGateLogin"),
    
    // Métricas
    statComments: document.getElementById("statComments"),
    statGifts: document.getElementById("statGifts"),
    statDiamonds: document.getElementById("statDiamonds"),
    
    // Pestañas
    tabButtons: document.querySelectorAll(".segment-btn"),
    tabPanes: document.querySelectorAll(".tab-pane"),
    
    // Chat
    chatFeed: document.getElementById("chatFeed"),
    btnClearChat: document.getElementById("btnClearChat"),
    btnMuteAudio: document.getElementById("btnMuteAudio"),
    queueCount: document.getElementById("queueCount"),
    
    // Voz & Presets
    selectEngine: document.getElementById("selectEngine"),
    selectVoice: document.getElementById("selectVoice"),
    voiceModelPanel: document.getElementById("voiceModelPanel"),
    voiceModelTitle: document.getElementById("voiceModelTitle"),
    voiceModelDesc: document.getElementById("voiceModelDesc"),
    voiceModelHint: document.getElementById("voiceModelHint"),
    btnVoiceModelDownload: document.getElementById("btnVoiceModelDownload"),
    voiceModelProgressWrap: document.getElementById("voiceModelProgressWrap"),
    voiceModelProgressBar: document.getElementById("voiceModelProgressBar"),
    voiceModelProgressText: document.getElementById("voiceModelProgressText"),
    selectPreset: document.getElementById("selectPreset"),
    presetDesc: document.getElementById("presetDesc"),
    rangeTone: document.getElementById("rangeTone"),
    lblToneValue: document.getElementById("lblToneValue"),
    rangeSpeed: document.getElementById("rangeSpeed"),
    lblSpeedValue: document.getElementById("lblSpeedValue"),
    rangeVolume: document.getElementById("rangeVolume"),
    lblVolumeValue: document.getElementById("lblVolumeValue"),
    chkReadUsername: document.getElementById("chkReadUsername"),
    txtUserFormat: document.getElementById("txtUserFormat"),
    txtTestVoice: document.getElementById("txtTestVoice"),
    btnTestVoice: document.getElementById("btnTestVoice"),
    btnDownloadVoice: document.getElementById("btnDownloadVoice"),
    testStatusBadge: document.getElementById("testStatusBadge"),
    testStatusDetail: document.getElementById("testStatusDetail"),
    
    // Donaciones
    chkDonationsActive: document.getElementById("chkDonationsActive"),
    chkWaitStreak: document.getElementById("chkWaitStreak"),
    numMinDiamonds: document.getElementById("numMinDiamonds"),
    btnDecDiamond: document.getElementById("btnDecDiamond"),
    btnIncDiamond: document.getElementById("btnIncDiamond"),
    chkReadDonation: document.getElementById("chkReadDonation"),
    txtDonationPrefix: document.getElementById("txtDonationPrefix"),
    txtDonationTemplate: document.getElementById("txtDonationTemplate"),
    chkSoundActive: document.getElementById("chkSoundActive"),
    selectSound: document.getElementById("selectSound"),
    btnTestDonation: document.getElementById("btnTestDonation"),
    chkMediaActionActive: document.getElementById("chkMediaActionActive"),
    selectMediaAction: document.getElementById("selectMediaAction"),
    numMediaMinDiamonds: document.getElementById("numMediaMinDiamonds"),
    btnDecMediaDiamond: document.getElementById("btnDecMediaDiamond"),
    btnIncMediaDiamond: document.getElementById("btnIncMediaDiamond"),
    btnTestMediaNext: document.getElementById("btnTestMediaNext"),
    btnTestMediaPrev: document.getElementById("btnTestMediaPrev"),
    btnTestMediaPlayPause: document.getElementById("btnTestMediaPlayPause"),

    // Bienvenidas
    chkWelcomeActive: document.getElementById("chkWelcomeActive"),
    chkWelcomeChat: document.getElementById("chkWelcomeChat"),
    chkWelcomeVoice: document.getElementById("chkWelcomeVoice"),
    chkWelcomeAntiRepeat: document.getElementById("chkWelcomeAntiRepeat"),
    txtWelcomeTemplate: document.getElementById("txtWelcomeTemplate"),
    numWelcomeCooldown: document.getElementById("numWelcomeCooldown"),
    btnDecWelcomeCooldown: document.getElementById("btnDecWelcomeCooldown"),
    btnIncWelcomeCooldown: document.getElementById("btnIncWelcomeCooldown"),
    txtTestWelcomeUser: document.getElementById("txtTestWelcomeUser"),
    btnTestWelcome: document.getElementById("btnTestWelcome"),
    
    // Filtros
    txtBannedWords: document.getElementById("txtBannedWords"),
    numMaxChars: document.getElementById("numMaxChars"),
    numMaxQueue: document.getElementById("numMaxQueue"),
    chkIgnoreRepeated: document.getElementById("chkIgnoreRepeated"),
    numRepeatTimeout: document.getElementById("numRepeatTimeout"),
    btnDecRepeatTimeout: document.getElementById("btnDecRepeatTimeout"),
    btnIncRepeatTimeout: document.getElementById("btnIncRepeatTimeout"),
    chkCleanUsernames: document.getElementById("chkCleanUsernames"),
    chkDynamicSpeed: document.getElementById("chkDynamicSpeed"),
    numQueueTtl: document.getElementById("numQueueTtl"),
    btnDecQueueTtl: document.getElementById("btnDecQueueTtl"),
    btnIncQueueTtl: document.getElementById("btnIncQueueTtl"),
    chkFilterLinks: document.getElementById("chkFilterLinks"),
    chkCompactEmojis: document.getElementById("chkCompactEmojis"),
    chkAutoReconnect: document.getElementById("chkAutoReconnect"),
    btnSaveConfig: document.getElementById("btnSaveConfig"),
    // Toasts
    toastContainer: document.getElementById("toastContainer"),

    // Modales de Binance y Actualización
    btnOpenBinance: document.getElementById("btnOpenBinance"),
    btnCloseBinance: document.getElementById("btnCloseBinance"),
    modalBinance: document.getElementById("modalBinance"),
    binancePayIdVal: document.getElementById("binancePayIdVal"),
    btnCopyPayId: document.getElementById("btnCopyPayId"),

    btnCheckUpdate: document.getElementById("btnCheckUpdate"),
    appBadgeVersion: document.querySelector(".app-badge-version"),
    footerVersion: document.querySelector(".footer-version"),
    btnCloseUpdate: document.getElementById("btnCloseUpdate"),
    modalUpdate: document.getElementById("modalUpdate"),
    btnDownloadUpdate: document.getElementById("btnDownloadUpdate"),
    btnInstallUpdate: document.getElementById("btnInstallUpdate"),
    btnLaterUpdate: document.getElementById("btnLaterUpdate"),
    lblCurrentVersion: document.getElementById("lblCurrentVersion"),
    lblNewVersion: document.getElementById("lblNewVersion"),
    updateChangelogList: document.getElementById("updateChangelogList"),
    updateProgressBox: document.getElementById("updateProgressBox"),
    updateProgressStatus: document.getElementById("updateProgressStatus"),
    updateProgressPercent: document.getElementById("updateProgressPercent"),
    updateProgressBar: document.getElementById("updateProgressBar"),
    updateProgressDetail: document.getElementById("updateProgressDetail"),
    updateProgressSpeed: document.getElementById("updateProgressSpeed")
  };

  /* ==========================================================================
     1. SECUENCIA DE SPLASH SCREEN iOS & LOGO EN PUNTOS
     ========================================================================== */
  function iniciarCanvasPuntos() {
    const canvas = document.getElementById("splashLogoCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    fetch("logoPoints.json")
      .then(res => res.json())
      .then(rawPoints => {
        const particles = [];
        const scale = canvas.width / 400;
        const colors = ["#38BDF8", "#22D3EE", "#007AFF", "#67E8F9", "#FFFFFF"];

        for (let i = 0; i < rawPoints.length; i++) {
          const [ptX, ptY] = rawPoints[i];
          const tx = ptX * scale;
          const ty = ptY * scale;
          const angle = Math.random() * Math.PI * 2;
          const dist = 30 + Math.random() * 60;
          particles.push({
            baseX: tx,
            baseY: ty,
            x: tx + Math.cos(angle) * dist,
            y: ty + Math.sin(angle) * dist,
            vx: 0,
            vy: 0,
            radius: Math.random() > 0.85 ? 2.2 : 1.3,
            color: colors[Math.floor(Math.random() * colors.length)],
            alpha: 0.5 + Math.random() * 0.5,
            phase: Math.random() * Math.PI * 2
          });
        }

        function render() {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          const time = performance.now() * 0.0025;
          const pulse = (performance.now() * 0.12) % particles.length;

          for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            const targetX = p.baseX + Math.sin(time + p.phase) * 1.2;
            const targetY = p.baseY + Math.cos(time + p.phase) * 1.2;

            p.vx = (p.vx + (targetX - p.x) * 0.09) * 0.82;
            p.vy = (p.vy + (targetY - p.y) * 0.09) * 0.82;
            p.x += p.vx;
            p.y += p.vy;

            const isPulse = Math.abs(i - pulse) < 25;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius * (isPulse ? 1.5 : 1), 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.globalAlpha = Math.min(1, p.alpha * (isPulse ? 1 : 0.85));
            if (isPulse || p.radius > 1.8) {
              ctx.shadowBlur = 8;
              ctx.shadowColor = "#38BDF8";
            } else {
              ctx.shadowBlur = 0;
            }
            ctx.fill();
          }

          splashAnimId = requestAnimationFrame(render);
        }
        splashAnimId = requestAnimationFrame(render);
      })
      .catch(err => {
        console.warn("No se pudieron cargar los puntos del logo:", err);
      });
  }

  function detenerCanvasPuntos() {
    if (splashAnimId) {
      cancelAnimationFrame(splashAnimId);
      splashAnimId = null;
    }
    const canvas = document.getElementById("splashLogoCanvas");
    if (canvas) {
      const ctx = canvas.getContext("2d");
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  function iniciarSplashScreen() {
    iniciarCanvasPuntos();

    const pasos = [
      { pct: 25, txt: "Inicializando motor de audio..." },
      { pct: 55, txt: "Cargando voces neuronales offline..." },
      { pct: 85, txt: "Sincronizando configuración de usuario..." },
      { pct: 100, txt: "MyBot listo." }
    ];

    let pasoIdx = 0;
    const intervalo = setInterval(() => {
      if (pasoIdx < pasos.length) {
        const p = pasos[pasoIdx];
        dom.splashBar.style.width = p.pct + "%";
        dom.splashStatus.textContent = p.txt;
        pasoIdx++;
      } else {
        clearInterval(intervalo);
        setTimeout(() => {
          dom.splash.classList.add("fade-out");
          setTimeout(() => {
            detenerCanvasPuntos();
            if (dom.splash) dom.splash.style.display = "none";
          }, 400);
        }, 350);
      }
    }, 280);
  }

  /* ==========================================================================
     2. GESTIÓN DE PESTAÑAS (SEGMENTED CONTROL iOS)
     ========================================================================== */
  function setupTabs() {
    dom.tabButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        const targetId = btn.getAttribute("data-tab");
        
        dom.tabButtons.forEach(b => b.classList.remove("active"));
        dom.tabPanes.forEach(p => p.classList.remove("active"));
        
        btn.classList.add("active");
        const targetPane = document.getElementById(targetId);
        if (targetPane) targetPane.classList.add("active");
      });
    });
  }

  /* ==========================================================================
     3. WEBSOCKET CLIENT BIDIRECCIONAL
     ========================================================================== */
  function setupWebSocket() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    // Token inyectado por el backend: impide que una página web externa se
    // conecte al servidor local y controle el bot.
    const metaToken = document.querySelector('meta[name="mybot-token"]');
    const token = metaToken ? metaToken.content.trim() : "";

    // Una página antigua de la caché de WebView2 no trae el token y el servidor
    // rechaza su WebSocket. Se recarga una sola vez con una URL sin caché.
    if (!token || token === "__MYBOT_TOKEN__") {
      if (!sessionStorage.getItem("mybot_token_reload")) {
        sessionStorage.setItem("mybot_token_reload", "1");
        const url = new URL(location.href);
        url.searchParams.set("v", String(Date.now()));
        location.replace(url.toString());
        return;
      }
      document.body.dataset.ws = "sin-token";
      showToast("La interfaz está desactualizada. Cierra y vuelve a abrir MyBot.");
      return;
    }

    const wsUrl = `${protocol}//${location.host}/ws?token=${encodeURIComponent(token)}`;

    const ws = new WebSocket(wsUrl);
    state.ws = ws;

    ws.onopen = () => {
      document.body.dataset.ws = "open";
      sessionStorage.removeItem("mybot_token_reload");
      console.log("[WS] Conectado al backend de MyBot.");
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleServerMessage(msg);
      } catch (e) {
        console.error("[WS] Error parseando mensaje:", e);
      }
    };

    ws.onclose = () => {
      document.body.dataset.ws = "closed";
      console.warn("[WS] Desconectado. Reintentando en 2 segundos...");
      setTimeout(setupWebSocket, 2000);
    };

    ws.onerror = (err) => {
      document.body.dataset.ws = "error";
      console.error("[WS] Error en socket:", err);
    };
  }

  function sendAction(action, payload = {}) {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
      state.ws.send(JSON.stringify({ action, ...payload }));
    } else {
      showToast("Sin conexión con el servidor de MyBot");
    }
  }

  // Abre un enlace en el navegador del sistema. Dentro de la aplicación de
  // escritorio se usa el puente de pywebview (window.pywebview.api); si la
  // interfaz se abre en un navegador normal, se abre una pestaña nueva.
  function abrirEnlaceExterno(url) {
    const api = window.pywebview && window.pywebview.api;
    if (api && typeof api.open_external === "function") {
      api.open_external(String(url));
      return;
    }
    window.open(url, "_blank");
  }

  /* ==========================================================================
     4. MANEJADOR DE MENSAJES DEL SERVIDOR
     ========================================================================== */
  function handleServerMessage(msg) {
    const { type, data } = msg;

    switch (type) {
      case "init":
        state.config = data.config || {};
        if (data.version) {
          VERSION_ACTUAL = String(data.version);
          refrescarVersionUI();
        }
        state.voicesEdge = data.voices_edge || [];
        state.voicesSapi5 = data.voices_sapi5 || [];
        state.voicesPiper = data.voices_piper || [];
        state.catalogoPiper = data.catalogo_piper || [];
        state.presets = data.presets || {};
        state.sounds = data.sounds || [];
        poblarControles();
        actualizarUsuarioAuth(data.auth_user || (state.config && state.config.auth_user) || null);
        break;

      case "auth_state":
        actualizarUsuarioAuth(data.user || null);
        break;

      case "join":
        appendWelcomeBubble(data.user);
        break;

      case "com":
        appendCommentBubble(data.user, data.comment, data.repetido);
        break;

      case "don":
        appendDonationCard(data.user, data.gift, data.count, data.diamonds);
        break;

      case "sis":
        appendSystemBubble("› " + data.message);
        break;

      case "err":
        appendSystemBubble(data.message, true);
        break;

      case "estado":
        actualizarEstadoConexion(data.text, data.status);
        break;

      case "tts_estado":
        actualizarTtsEstado(data.state, data.detail);
        break;

      case "voice_download":
        pintarProgresoVoz(data);
        break;

      case "catalogo_piper":
        actualizarCatalogoPiper(data.catalogo);
        break;

      case "queue":
        if (dom.queueCount) dom.queueCount.textContent = data.count;
        break;

      case "stats":
        state.stats = data;
        dom.statComments.textContent = data.comments;
        dom.statGifts.textContent = data.gifts;
        dom.statDiamonds.textContent = data.diamonds;
        break;

      case "toast":
        showToast(data.message);
        break;

      case "update_progress":
        if (dom.updateProgressBox) dom.updateProgressBox.style.display = "flex";
        if (dom.updateProgressBar) dom.updateProgressBar.style.width = `${data.percent}%`;
        if (dom.updateProgressPercent) dom.updateProgressPercent.textContent = `${data.percent}%`;
        if (dom.updateProgressDetail) dom.updateProgressDetail.textContent = `${data.downloaded_mb} MB / ${data.total_mb} MB`;
        if (dom.updateProgressSpeed) dom.updateProgressSpeed.textContent = data.speed || "";
        if (dom.updateProgressStatus) dom.updateProgressStatus.textContent = data.state === "starting" ? "Conectando al servidor..." : "Descargando actualización en la app...";
        break;

      case "update_ready":
        state.installerPath = data.installer_path;
        if (dom.updateProgressBar) dom.updateProgressBar.style.width = "100%";        if (dom.updateProgressPercent) dom.updateProgressPercent.textContent = "100%";
        if (dom.updateProgressStatus) dom.updateProgressStatus.textContent = "✓ ¡Descarga finalizada!";
        if (dom.btnDownloadUpdate) dom.btnDownloadUpdate.style.display = "none";
        if (dom.btnInstallUpdate) {
          dom.btnInstallUpdate.style.display = "block";
          dom.btnInstallUpdate.focus();
        }
        showToast("✓ Actualización lista. Pulsa 'Iniciar Instalador Ahora'.");
        break;

      case "update_error":
        if (dom.updateProgressStatus) dom.updateProgressStatus.textContent = "❌ Error en la descarga";
        if (dom.btnDownloadUpdate) {
          dom.btnDownloadUpdate.disabled = false;
          dom.btnDownloadUpdate.textContent = "Reintentar Descarga";
        }
        showToast(`Error: ${data.error}`);
        break;

      case "nueva_version":
        procesarActualizacion(data, Boolean(data.manual));
        break;

      case "sin_actualizacion":
        if (data.manual) showToast(`✓ Ya tienes la última versión (v${VERSION_ACTUAL}).`);
        break;

      case "error_actualizacion":
        if (data.manual) showToast("No se pudo comprobar las actualizaciones.");
        console.warn("[Update] Error al comprobar:", data.error);
        break;

      case "app_cerrando":
        // El instalador va a reemplazar los archivos de la aplicacion, asi que hay
        // que cerrarla. Se espera a que el asistente arranque para que el usuario
        // lo vea, y se para el audio para no dejarlo sonando sin interfaz.
        sendAction("mute");
        showToast("Instalador en marcha. MyBot se cerrara para actualizarse...");
        setTimeout(() => {
          const api = window.pywebview && window.pywebview.api;
          if (api && typeof api.cerrar_app === "function") api.cerrar_app();
        }, data.delay_ms || 2500);
        break;
    }
  }

  /* ==========================================================================
     5. ACTUALIZACIÓN VISUAL Y POBLACIÓN DE CONTROLES
     ========================================================================== */

  // Limpia emojis e iconos de nombres para mostrar texto plano y limpio
  function limpiarIconosTexto(str) {
    if (!str) return "";
    return str
      .replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE00}-\u{FE0F}\u{200D}]/gu, "")
      .replace(/^[\s·\-–—]+|[\s·\-–—]+$/g, "")
      .trim();
  }

  function poblarControles() {
    const cfg = state.config;

    // Usuario
    if (cfg.usuario) dom.tiktokUser.value = String(cfg.usuario).replace(/^@+/, "");

    // Motor (Piper offline es el preferido: sin Internet y sin el error 403 de Edge TTS)
    dom.selectEngine.value = cfg.motor || "piper";

    // Presets
    dom.selectPreset.innerHTML = "";
    Object.keys(state.presets).forEach(name => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = limpiarIconosTexto(name) || name;
      dom.selectPreset.appendChild(opt);
    });

    // Voces
    actualizarListaVoces();
    seleccionarVoz(cfg.voz_nombre);

    // Sonidos de alerta (catálogo enviado por el backend)
    if (state.sounds && state.sounds.length) {
      dom.selectSound.innerHTML = "";
      state.sounds.forEach(name => {
        const opt = document.createElement("option");
        opt.value = name;
        opt.textContent = limpiarIconosTexto(name) || name;
        dom.selectSound.appendChild(opt);
      });
    }

    // Sliders
    dom.rangeTone.value = cfg.tono || 0;
    dom.lblToneValue.textContent = `${cfg.tono > 0 ? "+" : ""}${cfg.tono || 0} Hz`;

    dom.rangeSpeed.value = cfg.velocidad || 0;
    dom.lblSpeedValue.textContent = `${cfg.velocidad > 0 ? "+" : ""}${cfg.velocidad || 0}%`;

    dom.rangeVolume.value = cfg.volumen || 100;
    dom.lblVolumeValue.textContent = `${cfg.volumen || 100}%`;

    // Nombre y plantilla
    dom.chkReadUsername.checked = cfg.leer_nombre !== false;
    dom.txtUserFormat.value = cfg.formato_usuario || "{usuario} dice: {mensaje}";

    // Donaciones
    dom.chkDonationsActive.checked = cfg.donaciones_activas !== false;
    dom.chkWaitStreak.checked = cfg.esperar_racha !== false;
    dom.numMinDiamonds.value = cfg.min_diamantes || 1;
    dom.chkReadDonation.checked = cfg.leer_donacion !== false;
    dom.txtDonationTemplate.value = cfg.tpl_donacion || "¡Muchas gracias a {usuario} por enviar {cantidad} {regalo}!";
    if (dom.txtDonationPrefix) {
      const tpl = dom.txtDonationTemplate.value;
      const match = tpl.split(/\{usuario\}/i)[0];
      dom.txtDonationPrefix.value = match ? match.trim() : "¡Muchas gracias a";
    }
    dom.chkSoundActive.checked = cfg.sonido_activo !== false;
    if (cfg.tipo_sonido) dom.selectSound.value = cfg.tipo_sonido;
    if (dom.chkMediaActionActive) dom.chkMediaActionActive.checked = Boolean(cfg.accion_multimedia_activa);
    if (dom.selectMediaAction) dom.selectMediaAction.value = cfg.tipo_accion_multimedia || "next";
    if (dom.numMediaMinDiamonds) dom.numMediaMinDiamonds.value = cfg.min_diamantes_multimedia || 1;

    // Bienvenidas
    if (dom.chkWelcomeActive) dom.chkWelcomeActive.checked = cfg.bienvenidas_activas !== false;
    if (dom.chkWelcomeChat) dom.chkWelcomeChat.checked = cfg.mostrar_bienvenida_chat !== false;
    if (dom.chkWelcomeVoice) dom.chkWelcomeVoice.checked = Boolean(cfg.leer_bienvenida);
    if (dom.chkWelcomeAntiRepeat) dom.chkWelcomeAntiRepeat.checked = cfg.anti_repeticion_bienvenida !== false;
    if (dom.txtWelcomeTemplate) dom.txtWelcomeTemplate.value = cfg.tpl_bienvenida || "¡Bienvenido {usuario} al directo!";
    if (dom.numWelcomeCooldown) dom.numWelcomeCooldown.value = cfg.cooldown_bienvenida || 10;

    // Filtros & Anti-repetición
    dom.txtBannedWords.value = cfg.baneadas || "ejemplo1,ejemplo2,ejemplo3";
    dom.numMaxChars.value = cfg.max_caracteres || 85;
    dom.numMaxQueue.value = cfg.max_cola || 8;
    if (dom.chkIgnoreRepeated) dom.chkIgnoreRepeated.checked = cfg.ignorar_comentarios_repetidos !== false;
    if (dom.numRepeatTimeout) dom.numRepeatTimeout.value = cfg.tiempo_anti_repeticion || 45;
    if (dom.chkCleanUsernames) dom.chkCleanUsernames.checked = cfg.limpiar_nombres_usuarios !== false;
    if (dom.chkDynamicSpeed) dom.chkDynamicSpeed.checked = cfg.aceleracion_dinamica !== false;
    if (dom.numQueueTtl) dom.numQueueTtl.value = cfg.ttl_comentarios_cola || 20;
    dom.chkFilterLinks.checked = cfg.filtrar_links !== false;
    dom.chkCompactEmojis.checked = cfg.compactar_emojis !== false;
    if (dom.chkAutoReconnect) dom.chkAutoReconnect.checked = cfg.auto_reconnect !== false;
  }

  function actualizarListaVoces() {
    const motor = dom.selectEngine.value;
    let lista = state.voicesEdge;
    if (motor === "sapi5") {
      lista = state.voicesSapi5;
    } else if (motor === "piper") {
      lista = (state.catalogoPiper || []).map(v => ({
        id: v.id,
        etiqueta: v.etiqueta,
        instalada: v.instalada,
        descargable: v.descargable,
        mb: v.mb,
        calidad: v.calidad
      }));
    }
    lista = lista || [];

    dom.selectVoice.innerHTML = "";
    lista.forEach(v => {
      const etiqueta = v[0] || v.etiqueta || "";
      const opt = document.createElement("option");
      // El backend resuelve el id real a partir de la etiqueta mostrada.
      opt.value = etiqueta;
      const textoLimpio = limpiarIconosTexto(etiqueta) || etiqueta;
      opt.textContent = v.instalada === false ? `${textoLimpio} · sin descargar` : textoLimpio;
      opt.dataset.vozId = (v.id || v[1] || "");
      opt.dataset.instalada = String(v.instalada !== false);
      opt.dataset.descargable = String(Boolean(v.descargable));
      opt.dataset.mb = String(v.mb || 0);
      opt.dataset.calidad = v.calidad || "";
      dom.selectVoice.appendChild(opt);
    });

    actualizarPanelVoz();
  }

  /* ==========================================================================
     DESCARGA DE LA VOZ NEURONAL OFFLINE
     Los modelos .onnx no se incluyen en el instalador: el usuario los descarga
     desde aquí y la app le indica claramente cuáles faltan.
     ========================================================================== */
  function vozSeleccionadaPendiente() {
    const opt = dom.selectVoice && dom.selectVoice.selectedOptions[0];
    if (!opt || dom.selectEngine.value !== "piper") return null;
    if (opt.dataset.descargable !== "true" || opt.dataset.instalada === "true") return null;
    return opt;
  }

  function actualizarPanelVoz() {
    const panel = dom.voiceModelPanel;
    if (!panel) return;

    const opt = vozSeleccionadaPendiente();
    if (!opt) {
      panel.hidden = true;
      panel.classList.remove("is-listening");
      return;
    }

    panel.hidden = false;
    panel.classList.remove("is-listening");
    if (dom.voiceModelProgressWrap) dom.voiceModelProgressWrap.hidden = true;
    if (dom.btnVoiceModelDownload) {
      dom.btnVoiceModelDownload.hidden = false;
      dom.btnVoiceModelDownload.disabled = false;
      dom.btnVoiceModelDownload.textContent = "⬇️ Descargar voz";
    }
    if (dom.voiceModelTitle) dom.voiceModelTitle.textContent = "Esta voz aún no está descargada";
    if (dom.voiceModelDesc) {
      const mb = parseFloat(opt.dataset.mb) || 0;
      dom.voiceModelDesc.textContent =
        `${opt.value}${opt.dataset.calidad ? " · " + opt.dataset.calidad : ""}` +
        `${mb ? ` · ${mb.toFixed(0)} MB` : ""}`;
    }
    if (dom.voiceModelHint) {
      dom.voiceModelHint.textContent = "Se descarga una sola vez y luego funciona sin Internet.";
    }
  }

  function pintarProgresoVoz(data) {
    const panel = dom.voiceModelPanel;
    if (!panel || !data) return;

    if (data.state === "error") {
      if (dom.voiceModelProgressWrap) dom.voiceModelProgressWrap.hidden = true;
      if (dom.voiceModelHint) dom.voiceModelHint.textContent = `⚠️ ${data.message || "Error al descargar."}`;
      if (dom.btnVoiceModelDownload) {
        dom.btnVoiceModelDownload.disabled = false;
        dom.btnVoiceModelDownload.textContent = "⬇️ Reintentar descarga";
      }
      return;
    }

    panel.hidden = false;
    panel.classList.add("is-listening");
    if (dom.voiceModelProgressWrap) dom.voiceModelProgressWrap.hidden = false;
    if (dom.btnVoiceModelDownload) {
      dom.btnVoiceModelDownload.disabled = true;
      dom.btnVoiceModelDownload.textContent = "⏳ Descargando...";
    }

    const pct = Math.max(0, Math.min(100, data.percent || 0));
    if (dom.voiceModelProgressBar) dom.voiceModelProgressBar.style.width = `${pct}%`;
    if (dom.voiceModelProgressText) {
      dom.voiceModelProgressText.textContent =
        data.state === "done"
          ? `✓ ${(data.mb || 0).toFixed(1)} MB instalados`
          : `${(data.mb || 0).toFixed(1)} / ${(data.total_mb || 0).toFixed(1)} MB`;
    }

    if (data.state === "done") {
      if (dom.voiceModelTitle) dom.voiceModelTitle.textContent = "¡Voz descargada!";
      if (dom.voiceModelDesc) dom.voiceModelDesc.textContent = data.message || "Ya puedes usarla en el directo.";
      if (dom.voiceModelHint) dom.voiceModelHint.textContent = "";
      if (dom.btnVoiceModelDownload) dom.btnVoiceModelDownload.hidden = true;
    } else if (dom.voiceModelDesc) {
      dom.voiceModelDesc.textContent = data.speed ? `Velocidad: ${data.speed}` : "Preparando la descarga...";
    }
  }

  function actualizarCatalogoPiper(catalogo) {
    if (!Array.isArray(catalogo) || !catalogo.length) return;
    const previo = dom.selectVoice.value;
    state.catalogoPiper = catalogo;
    state.voicesPiper = catalogo.filter(v => v.instalada).map(v => [v.etiqueta, v.id]);

    if (dom.selectEngine.value === "piper") {
      actualizarListaVoces();
      seleccionarVoz(previo);
    }

    const faltan = catalogo.filter(v => v.descargable && !v.instalada).length;
    const hay = catalogo.some(v => v.descargable && v.instalada);
    if (!hay) {
      showToast("⬇️ No tienes ninguna voz neuronal. Descarga una en Voz & Presets.");
    } else if (faltan === 0) {
      showToast("✓ Todas las voces neuronales están descargadas.");
    }
  }

  // Selecciona una voz comparando de forma tolerante (ignora emojis/banderas y mayúsculas).
  function seleccionarVoz(nombre) {
    const sel = dom.selectVoice;
    if (!sel || !sel.options.length) return;

    const normalizar = (s) => String(s || "")
      .replace(/[\u{1F1E6}-\u{1F1FF}\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}\u{200D}]/gu, "")
      .replace(/\b(offline|online)\b/gi, "")   // etiquetas antiguas: "Daniela (Argentina, offline)"
      .replace(/[\s,]+/g, " ")
      .trim()
      .toLowerCase();

    const objetivo = normalizar(nombre);
    let indice = -1;

    for (let i = 0; i < sel.options.length; i++) {
      const valor = sel.options[i].value;
      if (valor === nombre || (objetivo && normalizar(valor) === objetivo)) {
        indice = i;
        break;
      }
    }
    if (indice < 0 && objetivo) {
      for (let i = 0; i < sel.options.length; i++) {
        const valor = normalizar(sel.options[i].value);
        if (valor.includes(objetivo) || objetivo.includes(valor)) {
          indice = i;
          break;
        }
      }
    }

    sel.selectedIndex = indice >= 0 ? indice : 0;
    actualizarPanelVoz();
  }

  /* ==========================================================================
     6. CHAT FEED Y BURBUJAS
     ========================================================================== */
  const MAX_CHAT_ITEMS = 150;
  function trimChatFeed() {
    if (!dom.chatFeed) return;
    while (dom.chatFeed.children.length > MAX_CHAT_ITEMS) {
      dom.chatFeed.removeChild(dom.chatFeed.firstElementChild);
    }
  }

  function appendCommentBubble(user, text, repetido = false) {
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";

    const userEl = document.createElement("span");
    userEl.className = "bubble-user";
    userEl.textContent = `💬 ${user}`;

    if (repetido) {
      const tag = document.createElement("span");
      tag.className = "bubble-repeat-tag";
      tag.textContent = "Repetido";
      tag.title = "Comentario repetido silenciado en la voz";
      userEl.appendChild(tag);
    }

    const textEl = document.createElement("span");
    textEl.className = "bubble-text";
    textEl.textContent = text;

    bubble.appendChild(userEl);
    bubble.appendChild(textEl);
    dom.chatFeed.appendChild(bubble);
    trimChatFeed();
    autoScrollChat();
  }

  function appendWelcomeBubble(user) {
    const bubble = document.createElement("div");
    bubble.className = "welcome-bubble";
    bubble.innerHTML = `
      <span class="welcome-bubble-icon">👋</span>
      <span class="welcome-bubble-text"><strong>${escapeHtml(user)}</strong> se unió al directo</span>
    `;
    dom.chatFeed.appendChild(bubble);
    trimChatFeed();
    autoScrollChat();
  }

  function appendDonationCard(user, gift, count, diamonds) {
    const card = document.createElement("div");
    card.className = "donation-card";
    const safeCount = Number.isFinite(Number(count)) ? Number(count) : 0;
    const safeDiamonds = Number.isFinite(Number(diamonds)) ? Number(diamonds) : 0;

    card.innerHTML = `
      <div class="donation-icon">🎁</div>
      <div class="donation-content">
        <span class="donation-title">[DONACIÓN EN VIVO]</span>
        <span class="donation-desc"><strong>${escapeHtml(user)}</strong> envió ${safeCount}x ${escapeHtml(gift)} (${safeDiamonds} 💎)</span>
      </div>
    `;

    dom.chatFeed.appendChild(card);
    trimChatFeed();
    autoScrollChat();
  }

  function appendSystemBubble(msg, isError = false) {
    const el = document.createElement("div");
    el.className = "system-bubble";
    if (isError) {
      el.style.backgroundColor = "transparent";
      el.style.color = "var(--ios-red)";
      el.style.fontWeight = "500";
      el.style.border = "none";
      el.style.padding = "3px 6px";
    }
    el.textContent = msg;
    dom.chatFeed.appendChild(el);
    trimChatFeed();
    autoScrollChat();
  }

  function autoScrollChat() {
    if (!dom.chatFeed) return;
    const isNearBottom = (dom.chatFeed.scrollHeight - dom.chatFeed.scrollTop - dom.chatFeed.clientHeight) < 80;
    if (isNearBottom) {
      dom.chatFeed.scrollTop = dom.chatFeed.scrollHeight;
    }
  }

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, m => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[m]);
  }

  /* ==========================================================================
     7. ESTADOS Y BADGES
     ========================================================================== */
  function actualizarEstadoConexion(text, status) {
    if (dom.connStatusText) dom.connStatusText.textContent = text;
    if (dom.connStatusPill) {
      dom.connStatusPill.className = "metric-pill";
      if (status === "green") {
        dom.connStatusPill.classList.add("pill-status-connected");
      } else if (status === "amber") {
        dom.connStatusPill.classList.add("pill-status-connecting");
      } else {
        dom.connStatusPill.classList.add("pill-status-disconnected");
      }
    }

    if (dom.btnConnect) {
      if (status === "green") {
        dom.btnConnect.disabled = false;
        dom.btnConnect.className = "btn btn-danger";
        dom.btnConnect.textContent = "Desconectar";
        state.connected = true;
      } else if (status === "amber") {
        dom.btnConnect.disabled = true;
        dom.btnConnect.className = "btn btn-secondary";
        dom.btnConnect.textContent = "Conectando...";
      } else {
        dom.btnConnect.disabled = !state.authUser;
        dom.btnConnect.className = "btn btn-primary";
        dom.btnConnect.textContent = "Conectar";
        if (!state.authUser) {
          dom.btnConnect.title = "Inicia sesión con Google para usar MyBot";
        } else {
          dom.btnConnect.title = "";
        }
        state.connected = false;
      }
    }
  }

  function actualizarUsuarioAuth(user) {
    state.authUser = user;
    const isLogged = !!(user && user.uid);

    if (isLogged) {
      if (dom.btnHeaderLogin) dom.btnHeaderLogin.style.display = "none";
      if (dom.authUserPill) dom.authUserPill.style.display = "inline-flex";
      if (dom.authUserName) {
        const nom = (user.displayName || user.email || "Usuario").split(" ")[0];
        dom.authUserName.textContent = nom;
      }
      if (dom.authUserAvatar) {
        if (user.photoURL) {
          dom.authUserAvatar.src = user.photoURL;
          dom.authUserAvatar.style.display = "block";
        } else {
          dom.authUserAvatar.style.display = "none";
        }
      }
      if (dom.authGateBanner) dom.authGateBanner.style.display = "none";
      if (dom.tiktokUser) {
        dom.tiktokUser.disabled = false;
        dom.tiktokUser.placeholder = "l.am.lex_";
      }
      if (dom.btnConnect && !state.connected) {
        dom.btnConnect.disabled = false;
        dom.btnConnect.title = "";
      }
    } else {
      if (dom.btnHeaderLogin) dom.btnHeaderLogin.style.display = "inline-flex";
      if (dom.authUserPill) dom.authUserPill.style.display = "none";
      if (dom.authGateBanner) dom.authGateBanner.style.display = "flex";
      if (dom.tiktokUser && !state.connected) {
        dom.tiktokUser.disabled = true;
        dom.tiktokUser.placeholder = "Inicia sesión con Google";
      }
      if (dom.btnConnect && !state.connected) {
        dom.btnConnect.disabled = true;
        dom.btnConnect.title = "Inicia sesión con Google para usar MyBot";
      }
    }
  }

  function actualizarTtsEstado(st, detail) {
    let badgeText = "● Estado: Listo";
    let badgeClass = "pill-celeste";
    let topText = "Voz: Lista";

    if (st === "cargando") {
      badgeText = "⏳ Cargando...";
      badgeClass = "pill-warning";
      topText = "Voz: Descargando...";
    } else if (st === "reproduciendo") {
      badgeText = "🔊 Hablando...";
      badgeClass = "pill-status-connected";
      topText = "Voz: Hablando...";
    } else if (st === "fallando") {
      badgeText = "❌ Error";
      badgeClass = "pill-emergency";
      topText = "Voz: Error";
    }

    if (dom.testStatusBadge) {
      dom.testStatusBadge.className = `ios-pill ${badgeClass}`;
      dom.testStatusBadge.textContent = badgeText;
    }
    if (dom.testStatusDetail) {
      dom.testStatusDetail.textContent = detail || "Voz lista para usar en el directo.";
    }
    if (dom.topTtsStatusText) {
      dom.topTtsStatusText.textContent = topText;
    }
  }

  /* ==========================================================================
     8. TOAST NOTIFICATIONS
     ========================================================================== */
  function showToast(message) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    dom.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      toast.style.opacity = "0";
      toast.style.transform = "translateY(8px)";
      setTimeout(() => toast.remove(), 400);
    }, 2800);
  }

  /* ==========================================================================
     9. EVENT LISTENERS E INTERACCIÓN
     ========================================================================== */
  function setupEventListeners() {
    // Autenticación con Google mediante Firebase
    const triggerLogin = () => {
      sendAction("login_browser");
    };

    if (dom.btnHeaderLogin) dom.btnHeaderLogin.addEventListener("click", triggerLogin);
    if (dom.btnAuthGateLogin) dom.btnAuthGateLogin.addEventListener("click", triggerLogin);

    if (dom.btnHeaderLogout) {
      dom.btnHeaderLogout.addEventListener("click", (e) => {
        e.stopPropagation();
        if (confirm("¿Cerrar sesión de Google en MyBot?")) {
          sendAction("logout");
        }
      });
    }

    // Conectar / Desconectar unificado en un solo botón
    dom.btnConnect.addEventListener("click", () => {
      if (state.connected) {
        sendAction("disconnect");
        return;
      }
      if (!state.authUser) {
        showToast("Debes iniciar sesión con Google para usar MyBot");
        triggerLogin();
        return;
      }
      const user = dom.tiktokUser.value.trim().replace(/^@+/, "");
      if (!user) {
        showToast("Introduce tu usuario de TikTok");
        dom.tiktokUser.focus();
        return;
      }
      sendAction("connect", { user });
    });

    if (dom.btnDisconnect) {
      dom.btnDisconnect.addEventListener("click", () => {
        sendAction("disconnect");
      });
    }

    // Auto-eliminar @ si el usuario lo pega o escribe
    dom.tiktokUser.addEventListener("input", () => {
      if (dom.tiktokUser.value.startsWith("@")) {
        dom.tiktokUser.value = dom.tiktokUser.value.replace(/^@+/, "");
      }
    });

    // Enter en input de usuario
    dom.tiktokUser.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !dom.btnConnect.disabled) {
        dom.btnConnect.click();
      }
    });

    // Limpiar chat y Silenciar audio inmediato
    if (dom.btnClearChat) dom.btnClearChat.addEventListener("click", () => {
      dom.chatFeed.innerHTML = "";
      appendSystemBubble("Chat limpiado.");
    });

    if (dom.btnMuteAudio) dom.btnMuteAudio.addEventListener("click", () => {
      sendAction("mute");
    });

    // Cambio de motor
    dom.selectEngine.addEventListener("change", () => {
      actualizarListaVoces();
      if (dom.selectVoice.options.length) dom.selectVoice.selectedIndex = 0;
      actualizarPanelVoz();
      guardarConfiguracionDebounced();
    });

    // Cambio de voz (para saber si hay que descargarla)
    dom.selectVoice.addEventListener("change", () => {
      actualizarPanelVoz();
      guardarConfiguracionDebounced();
    });

    // Descargar la voz neuronal offline desde la propia app
    if (dom.btnVoiceModelDownload) {
      dom.btnVoiceModelDownload.addEventListener("click", () => {
        const opt = dom.selectVoice.selectedOptions[0];
        const vozId = opt && opt.dataset.vozId;
        if (!vozId) {
          showToast("Selecciona primero una voz neuronal offline.");
          return;
        }
        sendAction("download_voice_model", { id: vozId });
        pintarProgresoVoz({ state: "downloading", percent: 0, mb: 0, total_mb: parseFloat(opt.dataset.mb) || 0 });
      });
    }

    // Cambio de Preset
    dom.selectPreset.addEventListener("change", () => {
      const presetName = dom.selectPreset.value;
      const p = state.presets[presetName];
      if (p) {
        dom.rangeTone.value = p.tono;
        dom.lblToneValue.textContent = `${p.tono > 0 ? "+" : ""}${p.tono} Hz`;
        dom.rangeSpeed.value = p.vel;
        dom.lblSpeedValue.textContent = `${p.vel > 0 ? "+" : ""}${p.vel}%`;
        dom.presetDesc.textContent = p.desc;
        guardarConfiguracionDebounced();
      }
    });

    // Sliders en tiempo real
    dom.rangeTone.addEventListener("input", () => {
      const val = dom.rangeTone.value;
      dom.lblToneValue.textContent = `${val > 0 ? "+" : ""}${val} Hz`;
      guardarConfiguracionDebounced();
    });

    dom.rangeSpeed.addEventListener("input", () => {
      const val = dom.rangeSpeed.value;
      dom.lblSpeedValue.textContent = `${val > 0 ? "+" : ""}${val}%`;
      guardarConfiguracionDebounced();
    });

    dom.rangeVolume.addEventListener("input", () => {
      const val = dom.rangeVolume.value;
      dom.lblVolumeValue.textContent = `${val}%`;
      guardarConfiguracionDebounced();
    });

    // Stepper de diamantes
    dom.btnDecDiamond.addEventListener("click", () => {
      let v = parseInt(dom.numMinDiamonds.value) || 1;
      if (v > 1) {
        dom.numMinDiamonds.value = v - 1;
        guardarConfiguracionDebounced();
      }
    });

    dom.btnIncDiamond.addEventListener("click", () => {
      let v = parseInt(dom.numMinDiamonds.value) || 1;
      dom.numMinDiamonds.value = v + 1;
      guardarConfiguracionDebounced();
    });

    // Stepper de diamantes para acción multimedia
    if (dom.btnDecMediaDiamond && dom.numMediaMinDiamonds) {
      dom.btnDecMediaDiamond.addEventListener("click", () => {
        let v = parseInt(dom.numMediaMinDiamonds.value) || 1;
        if (v > 1) {
          dom.numMediaMinDiamonds.value = v - 1;
          guardarConfiguracionDebounced();
        }
      });
    }

    if (dom.btnIncMediaDiamond && dom.numMediaMinDiamonds) {
      dom.btnIncMediaDiamond.addEventListener("click", () => {
        let v = parseInt(dom.numMediaMinDiamonds.value) || 1;
        dom.numMediaMinDiamonds.value = v + 1;
        guardarConfiguracionDebounced();
      });
    }

    // Pruebas de multimedia (YouTube Music / Spotify)
    if (dom.btnTestMediaNext) {
      dom.btnTestMediaNext.addEventListener("click", () => {
        sendAction("test_media", { media_action: "next" });
      });
    }

    if (dom.btnTestMediaPrev) {
      dom.btnTestMediaPrev.addEventListener("click", () => {
        sendAction("test_media", { media_action: "prev" });
      });
    }

    if (dom.btnTestMediaPlayPause) {
      dom.btnTestMediaPlayPause.addEventListener("click", () => {
        sendAction("test_media", { media_action: "play_pause" });
      });
    }

    // Steppers de Bienvenida
    if (dom.btnDecWelcomeCooldown && dom.numWelcomeCooldown) {
      dom.btnDecWelcomeCooldown.addEventListener("click", () => {
        let v = parseInt(dom.numWelcomeCooldown.value) || 10;
        if (v > 3) {
          dom.numWelcomeCooldown.value = v - 1;
          guardarConfiguracionDebounced();
        }
      });
    }

    if (dom.btnIncWelcomeCooldown && dom.numWelcomeCooldown) {
      dom.btnIncWelcomeCooldown.addEventListener("click", () => {
        let v = parseInt(dom.numWelcomeCooldown.value) || 10;
        if (v < 60) {
          dom.numWelcomeCooldown.value = v + 1;
          guardarConfiguracionDebounced();
        }
      });
    }

    // Steppers de Anti-repetición de comentarios
    if (dom.btnDecRepeatTimeout && dom.numRepeatTimeout) {
      dom.btnDecRepeatTimeout.addEventListener("click", () => {
        let v = parseInt(dom.numRepeatTimeout.value) || 45;
        if (v > 10) {
          dom.numRepeatTimeout.value = v - 5;
          guardarConfiguracionDebounced();
        }
      });
    }

    if (dom.btnIncRepeatTimeout && dom.numRepeatTimeout) {
      dom.btnIncRepeatTimeout.addEventListener("click", () => {
        let v = parseInt(dom.numRepeatTimeout.value) || 45;
        if (v < 180) {
          dom.numRepeatTimeout.value = v + 5;
          guardarConfiguracionDebounced();
        }
      });
    }

    // Steppers de Queue TTL (Anti-lag)
    if (dom.btnDecQueueTtl && dom.numQueueTtl) {
      dom.btnDecQueueTtl.addEventListener("click", () => {
        let v = parseInt(dom.numQueueTtl.value) || 20;
        if (v > 5) {
          dom.numQueueTtl.value = v - 5;
          guardarConfiguracionDebounced();
        }
      });
    }

    if (dom.btnIncQueueTtl && dom.numQueueTtl) {
      dom.btnIncQueueTtl.addEventListener("click", () => {
        let v = parseInt(dom.numQueueTtl.value) || 20;
        if (v < 60) {
          dom.numQueueTtl.value = v + 5;
          guardarConfiguracionDebounced();
        }
      });
    }

    // Acciones de prueba de voz
    dom.btnTestVoice.addEventListener("click", () => {
      const text = dom.txtTestVoice.value.trim() || "Prueba de voz en directo.";
      sendAction("test_voice", { text });
    });

    if (dom.btnDownloadVoice) {
      dom.btnDownloadVoice.addEventListener("click", () => {
      const text = dom.txtTestVoice.value.trim() || "Prueba de voz en directo.";
      sendAction("download_voice", { text });
      });
    }

        if (dom.txtDonationPrefix) {
      dom.txtDonationPrefix.addEventListener("input", () => {
        const p = dom.txtDonationPrefix.value.trim();
        dom.txtDonationTemplate.value = `${p} {usuario} por enviar {cantidad} {regalo}!`.trim();
        guardarConfiguracionDebounced();
      });
    }

    if (dom.btnTestDonation) {
      dom.btnTestDonation.addEventListener("click", () => {
      sendAction("test_donation");
      });
    }

    if (dom.btnTestWelcome) {
      dom.btnTestWelcome.addEventListener("click", () => {
        const user = (dom.txtTestWelcomeUser && dom.txtTestWelcomeUser.value.trim()) || "Alex";
        const template = (dom.txtWelcomeTemplate && dom.txtWelcomeTemplate.value.trim()) || "¡Bienvenido {usuario} al directo!";
        sendAction("test_welcome", { user, template });
        showToast(`Probando bienvenida para ${user}...`);
      });
    }

    // Guardado manual
    if (dom.btnSaveConfig) {
      dom.btnSaveConfig.addEventListener("click", () => {
        guardarConfiguracion(true);
      });
    }

    // Inputs que guardan con debouncing
    const inputsAuto = [
      dom.selectVoice, dom.chkReadUsername, dom.txtUserFormat,
      dom.chkDonationsActive, dom.chkWaitStreak, dom.numMinDiamonds,
      dom.chkReadDonation, dom.txtDonationTemplate, dom.chkSoundActive,
      dom.selectSound, dom.chkMediaActionActive, dom.selectMediaAction,
      dom.numMediaMinDiamonds, dom.chkWelcomeActive, dom.chkWelcomeChat,
      dom.chkWelcomeVoice, dom.chkWelcomeAntiRepeat, dom.txtWelcomeTemplate,
      dom.numWelcomeCooldown, dom.txtBannedWords, dom.numMaxChars,
      dom.numMaxQueue, dom.chkIgnoreRepeated, dom.numRepeatTimeout,
      dom.chkCleanUsernames, dom.chkDynamicSpeed, dom.numQueueTtl,
      dom.chkFilterLinks, dom.chkCompactEmojis, dom.chkAutoReconnect
    ];

    inputsAuto.filter(Boolean).forEach(el => {
      el.addEventListener("change", () => guardarConfiguracionDebounced());
    });
    // Modal Binance
    if (dom.btnOpenBinance && dom.modalBinance) {
      dom.btnOpenBinance.addEventListener("click", () => {
        dom.modalBinance.style.display = "flex";
      });
      dom.btnCloseBinance.addEventListener("click", () => {
        dom.modalBinance.style.display = "none";
      });
      dom.modalBinance.addEventListener("click", (e) => {
        if (e.target === dom.modalBinance) dom.modalBinance.style.display = "none";
      });
    }

    // Copiar Pay ID / UID
    if (dom.btnCopyPayId) {
      dom.btnCopyPayId.addEventListener("click", () => {
        const text = dom.binancePayIdVal.value;
        navigator.clipboard.writeText(text).then(() => {
          showToast("✓ Binance UID copiado: 1175466526 (lexfabian)");
        });
      });
    }

    // Manejador de Enlaces Externos
    document.querySelectorAll(".external-link").forEach(link => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const url = link.getAttribute("href");
        if (url) abrirEnlaceExterno(url);
      });
    });

    // Modal Actualizaciones
    if (dom.btnCheckUpdate && dom.modalUpdate) {
      dom.btnCheckUpdate.addEventListener("click", () => {
        comprobarActualizaciones(true);
      });
      dom.btnCloseUpdate.addEventListener("click", () => {
        // Posponer: se recuerda la version para no volver a insistir al arrancar.
        if (state.updateInfo && state.updateInfo.version) omitirVersion(state.updateInfo.version);
        dom.modalUpdate.style.display = "none";
      });
      dom.modalUpdate.addEventListener("click", (e) => {
        if (e.target === dom.modalUpdate) dom.modalUpdate.style.display = "none";
      });
      dom.btnDownloadUpdate.addEventListener("click", () => {
        const url = (state.updateInfo && state.updateInfo.download_url)
          || "https://storage.googleapis.com/mybot-79861.firebasestorage.app/instaladores/MyBot_v1.3.3_Instalador.exe";
        dom.btnDownloadUpdate.disabled = true;
        dom.btnDownloadUpdate.textContent = "⏳ Descargando en la app...";
        if (dom.updateProgressBox) {
          dom.updateProgressBox.style.display = "flex";
          dom.updateProgressBar.style.width = "0%";
          dom.updateProgressPercent.textContent = "0%";
          dom.updateProgressStatus.textContent = "Iniciando descarga in-app...";
        }
        sendAction("download_update", { url, sha256: (state.updateInfo && state.updateInfo.sha256) || "" });
      });

      if (dom.btnInstallUpdate) {
        dom.btnInstallUpdate.addEventListener("click", () => {
          sendAction("launch_installer", { path: state.installerPath });
          showToast("🚀 Abriendo asistente de instalación...");
          setTimeout(() => {
            if (dom.modalUpdate) dom.modalUpdate.style.display = "none";
          }, 1200);
        });
      }

      // Posponer la actualización desde su propio boton (mismo efecto que la X).
      if (dom.btnLaterUpdate) {
        dom.btnLaterUpdate.addEventListener("click", () => {
          if (state.updateInfo && state.updateInfo.version) omitirVersion(state.updateInfo.version);
          dom.modalUpdate.style.display = "none";
          showToast(`Se avisará de nuevo al publicar una versión posterior.`);
        });
      }
    }
  }

  // ---------------------------------------------------------------------------
  // ACTUALIZACIONES
  // Al arrancar se consulta version.json en segundo plano. Si hay una version
  // nueva se ofrece descargarla e instalarla sin salir de la aplicacion; si el
  // usuario decide posponerla, no se vuelve a insistir con esa misma version.
  // ---------------------------------------------------------------------------
  const CLAVE_OMITIDA = "mybot_version_omitida";

  function versionOmitida() {
    try {
      return localStorage.getItem(CLAVE_OMITIDA) || "";
    } catch (e) {
      return "";
    }
  }

  function omitirVersion(version) {
    try {
      localStorage.setItem(CLAVE_OMITIDA, String(version || ""));
    } catch (e) {
      /* almacenamiento no disponible */
    }
  }

  function itemsChangelog(data) {
    const c = data.changelog_items || data.changelog;
    if (!c) return [];
    if (Array.isArray(c)) return c.map(String).filter(Boolean);
    return String(c).split(/\r?\n/).map(t => t.trim()).filter(Boolean);
  }

  function mostrarModalActualizacion(data) {
    if (!dom.modalUpdate) return;

    if (dom.lblCurrentVersion) dom.lblCurrentVersion.textContent = `v${VERSION_ACTUAL}`;
    if (dom.lblNewVersion) dom.lblNewVersion.textContent = data.version_name || data.version;

    if (dom.updateChangelogList) {
      const items = itemsChangelog(data);
      dom.updateChangelogList.innerHTML = "";
      if (items.length) {
        items.forEach(t => {
          const li = document.createElement("li");
          li.textContent = t;
          dom.updateChangelogList.appendChild(li);
        });
      } else {
        const li = document.createElement("li");
        li.textContent = "Mejoras de rendimiento y correccion de errores.";
        dom.updateChangelogList.appendChild(li);
      }
    }

    if (dom.btnDownloadUpdate) {
      dom.btnDownloadUpdate.style.display = "block";
      dom.btnDownloadUpdate.disabled = false;
      dom.btnDownloadUpdate.textContent = "⬇️ Descargar e Instalar Directamente";
    }
    if (dom.btnInstallUpdate) dom.btnInstallUpdate.style.display = "none";
    if (dom.updateProgressBox) dom.updateProgressBox.style.display = "none";
    dom.modalUpdate.style.display = "flex";
  }

  /** Refleja la version real de la aplicacion en el encabezado y el pie. */
  function refrescarVersionUI() {
    if (dom.appBadgeVersion) dom.appBadgeVersion.textContent = `v${VERSION_ACTUAL}`;
    if (dom.footerVersion) dom.footerVersion.textContent = `v${VERSION_ACTUAL}`;
  }

  function comprobarActualizaciones(esManual = false) {
    if (esManual) showToast("Buscando actualizaciones de MyBot...");

    // La consulta la hace el backend (Python): la aplicacion se sirve desde
    // 127.0.0.1, asi que un fetch() a mybot-79861.web.app seria de otro origen y
    // el navegador lo bloquearia por CORS. Si no hay WebSocket, se intenta
    // directamente como respaldo.
    const wsAbierto = state.ws && state.ws.readyState === WebSocket.OPEN;
    if (wsAbierto) {
      sendAction("check_update", { manual: esManual });
      return;
    }
    comprobarActualizacionesPorHttp(esManual);
  }

  /** Respaldo por HTTP directo (solo funciona si el origen coincide con UPDATE_URL). */
  function comprobarActualizacionesPorHttp(esManual = false) {
    fetch(`${UPDATE_URL}?t=${Date.now()}`, { cache: "no-store" })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => procesarActualizacion(data, esManual))
      .catch(err => {
        if (esManual) showToast("No se pudo comprobar las actualizaciones.");
        console.warn("[Update] Error al comprobar por HTTP:", err);
      });
  }

  /** Decide si se muestra el aviso de nueva version. */
  function procesarActualizacion(data, esManual = false) {
    if (!esVersionMayor(data.version, VERSION_ACTUAL)) {
      if (esManual) showToast(`✓ Ya tienes la última versión (v${VERSION_ACTUAL}).`);
      return;
    }

    state.updateInfo = data;

    // Una comprobacion automatica no insiste si esa version ya se pospuso.
    if (!esManual && versionOmitida() === String(data.version)) {
      console.info(`[Update] Version ${data.version} pospuesta por el usuario.`);
      return;
    }
    mostrarModalActualizacion(data);
  }

  /** Consulta version.json unos segundos despues de arrancar, sin bloquear la carga. */
  function comprobarActualizacionesAlArrancar() {
    setTimeout(() => comprobarActualizaciones(false), 5000);
  }

  let debounceTimer = null;
  function guardarConfiguracionDebounced() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => guardarConfiguracion(false), 500);
  }

  function guardarConfiguracion(showFeedback = false) {
    const payload = {
      usuario: dom.tiktokUser.value.trim(),
      motor: dom.selectEngine.value,
      voz_nombre: dom.selectVoice.value,
      tono: parseInt(dom.rangeTone.value) || 0,
      velocidad: parseInt(dom.rangeSpeed.value) || 0,
      volumen: parseInt(dom.rangeVolume.value) || 100,
      leer_nombre: dom.chkReadUsername.checked,
      formato_usuario: dom.txtUserFormat.value,
      donaciones_activas: dom.chkDonationsActive.checked,
      esperar_racha: dom.chkWaitStreak.checked,
      min_diamantes: parseInt(dom.numMinDiamonds.value) || 1,
      leer_donacion: dom.chkReadDonation.checked,
      tpl_donacion: dom.txtDonationTemplate.value,
      sonido_activo: dom.chkSoundActive.checked,
      tipo_sonido: dom.selectSound.value,
      accion_multimedia_activa: dom.chkMediaActionActive ? dom.chkMediaActionActive.checked : false,
      tipo_accion_multimedia: dom.selectMediaAction ? dom.selectMediaAction.value : "next",
      min_diamantes_multimedia: dom.numMediaMinDiamonds ? (parseInt(dom.numMediaMinDiamonds.value) || 1) : 1,
      bienvenidas_activas: dom.chkWelcomeActive ? dom.chkWelcomeActive.checked : true,
      mostrar_bienvenida_chat: dom.chkWelcomeChat ? dom.chkWelcomeChat.checked : true,
      leer_bienvenida: dom.chkWelcomeVoice ? dom.chkWelcomeVoice.checked : false,
      anti_repeticion_bienvenida: dom.chkWelcomeAntiRepeat ? dom.chkWelcomeAntiRepeat.checked : true,
      tpl_bienvenida: dom.txtWelcomeTemplate ? dom.txtWelcomeTemplate.value : "¡Bienvenido {usuario} al directo!",
      cooldown_bienvenida: dom.numWelcomeCooldown ? (parseInt(dom.numWelcomeCooldown.value) || 10) : 10,
      baneadas: dom.txtBannedWords.value,
      max_caracteres: parseInt(dom.numMaxChars.value) || 85,
      max_cola: parseInt(dom.numMaxQueue.value) || 8,
      ignorar_comentarios_repetidos: dom.chkIgnoreRepeated ? dom.chkIgnoreRepeated.checked : true,
      tiempo_anti_repeticion: dom.numRepeatTimeout ? (parseInt(dom.numRepeatTimeout.value) || 45) : 45,
      limpiar_nombres_usuarios: dom.chkCleanUsernames ? dom.chkCleanUsernames.checked : true,
      aceleracion_dinamica: dom.chkDynamicSpeed ? dom.chkDynamicSpeed.checked : true,
      ttl_comentarios_cola: dom.numQueueTtl ? (parseInt(dom.numQueueTtl.value) || 20) : 20,
      filtrar_links: dom.chkFilterLinks.checked,
      compactar_emojis: dom.chkCompactEmojis.checked,
      auto_reconnect: dom.chkAutoReconnect ? dom.chkAutoReconnect.checked : true
    };

    sendAction("save_config", { config: payload });
    if (showFeedback) showToast("Configuración guardada exitosamente");
  }

  /* ==========================================================================
     INICIALIZACIÓN
     ========================================================================== */
  document.addEventListener("DOMContentLoaded", () => {
    refrescarVersionUI();
    iniciarSplashScreen();
    setupTabs();
    setupWebSocket();
    setupEventListeners();

    // Configuración de transparencia y desacople de chat
    const rangeBg = document.getElementById("rangeChatBgOpacity");
    const lblBg = document.getElementById("lblChatBgOpacity");
    const rangeText = document.getElementById("rangeChatTextOpacity");
    const lblText = document.getElementById("lblChatTextOpacity");
    const btnPopout = document.getElementById("btnPopoutChat");
    const chatFeed = dom.chatFeed;
    const chatWrapper = document.querySelector(".chat-wrapper");

    function aplicarOpacidadChat(bgVal, textVal) {
      const bgPct = (parseInt(bgVal, 10) || 100) / 100;
      const textPct = (parseInt(textVal, 10) || 100) / 100;

      if (chatFeed) {
        chatFeed.style.backgroundColor = `rgba(250, 251, 253, ${bgPct})`;
        chatFeed.style.color = `rgba(28, 28, 30, ${textPct})`;
      }
      if (chatWrapper) {
        chatWrapper.style.backgroundColor = bgPct < 1 ? `rgba(255, 255, 255, ${Math.max(0.1, bgPct * 0.9)})` : "";
      }
      // Actualizar burbujas
      document.querySelectorAll(".chat-bubble, .welcome-bubble, .donation-card").forEach(el => {
        el.style.opacity = String(textPct);
        if (bgPct < 0.6) {
          el.style.backgroundColor = `rgba(255, 255, 255, ${Math.max(0.2, bgPct)})`;
          el.style.backdropFilter = "blur(4px)";
        } else {
          el.style.backgroundColor = "";
          el.style.backdropFilter = "";
        }
      });
    }

    if (rangeBg) {
      const savedBg = localStorage.getItem("mybot_chat_bg_opacity") || "100";
      rangeBg.value = savedBg;
      if (lblBg) lblBg.textContent = `${savedBg}%`;

      rangeBg.addEventListener("input", () => {
        const val = rangeBg.value;
        if (lblBg) lblBg.textContent = `${val}%`;
        localStorage.setItem("mybot_chat_bg_opacity", val);
        aplicarOpacidadChat(val, rangeText ? rangeText.value : 100);
      });
    }

    if (rangeText) {
      const savedText = localStorage.getItem("mybot_chat_text_opacity") || "100";
      rangeText.value = savedText;
      if (lblText) lblText.textContent = `${savedText}%`;

      rangeText.addEventListener("input", () => {
        const val = rangeText.value;
        if (lblText) lblText.textContent = `${val}%`;
        localStorage.setItem("mybot_chat_text_opacity", val);
        aplicarOpacidadChat(rangeBg ? rangeBg.value : 100, val);
      });
    }

    // Inicializar opacidad guardada
    aplicarOpacidadChat(
      localStorage.getItem("mybot_chat_bg_opacity") || "100",
      localStorage.getItem("mybot_chat_text_opacity") || "100"
    );

    if (btnPopout) {
      btnPopout.addEventListener("click", () => {
        const w = 420;
        const h = 640;
        const left = (screen.width - w) / 2;
        const top = (screen.height - h) / 2;
        window.open(
          location.href + (location.href.includes("?") ? "&" : "?") + "popout=chat",
          "MyBotChatWindow",
          `width=${w},height=${h},left=${left},top=${top},menubar=no,toolbar=no,status=no`
        );
      });
    }

    if (new URLSearchParams(location.search).get("popout") === "chat") {
      document.body.classList.add("is-popout");
    }

    comprobarActualizacionesAlArrancar();
  });

})();
