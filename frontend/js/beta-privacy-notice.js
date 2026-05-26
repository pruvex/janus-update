const ACK_STORAGE_KEY = "janus_beta_privacy_ack_v1";
const NOTICE_VERSION = "2026-05-21.1";

function readAck() {
  try {
    const raw = localStorage.getItem(ACK_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function hasCurrentAck() {
  const ack = readAck();
  return Boolean(ack && ack.accepted === true && ack.noticeVersion === NOTICE_VERSION);
}

function showModal() {
  const modal = document.getElementById("beta-privacy-modal");
  if (modal) {
    modal.classList.remove("hidden");
  }
}

function hideModal() {
  const modal = document.getElementById("beta-privacy-modal");
  if (modal) {
    modal.classList.add("hidden");
  }
}

function recordAck() {
  const payload = {
    accepted: true,
    noticeVersion: NOTICE_VERSION,
    acceptedAt: new Date().toISOString(),
    storage: "localStorage",
  };
  localStorage.setItem(ACK_STORAGE_KEY, JSON.stringify(payload));
  hideModal();
}

function openNotice() {
  window.open("documentation/beta/BETA_PRIVACY_NOTICE.md", "_blank", "noopener,noreferrer");
}

function initBetaPrivacyNotice() {
  const modal = document.getElementById("beta-privacy-modal");
  const checkbox = document.getElementById("beta-privacy-ack-checkbox");
  const acceptButton = document.getElementById("beta-privacy-accept-btn");
  const noticeButton = document.getElementById("beta-privacy-open-notice-btn");

  if (!modal || !checkbox || !acceptButton || !noticeButton) {
    return;
  }

  modal.dataset.noticeVersion = NOTICE_VERSION;

  checkbox.addEventListener("change", () => {
    acceptButton.disabled = !checkbox.checked;
  });
  acceptButton.addEventListener("click", recordAck);
  noticeButton.addEventListener("click", openNotice);

  if (!hasCurrentAck()) {
    showModal();
  }
}

document.addEventListener("DOMContentLoaded", initBetaPrivacyNotice);

export {
  ACK_STORAGE_KEY,
  NOTICE_VERSION,
  hasCurrentAck,
  initBetaPrivacyNotice,
};
