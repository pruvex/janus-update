FEATURE DOSSIER: DUAL CHAT WINDOW CONFLICT SYSTEM (Same-Chat Handling & UX Control)
🧠 1. ZIEL DES FEATURES

Janus soll eindeutig und nutzerfreundlich regeln:

was passiert, wenn ein Chat in zwei Fenstern gleichzeitig geöffnet werden soll
ohne Verwirrung, Datenkonflikte oder UX-Brüche
💥 CORE VALUE

💎 „Ein Chat existiert immer genau einmal – und Janus macht das transparent und kontrollierbar.“

🚨 2. PROBLEM
❌ Aktueller Zustand (ohne Regel)

Wenn derselbe Chat in zwei Fenstern geöffnet wird:

doppelte Darstellung
mögliche Inkonsistenzen
unklarer Fokus
potenzielle Race Conditions
❌ Konsequenz
Nutzer verliert Orientierung
Gefahr von Fehlern
System wirkt „unsauber“
💎 3. LÖSUNG

👉 Ein Chat darf immer nur in einem Fenster aktiv sein

🧠 Grundprinzip:
Single Active Instance pro Chat
klare UX-Reaktion bei Konflikt
🧱 4. ARCHITEKTURPOSITION
User klickt Chat
   ↓
System prüft:
„Ist Chat bereits geöffnet?“
   ↓
Ja → Conflict Handler
Nein → normal öffnen
⚙️ 5. TECHNISCHER KONTRAKT
📥 INPUT
class OpenChatRequest(BaseModel):
    chat_id: str
    target_window: str  # A oder B
📤 OUTPUT
class OpenChatResponse(BaseModel):
    action: str  # open | focus_existing | confirm_move
    source_window: str | None
🧠 6. CORE LOGIK (KERNVERHALTEN)
Fall 1: Chat ist NICHT geöffnet

→ normal öffnen

Fall 2: Chat ist bereits in anderem Fenster geöffnet

→ Konfliktfall

💎 7. UX LÖSUNG (BEST PRACTICE)
👉 Verhalten:
🟡 Soft Warning + Entscheidung
UI Message:
„Dieser Chat ist bereits in Fenster A geöffnet.

Was möchtest du tun?“

[➡ Zum bestehenden Fenster wechseln]  
[🔄 Hierher verschieben]
🧠 8. OPTIONEN ERKLÄRT
🟢 Option 1: „Zum bestehenden Fenster wechseln“

→ Fokus springt zu Fenster A
→ keine Zustandsänderung

🟡 Option 2: „Hierher verschieben“

→ Chat wird von Fenster A entfernt
→ in Fenster B geladen
→ Fenster A erhält leeren Chat

💎 9. WARUM DIESE LÖSUNG
❌ NICHT machen:
automatisch verschieben (verwirrend)
doppelt öffnen (inkonsistent)
✔ DIESE LÖSUNG:
gibt Kontrolle
ist transparent
verhindert Fehler
🖥️ 10. UI INTEGRATION
Chatliste:
zeigt:
welcher Chat in A
welcher Chat in B
Fenster:
aktives Fenster hervorgehoben
inaktives leicht ausgegraut
Conflict Popup:
minimal
klar
schnell klickbar
⚡ 11. PERFORMANCE & STATE HANDLING
🧠 Global Chat Registry
chat_id → active_window
🧠 Echtzeit-Update:
sofort synchronisieren
UI sofort aktualisieren
⚠️ 12. EDGE CASES
❗ Schnell mehrfach klicken

→ Debounce / Lock

❗ Fenster geschlossen

→ Chat wird freigegeben

❗ App Reload

→ Zustand rekonstruieren

🔐 13. SAFETY & KONSISTENZ
keine doppelte Instanz
klare Zustandslogik
keine Race Conditions
🚀 14. IMPLEMENTIERUNGSREIHENFOLGE
Phase 1
Registry System
Phase 2
Conflict Detection
Phase 3
UI Prompt
Phase 4
Move / Focus Logic
🧠 15. SYSTEM-DEFINITION

💎 Dieses System stellt sicher, dass jeder Chat eindeutig und konsistent im Interface existiert.

💎 FINAL FAZIT

❌ Chats können doppelt existieren
✔ Chats sind eindeutig und kontrolliert

💎 „Ein Chat, ein Ort – volle Kontrolle für den Nutzer.“