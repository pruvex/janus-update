"""Deterministic Renderer for ``system.price_comparison`` (Diamond Standard).

Converts structured PriceComparisonOutput data into a clean Markdown answer
with clickable shop links and an optional refurbished savings tip.
"""

from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class PriceComparisonRenderer(BaseRenderer):
    """Render price comparison results deterministically."""

    skill_id = "system.price_comparison"

    def render(self, data: dict) -> str:
        query = data.get("query", "Produkt")
        currency = data.get("currency", "EUR")
        results = data.get("results") or []
        refurbished_tip = data.get("refurbished_tip")

        if not results and not refurbished_tip:
            return f"Für **{query}** konnten leider keine Preise gefunden werden."

        currency_symbol = {"EUR": "€", "USD": "$", "GBP": "£"}.get(currency, currency)

        lines = [f"## 💶 Preisvergleich: {query}", ""]

        for entry in results:
            price = entry.get("price")
            source = entry.get("source", "Unbekannte Quelle")
            url = entry.get("url")
            variant = entry.get("variant")
            includes_shipping = entry.get("includes_shipping", False)

            price_str = f"{price:,.2f} {currency_symbol}".replace(",", "X").replace(".", ",").replace("X", ".")
            shipping_note = " (inkl. Versand)" if includes_shipping else ""
            variant_note = f" — {variant}" if variant else ""

            if url:
                source_link = f"[Angebot auf {source} 🔗]({url})"
            else:
                source_link = source

            lines.append(f"- **{price_str}**{shipping_note}{variant_note} · {source_link}")

        if refurbished_tip:
            r_price = refurbished_tip.get("price")
            r_source = refurbished_tip.get("source", "Unbekannte Quelle")
            r_url = refurbished_tip.get("url")
            r_variant = refurbished_tip.get("variant")

            r_price_str = f"{r_price:,.2f} {currency_symbol}".replace(",", "X").replace(".", ",").replace("X", ".")
            r_variant_note = f" — {r_variant}" if r_variant else ""

            new_prices = [e.get("price") for e in results if e.get("price") is not None]
            savings_note = ""
            if new_prices and r_price is not None:
                savings_pct = (min(new_prices) - r_price) / min(new_prices) * 100
                if savings_pct > 0:
                    savings_note = f" (ca. {savings_pct:.0f}% günstiger)"

            if r_url:
                r_source_link = f"[Angebot auf {r_source} 🔗]({r_url})"
            else:
                r_source_link = r_source

            lines.append("")
            lines.append(
                f"- 💡 **[SPAR-TIPP: Refurbished]** {r_price_str}{savings_note}{r_variant_note} · {r_source_link}"
            )

        retrieved_at = data.get("retrieved_at", "")
        if retrieved_at:
            try:
                date_part = retrieved_at[:10]
                lines.append("")
                lines.append(f"*Stand: {date_part}*")
            except Exception:
                pass

        return "\n".join(lines)


# Auto-register on import
register_renderer(PriceComparisonRenderer())
