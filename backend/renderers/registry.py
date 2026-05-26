"""Deterministic Renderer Registry (Diamond Standard).

Central lookup that maps ``skill_id`` → :class:`BaseRenderer` instance.

The registry is populated at import time by importing all concrete renderer
modules from ``backend.renderers.implementations``.  External code should
only use :func:`get_renderer`.

Design invariants
-----------------
* **Graceful Degradation** – ``get_renderer`` never raises.  It returns
  ``None`` when no renderer is registered for a given skill, allowing the
  caller to fall back to LLM synthesis transparently.
* **Idempotent** – Calling ``_ensure_loaded`` multiple times is safe.
* **No circular imports** – The registry imports implementations lazily on
  first access.
"""

import logging
from typing import Dict, Optional

from backend.renderers.base import BaseRenderer

logger = logging.getLogger("janus_backend")

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------

_RENDERERS: Dict[str, BaseRenderer] = {}
_loaded: bool = False


def _ensure_loaded() -> None:
    """Import all renderer implementations once (lazy, thread-safe enough for
    the single-process ASGI server we run)."""
    global _loaded
    if _loaded:
        return
    _loaded = True
    try:
        # Each module registers itself via ``register_renderer`` at import time.
        import backend.renderers.implementations.routing_renderer  # noqa: F401
        import backend.renderers.implementations.weather_renderer  # noqa: F401
        import backend.renderers.implementations.country_info_renderer  # noqa: F401
        import backend.renderers.implementations.create_pdf_renderer  # noqa: F401
        import backend.renderers.implementations.generate_image_renderer  # noqa: F401
        import backend.renderers.implementations.grant_permission_renderer  # noqa: F401
        import backend.renderers.implementations.local_business_renderer  # noqa: F401
        import backend.renderers.implementations.revoke_permission_renderer  # noqa: F401
        import backend.renderers.implementations.rss_news_renderer  # noqa: F401
        # 💎 DIAMOND: UnifiedWebSearchRenderer für deterministisches Post-Aggregation Rendering
        import backend.renderers.implementations.unified_websearch_renderer  # noqa: F401
        import backend.renderers.implementations.price_comparison_renderer  # noqa: F401
        
        logger.info(
            "RENDERER-REGISTRY: %d Renderer geladen: %s",
            len(_RENDERERS),
            list(_RENDERERS.keys()),
        )
    except Exception as exc:
        logger.error("RENDERER-REGISTRY: Fehler beim Laden der Renderer: %s", exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def register_renderer(renderer: BaseRenderer) -> None:
    """Register a renderer instance.  Called by implementation modules."""
    if not renderer.skill_id:
        logger.warning("RENDERER-REGISTRY: Renderer ohne skill_id uebersprungen: %s", type(renderer).__name__)
        return
    _RENDERERS[renderer.skill_id] = renderer
    logger.debug("RENDERER-REGISTRY: Renderer registriert fuer '%s'", renderer.skill_id)


def get_renderer(skill_id: str) -> Optional[BaseRenderer]:
    """Return the renderer for *skill_id*, or ``None`` if none exists.

    This function **never raises**.
    """
    _ensure_loaded()
    return _RENDERERS.get(skill_id)


def get_all_renderer_skill_ids() -> list:
    """Return all skill IDs that have a registered renderer."""
    _ensure_loaded()
    return list(_RENDERERS.keys())


# Registry-Instanz für Import als 'registry'
class _RendererRegistryFacade:
    """Facade zur einfachen Nutzung als 'registry' Import."""
    
    def get_renderer(self, skill_id: str) -> Optional[BaseRenderer]:
        return get_renderer(skill_id)
    
    def register_renderer(self, renderer: BaseRenderer) -> None:
        register_renderer(renderer)
    
    def get_all_skill_ids(self) -> list:
        return get_all_renderer_skill_ids()


registry = _RendererRegistryFacade()


# ---------------------------------------------------------------------------
# Circular Import Safety: Final Registrations
# ---------------------------------------------------------------------------
# We import implementations here to ensure that get_renderer() and 
# register_renderer() are already defined.
import backend.renderers.implementations.price_comparison_renderer  # noqa: F401
