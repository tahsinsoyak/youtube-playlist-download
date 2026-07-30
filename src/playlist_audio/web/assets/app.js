import { JobView } from "./job-view.js";

const form = document.querySelector("#download-form");
const urlInput = document.querySelector("#url");
const browserSelect = document.querySelector("#browser");
const browserProfile = document.querySelector("#browser-profile");
const dryRun = document.querySelector("#dry-run");
const submitButton = document.querySelector("#submit-button");
const buttonLabel = document.querySelector("#button-label");
const healthBadge = document.querySelector("#health-badge");
const jobView = new JobView();

let pollTimer = null;
let hasQueuedWork = false;
let isSubmitting = false;
let pendingPreviewJobId = null;
let previewReady = false;

function currentBrowser() {
  const agent = navigator.userAgent;
  if (agent.includes("Edg/")) return "edge";
  if (agent.includes("Firefox/")) return "firefox";
  if (agent.includes("OPR/")) return "opera";
  if (agent.includes("Chrome/")) return "chrome";
  return null;
}

function browserLabel(value) {
  return browserSelect.querySelector(`option[value="${value}"]`)?.textContent || value;
}

function updateModeLabel() {
  const isPreview = dryRun.checked;
  dryRun.closest(".toggle").querySelector("b").textContent = isPreview ? "Açık" : "Kapalı";

  if (isSubmitting) {
    buttonLabel.textContent = "Sıraya ekleniyor";
  } else if (hasQueuedWork) {
    buttonLabel.textContent = isPreview
      ? "Önizlemeyi sıraya ekle"
      : "Playlisti sıraya ekle";
  } else if (previewReady && !isPreview) {
    buttonLabel.textContent = "Kontrol tamam — MP3 indir";
  } else {
    buttonLabel.textContent = isPreview ? "Önizlemeyi başlat" : "MP3 indirmeyi başlat";
  }
}

function updateBrowserProfile() {
  browserProfile.disabled = !browserSelect.value;
  if (browserProfile.disabled) {
    browserProfile.value = "";
  }

  const browserHint = document.querySelector("#browser-hint");
  const selected = browserSelect.value;
  const chromiumBrowsers = ["brave", "chrome", "chromium", "edge", "opera", "vivaldi"];
  if (selected && selected === currentBrowser()) {
    browserHint.textContent =
      `Bu arayüz ${browserLabel(selected)}’da açık. Oturum kaynağı olarak ` +
      "tamamen kapalı başka bir tarayıcı seçin.";
  } else if (chromiumBrowsers.includes(selected)) {
    browserHint.textContent =
      "Windows’ta seçili tarayıcı tamamen kapalı olmalı; açıkken cookie kasası kilitlenir.";
  } else if (selected === "firefox") {
    browserHint.textContent = "Sorun yaşarsanız Firefox’u tamamen kapatıp yeniden deneyin.";
  } else {
    browserHint.textContent = "";
  }
}

function setSubmitting(value) {
  isSubmitting = value;
  submitButton.disabled = value;
  updateModeLabel();
}

function formPayload() {
  const data = new FormData(form);
  return {
    url: data.get("url"),
    output: data.get("output"),
    browser: data.get("browser"),
    browser_profile: data.get("browser_profile"),
    audio_quality: data.get("audio_quality"),
    playlist_items: data.get("playlist_items"),
    dry_run: data.has("dry_run"),
    embed_thumbnail: data.has("embed_thumbnail"),
    embed_metadata: data.has("embed_metadata"),
    confirm_rights: data.has("confirm_rights"),
  };
}

function schedulePoll() {
  window.clearTimeout(pollTimer);
  if (hasQueuedWork) {
    pollTimer = window.setTimeout(refreshJobs, 700);
  }
}

async function refreshJobs() {
  try {
    const response = await fetch("/api/jobs");
    const snapshot = await response.json();
    if (!response.ok) {
      throw new Error(snapshot.error || "Kuyruk durumu okunamadı.");
    }
    const previewJob = (snapshot.recent || []).find(
      (job) => job.id === pendingPreviewJobId,
    );
    if (previewJob?.state === "completed") {
      pendingPreviewJobId = null;
      previewReady = true;
      dryRun.checked = false;
    } else if (previewJob?.state === "failed") {
      pendingPreviewJobId = null;
      previewReady = false;
    }
    hasQueuedWork = jobView.renderSnapshot(snapshot);
    updateModeLabel();
    schedulePoll();
  } catch (error) {
    jobView.showError(error.message);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (browserSelect.value && browserSelect.value === currentBrowser()) {
    jobView.showError(
      `Arayüz ${browserLabel(browserSelect.value)}’da açık olduğu için bu oturum ` +
        "kilitli. Public playlist seçin veya tamamen kapalı başka bir tarayıcı kullanın.",
    );
    return;
  }

  setSubmitting(true);
  try {
    const payload = formPayload();
    const response = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "İş sıraya eklenemedi.");
    }
    if (payload.dry_run) {
      pendingPreviewJobId = result.id;
      previewReady = false;
    } else {
      pendingPreviewJobId = null;
      previewReady = false;
      urlInput.value = "";
    }
    await refreshJobs();
    urlInput.focus();
  } catch (error) {
    jobView.showError(error.message);
  } finally {
    setSubmitting(false);
  }
});

browserSelect.addEventListener("change", updateBrowserProfile);
dryRun.addEventListener("change", () => {
  if (dryRun.checked) {
    previewReady = false;
  }
  updateModeLabel();
});
urlInput.addEventListener("input", () => {
  pendingPreviewJobId = null;
  previewReady = false;
  updateModeLabel();
});

fetch("/api/health")
  .then(async (response) => {
    if (!response.ok) throw new Error();
    await response.json();
    healthBadge.dataset.connected = "true";
  })
  .catch(() => {
    healthBadge.querySelector("span:last-child").textContent = "Bağlantı sorunu";
  });

updateBrowserProfile();
updateModeLabel();
refreshJobs();
