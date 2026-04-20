import logging
from typing import Dict, List

from backend.services.prompting.compilers.base import BasePromptCompiler
from backend.services.prompting.core.model import Prompt, PromptBlock

logger = logging.getLogger("janus_backend")

# 💎 CLEAN-ARCHITECTURE: Skill choice directive
CRITICAL_SKILL_CHOICE_DIRECTIVE = """CRITICAL SKILL CHOICE DIRECTIVE (PRIORITY 1 - MANDATORY):
Regel: Für Preis-Informationen, nutze IMMER system.websearch.
Für Hintergrundwissen, Firmengeschichte oder Definitionen, nutze IMMER system.wikipedia_summary.
Mische niemals die Aufgaben!
"""

# 💎 HYBRID DIAMOND: Tag injection directives
ID_INJECTION_DIRECTIVE = """CRITICAL ID INJECTION DIRECTIVE (PRIORITY 1 - MANDATORY):
When mentioning specific products, items, or entities, you MUST use the following tag format:
- For products/items: [[PRODUCT:exact_name_or_id]]
- For background info: [[WIKI:topic_name]]

This ensures links are displayed correctly. The system will replace these tags with actual links.
"""

ID_INJECTION_REMINDER = """Reminder: Use [[PRODUCT:name]] for items and [[WIKI:topic]] for background info. This ensures links are displayed."""


class GeminiCompiler(BasePromptCompiler):
    """
    Kompiliert Prompt-AST in den Gemini-Dialekt.
    Nutzt strikte XML-Tags und Bottom-Heavy-Struktur.
    Garantiert, dass Instruktionen niemals durch Kontext-Limits abgeschnitten werden.
    """

    def compile_discovery_prompt(self, user_prompt: str) -> str:
        """Erstellt einen spezialisierten Prompt, der NUR die Entitäten extrahiert."""
        return (
            "<role>Du bist ein Recherche-Analyst. Deine einzige Aufgabe ist es, aus einer Anfrage die Kern-Entitäten zu extrahieren.</role>\n"
            "<task>Extrahiere aus der folgenden Anfrage die Namen der Spiele, Produkte oder Themen, die recherchiert werden sollen. Antworte NUR mit einer kommagetrennten Liste der Namen.</task>\n"
            f"<user_request>{user_prompt}</user_request>"
        )

    def compile(self, prompt_ast: Prompt, model_id: str, max_tokens: int, allow_links: bool = True) -> str:
        blocks_by_type: Dict[str, List[PromptBlock]] = {}
        for block in prompt_ast.blocks:
            blocks_by_type.setdefault(block.type, []).append(block)

        role_xml = ""
        if "system_role" in blocks_by_type:
            role_texts = [str(b.content).strip() for b in blocks_by_type["system_role"]]
            role_xml = "<role>\n" + "\n".join(role_texts) + "\n</role>"

        # Simple check for list queries (for constraints, not for tags)
        user_prompt_blocks = [str(b.content).strip() for b in blocks_by_type.get("user_prompt", [])]
        lowered = " ".join(user_prompt_blocks).lower()
        list_tokens = ("liste", "top", "alle", "neuerscheinungen", "highlights", "mehrere", "welche", "spiele", "games")
        is_list_query = any(token in lowered for token in list_tokens)

        context_xml = ""
        if "memory" in blocks_by_type:
            context_texts = [str(b.content).strip() for b in blocks_by_type["memory"]]
            raw_context = "\n\n".join(context_texts)

            max_context_chars = 28000
            if len(raw_context) > max_context_chars:
                logger.warning(
                    "GeminiCompiler: Context very large (%s chars). Trimming slightly to fit limits.",
                    len(raw_context),
                )
                raw_context = raw_context[:max_context_chars] + "\n... [Context truncated]"

            context_xml = "<context>\n" + raw_context + "\n</context>"

        instruction_parts = []

        constraints = []
        if "grounding_rules" in blocks_by_type:
            constraints.extend([str(b.content).strip() for b in blocks_by_type["grounding_rules"]])
        if "tool_rules" in blocks_by_type:
            constraints.extend([str(b.content).strip() for b in blocks_by_type["tool_rules"]])

        # is_list_query wurde bereits oben berechnet
        if is_list_query:
            if not allow_links:
                # 💎 HYBRID DIAMOND: Tag-based with instruction sandwich
                constraints.append(
                    "FORMATTING:\n"
                    "1. Antworte fundiert basierend auf den Suchergebnissen.\n"
                    "2. Hebe Produktnamen und Kernbegriffe fett hervor (**Produktname**).\n"
                    "3. Füge KEINE Markdown-Links [Text](URL) hinzu. Das System fügt Links automatisch hinzu.\n"
                    "4. WICHTIG: Für jedes Produkt oder jede Entität, verwende [[PRODUCT:Name]] Tags.\n"
                    "   Beispiel: 'Das **iPhone 15** [[PRODUCT:iPhone 15]] kostet...'"
                )
            else:
                constraints.append(
                    "CRITICAL HYBRID-LINKING DIRECTIVE:\n"
                    "1. For each item in the list, you MUST try to generate a specific deep-link URL.\n"
                    "2. First, try to find an exact URL in the provided <context>.\n"
                    "3. If no specific URL is found in the context, you are ALLOWED to CONSTRUCT a plausible-looking URL to a major German-language source (e.g., gamepro.de, ign.com/de, nintendo.de, spiegel.de, faz.net).\n"
                    "4. If you construct a link, you MUST label it as `[Kandidat]` in the link text.\n"
                    "   - Example (real): `[Quelle](https://www.gamestar.de/artikel/spiel-xyz)`\n"
                    "   - Example (constructed): `[Kandidat](https://www.gamestar.de/artikel/spiel-abc)`"
                )

        if not is_list_query:
            constraints.append(
                "CRITICAL UNIVERSAL LINKING DIRECTIVE:\n"
                "1. You MUST find a dedicated, highly specific source URL from the <context> for EACH fact, item, or entity in your answer.\n"
                "2. It is STRICTLY FORBIDDEN to use a generic root domain link (like 'www.nintendo.de', 'www.wikipedia.org', 'www.spiegel.de') as a source. The URL must point directly to the specific article, product page, or subpage that contains the exact information.\n"
                "3. If an entity or fact is mentioned in the context, but you cannot find a specific, deep-link URL for it, you MUST write `(Keine spezifische Quelle gefunden)` instead of generating a fake or generic markdown link.\n"
                "4. SOURCE-LANGUAGE-FILTER: You MUST prioritize German domains (.de, .at, .ch) over any other domain (.com, .net).\n"
                "5. ACCURACY OVER COMPLETENESS: A missing link is better than a generic or wrong link. Never guess URLs.\n"
                "\n" + CRITICAL_SKILL_CHOICE_DIRECTIVE
            )
        if constraints:
            instruction_parts.append("<constraints>\n" + "\n\n".join(constraints) + "\n</constraints>")

        # 💎 HYBRID DIAMOND: Instruction Sandwich - inject at beginning
        if is_list_query and not allow_links:
            instruction_parts.insert(0, f"<critical_directive>\n{ID_INJECTION_DIRECTIVE}\n</critical_directive>")

        if "output_contract" in blocks_by_type:
            output_texts = [str(b.content).strip() for b in blocks_by_type["output_contract"]]
            instruction_parts.append(
                "<output_format>\n"
                "Du MUSST die Antwort exakt nach dem angegebenen Schema strukturieren. Jede Abweichung ist ein Fehler.\n\n"
                + "\n\n".join(output_texts) +
                "\n</output_format>"
            )

        if "user_prompt" in blocks_by_type:
            task_texts = [str(b.content).strip() for b in blocks_by_type["user_prompt"]]
            instruction_parts.append(
                "<task>\nBeantworte die folgende Nutzerfrage:\n" + "\n\n".join(task_texts) + "\n</task>"
            )

        # 💎 HYBRID DIAMOND: Instruction Sandwich - reminder at end
        if is_list_query and not allow_links:
            instruction_parts.append(f"<reminder>\n{ID_INJECTION_REMINDER}\n</reminder>")

        instructions_xml = "\n\n".join(instruction_parts)
        final_prompt = f"{role_xml}\n\n{context_xml}\n\n{instructions_xml}".strip()

        return final_prompt

    def _render_block(self, block: PromptBlock) -> str:
        if block.type == "skill_directive":
            skill_id = str(getattr(block.content, "skill_id", "") or "").strip()
            instruction_set = getattr(block.content, "instruction_set", {}) or {}
            selected = instruction_set.get("standard") or instruction_set.get("mini") or instruction_set.get("nano") or ""
            selected = str(selected or "").strip()
            if not selected:
                return ""
            if skill_id:
                return f"[skill:{skill_id}]\n{selected}"
            return selected
        return str(block.content or "").strip()
