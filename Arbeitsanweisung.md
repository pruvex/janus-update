AGENTIC HANDlungsplan: Kosmetische Überarbeitung des Kosten-Detail-Modals
Dein Ziel: Das Design und Layout des Kosten-Detail-Modals verbessern, um es klarer, informativer und ästhetisch ansprechender zu gestalten.
Der Plan:
Stufe 1: Validierung & Vorbereitung
An den CLI-Agenten: git status. Bestätige, dass wir uns auf dev/kosten-gemini-tracking-9 befinden.
Stufe 2: HTML-Struktur anpassen (index.html)
An den CLI-Agenten: Lese die Datei frontend/index.html.
Ankerpunkt-Strategie: Finde die <thead>-Sektion der <table id="cost-details-table">.
Ersetze: den Inhalt des <thead>:
code
Html
<thead>
  <tr>
    <th>Datum</th>
    <th>Modell</th>
    <th>Details</th> <!-- Dieser Header wird jetzt umbenannt -->
    <th>Kosten</th>
  </tr>
</thead>
Mit:
code
Html
<thead>
  <tr>
    <th>Modell</th>
    <th>Tokens</th> <!-- Spalten umbenannt und "Typ" entfernt -->
    <th>Gesamtkosten (€)</th>
  </tr>
</thead>
(Hinweis: Wir entfernen auch "Datum" für mehr Kompaktheit und weil es in der linken Liste bereits angezeigt wird).
Stufe 3: JavaScript-Logik anpassen (cost-visualizer.js)
An den CLI-Agenten: Lese die Datei frontend/js/cost-visualizer.js.
Ankerpunkt-Strategie: Finde die details.forEach(item => { ... })-Schleife, die die Tabelle befüllt.
Ersetze: Den Inhalt dieser Schleife.
Mit: der neuen Logik, die zur neuen Tabellenstruktur passt:
code
JavaScript
details.forEach(item => {
  const row = tableBody.insertRow();
  row.insertCell(0).textContent = item.model;
  
  let detailText = '';
  if (item.input_tokens !== null) {
    detailText = `Eingabe: ${item.input_tokens}, Ausgabe: ${item.output_tokens}`;
  } else if (item.image_quality) {
    detailText = `Bilder: ${item.count} (${item.quality})`; // Annahme, Backend wird dies aggregieren
  }
  row.insertCell(1).textContent = detailText;
  
  row.insertCell(2).textContent = item.total_cost.toFixed(4);
});
Stufe 4: CSS-Styling anpassen (styles.css)
An den CLI-Agenten: Lese die Datei frontend/src/styles.css.
Ankerpunkt-Strategie: Finde die .modal-content-Regel.
Modifiziere sie, um das Modal breiter zu machen:
Ändere max-width: 700px; zu max-width: 800px;.
Füge neue Regeln hinzu, um die Tabelle "hübscher" zu machen:
code
Css
#cost-details-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}
#cost-details-table th, #cost-details-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--surface-color);
}
#cost-details-table th {
  background-color: var(--accent-color);
  color: var(--background-primary);
}
#cost-details-table td:last-child {
    text-align: right; /* Kosten rechtsbündig für bessere Lesbarkeit */
    font-weight: 600;
}
Stufe 5: Implementierungs-Abschluss & Übergabe zur Verifizierung
[KRITISCHER SCHRITT] Alle Änderungen sind implementiert. KEIN COMMIT.
Ich übergebe die Kontrolle an Sie.
Bitte überprüfen Sie das neue Modal-Design:
Ist die "Typ"-Spalte verschwunden und "Details" zu "Tokens" umbenannt?
Ist das Modal breiter?
Hat die Tabelle das neue, saubere Styling?
Ich warte auf Ihr expliziertes 'success'-Signal.