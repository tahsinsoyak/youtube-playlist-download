import { formatEta, formatSpeed, formatTransfer } from "./formatters.js";

const STATE_LABELS = {
  queued: "QUEUED",
  completed: "COMPLETE",
  failed: "ERROR",
};

export class JobView {
  constructor(onCancel, onRetry, onOpenFolder, onClearHistory) {
    this.onCancel = onCancel;
    this.onRetry = onRetry;
    this.onOpenFolder = onOpenFolder;
    this.onClearHistory = onClearHistory;
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
    this.cancelActiveButton = document.querySelector("#cancel-active-button");
    this.retryJobButton = document.querySelector("#retry-job-button");
    this.openFolderButton = document.querySelector("#open-folder-button");
    this.copyPathButton = document.querySelector("#copy-path-button");
    this.queuePanel = document.querySelector("#queue-panel");
    this.queueCount = document.querySelector("#queue-count");
    this.queueList = document.querySelector("#queue-list");
    this.historyPanel = document.querySelector("#history-panel");
    this.historyList = document.querySelector("#history-list");
    this.clearHistoryButton = document.querySelector("#clear-history-button");

    this.cancelActiveButton?.addEventListener("click", () => {
      if (this.currentJobId) this.onCancel?.(this.currentJobId);
    });
    this.retryJobButton?.addEventListener("click", () => {
      if (this.currentJobId) this.onRetry?.(this.currentJobId);
    });
    this.openFolderButton?.addEventListener("click", () => {
      if (this.currentJobId) this.onOpenFolder?.(this.currentJobId);
    });
    this.copyPathButton?.addEventListener("click", () => {
      if (this.currentJobOutput) {
        navigator.clipboard.writeText(this.currentJobOutput).then(() => {
          const original = this.copyPathButton.textContent;
          this.copyPathButton.textContent = "Copied!";
          setTimeout(() => {
            this.copyPathButton.textContent = original;
          }, 1500);
        });
      }
    });
    this.clearHistoryButton?.addEventListener("click", () => {
      this.onClearHistory?.();
    });
  }

  showError(message) {
    this.statusPanel.hidden = false;
    this.statusPanel.dataset.state = "failed";
    this.statusPanel.dataset.warning = "false";
    this.jobState.textContent = "ERROR";
    this.jobMessage.textContent = message;
    this.jobItem.textContent = "Review the settings and try again.";
    this.jobProgress.removeAttribute("value");
    this.jobPercent.textContent = "";
    this._renderMetrics({});
    if (this.cancelActiveButton) this.cancelActiveButton.hidden = true;
    if (this.retryJobButton) this.retryJobButton.hidden = true;
    if (this.openFolderButton) this.openFolderButton.hidden = true;
    if (this.copyPathButton) this.copyPathButton.hidden = true;
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
    this._renderHistory(recent);
    return Boolean(active || (snapshot.queued || []).length);
  }

  _renderJob(job) {
    this.currentJobId = job.id;
    this.currentJobOutput = job.output || "";
    this.statusPanel.hidden = false;
    this.statusPanel.dataset.state = job.state;
    this.statusPanel.dataset.warning = String(Boolean(job.unavailable_items));
    this.jobState.textContent =
      job.state === "running"
        ? job.dry_run
          ? "PREVIEW"
          : "RECORDING"
        : job.state === "completed" && job.unavailable_items
          ? "COMPLETE · WARNING"
        : STATE_LABELS[job.state] || "PROCESSING";
    this.jobMessage.textContent = job.message;
    this.jobItem.textContent =
      job.current_item || job.playlist_title || `Destination: ${job.output}`;

    if (typeof job.progress === "number") {
      const rounded = Math.round(job.progress);
      this.jobProgress.value = rounded;
      this.jobPercent.textContent = `%${rounded}`;
    } else {
      this.jobProgress.removeAttribute("value");
      this.jobPercent.textContent = "";
    }
    this._renderMetrics(job);
    if (this.cancelActiveButton) {
      this.cancelActiveButton.hidden = job.state !== "running";
      this.cancelActiveButton.disabled = job.message === "Cancellation requested";
      this.cancelActiveButton.textContent = this.cancelActiveButton.disabled
        ? "Stopping…"
        : "Cancel active job";
    }
    if (this.retryJobButton) {
      this.retryJobButton.hidden = !["failed", "cancelled"].includes(job.state);
    }

    const hasFolder = !job.dry_run && Boolean(job.output);
    if (this.openFolderButton) {
      this.openFolderButton.hidden = !hasFolder;
    }
    if (this.copyPathButton) {
      this.copyPathButton.hidden = !hasFolder;
    }
  }

  _renderMetrics(job) {
    this.metricTrack.textContent =
      job.item_index && job.item_count ? `${job.item_index} / ${job.item_count}` : "—";
    this.metricSpeed.textContent = formatSpeed(job.speed);
    this.metricBytes.textContent = formatTransfer(job.downloaded_bytes, job.total_bytes);
    this.metricEta.textContent =
      job.state === "completed" ? "Done" : formatEta(job.eta);
  }

  _renderQueue(queued) {
    this.queuePanel.hidden = queued.length === 0;
    this.queueCount.textContent = `${queued.length} waiting`;
    this.queueList.replaceChildren();

    queued.forEach((job) => {
      const item = document.createElement("li");
      const copy = document.createElement("div");
      const title = document.createElement("strong");
      const detail = document.createElement("small");
      const position = document.createElement("span");
      const cancel = document.createElement("button");

      title.textContent = `Playlist job ${String(job.sequence).padStart(2, "0")}`;
      const format = (job.audio_format || "audio").toUpperCase();
      detail.textContent = job.dry_run ? "Safe preview" : `${format} · ${job.output}`;
      position.className = "queue-position";
      position.textContent = `Position ${job.queue_position}`;
      cancel.type = "button";
      cancel.className = "queue-cancel";
      cancel.textContent = "Cancel";
      cancel.setAttribute("aria-label", `Cancel playlist job ${job.sequence}`);
      cancel.addEventListener("click", () => this.onCancel?.(job.id));
      copy.append(title, detail);
      item.append(copy, position, cancel);
      this.queueList.append(item);
    });
  }

  _renderHistory(recent) {
    if (!this.historyPanel) return;
    this.historyPanel.hidden = recent.length === 0;
    if (!this.historyList) return;
    this.historyList.replaceChildren();

    recent.forEach((job) => {
      const item = document.createElement("li");
      const copy = document.createElement("div");
      const title = document.createElement("strong");
      const detail = document.createElement("small");
      const tag = document.createElement("span");
      const actions = document.createElement("div");

      title.textContent =
        job.playlist_title || `Playlist job ${String(job.sequence).padStart(2, "0")}`;
      const format = (job.audio_format || "audio").toUpperCase();
      detail.textContent = job.dry_run
        ? "Safe preview"
        : `${format} · ${job.output}`;

      tag.className = "history-tag";
      tag.dataset.state = job.state;
      tag.textContent = STATE_LABELS[job.state] || job.state.toUpperCase();

      actions.className = "history-actions";

      if (["failed", "cancelled"].includes(job.state)) {
        const retryBtn = document.createElement("button");
        retryBtn.type = "button";
        retryBtn.className = "history-btn";
        retryBtn.textContent = "Retry";
        retryBtn.title = "Retry this archive job";
        retryBtn.addEventListener("click", () => this.onRetry?.(job.id));
        actions.append(retryBtn);
      }

      if (!job.dry_run && job.output) {
        const openBtn = document.createElement("button");
        openBtn.type = "button";
        openBtn.className = "history-btn";
        openBtn.textContent = "Open";
        openBtn.title = "Open destination folder in File Explorer";
        openBtn.addEventListener("click", () => this.onOpenFolder?.(job.id));

        const copyBtn = document.createElement("button");
        copyBtn.type = "button";
        copyBtn.className = "history-btn";
        copyBtn.textContent = "Copy";
        copyBtn.title = "Copy folder path to clipboard";
        copyBtn.addEventListener("click", () => {
          navigator.clipboard.writeText(job.output).then(() => {
            const original = copyBtn.textContent;
            copyBtn.textContent = "Copied!";
            setTimeout(() => {
              copyBtn.textContent = original;
            }, 1500);
          });
        });
        actions.append(openBtn, copyBtn);
      }

      copy.append(title, detail);
      item.append(copy, tag, actions);
      this.historyList.append(item);
    });
  }
}
