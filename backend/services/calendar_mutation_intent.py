"""TASK-067-B: Kalender-Mutations-Risiko (ohne Package ``calendar``, kein Import-Zirkel)."""

from __future__ import annotations

from typing import Literal, Optional

CalendarMutationIntent = Literal["TIME_MUTATION", "DATA_MUTATION", "NONE"]


def classify_calendar_mutation_intent(
    *,
    cancel_event: Optional[bool] = None,
    new_start_time: Optional[str] = None,
    new_end_time: Optional[str] = None,
    new_summary: Optional[str] = None,
    new_location: Optional[str] = None,
    new_description: Optional[str] = None,
) -> CalendarMutationIntent:
    """TASK-067-B: Risiko für den Mutation-Guard.

    * **TIME_MUTATION** — Start/Ende ändern oder ``cancel_event``: User-Bestätigung nötig.
    * **DATA_MUTATION** — nur Titel/Ort/Beschreibung: direkter PATCH ohne Guard.
    * **NONE** — keine dieser Felder gesetzt.

    Kombination Zeit + Daten ⇒ **TIME_MUTATION** (vorsichtiger).
    """
    if cancel_event:
        return "TIME_MUTATION"
    if new_start_time or new_end_time:
        return "TIME_MUTATION"
    if new_summary or new_location or new_description:
        return "DATA_MUTATION"
    return "NONE"
