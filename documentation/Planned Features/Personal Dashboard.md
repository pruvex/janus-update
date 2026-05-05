
Janus Modul: Personal Dashboard / Command Center

Version: 1.0
Ziel: Produktionsreife Spezifikation für Pruki / Janus

🧠 1. Konzept-Definition
Offizieller Name

Personal Command Center (PCC)

Einordnung

Kein klassisches Dashboard, sondern:

Ein On-Demand Intelligence Overlay, das in wenigen Sekunden die wichtigsten, personalisierten Informationen liefert.

🎯 2. Kernziel

Der Nutzer soll innerhalb von 3–5 Sekunden:

seine aktuelle Situation verstehen
Prioritäten erkennen
direkt in Aktionen springen können
⚠️ 3. Design-Prinzipien (nicht verhandelbar)
3.1 On-Demand statt Persistent
Wird nur aktiv geöffnet
Kein permanentes UI-Element notwendig
3.2 Information Density > Detailtiefe
Fokus auf:
Relevanz
Priorisierung
Kein „Daten anzeigen“, sondern:
„Entscheidungen ermöglichen“
3.3 Hub, nicht Ziel
Dashboard zeigt nur Überblick
Klick → öffnet jeweiliges Modul
3.4 Kuratiert statt frei
Keine komplett freie Widget-Bastelei
Nur definierte Module auswählbar
3.5 Smart > Raw Data

Langfristig:

AI priorisiert Inhalte
nicht nur Anzeige, sondern Bewertung
🧱 4. Architektur
4.1 Trennung der Verantwortlichkeiten
dashboard.core
  ├── widget.system
  ├── user.config
  ├── data.aggregation
  └── intelligence.layer (future)

ui.universal-modal
  └── render.target (nur Darstellung)
4.2 Wichtige Regel

❌ Dashboard = Modal
✅ Dashboard = Logik + Widgets
✅ Modal = Render-Container

🧩 5. Widget-System
5.1 Initial verfügbare Widgets
📧 Email Widget
letzte 3 / 5 Mails
später: „wichtigste Mail“
📅 Calendar Widget
nächste Termine
Zeit bis zum nächsten Event
🌤 Weather Widget
aktuelles Wetter
konfigurierbare Location
📰 News Widget
1–3 Headlines
Kategorien wählbar
5.2 Widget-Interface (Standard)
interface DashboardWidget {
  id: string;
  enabled: boolean;
  config: object;

  fetchData(): Promise<Data>;
  renderCompact(): UIComponent;
  onClick(): void; // Drilldown
}
5.3 Widget-Konfiguration (User)

Minimal halten:

{
  emails: { count: 3 },
  calendar: { range: "today" },
  weather: { location: "auto" },
  news: { topics: ["general"] }
}
⚙️ 6. User Experience
6.1 Öffnen
Shortcut: Cmd + D
optional:
Command Palette Integration
kontextbasierte Vorschläge (später)
6.2 Layout

Vertikale kompakte Liste:

[ Emails ]
→ 1 wichtige Mail

[ Termine ]
→ Meeting in 1h

[ Wetter ]
→ Regen ab 15:00

[ News ]
→ 1–2 Headlines
6.3 Interaktion
Klick auf Widget:
→ öffnet Modul (Mail, Kalender etc.)
kein Deep Interaction im Dashboard selbst
6.4 Settings
Zugriff:
⚙️ Button im Modal
Funktionen:
Widgets aktivieren/deaktivieren
einfache Konfiguration pro Widget
6.5 „Add Widget“
klare Liste verfügbarer Widgets
kein freies Layout-System (Phase 1)
🚀 7. Smart Layer (Phase 2+)
Ziel:

Transformation von Anzeige → Intelligenz

Beispiele:

Statt:

„5 neue Mails“

→

„Wichtige Mail – Antwort ausstehend“

Statt:

„Meeting um 14:00“

→

„Meeting in 2h – keine Notizen vorhanden“

Daily Summary (optional)

„Heute: 2 Meetings, 1 wichtige Mail, Regen am Nachmittag“

🧠 8. Erweiterungen (Zukunft)
Kontext-Modi:
Arbeit
Freizeit
Focus Mode:
zeigt nur Top 2–3 Items
Adaptive Priorisierung (AI)
🧪 9. Testbarkeit (Playwright-ready)
9.1 Kern-Tests
Öffnen des Dashboards
test('opens dashboard via shortcut', async ({ page }) => {
  await page.keyboard.press('Meta+D');
  await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
});
Widget Rendering
test('renders enabled widgets', async ({ page }) => {
  const widgets = page.locator('[data-widget]');
  await expect(widgets).toHaveCount(3);
});
Widget Interaktion
test('clicking widget opens module', async ({ page }) => {
  await page.click('[data-widget="email"]');
  await expect(page.locator('[data-module="email"]')).toBeVisible();
});
Settings Änderung
test('toggle widget visibility', async ({ page }) => {
  await page.click('[data-settings]');
  await page.click('[data-toggle="weather"]');
  await expect(page.locator('[data-widget="weather"]')).not.toBeVisible();
});
🧩 10. Default-Konfiguration (entscheidend)

Beim ersten Start:

{
  "emails": { "enabled": true, "count": 3 },
  "calendar": { "enabled": true },
  "weather": { "enabled": true, "location": "auto" },
  "news": { "enabled": true, "topics": ["general"] }
}
⚠️ 11. Anti-Patterns (vermeiden!)

❌ Zu viele Widgets
❌ Freies Drag & Drop Layout (Phase 1)
❌ Zu viele Einstellungen
❌ Reine Datenanzeige ohne Priorisierung
❌ Dashboard als alleinige Modal-Logik implementieren

🏁 12. Fazit

Dieses Modul ist:

kein Feature – sondern ein zentrales Nutzungselement

Richtig umgesetzt wird es:

täglich genutzt
Einstiegspunkt in alle Module
Basis für zukünftige AI-Intelligenz
🔥 Kurzform für Orchestrator

Baue ein modulares, On-Demand Command Center im Universal Modal,
basierend auf kuratierten Widgets, mit Fokus auf verdichtete Information,
klarer Drilldown-Navigation und zukünftiger AI-Priorisierung.