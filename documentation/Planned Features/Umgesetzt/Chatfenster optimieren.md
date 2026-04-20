jetzt hat die texteinggabe nur eine zeile. was wir möchten, eine texteingabe die einen zeilenumbruch hat und sich wie bei chatgpt dynamisch vergrößtert, damit auch bei größeren prompts der komplette chatinhalt zu sehen ist.
Best UX Pattern (so solltest du es bauen)
Verhalten:
Start: 1 Zeile
Wachstum: bis ca. 4–8 Zeilen
Danach: interner Scroll im Input

👉 Wichtig: NICHT unendlich wachsen lassen, sonst:

Chat verschwindet nach oben
Fokus geht verloren
💡 Bonus UX (was richtig stark wäre)
1. Shift + Enter = neue Zeile

Standard, MUSS drin sein

2. Enter = senden (optional togglebar)

Power-User lieben das

3. Soft Shadow / Highlight bei Fokus

→ gibt visuelles Feedback

4. Attachments + Buttons fix ausgerichtet

Nicht mitskalieren lassen, sondern:

Input wächst
Icons bleiben sauber aligned
🧩 Technisch (kurz & konkret)

Falls du z. B. in React bist:

<textarea
  rows={1}
  style={{ resize: "none", overflow: "hidden" }}
  onInput={(e) => {
    e.target.style.height = "auto";
    e.target.style.height = e.target.scrollHeight + "px";
  }}
/>

Mit max-height:

textarea {
  max-height: 200px;
  overflow-y: auto;
}
🧠 UX Fazit (ehrlich)

Was du vorhast (Sidebar + Input Fix) geht genau in die richtige Richtung:

Sidebar → Struktur & Klarheit
Input → Flow & Usability

👉 Wenn du NUR eine Sache fixen müsstest:
→ Mach zuerst den Input. Der Impact ist sofort spürbar.
