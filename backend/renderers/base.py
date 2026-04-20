"""Deterministic Renderer – Abstract Base Class (Diamond Standard).

Every renderer converts structured tool-result *data* (the ``data`` dict from a
``SkillResponse``) into a human-readable, Markdown-formatted string **without**
calling the LLM.  This guarantees deterministic, low-latency output for skills
whose response shape is well-defined.

Usage::

    class MyRenderer(BaseRenderer):
        skill_id = "system.my_skill"

        def render(self, data: dict) -> str:
            return f"Result: {data.get('value', 'n/a')}"
"""

from abc import ABC, abstractmethod


class BaseRenderer(ABC):
    """Interface contract for deterministic renderers.

    Subclasses **must** set ``skill_id`` (the canonical skill identifier,
    e.g. ``"system.routing"``) and implement :meth:`render`.
    """

    skill_id: str = ""

    @abstractmethod
    def render(self, data: dict) -> str:
        """Convert tool-result *data* into a user-facing answer string.

        Parameters
        ----------
        data:
            The ``data`` dict extracted from a successful ``SkillResponse``
            (i.e. ``status == "ok"``).  Implementations **must** use
            ``.get()`` with sensible defaults for every field to be robust
            against missing or unexpected keys.

        Returns
        -------
        str
            A Markdown-formatted, human-readable answer in Janus style.

        Raises
        ------
        No exceptions should escape this method.  If rendering is impossible,
        return a short fallback string (e.g. ``"Daten konnten nicht
        aufbereitet werden."``) so the caller can decide to degrade to LLM
        synthesis.
        """
        ...
