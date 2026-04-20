Implementierungsplan: Janus Prompting Engine V2 (Dialect Factory)
Version: 1.0
Datum: 2026-03-19
Status: Geplant für Janus v0.5.0

1. Executive Summary
Dieses Dokument beschreibt den risikoarmen, phasenweisen Umbau der Prompt-Generierung in Janus. Das Ziel ist der Ersatz der statischen Prompt-Strings durch eine "Dialect Engine". Diese Engine nutzt das Abstract Factory Pattern, um für jeden LLM-Provider (OpenAI, Gemini, Ollama) hochoptimierte, native Prompts zu kompilieren. Die Implementierung erfolgt schrittweise, um die Stabilität des bestehenden Systems zu gewährleisten, und fokussiert sich zunächst auf die Perfektionierung des GPT-Dialekts.

2. Kernprinzipien & Ziele
Entkopplung: Die Orchestrator-Logik wird von den Prompt-Implementierungsdetails vollständig getrennt.
Performance: Jeder Provider erhält den für ihn optimalen Prompt, um Latenz zu minimieren und Antwortqualität zu maximieren.
Wartbarkeit: Das Hinzufügen neuer Modelle (z.B. GPT-5.5) oder Provider erfordert nur das Hinzufügen einer neuen "Compiler"-Klasse, ohne die Kernlogik zu berühren.
Robustheit: Durch strukturierte Prompt-Objekte (AST), Token-Budgeting und Output-Validierung wird die Stabilität von Agenten-Workflows drastisch erhöht.

3. Phasenweiser Implementierungsplan (Risikoarm)
Phase 0: Fundament schaffen (Zero-Risk, Non-Breaking)
In dieser Phase wird die gesamte neue Struktur angelegt, ohne eine einzige Zeile des produktiven Codes zu ändern. Das bestehende System läuft unverändert weiter.
Schritte:
Erstelle die neue Verzeichnisstruktur:
```bash
mkdir -p backend/services/prompting/compilers
mkdir -p backend/services/prompting/core
mkdir -p backend/services/prompting/runtime
touch backend/services/prompting/__init__.py
touch backend/services/prompting/compilers/__init__.py
touch backend/services/prompting/core/__init__.py
touch backend/services/prompting/runtime/__init__.py
```
Definiere das Abstrakte Datenmodell (AST) in backend/services/prompting/core/model.py:
```python
# backend/services/prompting/core/model.py
from pydantic import BaseModel, Field
from typing import Any, List, Literal, Dict

class PromptBlock(BaseModel):
    type: Literal["system_role", "grounding_rules", "output_contract", "tool_rules", "memory", "user_prompt"]
    content: Any
    priority: int = 10 # 1=höchste Prio, wird nie gekürzt
    required: bool = False

class Prompt(BaseModel):
    blocks: List[PromptBlock] = Field(default_factory=list)
    version: str = "v0.5.0"

# --- Beispiel-Direktiven (stark typisiert) ---
class StrictGroundingDirective(BaseModel):
    source: str

class OutputContractDirective(BaseModel):
    format: Literal["json", "markdown_list", "prose"]
    fields: List[str] = Field(default_factory=list)
```
Lege die Compiler-Schnittstelle in backend/services/prompting/compilers/base.py an:
```python
# backend/services/prompting/compilers/base.py
from abc import ABC, abstractmethod
from ..core.model import Prompt

class BasePromptCompiler(ABC):
    @abstractmethod
    def compile(self, prompt_ast: Prompt, max_tokens: int) -> str:
        """Kompiliert das Prompt-AST in einen finalen String."""
        pass
```

Phase 1: Pilot-Implementierung im AgentPlanner (Isoliert & Testbar)
Wir testen die neue Engine an einer isolierten, unkritischen Komponente: dem AgentPlanner. Dessen Aufgabe ist klar definiert (JSON-Output), was ihn zum perfekten Testfeld macht.
Schritte:
Implementiere den OpenAICompiler in backend/services/prompting/compilers/openai.py:
Dieser Compiler wird anfangs nur die für den AgentPlanner nötigen XML-Tags rendern.
Erstelle den PromptBuilder in backend/services/prompting/runtime/builder.py:
Dieser Service wird die zentrale Schnittstelle, um das Prompt-AST zu erstellen.
Passe backend/services/agent_planner.py an:
Die bestehende _build_planner_prompt Methode wird beibehalten.
Eine neue Methode _build_planner_prompt_v2 wird hinzugefügt, die den PromptBuilder und OpenAICompiler nutzt.
Im plan-Flow wird (z.B. über eine temporäre Variable) die neue Methode aufgerufen und ihr Output geloggt. Das Ergebnis wird noch nicht an das LLM gesendet.
Ziel: Wir vergleichen im Log den Output des alten und neuen Systems und stellen sicher, dass der neue Prompt korrekt und GPT-5.4-konform ist.

Phase 2: GPT-Dialekt fertigstellen & A/B-Testing (Kontrollierte Integration)
Nach erfolgreichem Pilot-Test wird der GPT-Compiler voll ausgebaut und hinter einem Feature-Flag im Haupt-Chat-Flow aktiviert.
Schritte:
Vervollständige den OpenAICompiler: Implementiere das Rendern aller PromptBlock-Typen mit den korrekten XML-Tags aus der Prompütinghgpt.md.
Implementiere den Optimizer in backend/services/prompting/runtime/optimizer.py:
Dieser Service erhält ein Prompt-AST und ein Token-Budget. Er kürzt oder entfernt Blöcke mit niedriger Priorität, bis das Budget eingehalten wird.
Integriere die Engine in llm_gateway.py (hinter einem Schalter):
Füge eine Konfigurationsoption hinzu, z.B. USE_PROMPTING_ENGINE_V2: bool = False.
In reason_and_respond wird je nach Schalter entweder der alte Prompt-String oder der neue, kompilierte Prompt verwendet.
Ziel: Wir können das neue System gezielt für Test-Chats aktivieren, ohne alle User zu beeinflussen. Ein Rollback ist durch Umlegen des Schalters jederzeit möglich.

Phase 3: Migration & Cleanup (Der finale Switch)
Wenn die A/B-Tests erfolgreich sind und die Stabilität nachgewiesen ist, wird die neue Engine zum Standard.
Schritte:
Setze den Konfigurations-Schalter USE_PROMPTING_ENGINE_V2 auf True.
Refactoring: Entferne die alten, statischen Prompt-Strings und _build..._prompt-Funktionen aus chat_orchestrator.py, llm_gateway.py und context_manager.py. Ersetze sie durch Aufrufe an den PromptBuilder.
Code-Cleanup: Lösche allen Code, der nur für das alte System benötigt wurde.

Phase 4: Expansion (Gemini & Ollama)
Mit dem bewährten Framework ist die Unterstützung weiterer Provider nur noch eine Erweiterung.
Schritte:
Implementiere den GeminiCompiler in backend/services/prompting/compilers/gemini.py (nutzt Markdown).
Implementiere den OllamaCompiler in backend/services/prompting/compilers/ollama.py (nutzt Plaintext).
Die get_prompt_builder Factory in backend/services/prompting/factory.py wird erweitert, um basierend auf dem provider-String den passenden Compiler auszuwählen.
