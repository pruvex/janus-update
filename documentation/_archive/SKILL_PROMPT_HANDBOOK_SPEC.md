# Spezifikation: Janus Skill-Prompt-Handbuch (Directives V2)

## 1. Konzept
Das Skill-Handbuch ist eine "Instruction-Datenbank" innerhalb der Prompting Engine. Es ordnet jeder `Skill-ID` (z.B. `system.websearch`) spezifische Verhaltensregeln zu, die je nach `Model-ID` (Nano vs. Standard) und `Provider` (OpenAI vs. Gemini) unterschiedlich kompiliert werden.

## 2. Die Prompt-Skill-Matrix
| Skill-ID | Ziel des Handbuchs | Nano-Direktive | Standard-Direktive |
| :--- | :--- | :--- | :--- |
| **system.websearch** | Daten-Extraktion + kompakte Synthese | "STRICT_TRUTH: Trust snippets. Extract prices. Final answer only." | "Reason about conflicting sources. Cite precisely." |
| **system.create_pdf** | Parser-Stabilität | "ULTRA_SIMPLE_MD: No parentheses in headers." | "Use professional layout. Group logical sections." |
| **filesystem.*** | Sicherheit | "LOCKDOWN: Only work in current dir." | "Analyze file structure before mutation." |

## 3. Implementierungsweg
1. **Definition:** Direktiven werden in `core/model.py` als Pydantic-Modelle definiert.
2. **Registry:** Der `PromptBuilder` schlägt im Handbuch nach, welche Direktive zum Skill passt.
3. **Compiler:** Der Provider-Compiler übersetzt die Direktive in sein natives Format (XML, Markdown oder Plaintext).
4. **Research-Kompaktierung:** Für `system.websearch` darf vor der finalen Synthese zusätzlich ein kompaktes Faktenobjekt (`facts`, `urls`, `sources`, `source_count`) aus dem Tool-Output gebildet werden, solange der öffentliche Skill-Contract unverändert bleibt.
5. **Listen-Regel:** Bei Release-, Ranking- oder sonstigen Listenfragen muss die Direktive genug Struktur vorgeben, damit pro Listeneintrag ein passender Markdown-Link aus dem Material ausgegeben werden kann.
