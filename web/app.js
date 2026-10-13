/**
 * ============================================================================
 *  MyBot — Lógica del Frontend Web (JavaScript ES6)
 * ============================================================================
 */

(function () {
  "use strict";

  // Estado global de la aplicación
  const state = {
    connected: false,
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
  const VERSION_ACTUAL = "1.2.0";
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
    btnCloseUpdate: document.getElementById("btnCloseUpdate"),
    modalUpdate: document.getElementById("modalUpdate"),
    btnDownloadUpdate: document.getElementById("btnDownloadUpdate"),
    btnInstallUpdate: document.getElementById("btnInstallUpdate"),
    lblCurrentVersion: document.getElementById("lblCurrentVersion"),
    lblNewVersion: document.getElementById("lblNewVersion"),
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

        let animId = 0;
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

          animId = requestAnimationFrame(render);
        }
        render();
      })
      .catch(err => {
        console.warn("No se pudieron cargar los puntos del logo:", err);
      });
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
    const wsUrl = `${protocol}//${location.host}/ws`;

    const ws = new WebSocket(wsUrl);
    state.ws = ws;

    ws.onopen = () => {
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
      console.warn("[WS] Desconectado. Reintentando en 2 segundos...");
      setTimeout(setupWebSocket, 2000);
    };

    ws.onerror = (err) => {
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

  /* ==========================================================================
     4. MANEJADOR DE MENSAJES DEL SERVIDOR
     ========================================================================== */
  function handleServerMessage(msg) {
    const { type, data } = msg;

    switch (type) {
      case "init":
        state.config = data.config || {};
        state.voicesEdge = data.voices_edge || [];
        state.voicesSapi5 = data.voices_sapi5 || [];
        state.voicesPiper = data.voices_piper || [];
        state.catalogoPiper = data.catalogo_piper || [];
        state.presets = data.presets || {};
        state.sounds = data.sounds || [];
        poblarControles();
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
        appendSystemBubble("⚠️ " + data.message, true);
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
        dom.queueCount.textContent = data.count;
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
        if (dom.updateProgressBar) dom.updateProgressBar.style.width = "100%";
        if (dom.updateProgressPercent) dom.updateProgressPercent.textContent = "100%";
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
    }
  }

  /* ==========================================================================
     5. ACTUALIZACIÓN VISUAL Y POBLACIÓN DE CONTROLES
     ========================================================================== */
  function poblarControles() {
    const cfg = state.config;

    // Usuario
    if (cfg.usuario) dom.tiktokUser.value = cfg.usuario;

    // Motor (Piper offline es el preferido: sin Internet y sin el error 403 de Edge TTS)
    dom.selectEngine.value = cfg.motor || "piper";

    // Presets
    dom.selectPreset.innerHTML = "";
    Object.keys(state.presets).forEach(name => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
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
        opt.textContent = name;
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
      opt.textContent = v.instalada === false ? `${etiqueta} · sin descargar` : etiqueta;
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

    card.innerHTML = `
      <div class="donation-icon">🎁</div>
      <div class="donation-content">
        <span class="donation-title">[DONACIÓN EN VIVO]</span>
        <span class="donation-desc"><strong>${escapeHtml(user)}</strong> envió ${count}x ${escapeHtml(gift)} (${diamonds} 💎)</span>
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
      el.style.backgroundColor = "var(--ios-red-light)";
      el.style.color = "var(--ios-red)";
      el.style.fontWeight = "600";
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
    dom.connStatusText.textContent = text;
    dom.connStatusPill.className = "metric-pill";

    if (status === "green") {
      dom.connStatusPill.classList.add("pill-status-connected");
      dom.btnConnect.disabled = true;
      dom.btnDisconnect.disabled = false;
      state.connected = true;
    } else if (status === "amber") {
      dom.connStatusPill.classList.add("pill-status-connecting");
      dom.btnConnect.disabled = true;
      dom.btnDisconnect.disabled = false;
    } else {
      dom.connStatusPill.classList.add("pill-status-disconnected");
      dom.btnConnect.disabled = false;
      dom.btnDisconnect.disabled = true;
      state.connected = false;
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

    dom.testStatusBadge.className = `ios-pill ${badgeClass}`;
    dom.testStatusBadge.textContent = badgeText;
    dom.testStatusDetail.textContent = detail || "Voz lista para usar en el directo.";
    dom.topTtsStatusText.textContent = topText;
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
    // Conectar / Desconectar
    dom.btnConnect.addEventListener("click", () => {
      const user = dom.tiktokUser.value.trim();
      if (!user) {
        showToast("Introduce un usuario o link de TikTok Live");
        dom.tiktokUser.focus();
        return;
      }
      sendAction("connect", { user });
    });

    dom.btnDisconnect.addEventListener("click", () => {
      sendAction("disconnect");
    });

    // Enter en input de usuario
    dom.tiktokUser.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !dom.btnConnect.disabled) {
        dom.btnConnect.click();
      }
    });

    // Limpiar chat y Silenciar audio inmediato
    dom.btnClearChat.addEventListener("click", () => {
      dom.chatFeed.innerHTML = "";
      appendSystemBubble("Chat limpiado.");
    });

    dom.btnMuteAudio.addEventListener("click", () => {
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

    dom.btnDownloadVoice.addEventListener("click", () => {
      const text = dom.txtTestVoice.value.trim() || "Prueba de voz en directo.";
      sendAction("download_voice", { text });
    });

    dom.btnTestDonation.addEventListener("click", () => {
      sendAction("test_donation");
    });

    if (dom.btnTestWelcome) {
      dom.btnTestWelcome.addEventListener("click", () => {
        const user = (dom.txtTestWelcomeUser && dom.txtTestWelcomeUser.value.trim()) || "Alex";
        sendAction("test_welcome", { user });
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
        if (url) {
          if (window.electronAPI && window.electronAPI.openExternal) {
            window.electronAPI.openExternal(url);
          } else {
            window.open(url, "_blank");
          }
        }
      });
    });

    // Modal Actualizaciones
    if (dom.btnCheckUpdate && dom.modalUpdate) {
      dom.btnCheckUpdate.addEventListener("click", () => {
        comprobarActualizaciones(true);
      });
      dom.btnCloseUpdate.addEventListener("click", () => {
        dom.modalUpdate.style.display = "none";
      });
      dom.modalUpdate.addEventListener("click", (e) => {
        if (e.target === dom.modalUpdate) dom.modalUpdate.style.display = "none";
      });
      dom.btnDownloadUpdate.addEventListener("click", () => {
        const url = (state.updateInfo && state.updateInfo.download_url)
          || "https://mybot-79861.web.app/downloads/MyBot_v1.2_Instalador.exe";
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
    }
  }

  function comprobarActualizaciones(esManual = false) {
    if (esManual) showToast("Buscando actualizaciones de MyBot...");
    fetch(`${UPDATE_URL}?t=${Date.now()}`, { cache: "no-store" })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (esVersionMayor(data.version, VERSION_ACTUAL)) {
          state.updateInfo = data;
          if (dom.modalUpdate) {
            if (dom.lblCurrentVersion) dom.lblCurrentVersion.textContent = `v${VERSION_ACTUAL}`;
            dom.lblNewVersion.textContent = data.version_name || data.version;
            if (dom.btnDownloadUpdate) {
              dom.btnDownloadUpdate.style.display = "block";
              dom.btnDownloadUpdate.disabled = false;
              dom.btnDownloadUpdate.textContent = "⬇️ Descargar e Instalar Directamente";
            }
            if (dom.btnInstallUpdate) dom.btnInstallUpdate.style.display = "none";
            if (dom.updateProgressBox) dom.updateProgressBox.style.display = "none";
            dom.modalUpdate.style.display = "flex";
          }
        } else if (esManual) {
          showToast(`✓ Ya tienes la última versión (v${VERSION_ACTUAL}).`);
        }
      })
      .catch(err => {
        if (esManual) showToast("No se pudo comprobar las actualizaciones.");
        console.warn("[Update] Error al comprobar:", err);
      });
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
    iniciarSplashScreen();
    setupTabs();
    setupWebSocket();
    setupEventListeners();
  });

})();
