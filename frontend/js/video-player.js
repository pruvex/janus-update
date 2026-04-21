/**
 * MCL renderer for dock module `video-player` (type `video`).
 * Z-order: `modal-api.js` syncs `dock.modules['video-player'].zIndex` → `#video-player-modal`.
 */

import { closeModal, bringToFront } from "./modal-api.js";
import { subscribeWindowState, getDockModuleState, dockMinimize, registerDockModule, dockOpen, dockClose, setDockModuleExists } from "./window-state.js";
import interact from "interactjs";

const MODULE_ID = "video-player";
const TRANSCRIPT_MODULE_ID = "transcript";

const YOUTUBE_RE =
  /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?(?:[^#&\s]*&)?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/i;
const VIMEO_RE = /(?:https?:\/\/)?(?:www\.)?vimeo\.com\/(?:video\/)?(\d+)/i;

/** Only these embed origins may load in the iframe (direct embed_url or normalized from url). */
const EMBED_DOMAIN_WHITELIST_RE =
  /^https:\/\/(www\.)?(youtube\.com|youtube-nocookie\.com|player\.vimeo\.com)\//i;
let wasVisible = false;
let dragActive = false;
let dragOffsetX = 0;
let dragOffsetY = 0;

// Position transcript-modal exactly above video-modal
function positionTranscriptAboveVideo() {
  const transcriptModal = document.getElementById('transcript-modal');
  const videoModal = document.getElementById('video-player-modal');

  if (!transcriptModal) return;

  // Verzögerte Positionierung, um sicherzustellen, dass Video-Modal sichtbar ist
  setTimeout(() => {
    const videoModalDelayed = document.getElementById('video-player-modal');

    if (!videoModalDelayed) {
      // Fallback: Position bei 640px links, 70px oben
      transcriptModal.style.left = '640px';
      transcriptModal.style.top = '70px';
      transcriptModal.style.width = '700px';
      transcriptModal.style.height = '450px';
      return;
    }

    const videoRect = videoModalDelayed.getBoundingClientRect();

    // Positioniere Transkript GENAU ÜBER Video (gleiche linke obere Ecke)
    transcriptModal.style.left = videoRect.left + 'px';
    transcriptModal.style.top = videoRect.top + 'px'; // GENAU ÜBER
    transcriptModal.style.width = videoRect.width + 'px';
    transcriptModal.style.height = '450px'; // Feste Höhe
  }, 100); // 100ms Verzögerung
}

function isWhitelistedEmbedUrl(url) {
  const s = String(url || "").trim();
  return Boolean(s && EMBED_DOMAIN_WHITELIST_RE.test(s));
}

function ensureHttp(url) {
  const u = String(url || "").trim();
  if (!u) return u;
  if (u.startsWith("//")) return `https:${u}`;
  if (!/^https?:\/\//i.test(u)) return `https://${u.replace(/^\/+/, "")}`;
  return u;
}

/**
 * Normalize watch/share URLs to iframe-safe embed URLs (YouTube / Vimeo).
 * @param {string} rawUrl
 * @returns {string | null}
 */
export function normalizeVideoEmbedUrl(rawUrl) {
  const u = ensureHttp(rawUrl);
  if (!u) return null;
  let m = u.match(YOUTUBE_RE);
  if (m) return `https://www.youtube-nocookie.com/embed/${m[1]}?rel=0`;
  m = u.match(VIMEO_RE);
  if (m) return `https://player.vimeo.com/video/${m[1]}?api=1`;
  return null;
}

function enrichEmbedUrlForApi(raw) {
  const s = String(raw || "").trim();
  if (!s) return s;
  try {
    const u = new URL(s);
    const host = u.hostname.toLowerCase();
    if (host.includes("youtube.com") || host.includes("youtube-nocookie.com")) {
      // NOTE: enablejsapi=1 requires a matching origin= query parameter that
      // YouTube only validates as http(s) origin. Our app runs under
      // janus://app (packaged) or http://localhost (dev), which causes
      // Error 153 ("Video player configuration error"). We intentionally do
      // NOT set enablejsapi here. pauseVideoPlayback/resumeVideoPlayback via
      // postMessage will be no-ops (player ignores without JS API), but the
      // video itself plays fine with the native controls.
      u.searchParams.delete("enablejsapi");
      if (!u.searchParams.has("rel")) u.searchParams.set("rel", "0");
    } else if (host.includes("vimeo.com")) {
      if (!u.searchParams.has("api")) u.searchParams.set("api", "1");
    }
    return u.toString();
  } catch {
    return s;
  }
}

function resolveEmbedSrc(payload) {
  if (!payload || typeof payload !== "object") return null;
  const direct = String(payload.embed_url || "").trim();
  if (direct && isWhitelistedEmbedUrl(direct)) return enrichEmbedUrlForApi(direct);
  const fromUrl = normalizeVideoEmbedUrl(payload.url);
  if (fromUrl && isWhitelistedEmbedUrl(fromUrl)) return enrichEmbedUrlForApi(fromUrl);
  return null;
}

function postToIframe(message) {
  const iframe = document.getElementById("video-player-iframe");
  const src = String(iframe?.getAttribute("src") || "");
  if (!iframe?.contentWindow || !src) return;
  try {
    iframe.contentWindow.postMessage(message, "*");
  } catch {
    /* ignore cross-origin postMessage errors */
  }
}

function pauseVideoPlayback() {
  const iframe = document.getElementById("video-player-iframe");
  const src = String(iframe?.getAttribute("src") || "").toLowerCase();
  if (!src || src === "about:blank") return;
  if (src.includes("youtube.com/embed") || src.includes("youtube-nocookie.com/embed")) {
    postToIframe('{"event":"command","func":"pauseVideo","args":""}');
    return;
  }
  if (src.includes("player.vimeo.com/video/")) {
    postToIframe({ method: "pause" });
  }
}

function resumeVideoPlayback() {
  const iframe = document.getElementById("video-player-iframe");
  const src = String(iframe?.getAttribute("src") || "").toLowerCase();
  if (!src || src === "about:blank") return;
  if (src.includes("youtube.com/embed") || src.includes("youtube-nocookie.com/embed")) {
    postToIframe('{"event":"command","func":"playVideo","args":""}');
    return;
  }
  if (src.includes("player.vimeo.com/video/")) {
    postToIframe({ method: "play" });
  }
}

function setVisible(show) {
  const el = document.getElementById("video-player-modal");
  if (!el) return;
  if (show) {
    el.classList.add("video-player-mcl-host--open");
    el.style.display = "flex";
  } else {
    el.classList.remove("video-player-mcl-host--open");
    el.style.display = "none";
  }
}

function applyDefaultDockLayout(hostEl) {
  const content = hostEl?.querySelector(".video-player-mcl-content");
  if (!hostEl || !content) return;
  const maxWidth = Math.max(480, Math.min(800, window.innerWidth - 32));
  const maxHeight = Math.round((maxWidth * 9) / 16);
  hostEl.style.justifyContent = "flex-start";
  hostEl.style.alignItems = "flex-start";
  const chatB = document.getElementById("chat-window-B");
  const chatBRect = chatB?.getBoundingClientRect?.();
  const chatBVisible =
    !!chatBRect &&
    Number.isFinite(chatBRect.left) &&
    Number.isFinite(chatBRect.top) &&
    chatBRect.width > 0 &&
    chatBRect.height > 0;
  let left = null;
  let top = null;
  if (chatBVisible) {
    left = Math.round(chatBRect.left);
    top = Math.round(chatBRect.top);
  } else {
    // Fallback: derive virtual B anchor from current chat-window-A geometry.
    const chatA = document.getElementById("chat-window-A");
    const chatARect = chatA?.getBoundingClientRect?.();
    const chatAVisible =
      !!chatARect &&
      Number.isFinite(chatARect.left) &&
      Number.isFinite(chatARect.top) &&
      chatARect.width > 0 &&
      chatARect.height > 0;
    if (chatAVisible) {
      left = Math.round(chatARect.left + chatARect.width + 1);
      top = Math.round(chatARect.top);
    }
  }
  if (!Number.isFinite(left) || !Number.isFinite(top)) {
    left = Math.max(0, window.innerWidth - maxWidth - 16);
    top = 16;
  }
  content.style.transform = "none";
  content.style.width = `${maxWidth}px`;
  content.style.maxWidth = `${maxWidth}px`;
  content.style.height = `${maxHeight}px`;
  content.style.position = "fixed";
  content.style.left = `${left}px`;
  content.style.top = `${top}px`;
  content.style.margin = "0";
  content.style.padding = "12px";
  content.setAttribute("data-x", String(left));
  content.setAttribute("data-y", String(top));
}

function resetVideoWindow() {
  const hostEl = document.getElementById("video-player-modal");
  const content = hostEl?.querySelector(".video-player-mcl-content");
  if (!hostEl || !content) return;
  content.style.transform = "none";
  content.removeAttribute("data-x");
  content.removeAttribute("data-y");
  applyDefaultDockLayout(hostEl);
}

function clampVideoRect(content) {
  if (!content) return;
  const width = content.offsetWidth;
  const height = content.offsetHeight;
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) return;
  let x = parseFloat(content.getAttribute("data-x"));
  let y = parseFloat(content.getAttribute("data-y"));
  if (!Number.isFinite(x)) x = parseFloat(content.style.left) || content.offsetLeft || 0;
  if (!Number.isFinite(y)) y = parseFloat(content.style.top) || content.offsetTop || 0;
  const maxX = Math.max(0, window.innerWidth - width);
  const maxY = Math.max(0, window.innerHeight - height);
  x = Math.max(0, Math.min(x, maxX));
  y = Math.max(0, Math.min(y, maxY));
  content.style.left = `${x}px`;
  content.style.top = `${y}px`;
  content.style.transform = "none";
  content.setAttribute("data-x", String(x));
  content.setAttribute("data-y", String(y));
}

function persistVideoGeometry(content) {
  if (!content) return;
  const left = parseFloat(content.style.left) || content.offsetLeft || 0;
  const top = parseFloat(content.style.top) || content.offsetTop || 0;
  const width = content.offsetWidth || parseFloat(content.style.width) || 800;
  const height = content.offsetHeight || parseFloat(content.style.height) || 450;
  registerDockModule(MODULE_ID, {
    position: { x: Math.round(left), y: Math.round(top) },
    size: { w: Math.round(width), h: Math.round(height) },
  });
}

function initInteractions(root) {
  const content = root?.querySelector(".video-player-mcl-content");
  if (!content) return;
  interact(content).resizable({
      edges: {
        right: ".video-player-resize-handle--right, .video-player-resize-handle--corner",
        bottom: ".video-player-resize-handle--bottom, .video-player-resize-handle--corner",
      },
      inertia: true,
      modifiers: [
        interact.modifiers.restrictEdges({ outer: "parent" }),
        interact.modifiers.restrictSize({ min: { width: 420, height: 260 } }),
      ],
      listeners: {
        move(event) {
          const target = event.target;
          const width = Math.round(event.rect.width);
          const height = Math.round(event.rect.height);
          let x = (parseFloat(target.getAttribute("data-x")) || 0) + event.deltaRect.left;
          let y = (parseFloat(target.getAttribute("data-y")) || 0) + event.deltaRect.top;
          const maxX = Math.max(0, window.innerWidth - width);
          const maxY = Math.max(0, window.innerHeight - height);
          x = Math.max(0, Math.min(x, maxX));
          y = Math.max(0, Math.min(y, maxY));
          target.style.width = `${width}px`;
          target.style.height = `${height}px`;
          target.style.left = `${x}px`;
          target.style.top = `${y}px`;
          target.style.transform = "none";
          target.setAttribute("data-x", String(x));
          target.setAttribute("data-y", String(y));
        },
        end(event) {
          persistVideoGeometry(event.target);
          positionTranscriptAboveVideo(); // Re-align after resize
        },
      },
    });
}

function initHeaderDrag(root) {
  const content = root?.querySelector(".video-player-mcl-content");
  const header = root?.querySelector(".dock-panel-header");
  if (!content || !header) return;
  header.addEventListener("mousedown", (event) => {
    // Ignore clicks on control buttons; only drag from free header space.
    if (event.target.closest("button")) return;
    dragActive = true;
    dragOffsetX = event.clientX - content.offsetLeft;
    dragOffsetY = event.clientY - content.offsetTop;
    event.preventDefault();
  });
  document.addEventListener("mousemove", (event) => {
    if (!dragActive) return;
    const maxX = Math.max(0, window.innerWidth - content.offsetWidth);
    const maxY = Math.max(0, window.innerHeight - content.offsetHeight);
    const x = Math.max(0, Math.min(event.clientX - dragOffsetX, maxX));
    const y = Math.max(0, Math.min(event.clientY - dragOffsetY, maxY));
    content.style.left = `${x}px`;
    content.style.top = `${y}px`;
    content.style.transform = "none";
    content.setAttribute("data-x", String(x));
    content.setAttribute("data-y", String(y));
  });
  document.addEventListener("mouseup", () => {
    if (dragActive) {
      persistVideoGeometry(content);
      positionTranscriptAboveVideo(); // Re-align after drag
    }
    dragActive = false;
  });
}

function clearIframe() {
  const iframe = document.getElementById("video-player-iframe");
  if (iframe) iframe.src = "about:blank";
  clearFallbackLink();
}

function resolveExternalWatchUrl(payload) {
  if (!payload || typeof payload !== "object") return null;
  const u = String(payload.url || "").trim();
  if (u && /^https?:\/\//i.test(ensureHttp(u))) return ensureHttp(u);
  const emb = String(payload.embed_url || "");
  const ym = emb.match(/youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/i);
  if (ym) return `https://www.youtube.com/watch?v=${ym[1]}`;
  const vm = emb.match(/player\.vimeo\.com\/video\/(\d+)/i);
  if (vm) return `https://vimeo.com/${vm[1]}`;
  return null;
}

function setFallbackLink(payload) {
  const line = document.getElementById("video-player-fallback-line");
  const a = document.getElementById("video-player-external-link");
  const muted = document.querySelector("#video-player-fallback-line .video-player-fallback-muted");
  if (!line || !a) return;
  const ext = resolveExternalWatchUrl(payload);
  const externalOnly = !!payload?.external_only || payload?.is_embeddable === false;
  if (ext) {
    a.href = ext;
    const src = String(payload.source || "").toLowerCase();
    a.textContent = src === "vimeo" ? "Auf Vimeo öffnen" : "Auf YouTube öffnen";
    if (muted) {
      muted.textContent = externalOnly
        ? String(payload.external_hint || "Nur direkt auf YouTube verfügbar.")
        : "Spielt nicht ab?";
    }
    // v0.4.16-beta.7: Always show the external-open button, not only on error.
    // Error 153 (YouTube player config error) cannot be detected via iframe.onerror
    // because the iframe itself loads (HTTP 200) and the error is only displayed
    // by the YouTube player JS inside the cross-origin iframe. Giving users a
    // one-click escape hatch is the most reliable workaround for all embed issues
    // (restricted mode, embeds disabled, regional blocks, corporate firewalls).
    line.hidden = false;
    // Route click through Electron shell.openExternal when available to ensure
    // the link actually opens in the user's default OS browser (which works in
    // scenarios where the in-app embed doesn't).
    if (!a.dataset.electronBound) {
      a.dataset.electronBound = "1";
      a.addEventListener("click", (ev) => {
        const url = a.getAttribute("href") || "";
        if (!url || url === "#") return;
        if (window.electron && typeof window.electron.openExternalLink === "function") {
          ev.preventDefault();
          try {
            window.electron.openExternalLink(url);
          } catch (err) {
            console.warn("openExternalLink failed, falling back to target=_blank", err);
          }
        }
        // else: normal target="_blank" behaviour (dev in browser)
      });
    }
  } else {
    line.hidden = true;
    a.removeAttribute("href");
    if (muted) muted.textContent = "Spielt nicht ab?";
  }
}

function clearFallbackLink() {
  const line = document.getElementById("video-player-fallback-line");
  const a = document.getElementById("video-player-external-link");
  if (line) line.hidden = true;
  if (a) a.removeAttribute("href");
}

function applyPayload(payload) {
  const iframe = document.getElementById("video-player-iframe");
  const titleEl = document.getElementById("video-player-modal-title");
  if (!iframe) return;
  const externalOnly = !!payload?.external_only || payload?.is_embeddable === false;
  if (externalOnly) {
    clearIframe();
    const t = payload && typeof payload.title === "string" && payload.title.trim();
    if (titleEl) titleEl.textContent = t || "Video";
    setFallbackLink(payload || {});
    return;
  }
  const src = resolveEmbedSrc(payload);
  if (!src) {
    clearIframe();
    return;
  }
  const currentSrc = String(iframe.getAttribute("src") || "").trim();
  if (currentSrc !== src) {
    iframe.src = src;
  }
  const t = payload && typeof payload.title === "string" && payload.title.trim();
  if (titleEl) titleEl.textContent = t || "Video";
  setFallbackLink(payload);
  
  // Auto-show fallback link if iframe fails to load (YouTube Error 153, etc.)
  iframe.onerror = () => {
    console.warn("Video iframe failed to load, showing fallback link");
    const fallbackLine = document.getElementById("video-player-fallback-line");
    if (fallbackLine) fallbackLine.hidden = false;
  };
  
  // Also listen for load errors via postMessage (YouTube specific)
  window.addEventListener("message", (event) => {
    if (event.origin !== "https://www.youtube.com" && event.origin !== "https://player.vimeo.com") return;
    if (event.data && event.data.event === "error") {
      console.warn("Video player error event:", event.data);
      const fallbackLine = document.getElementById("video-player-fallback-line");
      if (fallbackLine) fallbackLine.hidden = false;
    }
  });
}

function syncFromState() {
  const mod = getDockModuleState(MODULE_ID);
  if (!mod || !mod.exists) {
    setVisible(false);
    clearIframe();
    wasVisible = false;
    return;
  }
  if (mod.isOpen && !mod.minimized) {
    const wasHidden = !wasVisible;
    setVisible(true);
    const host = document.getElementById("video-player-modal");
    if (host && !wasVisible) {
      applyDefaultDockLayout(host);
    }
    wasVisible = true;
    applyPayload(mod.payload);
    if (wasHidden) {
      setTimeout(() => resumeVideoPlayback(), 80);
    }
  } else {
    if (mod.isOpen && mod.minimized) {
      pauseVideoPlayback();
      setVisible(false);
      wasVisible = false;
      return;
    }
    setVisible(false);
    clearIframe();
    wasVisible = false;
  }
}

function onClose() {
  clearIframe();
  closeModal(MODULE_ID);
}

function initVideoPlayerMcl() {
  const root = document.getElementById("video-player-modal");
  const closeBtn = document.getElementById("close-video-player-modal");
  const minimizeBtn = document.getElementById("video-player-minimize-btn");
  const resetBtn = document.getElementById("video-player-reset-btn");
  const header = root?.querySelector(".dock-panel-header");
  initInteractions(root);
  initHeaderDrag(root);

  closeBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    // Hide analysis status when modal is closed
    const statusEl = document.getElementById("video-analysis-status");
    if (statusEl) {
      statusEl.style.display = "none";
    }
    onClose();
  });
  minimizeBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    pauseVideoPlayback();
    dockMinimize(MODULE_ID, true);
  });
  resetBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    resetVideoWindow();
  });

  // Brain button for video analysis - Event Delegation for robustness
  const modal = document.getElementById("video-player-modal");
  modal?.addEventListener("click", (e) => {
    const analyzeBtn = e.target.closest("#btn-video-analyze");
    if (!analyzeBtn) return;

    e.preventDefault();
    e.stopPropagation();
    console.log("🧠 Brain-Button geklickt!");

    // Check if transcript-modal is already minimized and reopen it
    const transcriptModal = document.getElementById("transcript-modal");
    const transcriptDockState = getDockModuleState(TRANSCRIPT_MODULE_ID);

    console.log("🔍 Dock-Status beim Brain-Button-Klick:", transcriptDockState);

    if (transcriptDockState?.isOpen && transcriptDockState?.minimized) {
      console.log("🔄 Transkript ist minimiert, wird wieder geöffnet...");
      dockOpen(TRANSCRIPT_MODULE_ID);
      return;
    }

    console.log("🧠 Starte direkte API-Analyse...");

    // INSTANT REVEAL: Open transcript-modal with loading animation IMMEDIATELY
    if (!transcriptModal) {
      console.error("❌ transcript-modal element NOT FOUND!");
      return;
    }
    transcriptModal.classList.add('dock-panel--open'); // CSS handles everything

    // Register transcript-modal as dock module
    registerDockModule(TRANSCRIPT_MODULE_ID, {
      type: 'transcript',
      payload: null,
      zIndex: 1000000,
      position: { x: 892, y: 480 },
      size: { w: 800, h: 450 },
      isOpen: true,
      minimized: false,
    });

    // Positioniere Transkript GENAU ÜBER Video (direkt ohne Verzögerung)
    const videoModal = document.getElementById('video-player-modal');
    console.log("🎯 Video-Modal gefunden:", videoModal);
    if (videoModal) {
      const videoRect = videoModal.getBoundingClientRect();
      console.log("📐 Video-Rect:", videoRect);
      transcriptModal.style.left = videoRect.left + 'px';
      transcriptModal.style.top = videoRect.top + 'px';
      transcriptModal.style.width = videoRect.width + 'px';
      transcriptModal.style.height = '450px';
      console.log("📍 Transkript positioniert bei:", { left: videoRect.left, top: videoRect.top, width: videoRect.width });
    } else {
      console.error("❌ Video-Modal nicht gefunden!");
    }

    // Icons initialisieren (Lucide Fix)
    if (window.lucide) window.lucide.createIcons();

    const transcriptLoading = document.getElementById("transcript-loading");
    const transcriptResult = document.getElementById("transcript-result");

    console.log("📋 Modal elements:", { transcriptModal, transcriptLoading, transcriptResult });

    if (transcriptModal) {
      console.log("✅ Opening modal now...");

      // Add open class (CSS handles display)
      transcriptModal.classList.add("dock-panel--open");

      transcriptLoading.style.display = "block";
      transcriptResult.style.display = "none";

      console.log("🎨 After class add, display is:", window.getComputedStyle(transcriptModal).display);

      console.log("🎨 Modal opened, classes:", transcriptModal.className);
    } else {
      console.error("❌ transcript-modal element NOT FOUND!");
    }

    // Extract video_id from current video URL
    const iframe = root?.querySelector("iframe");
    if (!iframe) {
      console.error("❌ No iframe found in video player");
      return;
    }
    const src = iframe.src || "";
    const videoIdMatch = src.match(/(?:embed\/|v=)([a-zA-Z0-9_-]{11})/);
    const videoId = videoIdMatch ? videoIdMatch[1] : null;

    if (videoId) {
      console.log("🚀 Starting API call for video:", videoId);
      // Call API directly
      fetch("/api/video/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ video_id: videoId }),
      })
        .then((response) => {
          console.log("📡 API response received:", response.status);
          return response.json();
        })
        .then((data) => {
          console.log("📊 Analyse-Ergebnis:", data);

          // Trigger cost update event for sidebar/dashboard refresh
          window.dispatchEvent(new CustomEvent('janus:cost-update'));

          // Populate modal with data
          const summaryEl = document.getElementById("transcript-summary");
          const keyPointsEl = document.getElementById("transcript-key-points");

          console.log("📝 Elements found:", { summaryEl, keyPointsEl, transcriptLoading, transcriptResult });

          if (summaryEl) {
            summaryEl.textContent = data.summary || "Keine Zusammenfassung verfügbar.";
            console.log("✅ Summary written to DOM");
          } else {
            console.error("❌ transcript-summary element not found!");
          }

          if (keyPointsEl && data.key_points) {
            keyPointsEl.innerHTML = "";
            data.key_points.forEach((point) => {
              const li = document.createElement("li");
              li.textContent = point;
              keyPointsEl.appendChild(li);
            });
            console.log("✅ Key points written to DOM");
          }

          // Icons initialisieren (Lucide Fix)
          if (window.lucide) window.lucide.createIcons();

          // Re-align after content is loaded
          positionTranscriptAboveVideo();

          // Scroll nach oben
          const modalContent = transcriptModal.querySelector('.modal-content');
          if (modalContent) modalContent.scrollTop = 0;

          // Hide loading, show result
          if (transcriptLoading) {
            transcriptLoading.style.display = "none";
            console.log("🔄 Loading hidden");
          }
          if (transcriptResult) {
            transcriptResult.style.display = "block";
            console.log("👁️ Result area shown");
            // Auto-scroll to top of transcript content
            const transcriptContent = document.getElementById("transcript-content");
            if (transcriptContent) {
              transcriptContent.scrollTop = 0;
            }
          }
        })
        .catch((error) => {
          console.error("❌ Analyse fehlgeschlagen:", error);
          if (transcriptLoading) transcriptLoading.style.display = "none";
          const summaryEl = document.getElementById("transcript-summary");
          if (summaryEl) summaryEl.textContent = "Fehler bei der Analyse: " + error.message;
          if (transcriptResult) transcriptResult.style.display = "block";
        });
    } else {
      console.error("❌ No video ID found in iframe src:", src);
    }
  });

  // Update transcript position when video-modal is dragged
  // No longer needed - CSS handles alignment through DOM nesting

  // Close transcript-modal when video-modal is closed
  const closeVideoBtn = document.getElementById("close-video-player-modal");
  if (closeVideoBtn) {
    closeVideoBtn.addEventListener("click", () => {
      const transcriptModal = document.getElementById("transcript-modal");
      if (transcriptModal) {
        transcriptModal.classList.remove("dock-panel--open");
      }
    });
  }

  // Close transcript-modal when close button is clicked
  const closeTranscriptBtn = document.getElementById("transcript-close-btn");
  if (closeTranscriptBtn) {
    closeTranscriptBtn.addEventListener("click", () => {
      dockClose(TRANSCRIPT_MODULE_ID);
    });
  }

  // Register transcript-modal as dock module
  setDockModuleExists(TRANSCRIPT_MODULE_ID, true);

  // Dock state synchronization for transcript-modal
  const syncTranscriptFromDockState = () => {
    const m = getDockModuleState(TRANSCRIPT_MODULE_ID);
    const visible = !!m?.isOpen && !m?.minimized;
    const transcriptModal = document.getElementById("transcript-modal");
    if (transcriptModal) {
      transcriptModal.classList.toggle("dock-panel--open", visible);
    }
    // Update dock button minimized state
    const dockTranscriptBtn = document.getElementById("dock-transcript");
    if (dockTranscriptBtn) {
      dockTranscriptBtn.classList.toggle("is-minimized", !!m?.isOpen && !!m?.minimized);
    }
  };

  subscribeWindowState(syncTranscriptFromDockState);

  // Event listener for dock-transcript button
  const dockTranscriptBtn = document.getElementById("dock-transcript");
  if (dockTranscriptBtn) {
    dockTranscriptBtn.addEventListener("click", () => {
      dockOpen(TRANSCRIPT_MODULE_ID);
    });
  }

  // Minimize transcript-modal when minimize button is clicked
  const minimizeTranscriptBtn = document.getElementById("transcript-minimize-btn");
  if (minimizeTranscriptBtn) {
    minimizeTranscriptBtn.addEventListener("click", () => {
      dockMinimize(TRANSCRIPT_MODULE_ID, true);
    });
  }

  // Reset transcript-modal to initial position when reset button is clicked
  const resetTranscriptBtn = document.getElementById("transcript-reset-btn");
  if (resetTranscriptBtn) {
    resetTranscriptBtn.addEventListener("click", () => {
      const transcriptModal = document.getElementById("transcript-modal");
      if (transcriptModal) {
        transcriptModal.style.top = '480px';
        transcriptModal.style.left = '892px';
        transcriptModal.style.width = '800px';
        transcriptModal.style.height = '450px';
      }
    });
  }

  // Klick-Blockade für transcript-modal
  const tModal = document.getElementById('transcript-modal');
  if (tModal) {
    // Verhindert, dass Klick-Events an das darunterliegende Video-Modal weitergegeben werden
    tModal.addEventListener('click', (e) => {
      e.stopPropagation();
    });
    // Verhindert auch Scroll-Interferenzen
    tModal.addEventListener('wheel', (e) => {
      e.stopPropagation();
    }, { passive: false });
  }

  // Drag-Funktionalität für transcript-modal
  const transcriptModal = document.getElementById('transcript-modal');
  const transcriptHeader = transcriptModal?.querySelector('.transcript-mcl-header');
  const transcriptContent = transcriptModal?.querySelector('.transcript-mcl-content');

  if (transcriptModal && transcriptHeader && transcriptContent) {
    let transcriptDragActive = false;
    let transcriptDragOffsetX = 0;
    let transcriptDragOffsetY = 0;

    transcriptHeader.addEventListener('mousedown', (event) => {
      if (event.target.closest('button')) return;
      transcriptDragActive = true;
      transcriptDragOffsetX = event.clientX - transcriptContent.offsetLeft;
      transcriptDragOffsetY = event.clientY - transcriptContent.offsetTop;
      event.preventDefault();
    });

    document.addEventListener('mousemove', (event) => {
      if (!transcriptDragActive) return;
      const maxX = Math.max(0, window.innerWidth - transcriptContent.offsetWidth);
      const maxY = Math.max(0, window.innerHeight - transcriptContent.offsetHeight);
      const x = Math.max(0, Math.min(event.clientX - transcriptDragOffsetX, maxX));
      const y = Math.max(0, Math.min(event.clientY - transcriptDragOffsetY, maxY));
      transcriptContent.style.left = `${x}px`;
      transcriptContent.style.top = `${y}px`;
      transcriptContent.style.transform = 'none';
      transcriptContent.setAttribute('data-x', String(x));
      transcriptContent.setAttribute('data-y', String(y));
    });

    document.addEventListener('mouseup', () => {
      if (transcriptDragActive) {
        transcriptDragActive = false;
      }
    });
  }

  // Resize-Funktionalität für transcript-modal
  const transcriptResizeHandles = transcriptModal?.querySelectorAll('.transcript-resize-handle');
  if (transcriptModal && transcriptContent && transcriptResizeHandles.length > 0) {
    let transcriptResizeActive = false;
    let transcriptResizeType = '';
    let transcriptResizeStartX = 0;
    let transcriptResizeStartY = 0;
    let transcriptResizeStartWidth = 0;
    let transcriptResizeStartHeight = 0;

    transcriptResizeHandles.forEach(handle => {
      handle.addEventListener('mousedown', (event) => {
        transcriptResizeActive = true;
        transcriptResizeType = handle.classList.contains('transcript-resize-handle--right') ? 'right' :
                              handle.classList.contains('transcript-resize-handle--bottom') ? 'bottom' : 'corner';
        transcriptResizeStartX = event.clientX;
        transcriptResizeStartY = event.clientY;
        transcriptResizeStartWidth = transcriptContent.offsetWidth;
        transcriptResizeStartHeight = transcriptContent.offsetHeight;
        event.preventDefault();
      });
    });

    document.addEventListener('mousemove', (event) => {
      if (!transcriptResizeActive) return;
      const deltaX = event.clientX - transcriptResizeStartX;
      const deltaY = event.clientY - transcriptResizeStartY;

      if (transcriptResizeType === 'right' || transcriptResizeType === 'corner') {
        const newWidth = Math.max(400, transcriptResizeStartWidth + deltaX);
        transcriptContent.style.width = `${newWidth}px`;
      }

      if (transcriptResizeType === 'bottom' || transcriptResizeType === 'corner') {
        const newHeight = Math.max(300, transcriptResizeStartHeight + deltaY);
        transcriptContent.style.height = `${newHeight}px`;
      }
    });

    document.addEventListener('mouseup', () => {
      if (transcriptResizeActive) {
        transcriptResizeActive = false;
      }
    });
  }

  header?.addEventListener("pointerdown", () => {
    bringToFront(MODULE_ID);
  });

  window.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const mod = getDockModuleState(MODULE_ID);
    if (mod?.isOpen && !mod.minimized) onClose();
  });
  window.addEventListener("resize", () => {
    const mod = getDockModuleState(MODULE_ID);
    if (!mod?.isOpen || mod.minimized) return;
    const content = document.querySelector("#video-player-modal .video-player-mcl-content");
    if (content) clampVideoRect(content);
  });

  window.addEventListener("janus:modal-event", (e) => {
    const d = e.detail;
    if (!d || d.modalId !== MODULE_ID) return;
    if (d.event === "opened" || d.event === "focus") syncFromState();
    if (d.event === "closed") {
      setVisible(false);
      clearIframe();
    }
  });

  subscribeWindowState(() => syncFromState());
  syncFromState();
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initVideoPlayerMcl, { once: true });
  } else {
    initVideoPlayerMcl();
  }
}
