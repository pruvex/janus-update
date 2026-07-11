from __future__ import annotations


def apply_weather_shortcut(
    relevant_skill_ids: list[str] | None,
    *,
    weather_on: bool,
    calendar_on: bool,
) -> list[str]:
    skills = list(relevant_skill_ids or [])
    if not weather_on:
        return skills
    if calendar_on:
        return skills
    return ["system.weather"]


def choose_follow_up_handler(
    *,
    pending_mail_confirmation: bool,
    pending_routine_offer: bool,
    user_text: str,
) -> str | None:
    normalized = str(user_text or "").strip().lower()
    control_reply = normalized in {"ja", "j", "yes", "y", "nein", "n", "no", "1", "2", "3"}
    if pending_routine_offer and normalized in {"ja", "j", "yes", "y"}:
        return "routine_offer"
    if pending_mail_confirmation and control_reply:
        return "mail_confirmation"
    return None
