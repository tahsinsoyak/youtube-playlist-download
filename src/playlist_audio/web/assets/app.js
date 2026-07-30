const form = document.querySelector("#download-form");
const browserSelect = document.querySelector("#browser");
const browserProfile = document.querySelector("#browser-profile");
const dryRun = document.querySelector("#dry-run");
const submitButton = document.querySelector("#submit-button");
const buttonLabel = document.querySelector("#button-label");
const statusPanel = document.querySelector("#job-status");
const jobState = document.querySelector("#job-state");
const jobMessage = document.querySelector("#job-message");
const jobItem = document.querySelector("#job-item");
const jobProgress = document.querySelector("#job-progress");
const jobPercent = document.querySelector("#job-percent");
const healthBadge = document.querySelector("#health-badge");

let pollTimer = null;

function updateModeLabel() {
  const isPreview = dryRun.checked;
  buttonLabel.textContent = isPreview ? "Önizlemeyi başlat" : "MP3 indirmeyi başlat";
  dryRun.closest(".toggle").querySelector("b").textContent = isPreview ? "Açık" : "Kapalı";
}

function updateBrowserProfile() {
  browserProfile.disabled = !browserSelect.value;
  if (browserProfile.disabled) {
    browserProfile.value = "";
  }
}

function setBusy(busy) {
  submitButton.disabled = busy;
  form.querySelectorAll("input, select, summary").forEach((element) => {
    if (element !== submitButton) {
      element.toggleAttribute("aria-disabled", busy);
    }
  });
}

function showError(message) {
  statusPanel.hidden = false;
  statusPanel.dataset.state = "failed";
  jobState.textContent = "HATA";
  jobMessage.textContent = message;
  jobItem.textContent = "Ayarları kontrol edip yeniden deneyin.";
  jobProgress.removeAttribute("value");
  jobPercent.textContent = "";
  setBusy(false);
}

function renderJob(job) {
  statusPanel.hidden = false;
  statusPanel.dataset.state = job.state;
  jobState.textContent = {
    queued: "SIRADA",
    running: job.dry_run ? "ÖNİZLEME" : "KAYIT",
    completed: "TAMAMLANDI",
    failed: "HATA",
  }[job.state] || "İŞLENİYOR";
  jobMessage.textContent = job.message;
  jobItem.textContent = job.current_item || `Hedef: ${job.output}`;

  if (typeof job.progress === "number") {
    const rounded = Math.round(job.progress);
    jobProgress.value = rounded;
    jobPercent.textContent = `%${rounded}`;
  } else {
    jobProgress.removeAttribute("value");
    jobPercent.textContent = "";
  }

  if (job.state === "completed" || job.state === "failed") {
    window.clearTimeout(pollTimer);
    setBusy(false);
    if (job.state === "completed" && job.dry_run) {
      dryRun.checked = false;
      updateModeLabel();
      buttonLabel.textContent = "Kontrol tamam — MP3 indir";
    }
  }
}

async function pollJob(jobId) {
  try {
    const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`);
    const job = await response.json();
    if (!response.ok) {
      throw new Error(job.error || "İş durumu okunamadı.");
    }
    renderJob(job);
    if (job.state === "queued" || job.state === "running") {
      pollTimer = window.setTimeout(() => pollJob(jobId), 850);
    }
  } catch (error) {
    showError(error.message);
  }
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

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  window.clearTimeout(pollTimer);
  setBusy(true);
  statusPanel.hidden = false;
  statusPanel.dataset.state = "queued";
  jobState.textContent = "GÖNDERİLİYOR";
  jobMessage.textContent = "Ayarlar doğrulanıyor";
  jobItem.textContent = "";
  jobProgress.removeAttribute("value");
  jobPercent.textContent = "";

  try {
    const response = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formPayload()),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "İş başlatılamadı.");
    }
    renderJob(result);
    pollJob(result.id);
  } catch (error) {
    showError(error.message);
  }
});

browserSelect.addEventListener("change", updateBrowserProfile);
dryRun.addEventListener("change", updateModeLabel);

fetch("/api/health")
  .then(async (response) => {
    if (!response.ok) {
      throw new Error();
    }
    await response.json();
    healthBadge.dataset.connected = "true";
  })
  .catch(() => {
    healthBadge.querySelector("span:last-child").textContent = "Bağlantı sorunu";
  });

updateBrowserProfile();
updateModeLabel();
