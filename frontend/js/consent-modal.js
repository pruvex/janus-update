/**
 * Path Sentinel Consent Modal
 * Handles user consent for file system access
 */

let currentChallengeId = null;
let currentOnResolveCallback = null;

/**
 * Show the consent modal with the given challenge details
 * @param {string} challengeId - The challenge ID from the backend
 * @param {string} path - The file path requiring access
 * @param {string} op - The operation type (READ/WRITE/DELETE)
 * @param {Function} onResolveCallback - Callback function called after user decision
 */
export function showConsentModal(challengeId, path, op, onResolveCallback) {
    currentChallengeId = challengeId;
    currentOnResolveCallback = onResolveCallback;

    // Set modal content
    const pathDisplay = document.getElementById('consent-path-display');
    const opDisplay = document.getElementById('consent-op-display');
    
    if (pathDisplay) {
        pathDisplay.textContent = path;
    }
    if (opDisplay) {
        opDisplay.textContent = op.toUpperCase();
    }

    // Show modal
    const modal = document.getElementById('consent-modal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

/**
 * Hide the consent modal
 */
function hideConsentModal() {
    const modal = document.getElementById('consent-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
    currentChallengeId = null;
    currentOnResolveCallback = null;
}

/**
 * Resolve consent by sending decision to backend
 * @param {string} decision - The user's decision (once/session/always/deny)
 */
async function resolveConsent(decision) {
    if (!currentChallengeId) {
        console.error('No active challenge to resolve');
        hideConsentModal();
        return;
    }

    try {
        const response = await fetch('/api/consent/resolve', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                challenge_id: currentChallengeId,
                decision: decision,
            }),
        });

        if (response.ok) {
            const result = await response.json();
            hideConsentModal();
            
            if (currentOnResolveCallback) {
                currentOnResolveCallback(decision);
            }
        } else {
            console.error('Failed to resolve consent:', response.statusText);
            hideConsentModal();
        }
    } catch (error) {
        console.error('Error resolving consent:', error);
        hideConsentModal();
    }
}

// Initialize event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Close button
    const closeBtn = document.getElementById('close-consent-modal');
    if (closeBtn) {
        closeBtn.addEventListener('click', hideConsentModal);
    }

    // Deny button
    const denyBtn = document.getElementById('consent-deny-btn');
    if (denyBtn) {
        denyBtn.addEventListener('click', () => resolveConsent('deny'));
    }

    // Once button
    const onceBtn = document.getElementById('consent-once-btn');
    if (onceBtn) {
        onceBtn.addEventListener('click', () => resolveConsent('once'));
    }

    // Session button
    const sessionBtn = document.getElementById('consent-session-btn');
    if (sessionBtn) {
        sessionBtn.addEventListener('click', () => resolveConsent('session'));
    }

    // Always button
    const alwaysBtn = document.getElementById('consent-always-btn');
    if (alwaysBtn) {
        alwaysBtn.addEventListener('click', () => resolveConsent('always'));
    }

    // Close modal on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const modal = document.getElementById('consent-modal');
            if (modal && !modal.classList.contains('hidden')) {
                resolveConsent('deny');
            }
        }
    });

    // Close modal on backdrop click
    const modal = document.getElementById('consent-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                resolveConsent('deny');
            }
        });
    }
});
