/**
 * Pi-Detect — main.js
 * Polls /api/stats every second and updates the live metrics panel.
 */

const POLL_INTERVAL_MS = 1000;

const els = {
  statusDot:   document.getElementById("statusDot"),
  statusLabel: document.getElementById("statusLabel"),
  statFps:     document.getElementById("statFps"),
  statInference: document.getElementById("statInference"),
  statCount:   document.getElementById("statCount"),
  objectList:  document.getElementById("objectList"),
  configGrid:  document.getElementById("configGrid"),
  videoFeed:   document.getElementById("videoFeed"),
  videoOverlay: document.getElementById("videoOverlay"),
};

let consecutiveErrors = 0;

// ── Stats polling ──────────────────────────────────────────────────────────
async function fetchStats() {
  try {
    const res = await fetch("/api/stats", { cache: "no-store" });
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();

    setOnline();
    updateMetrics(data);
    consecutiveErrors = 0;
  } catch {
    consecutiveErrors++;
    if (consecutiveErrors >= 3) setOffline();
  }
}

function updateMetrics({ fps, inference_ms, detections, objects }) {
  els.statFps.textContent = fps ?? "—";
  els.statInference.innerHTML = inference_ms != null
    ? `${inference_ms}<span class="stat-unit">ms</span>`
    : "—";
  els.statCount.textContent = detections ?? "—";

  // Object list
  if (objects && objects.length > 0) {
    els.objectList.innerHTML = objects
      .map(o => `<li class="object-item">${o}</li>`)
      .join("");
  } else {
    els.objectList.innerHTML =
      `<li class="object-item object-item--empty">None detected</li>`;
  }
}

function setOnline() {
  els.statusDot.className  = "status-dot online";
  els.statusLabel.textContent = "Online";
}

function setOffline() {
  els.statusDot.className  = "status-dot offline";
  els.statusLabel.textContent = "Offline";
}

// ── Config panel ───────────────────────────────────────────────────────────
async function loadConfig() {
  try {
    const res  = await fetch("/api/config");
    const data = await res.json();
    els.configGrid.innerHTML = Object.entries(data)
      .map(([k, v]) => `
        <div class="config-item">
          <div class="config-key">${k.replace(/_/g, " ")}</div>
          <div class="config-val">${v}</div>
        </div>`)
      .join("");
  } catch {
    els.configGrid.innerHTML = `<p style="color:var(--text-muted);font-size:12px">Could not load config</p>`;
  }
}

// ── Video stream error handling ────────────────────────────────────────────
function handleStreamError() {
  els.videoOverlay.classList.add("visible");
  // Auto-retry after 3 s
  setTimeout(() => {
    els.videoFeed.src = "/stream/video?" + Date.now();
    els.videoOverlay.classList.remove("visible");
  }, 3000);
}

window.handleStreamError = handleStreamError;

// ── Snapshot ───────────────────────────────────────────────────────────────
async function takeSnapshot() {
  const res  = await fetch("/stream/snapshot");
  const blob = await res.blob();
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = `snapshot_${Date.now()}.jpg`;
  a.click();
  URL.revokeObjectURL(url);
}
window.takeSnapshot = takeSnapshot;

// ── Fullscreen ─────────────────────────────────────────────────────────────
function toggleFullscreen() {
  const wrapper = document.querySelector(".video-wrapper");
  if (!document.fullscreenElement) {
    wrapper.requestFullscreen();
  } else {
    document.exitFullscreen();
  }
}
window.toggleFullscreen = toggleFullscreen;

// ── Boot ───────────────────────────────────────────────────────────────────
loadConfig();
fetchStats();
setInterval(fetchStats, POLL_INTERVAL_MS);
