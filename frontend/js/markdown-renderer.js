const MARKED_OPTIONS = {
  breaks: true,
  gfm: true,
};

function getMarked() {
  const candidate = globalThis.window?.marked || globalThis.marked;
  if (!candidate || typeof candidate.parse !== "function") {
    return null;
  }
  return candidate;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function isSafeMarkdownUrl(value) {
  const url = String(value ?? "").trim();
  if (!url) return false;
  return /^(https?:|mailto:|tel:|\/|#)/i.test(url);
}

function renderInlineMarkdown(value) {
  const text = String(value ?? "");
  const linkPattern = /(!?)\[([^\]\n]*)\]\(([^)\s]+)\)/g;
  let html = "";
  let lastIndex = 0;
  let match;

  const renderText = (part) =>
    escapeHtml(part)
      .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
      .replace(/__([^_\n]+)__/g, "<strong>$1</strong>")
      .replace(/`([^`\n]+)`/g, "<code>$1</code>");

  while ((match = linkPattern.exec(text)) !== null) {
    html += renderText(text.slice(lastIndex, match.index));

    const isImage = match[1] === "!";
    const label = match[2] || "";
    const url = match[3] || "";

    if (isSafeMarkdownUrl(url)) {
      const safeLabel = escapeHtml(label || url);
      const safeUrl = escapeHtml(url);
      if (isImage) {
        html += `<img src="${safeUrl}" alt="${safeLabel}">`;
      } else {
        html += `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer">${safeLabel}</a>`;
      }
    } else {
      html += renderText(match[0]);
    }

    lastIndex = linkPattern.lastIndex;
  }

  html += renderText(text.slice(lastIndex));
  return html;
}

export function configureMarkdownRenderer() {
  const marked = getMarked();
  if (marked && typeof marked.setOptions === "function") {
    marked.setOptions(MARKED_OPTIONS);
  }
}

export function renderChatMarkdown(markdownText) {
  const marked = getMarked();
  if (marked) {
    return marked.parse(String(markdownText ?? ""));
  }

  return renderInlineMarkdown(markdownText).replace(/\r?\n/g, "<br>");
}

export const __markdownRendererTestHooks = {
  escapeHtml,
  renderInlineMarkdown,
  isSafeMarkdownUrl,
};
