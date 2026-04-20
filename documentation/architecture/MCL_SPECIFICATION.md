# MCL Specification (Modal Contract Layer)

## Core Rule

All UI extensions must use the Modal Contract Layer (MCL).

No new feature may open or control dock/modals directly with ad-hoc DOM logic when an MCL contract type exists.

## Contract Flow

1. Backend returns a `modal_request` object in the API response.
2. Frontend consumes `modal_request`.
3. Frontend opens/focuses via `modal-api.js` (`openModal`, `bringToFront`, `closeModal`).
4. `window-state.js` remains the single source of truth for open/minimized/z-index state.

### Backend Contract Shape

```json
{
  "modal_request": {
    "type": "video",
    "payload": {
      "url": "https://youtu.be/...",
      "title": "Pizzateig in 10 Minuten"
    },
    "options": {
      "position": { "x": 980, "y": 20 },
      "size": { "w": 800, "h": 450 }
    }
  }
}
```

## Mandatory Rules

- **Stateless MCL:** modal-api is a facade; no separate hidden modal state.
- **Z-Stack Management:** base z-index is `100`, focus raises z-index monotonically.
- **FIFO Soft Guard:** maximum 4 open non-minimized modals; opening a 5th minimizes the oldest open modal.
- **Escape-to-close:** `Escape` closes the currently topmost modal (highest z-index).
- **Open path:** use `openModal({ type, payload, options })`, not direct `dockOpen(...)` calls.

## Level 9 Example (UI Modality Skill)

Use this pattern when adding a new skill with UI modality.

```python
# backend/services/orchestrator/execution_engine.py (example)
response.modal_request = {
    "type": "gallery",
    "payload": {
        "focus_image_id": image_id,
        "source": "system.image_search"
    },
    "options": {
        "size": {"w": 920, "h": 640}
    },
}
```

```javascript
// frontend/js/chat.js (example)
import { openModal } from "./modal-api.js";

if (msg?.modal_request?.type) {
  openModal({
    type: msg.modal_request.type,
    payload: msg.modal_request.payload || {},
    options: msg.modal_request.options || {},
  });
}
```

## Scope

Applies to all modal-capable UI modules:

- knowledge-center
- image-studio
- gallery
- video-player
- image-viewer
