"""Thin re-export of ``contact_tools`` for naming consistency (contacts vs contact)."""

from backend.tools.contact_tools import extract_and_save_contact_from_text

__all__ = ["extract_and_save_contact_from_text"]
