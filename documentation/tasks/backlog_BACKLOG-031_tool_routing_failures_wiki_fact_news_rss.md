# BACKLOG TASK – BACKLOG-031 – Tool Routing Failures: wiki_fact und news_rss nicht aufgerufen

## 1. Ziel
Die Intent Engine soll die Tools system.wiki_fact und system.news_rss korrekt aufrufen, wenn der Intent erkannt wurde, statt generische Ablehnungen oder internes Wissen zu verwenden.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-031
- **Beeinflusst:** Intent Engine / Skill Selector / Tool Routing / Capability Registry
- **Risiko-Einschätzung:** MEDIUM

## 3. Scope
### IN SCOPE
- SkillSelector fallback policy aktualisieren: wiki_fact und news_rss zur mandatory-Liste hinzufügen für Wikipedia/News-Intents
- Capability Registry Logik prüfen und synchronisieren mit fallback policy
- Test TC-002, TC-004, INT-002, INT-004 mit Tool-Call-Evidence bestehen

### OUT OF SCOPE
- Andere Tools (weather, geo) sind bereits durch BACKLOG-029/BACKLOG-030 abgedeckt
- Keine Änderung an LLM-Modellen oder Provider-Logik

## 4. Umsetzungsschritte
1. backend/services/skill_selector.py prüfen: fallback policy für Wikipedia/News-Intents
2. wiki_fact und news_rss von boosted zu mandatory ändern in fallback policy (ähnlich wie BACKLOG-029 Fix für weather)
3. Capability Registry prüfen: sicherstellen dass wiki_fact/news_rss als mandatory markiert sind
4. Backend neu starten und Tool-Call-Verifikation durchführen
5. Test TC-002 (Wikipedia) und TC-004 (News) mit GPT ausführen
6. Evidence prüfen: wiki_fact/news_rss Tool-Call muss in SSE stream sichtbar sein

## 5. Acceptance Criteria
- [ ] Wikipedia-Abfragen lösen system.wiki_fact Tool-Call aus
- [ ] News-Abfragen lösen system.news_rss Tool-Call aus
- [ ] Tool-Call enthält korrekte Parameter
- [ ] Modelle nutzen nicht internes Wissen statt Tools für diese Intents
- [ ] Test TC-002, TC-004, INT-002, INT-004 bestehen mit Tool-Call-Evidence

## 6. Tests / Validierung
- Manual Janus Test: "Wer ist Nikola Tesla?" → wiki_fact Tool-Call muss sichtbar sein
- Manual Janus Test: "Was gibt es Neues bei Heise?" → news_rss Tool-Call muss sichtbar sein
- Playwright E2E Test TC-002 und TC-004 ausführen und Tool-Call-Evidence prüfen

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für atomaren klaren Fix (SkillSelector fallback policy)
