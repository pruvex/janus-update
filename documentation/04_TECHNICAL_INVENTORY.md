# Janus Technisches Inventar (V2.1)

**Stand:** 2026-03-28  
**Standard:** Diamond-Standard V2.1 (Zero-Base Audit aktiv)
**Scope:** Vollständiges Verzeichnis aller architektonischen Bausteine, Features und Skills.

---

## 🏗 Domain: Core Architecture
*Das Fundament und die Steuerung von Janus.*

### System: Diamond OS (Governance)
- **Beschreibung:** Workflow-Schutz, Enforcement-Layer und Automatisierung.
- **Dateien:** `.cursor/rules/`, `scripts/auto_fill_task.js`, `scripts/diamond_check.sh` 

### System: LLM Gateway & Prompting
- **Beschreibung:** Managed API-Verbindungen (OpenAI, Gemini, Ollama) und kompiliert Dialekt-spezifische Prompts.
- **Dateien:** `backend/services/llm_gateway.py`, `backend/services/prompting/` 

### System: Chat Orchestrator
- **Beschreibung:** Zentrale Steuerlogik. Koordiniert Subsysteme, führt den Tool-Loop aus und synchronisiert den Zustand.
- **Dateien:** `backend/services/chat_orchestrator.py`, `backend/services/orchestrator/` 

### System: Agent Planner & Tool Executor
- **Beschreibung:** Analysiert Anfragen, plant Schritte und führt Skills über den Skill-Router aus.
- **Dateien:** `backend/services/agent_planner.py`, `backend/services/tool_executor.py` 

---

## 📚 Domain: Knowledge Management
- **Beschreibung:** Vektor-basierte Dokumentensuche (RAG) und PDF-Bearbeitung.
- **Features:** PDF Fact-Checking, Knowledge Center UI.
- **Status:** Alle Skills (`knowledge.*`) auf 🔍 Audit gesetzt.

## 🧠 Domain: Memory & Context
- **Beschreibung:** Kurz- und Langzeitgedächtnis (STM/LTM) sowie semantische Vektor-Suche.
- **Features:** Long-Term Memory, Conversation Summarizer.
- **Status:** Alle Skills (`memory.*`) auf 🔍 Audit gesetzt.

## 💬 Domain: Communication & Finance
- **Beschreibung:** Adressbuch-Verwaltung, E-Mail Integration und Preisvergleichs-Dienste.
- **Features:** Preis-Lookup (Idealo/Geizhals), E-Mail Automation.
- **Status:** Alle Skills (`contacts.*`, `communication.*`, `system.price_comparison`) auf 🔍 Audit gesetzt.

---

## 🔍 Anhang A: Vollständiges Skill-Register (Stand 28.03.26)
*Hinweis: Alle funktionalen Skills wurden zur Neu-Validierung auf 'Audit' zurückgesetzt.*

| Skill ID | Domain | Status | Notiz / Mangel |
| :--- | :--- | :--- | :--- |
| **system.websearch** | Web & Research | 🔍 Audit | GPT-Pricing & XML-Sandwich Drift |
| **system.price_comparison** | Finance | 🔍 Audit | Regex-Schwäche & Versandkosten |
| **system.generate_image** | Content Gen | 🔍 Audit | Prompt-Expansion fehlt |
| **system.wikipedia_summary**| Web & Research | 🔍 Audit | Keine Disambiguierung |
| **system.weather** | Location & Geo | 🔍 Audit | Keine Standort-Persistenz |
| **system.country_info** | Location & Geo | 🔍 Audit | Re-Validation V2.1 |
| **system.create_pdf** | Content Gen | 🔍 Audit | Re-Validation V2.1 |
| **system.save_mp3** | Content Gen | 🔍 Audit | Re-Validation V2.1 |
| **calendar.* (8 Skills)** | Calendar | 🔍 Audit | Vollständiger Audit-Lauf nötig |
| **communication.* (4 Skills)**| Communication | 🔍 Audit | Vollständiger Audit-Lauf nötig |
| **contacts.* (3 Skills)** | Communication | 🔍 Audit | Vollständiger Audit-Lauf nötig |
| **filesystem.* (10 Skills)**| File Ops | 🔍 Audit | Vollständiger Audit-Lauf nötig |
| **knowledge.list_documents**| Knowledge | 🔴 Broken | Bekannte Fehlfunktion |

---

## 💡 Status-Legende (V2.1)
- ✅ **Diamond:** Vollständig gehärtet (Pydantic In/Out, Renderer-Autorität, Benchmarked).
- 🔍 **Audit:** Funktional vorhanden, aber Diamond-Validierung V2.1 steht aus.
- 🔴 **Broken:** Bekannte Probleme, erfordert Reparatur.
