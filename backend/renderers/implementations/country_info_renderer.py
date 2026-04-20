"""Deterministic Renderer for ``system.country_info`` (Diamond Standard).

Converts country-info tool-result data into a human-readable Markdown answer
including name, capital, population, region, currencies, and languages.
"""

from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class CountryInfoRenderer(BaseRenderer):
    """Render country information deterministically."""

    skill_id = "system.country_info"

    def render(self, data: dict) -> str:
        name = data.get("name", "Unbekannt")
        capital = data.get("capital", "Unbekannt")
        population = data.get("population")
        region = data.get("region", "")
        currencies = data.get("currencies", [])
        languages = data.get("languages", [])

        pop_str = self._format_population(population) if population else "Unbekannt"

        currencies_str = ", ".join(str(c) for c in currencies) if currencies else "Unbekannt"
        languages_str = ", ".join(str(lang) for lang in languages) if languages else "Unbekannt"

        lines = [
            f"**{name}**",
            "",
            f"- **Hauptstadt:** {capital}",
            f"- **Bevölkerung:** {pop_str}",
        ]

        if region:
            lines.append(f"- **Region:** {region}")

        lines.append(f"- **Währung(en):** {currencies_str}")
        lines.append(f"- **Sprache(n):** {languages_str}")

        return "\n".join(lines)

    @staticmethod
    def _format_population(population: int) -> str:
        """Format a population number with German-style thousand separators."""
        try:
            num = int(population)
            if num >= 1_000_000_000:
                return f"{num / 1_000_000_000:.2f} Mrd."
            if num >= 1_000_000:
                return f"{num / 1_000_000:.1f} Mio."
            return f"{num:,}".replace(",", ".")
        except (ValueError, TypeError):
            return str(population)


# Auto-register on import
register_renderer(CountryInfoRenderer())
