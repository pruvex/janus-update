# BACKLOG TASK – BACKLOG-033 – Provider Parity: Gemini liefert generische Antworten statt spezifischen Antworten

## 1. Ziel
Gemini-Provider (gemini-3-flash-preview) soll für gleiche Prompts äquivalente Qualität und Spezifität der Antworten liefern wie GPT-5.4-nano, um die Provider-Parity-Anforderung zu erfüllen.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-033
- **Beeinflusst:** Intent Engine / Skill Selector / Provider Parity / Gemini Integration
- **Risiko-Einschätzung:** MEDIUM

## 3. Scope
### IN SCOPE
- SkillSelector Provider-spezifische Tool-Selection-Logik prüfen
- Intent-Interpretation für Gemini vs GPT vergleichen
- Tool-Liste für Gemini prüfen: sind wiki_fact/news_rss enthalten?
- Provider-spezifisches Intent-Mapping korrigieren falls nötig
- Test TC-002-GEMINI und TC-004-GEMINI bestehen

### OUT OF SCOPE
- Keine Änderung an GPT-Verhalten (dies ist bereits korrekt)
- Keine Änderung an Model-Selection-Logik für andere Intents

## 4. Umsetzungsschritte
1. backend/services/skill_selector.py prüfen: Provider-spezifische Tool-Liste für Gemini
2. Prüfen ob wiki_fact und news_rss in Gemini Tool-Liste enthalten sind
3. Intent-Interpretation für Gemini prüfen: werden Wikipedia/News-Intents korrekt erkannt?
4. Provider-spezifisches Intent-Mapping aktualisieren falls nötig
5. Backend neu starten und Tool-Call-Verifikation durchführen
6. Test TC-002-GEMINI (Wikipedia) und TC-004-GEMINI (News) ausführen
7. Evidence prüfen: Gemini muss spezifische Informationen liefern statt generischen Antworten

## 5. Acceptance Criteria
- [ ] Gemini liefert für Wikipedia-Abfragen spezifische Informationen statt generischen Antworten
- [ ] Gemini ruft für gleiche Intents die gleichen Tools auf wie GPT
- [ ] Provider Parity ist erreicht (äquivalente Antwortqualität)
- [ ] Test TC-002-GEMINI, TC-004-GEMINI bestehen mit äquivalenten Ergebnissen wie GPT

## 6. Tests / Validierung
- Manual Janus Test mit Gemini: "Wer ist Nikola Tesla?" → spezifische Tesla-Info (nicht generische Antwort)
- Manual Janus Test mit Gemini: "Was gibt es Neues bei Heise?" → news_rss Tool-Call oder spezifische News-Antwort
- Playwright E2E Test TC-002-GEMINI und TC-004-GEMINI ausführen
- Antworten mit GPT-Vergleich prüfen: äquivalente Qualität

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für Provider-Parity Fix (SkillSelector Provider-spezifische Logik)
