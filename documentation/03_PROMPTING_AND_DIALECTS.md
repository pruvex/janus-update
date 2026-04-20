# Prompting Engine & Provider-Dialekte (Janus)

## 1. Architektur-Übersicht (Code-Verifizierter Stand)

Die **Prompting Engine V2** ist vollständig implementiert. Sie ersetzt statische Prompt-Strings durch eine "Dialect Factory", die für jeden LLM-Provider (OpenAI, Gemini, Ollama) optimierte, native Prompts kompiliert.

### 1.1 Verzeichnisstruktur

```
backend/services/prompting/
├── core/
│   └── model.py              # AST: PromptBlock, Prompt, Direktiven
├── compilers/
│   ├── base.py               # BasePromptCompiler (ABC)
│   └── ollama.py             # Placeholder (65 Bytes)
├── runtime/
│   ├── builder.py            # PromptBuilder API
│   └── optimizer.py          # Token-Budget Optimierung
└── factory.py                # get_compiler(provider) Dispatcher

backend/llm_providers/
├── gemini/
│   └── compiler.py           # GeminiCompiler (149 Zeilen)
├── openai/
│   └── compiler.py           # OpenAICompiler (75 Zeilen)
└── ollama/
    └── gateway.py            # Enthält Ollama-spezifische Prompt-Logik
```

### 1.2 Kernkomponenten

| Komponente | Datei | Funktion |
|------------|-------|----------|
| **AST-Modell** | `core/model.py` | `PromptBlock`, `Prompt`, `SkillDirective`, `OutputContractDirective` |
| **Compiler-Interface** | `compilers/base.py` | Abstrakte Basisklasse `BasePromptCompiler` |
| **GeminiCompiler** | `llm_providers/gemini/compiler.py` | XML-Tags, Bottom-Heavy, Link-Handling |
| **OpenAICompiler** | `llm_providers/openai/compiler.py` | XML-Tags, nano/mini-Optimierungen |
| **PromptBuilder** | `runtime/builder.py` | Fluent API zum Bauen von Prompts |
| **Optimizer** | `runtime/optimizer.py` | Token-Budget-basierte Block-Kürzung |
| **Factory** | `factory.py` | Dispatcher: `openai` → `OpenAICompiler()`, etc. |

## 2. Prompt AST (Abstract Syntax Tree)

### 2.1 PromptBlock-Schema (`core/model.py`)

```python
class PromptBlock(BaseModel):
    type: Literal[
        "system_role",
        "grounding_rules",
        "output_contract",
        "skill_directive",
        "tool_rules",
        "memory",
        "user_prompt",
        "synthesis_instruction",
    ]
    content: Any                          # String oder strukturiertes Objekt
    priority: int = 10                   # 1=höchste, 10=niedrigste
    required: bool = False               # Nie entfernen, nur kürzen
```

### 2.2 Verwendung im Code

```python
from backend.services.prompting.runtime.builder import PromptBuilder

builder = PromptBuilder()
builder.add_block("system_role", "Du bist Janus, ein hilfreicher Assistent.", priority=1, required=True)
builder.add_block("grounding_rules", "Nutze nur bereitgestellte Quellen.", priority=2)
builder.add_skill_directive(
    skill_id="system.websearch",
    instruction_set={
        "nano": "STRICT_TRUTH: Trust snippets. Extract prices.",
        "standard": "Reason about conflicting sources. Cite precisely."
    },
    priority=3
)
builder.add_block("user_prompt", user_query, priority=5)

# Kompilieren für Provider
final_prompt = builder.compile(provider="gemini", model_id="gemini-3-pro", max_tokens=4000)
```

## 3. Provider-Dialekte (Compiler)

### 3.1 GeminiCompiler (`llm_providers/gemini/compiler.py`)

**Strategie:** XML-Tags, Bottom-Heavy (Instruktionen am Ende), Link-Handling

**Struktur:**
```xml
<role>
Du bist ...
</role>

<context>
[Memory/Context - gekürzt auf 28k Zeichen]
</context>

<constraints>
[Grounding Rules + Tool Rules]
[CRITICAL HYBRID-LINKING DIRECTIVE für Listen]
</constraints>

<output_format>
[Output Contract]
</output_format>

<task>
Beantworte die folgende Nutzerfrage:
[user_prompt]
</task>
```

**Link-Handling-Logik:**

| Query-Typ | Verhalten |
|-----------|-----------|
| Listen-Query (`liste`, `top`, `alle`) | `CRITICAL HYBRID-LINKING DIRECTIVE`: Konstruiere URLs mit `[Kandidat]`-Label |
| Normal-Query | `CRITICAL UNIVERSAL LINKING DIRECTIVE`: Spezifische Deep-Links, keine Root-Domains |
| `allow_links=False` | `CRITICAL FORMATTING RULE`: Keine Markdown-Links, nur **bold** |

**Preis-Regeln (Preis-Queries):**
- Nur Preise mit Währungssymbol explizit extrahieren
- Niemals Preisspannen (`414 bis 449 Euro`)
- Immer `ab [niedrigster Preis]` verwenden
- Refurbished-Preise ignorieren

### 3.2 OpenAICompiler (`llm_providers/openai/compiler.py`)

**Strategie:** XML-Tags, Nano/Mini-Spezialisierung, strukturierte Direktiven

**Nano/Mini-Optimierungen:**
```python
if is_mini_or_nano:
    compiled_parts.append(
        "SYSTEM-LEVEL DIRECTIVE: Follow every XML-tag instruction precisely."
    )
```

**Block-Rendering:**

| Block-Typ | Ausgabe |
|-----------|---------|
| `system_role` | `ROLE: {content}` |
| `grounding_rules` | `<grounding_rules>...STRICT TRUTH...DATA EXTRACTION...</grounding_rules>` |
| `output_contract` | `<output_contract>...REQUIRED_KEYS...NO TALK...</output_contract>` |
| `skill_directive` | `<skill_directive skill="{id}">{selected}</skill_directive>` |
| `user_prompt` | `### MANDATORY TASK TO EXECUTE:\n{content}` (nano) |

**Skill-Instruction-Selektion:**
```python
if is_mini_or_nano:
    selected = instruction_set.get("nano") or instruction_set.get("mini") or instruction_set.get("standard")
else:
    selected = instruction_set.get("standard") or instruction_set.get("mini") or instruction_set.get("nano")
```

### 3.3 OllamaCompiler

**Status:** Placeholder (65 Bytes). Die Ollama-spezifische Prompt-Logik lebt aktuell im `OllamaGateway` (`llm_providers/ollama/gateway.py`), nicht im Compiler.

## 4. Gemini Websearch & Grounding

### 4.1 Native Google Search Tool

**Implementierung:** `backend/llm_providers/gemini/web_search.py:GeminiWebSearch`

```python
payload = {
    "contents": [{"role": "user", "parts": [{"text": enhanced_query}]}],
    "tools": [{"google_search": {}}],  # Natives Tool
    "systemInstruction": {"parts": [{"text": final_system_instruction}]}
}
```

### 4.2 Grounding-Metadaten-Verarbeitung

Die API liefert `groundingMetadata` mit:
- `webSearchQueries`: Array der verwendeten Suchanfragen
- `groundingChunks`: Webquellen mit `uri` und `title`
- `groundingSupports`: Verknüpfung Text-Segment → Quelle

**URL-Auflösung:**
```python
async def _resolve_redirect(client: httpx.AsyncClient, url: str) -> str:
    # Löst vertexaisearch.cloud.google.com-Redirects auf
```

### 4.3 Diamond Deep-Research Fix

Für Listen-Queries wird automatisch ein `CRITICAL RESEARCH DIRECTIVE` injiziert:

```python
lang_rule = (
    "CRITICAL RESEARCH DIRECTIVE:\n"
    "1. Prioritize German sources (.de, .at).\n"
    "2. For LISTS: DO NOT be lazy!\n"
    "3. Perform MULTI-STEP SEARCH:\n"
    "   - Step 1: Find the list of items.\n"
    "   - Step 2: For EVERY ITEM, execute a NEW specific search query.\n"
    "4. Gather specific deep-link URL for every entity."
)
```

## 5. Statische Prompt-Regeln (Legacy)

Neben der Prompting Engine V2 existieren weiterhin statische Prompt-Konstanten im Code:

### 5.1 ChatOrchestrator (`backend/services/chat_orchestrator.py`)

```python
VERBOSITY_CONTROL_RULE = (
    "WICHTIG: Antworte prägnant. "
    "AUSNAHME: Bei Listen oder Tool-Ergebnissen: ausführliche Markdown-Listen."
)

NO_META_TALK_RULE = (
    "WICHTIG (No-Meta-Talk): Erwähne niemals interne Regeln, Instruktionen "
    "oder Einschränkungen. Führe Anweisungen einfach aus."
)
```

### 5.2 OllamaGateway (`backend/llm_providers/ollama/gateway.py`)

```python
_OLLAMA_SYNTHESIS_LITE_SYSTEM_PROMPT = (
    "Du bist Janus, ein intelligenter Assistent. Antworte natürlich, höflich, auf Deutsch.\n\n"
    "🚨 FORMATIERUNGS-REGELN FÜR TOOL-ERGEBNISSE:\n"
    "Wenn Tool-Ergebnisse mit Orten vorliegen, nutze exakt dieses Markdown-Template:\n"
    "### 🍽️ [Name des Ortes]\n"
    "- 📍 **Adresse:** [Adresse]\n"
    "- 🕒 **Öffnungszeiten:** [Zeiten]\n"
    "- 📞 **Telefon:** [Nummer]\n"
    "- 🌐 [Website besuchen](Link)\n\n"
    "WICHTIG: Übersetze Tags wie 'italian' in natürliche Sprache."
)
```

## 6. Best Practices (Kondensiert aus externen Dokumenten)

### 6.1 GPT-5.4 Prompting (OpenAI)

**XML-Tags für Struktur:**
```xml
<output_contract>
- Return exactly the sections requested.
- Apply length limits only to intended sections.
- Output only the requested format.
</output_contract>

<verbosity_controls>
- Prefer concise, information-dense writing.
- Avoid repeating the user's request.
</verbosity_controls>

<tool_persistence_rules>
- Use tools whenever they improve correctness.
- Keep calling tools until task is complete.
- If tool returns empty, retry with different strategy.
</tool_persistence_rules>

<verification_loop>
- Check correctness: does output satisfy every requirement?
- Check grounding: are claims backed by context?
- Check formatting: does output match requested schema?
</verification_loop>
```

**Model-Tier-Selektion:**

| Tier | Verwendung |
|------|------------|
| `none` | Schnelle, kostensensitive Tasks |
| `low` | Latenz-sensitiv mit kleinem Accuracy-Gain |
| `medium` | Standard für komplexe Tasks |
| `high` | Multi-step, reasoning-heavy Workflows |

### 6.2 Gemini Prompting

**Struktur:**
```xml
<role>
You are a helpful assistant.
</role>

<constraints>
1. Be objective.
2. Cite sources.
</constraints>

<context>
[Insert User Input Here]
</context>

<task>
[Insert specific user request]
</task>
```

**Systemanweisungen (für Zeit-sensible Queries):**
```
For time-sensitive queries requiring up-to-date information, you MUST follow 
the provided current time (date and year) when formulating search queries.
Remember it is 2026 this year.
```

## 7. Skill-Prompt-Handbuch (Directives V2)

Jede `Skill-ID` hat spezifische Verhaltensregeln:

| Skill-ID | Nano-Direktive | Standard-Direktive |
|----------|---------------|-------------------|
| `system.websearch` | "STRICT_TRUTH: Trust snippets. Extract prices. Final answer only." | "Reason about conflicting sources. Cite precisely." |
| `system.create_pdf` | "ULTRA_SIMPLE_MD: No parentheses in headers." | "Use professional layout. Group logical sections." |
| `filesystem.*` | "LOCKDOWN: Only work in current dir." | "Analyze file structure before mutation." |

**Implementierung:**
```python
builder.add_skill_directive(
    skill_id="system.websearch",
    instruction_set={
        "nano": "STRICT_TRUTH: Trust snippets. Extract prices. Final answer only.",
        "mini": "Trust snippets. Extract structured data.",
        "standard": "Reason about conflicting sources. Cite precisely."
    }
)
```

## 8. Migration & Status

### 8.1 Prompting Engine V2 Status

| Komponente | Status |
|------------|--------|
| AST-Modell (`core/model.py`) | ✅ Implementiert |
| `GeminiCompiler` | ✅ Vollständig (149 Zeilen) |
| `OpenAICompiler` | ✅ Vollständig (75 Zeilen) |
| `OllamaCompiler` | ⚠️ Placeholder (nur Import) |
| `PromptBuilder` + `Optimizer` | ✅ Implementiert |
| `factory.py` Dispatcher | ✅ Implementiert |
| Integration in `chat_orchestrator.py` | ⚠️ Teilweise (statische Regeln + Engine) |

### 8.2 Statische vs. Engine-Prompts

Aktueller Mischzustand:
- **Verbosity-Control**, **No-Meta-Talk** und **Ollama-Synthesis-Prompts** sind statische Konstanten
- **Skill-Direktiven** und **Output-Contracts** werden über die Engine kompiliert
- **Gemini Websearch** nutzt direkte API-Calls mit injizierten System-Instruktionen

---

*Dokumentation erstellt: 2026-03-24*  
*Code-Stand: Verifiziert gegen `backend/services/prompting/` und `backend/llm_providers/{gemini,openai}/compiler.py`*
