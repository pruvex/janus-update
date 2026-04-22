FEATURE DOSSIER: CONTEXT AWARENESS SYSTEM + SMART COMPRESSION (Context Ampel & Chat-Bereinigung)
🧠 1. ZIEL DES FEATURES

Janus soll jederzeit:

den aktuellen Zustand des Kontextfensters sichtbar machen
den Nutzer aktiv warnen, bevor Qualität verloren geht
und intelligente Maßnahmen zur Kontext-Optimierung anbieten
💥 CORE VALUE

💎 „Janus verhindert, dass LLMs dumm werden – bevor es passiert.“

🚨 2. PROBLEM
❌ Aktueller Zustand bei LLMs
Kontextfenster ist begrenzt
Nutzer sieht nicht, wie voll es ist
Qualität sinkt schleichend
❌ Konsequenz
Antworten werden schlechter
Kontext geht verloren
Nutzer merkt es zu spät
💎 3. LÖSUNG

👉 Visuelles Kontext-Monitoring + intelligente Eingriffe

🧠 Kernkomponenten:
Context Meter (Ampelsystem)
Model-aware Kontextberechnung
Smart Compression Engine
User Decision Layer
🧱 4. ARCHITEKTURPOSITION
Chat State
   ↓
Token Counter
   ↓
Model Context Limit Resolver
   ↓
Context Ratio (0–100%)
   ↓
Ampel Renderer
   ↓
User Decision / Smart Compression
⚙️ 5. TECHNISCHER KONTRAKT
📥 INPUT
class ContextStateInput(BaseModel):
    chat_id: str
    model: str
    messages: list[str]
📤 OUTPUT
class ContextStateOutput(BaseModel):
    total_tokens: int
    max_context: int
    usage_ratio: float
    status: str  # green | yellow | orange | red
🧮 6. CONTEXT BERECHNUNG
Formel:
usage_ratio = total_tokens / max_context
Beispiel:
500.000 Tokens / 1.000.000 Kontext → 50% → 🟡
120.000 Tokens / 128.000 Kontext → 93% → 🔴
🚦 7. AMPELSYSTEM (UX KERN)
Statuslogik:
Status	Bereich	Bedeutung
🟢 Grün	0–50%	alles optimal
🟡 Gelb	50–70%	leichte Einschränkung
🟠 Orange	70–85%	kritisch
🔴 Rot	85–100%	Gefahr von Qualitätsverlust
UI:
Anzeige oben im Chat
farbig + Prozentwert
optional Tooltip mit Details
🔁 8. MODEL SWITCH HANDLING (KRITISCH)
Problem:

Modelle haben unterschiedliche Kontextgrößen

Lösung:
User wechselt Modell
   ↓
Neuberechnung Kontext
   ↓
Ampel aktualisiert sich sofort
💥 UX Effekt:

Wechsel von großem → kleinem Modell kann sofort 🔴 anzeigen

Beispiel:
Chat: 500k Tokens
Modell A: 1M Kontext → 🟡
Modell B: 128k Kontext → 🔴
⚠️ 9. USER WARNING SYSTEM
Trigger:
Ampel wird 🔴
oder Modellwechsel führt zu Überlauf
UX:

Popup / Inline Hinweis:

„Dieses Modell hat ein kleineres Kontextfenster.
Möchtest du:

1. Beim aktuellen Modell bleiben  
2. Chat komprimieren  
3. Neuen Chat starten“
🧠 10. SMART COMPRESSION ENGINE
Ziel:
Kontext verkleinern
Wissen erhalten
Prinzip:

Alte Inhalte → Zusammenfassung → aus Kontext entfernen → in Memory speichern

Ablauf:
Ältere Nachrichten
   ↓
LLM Summary
   ↓
komprimierter Block
   ↓
Originale entfernen
   ↓
Summary bleibt im Kontext
   ↓
Originale im RAG Memory speichern
💎 11. KONTEXT + RAG HYBRID
Wichtig:
Entfernte Inhalte gehen nicht verloren
werden im Memory gespeichert
Bei Bedarf:
User fragt nach alten Infos
   ↓
RAG Retrieval
   ↓
Kontext wiederhergestellt
📦 12. CHAT-BEREINIGUNG (UX DESIGN)
Verhalten:
alte Teile werden „eingeklappt“
sichtbar als:
„Zusammengefasst“
„Archiviert“
Aktionen:
aufklappen (RAG Trigger)
Details anzeigen
erneut erweitern
🧠 13. USER CONTROL (WICHTIG)
❌ NICHT:
automatische, unsichtbare Kompression
✔ JA:
Vorschläge geben
User entscheidet
💎 Grundsatz:

„User bleibt in Kontrolle über seinen Kontext“

⚙️ 14. OPTIONALE AUTOMATIK
Soft Automation:
Vorschlag bei 🟠 / 🔴
optional Auto-Modus (opt-in)
⚡ 15. PERFORMANCE STRATEGIE
Token Counting:
incremental statt komplett neu berechnen
Compression:
nur bei Bedarf ausführen
batchweise
⚠️ 16. EDGE CASES
❗ Sehr lange Chats
mehrere Kompressionsblöcke
❗ Wichtiges Wissen verloren?
RAG als Backup
❗ falsche Summary
expand / retry möglich
🔐 17. SAFETY & QUALITÄT
keine aggressive Löschung
reversible Kompression
vollständige Nachvollziehbarkeit
🚀 18. IMPLEMENTIERUNGSREIHENFOLGE
Phase 1
Token Counting
Ampel UI
Phase 2
Model Switch Handling
Phase 3
Smart Compression
Phase 4
RAG Integration
🧠 19. SYSTEM-DEFINITION

💎 Dieses System macht Kontext sichtbar, kontrollierbar und optimierbar.

💎 FINAL FAZIT

❌ Kontext ist unsichtbar und bricht
✔ Kontext wird aktiv gemanagt

💎 „Janus hält den Kontext schlank – und das Wissen vollständig.“