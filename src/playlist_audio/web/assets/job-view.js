import { formatEta, formatSpeed, formatTransfer } from "./formatters.js";

const STATE_LABELS = {
  queued: "SIRADA",
  completed: "TAMAMLANDI",
  failed: "HATA",
};

export class JobView {
  constructor() {
    this.statusPanel = document.querySelector("#job-status");
    this.jobState = document.querySelector("#job-state");
    this.jobMessage = document.querySelector("#job-message");
    this.jobItem = document.querySelector("#job-item");
    this.jobProgress = document.querySelector("#job-progress");
    this.jobPercent = document.querySelector("#job-percent");
    this.metricTrack = document.querySelector("#metric-track");
    this.metricSpeed = document.querySelector("#metric-speed");
    this.metricBytes = document.querySelector("#metric-bytes");
    this.metricEta = document.querySelector("#metric-eta");
    this.queuePanel = document.querySelector("#queue-panel");
    this.queueCount = document.querySelector("#queue-count");
    this.queueList = document.querySelector("#queue-list");
  }

  showError(message) {
    this.statusPanel.hidden = false;
    this.statusPanel.dataset.state = "failed";
    this.jobState.textContent = "HATA";
    this.jobMessage.textContent = message;
    this.jobItem.textContent = "Ayarları kontrol edip yeniden deneyin.";
    this.jobProgress.removeAttribute("value");
    this.jobPercent.textContent = "";
    this._renderMetrics({});
  }

  renderSnapshot(snapshot) {
    const active = snapshot.active;
    const recent = snapshot.recent || [];
    const displayJob = active || recent[0];

    if (displayJob) {
      this._renderJob(displayJob);
    } else {
      this.statusPanel.hidden = true;
    }
    this._renderQueue(snapshot.queued || []);
    return Boolean(active || (snapshot.queued || []).length);
  }

  _renderJob(job) {
    this.statusPanel.hidden = false;
    this.statusPanel.dataset.state = job.state;
    this.jobState.textContent =
      job.state === "running"
        ? job.dry_run
          ? "ÖNİZLEME"
          : "KAYIT"
        : STATE_LABELS[job.state] || "İŞLENİYOR";
    this.jobMessage.textContent = job.message;
    this.jobItem.textContent =
      job.current_item || job.playlist_title || `Hedef: ${job.output}`;

    if (typeof job.progress === "number") {
      const rounded = Math.round(job.progress);
      this.jobProgress.value = rounded;
      this.jobPercent.textContent = `%${rounded}`;
    } else {
      this.jobProgress.removeAttribute("value");
      this.jobPercent.textContent = "";
    }
    this._renderMetrics(job);
  }

  _renderMetrics(job) {
    this.metricTrack.textContent =
      job.item_index && job.item_count ? `${job.item_index} / ${job.item_count}` : "—";
    this.metricSpeed.textContent = formatSpeed(job.speed);
    this.metricBytes.textContent = formatTransfer(job.downloaded_bytes, job.total_bytes);
    this.metricEta.textContent =
      job.state === "completed" ? "Bitti" : formatEta(job.eta);
  }

  _renderQueue(queued) {
    this.queuePanel.hidden = queued.length === 0;
    this.queueCount.textContent = `${queued.length} bekliyor`;
    this.queueList.replaceChildren();

    queued.forEach((job) => {
      const item = document.createElement("li");
      const copy = document.createElement("div");
      const title = document.createElement("strong");
      const detail = document.createElement("small");
      const position = document.createElement("span");

      title.textContent = `Playlist işi ${String(job.sequence).padStart(2, "0")}`;
      detail.textContent = job.dry_run ? "Güvenli önizleme" : `MP3 · ${job.output}`;
      position.className = "queue-position";
      position.textContent = `${job.queue_position}. sıra`;
      copy.append(title, detail);
      item.append(copy, position);
      this.queueList.append(item);
    });
  }
}
