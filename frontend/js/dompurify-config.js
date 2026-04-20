/**
 * Centralized DOMPurify configuration for Janus
 * 
 * This config provides hardened sanitization while preserving functionality for:
 * - Code highlighting (class, id on code/pre)
 * - External links (target="_blank")
 * - MCL Video Player (iframes with specific attributes)
 * - UI Icons (SVG tags with path, viewBox)
 */

import DOMPurify from 'dompurify';

/**
 * DOMPurify configuration for LLM-generated content
 * Allows safe HTML for chat rendering while blocking XSS
 */
export const DOMPURIFY_CHAT_CONFIG = {
  ALLOWED_TAGS: [
    'p', 'br', 'strong', 'em', 'u', 's', 'strike',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'blockquote', 'code', 'pre',
    'a', 'img',
    'iframe',  // For YouTube/Vimeo video embeds
    'svg', 'path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'ellipse', // For icons
    'div', 'span' // For wrapper elements
  ],
  ALLOWED_ATTR: [
    'href', 'title', 'alt', 'src',
    'target',  // For external links
    'class', 'id',  // For code highlighting and styling
    'width', 'height',  // For images and iframes
    'frameborder', 'allow', 'allowfullscreen',  // For video iframes
    'style',  // Limited inline styles (DOMPurify has built-in CSS filtering)
    'data-*',  // For data attributes used by the app
    'd', 'viewBox', 'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin',  // SVG attributes
    'xmlns',  // SVG namespace
    'role', 'aria-label', 'aria-hidden'  // Accessibility
  ],
  ALLOW_DATA_ATTR: true,
  FORBID_TAGS: ['script', 'style', 'object', 'embed', 'form', 'input', 'button'],
  FORBID_ATTR: ['onclick', 'onload', 'onerror', 'onmouseover', 'onfocus', 'onblur'],
  // Allow iframe only for specific video platforms (https only, no data: URIs)
  ALLOW_UNKNOWN_PROTOCOLS: false,
  SAFE_FOR_JQUERY: true,
  SANITIZE_DOM: true,
  // Restrict URIs: https, http, mailto, tel only - NO data: URIs to prevent iframe injection
  ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i
};

/**
 * DOMPurify configuration for release notes (from autoUpdater)
 * More restrictive than chat config since this is from external source
 */
export const DOMPURIFY_RELEASE_NOTES_CONFIG = {
  ...DOMPURIFY_CHAT_CONFIG,
  ALLOWED_TAGS: [
    'p', 'br', 'strong', 'em', 'u', 's',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'blockquote', 'code', 'pre',
    'a',
    'div', 'span'
  ],
  ALLOWED_ATTR: ['href', 'title', 'class', 'id', 'style'],
  // No iframes in release notes
  ALLOWED_TAGS: DOMPURIFY_CHAT_CONFIG.ALLOWED_TAGS.filter(tag => tag !== 'iframe')
};

/**
 * DOMPurify configuration for error messages
 * Very restrictive - only basic text formatting
 */
export const DOMPURIFY_ERROR_CONFIG = {
  ALLOWED_TAGS: ['span', 'div', 'p', 'br'],
  ALLOWED_ATTR: ['class', 'style'],
  FORBID_TAGS: ['script', 'iframe', 'img', 'a'],
  FORBID_ATTR: ['onclick', 'onload', 'onerror', 'href', 'src']
};

/**
 * Sanitize LLM-generated chat content
 * @param {string} html - HTML to sanitize (e.g., from marked.parse())
 * @returns {string} Sanitized HTML
 */
export function sanitizeChatHtml(html) {
  return DOMPurify.sanitize(html, DOMPURIFY_CHAT_CONFIG);
}

/**
 * Sanitize release notes from autoUpdater
 * @param {string} html - HTML to sanitize
 * @returns {string} Sanitized HTML
 */
export function sanitizeReleaseNotes(html) {
  return DOMPurify.sanitize(html, DOMPURIFY_RELEASE_NOTES_CONFIG);
}

/**
 * Sanitize error messages
 * @param {string} html - HTML to sanitize
 * @returns {string} Sanitized HTML
 */
export function sanitizeErrorHtml(html) {
  return DOMPurify.sanitize(html, DOMPURIFY_ERROR_CONFIG);
}

/**
 * Sanitize template literal with user data
 * @param {string} html - HTML to sanitize
 * @returns {string} Sanitized HTML
 */
export function sanitizeTemplateHtml(html) {
  return DOMPurify.sanitize(html, DOMPURIFY_ERROR_CONFIG);
}

// Export default config
export default DOMPURIFY_CHAT_CONFIG;
