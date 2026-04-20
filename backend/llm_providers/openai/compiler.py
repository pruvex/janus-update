from backend.services.prompting.compilers.base import BasePromptCompiler
from backend.services.prompting.core.model import Prompt, PromptBlock


class OpenAICompiler(BasePromptCompiler):
    def compile(self, prompt_ast: Prompt, model_id: str, max_tokens: int) -> str:
        self.model_id = (model_id or "").lower()
        compiled_parts = []

        is_mini_or_nano = any(marker in self.model_id for marker in ("mini", "nano"))

        if is_mini_or_nano:
            compiled_parts.append(
                "SYSTEM-LEVEL DIRECTIVE: Follow every XML-tag instruction precisely. Do not skip constraints."
            )

        for block in prompt_ast.blocks:
            rendered = self._render_block(block, is_mini_or_nano)
            if rendered:
                compiled_parts.append(rendered)

        return "\n\n".join(compiled_parts)

    def _render_block(self, block: PromptBlock, is_mini_or_nano: bool) -> str:
        b_type = block.type
        content = block.content

        if b_type == "system_role":
            return f"ROLE: {content}"

        elif b_type == "grounding_rules":
            rules = f"<grounding_rules>\n{content}\n"
            rules += "- STRICT TRUTH: Treat web search snippets as absolute truth.\n"
            rules += "- DATA EXTRACTION: If you see numbers/prices, extract them. Do not apologize for missing timestamps if the data is present.\n"
            rules += "</grounding_rules>"
            return rules

        elif b_type == "output_contract":
            output_format = str(getattr(content, "format", "") or "").strip().lower()
            if is_mini_or_nano and output_format == "json":
                return (
                    "<output_contract>\n"
                    "- FORMAT: JSON ONLY\n"
                    "- REQUIRED_KEYS: [\"name\", \"goal\", \"required_skills\", \"instructions\", \"max_iterations\"]\n"
                    "- RULE: Do not explain. Do not use markdown backticks.\n"
                    "- PDF CONTENT RULE: Use ultra-simple Markdown. NEVER use parentheses '(' or ')' in headers (##). Use dots like '1.' instead of '1)'.\n"
                    "- FILENAME LOCK: Use exactly the filename and location provided in the task.\n"
                    "- NO TALK: Output ONLY the raw JSON object. No markdown fences. No preamble.\n"
                    "- TEMPLATE: {\"name\": \"Agent\", \"goal\": \"...\", \"required_skills\": [], \"instructions\": \"...\", \"max_iterations\": 1}\n"
                    "</output_contract>"
                )
            return f"<output_contract>\n{content}\n</output_contract>"

        elif b_type == "skill_directive":
            skill_id = str(getattr(content, "skill_id", "") or "").strip()
            instruction_set = getattr(content, "instruction_set", {}) or {}
            if is_mini_or_nano:
                selected = (
                    instruction_set.get("nano")
                    or instruction_set.get("mini")
                    or instruction_set.get("standard")
                    or ""
                )
            else:
                selected = instruction_set.get("standard") or instruction_set.get("mini") or instruction_set.get("nano") or ""
            if not selected:
                return ""
            return f"<skill_directive skill=\"{skill_id}\">\n{selected}\n</skill_directive>"

        elif b_type == "user_prompt":
            prefix = "### MANDATORY TASK TO EXECUTE:\n" if is_mini_or_nano else "### USER-INTENT:\n"
            return f"{prefix}{content}"

        return str(content)
