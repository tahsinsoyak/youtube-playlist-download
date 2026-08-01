export function formatBytes(value) {
  if (!Number.isFinite(value) || value < 0) {
    return "—";
  }
  if (value < 1024 * 1024) {
    return `${Math.round(value / 1024)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatTransfer(downloaded, total) {
  const current = formatBytes(downloaded);
  return Number.isFinite(total) ? `${current} / ${formatBytes(total)}` : current;
}

export function formatSpeed(value) {
  if (!Number.isFinite(value) || value <= 0) {
    return "—";
  }
  if (value < 1024 * 1024) {
    return `${Math.round(value / 1024)} KB/s`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB/s`;
}

export function formatEta(value) {
  if (!Number.isFinite(value) || value < 0) {
    return "—";
  }
  const seconds = Math.round(value);
  if (seconds < 60) {
    return `${seconds} sec`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes} min ${remainder} sec`;
}
