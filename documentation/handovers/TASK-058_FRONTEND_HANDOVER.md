# TASK-058: Calendar Modal — Frontend Phase 1 Handover

**Handover an:** Cursor Auto-Mode / SWE-1.6 (Agent-First)
**Thread:** 🛠️ Calendar Frontend Phase 1
**Git-Branch:** develop
**Backend-Status:** ✅ Phase 1 COMPLETE
**Frontend-Status:** 🚀 Phase 1 IN PROGRESS

---

## 1. Backend-Status (COMPLETE)

### API-Endpoints (unter `/api/calendar/`)

| Methode | Endpoint | Beschreibung | Auth |
|---------|----------|-------------|------|
| GET | `/events` | Events abrufen (Query: `start_date`, `end_date`) | ✅ |
| POST | `/events` | Event erstellen | ✅ |
| PUT | `/events/{id}` | Event aktualisieren | ✅ |
| DELETE | `/events/{id}` | Event löschen | ✅ |
| GET | `/sync/status` | Sync-Status abrufen | ✅ |
| POST | `/ai/plan` | AI-Plan erstellen (Platzhalter) | ✅ |

### Schemas (JanusCalendarEvent)

```json
{
  "id": "string",
  "summary": "string",
  "start": "string (ISO)",
  "end": "string (ISO)",
  "location": "string | null",
  "description": "string | null",
  "color": "string (Google-Blau)",
  "source": "google"
}
```

### Service-Layer

- `CalendarService` in `backend/services/calendar/calendar_service.py`
- Normalisiert Google Calendar Events zu JanusCalendarEvent
- Konflikterkennung zwischen Events
- Wrappt `calendar_tools.py` ohne Modifikation

### Tests

- `backend/tests/test_calendar_modal.py` — 17 Testfälle
- Compile-Check: ✅ Bestanden
- API-Tests: ⚠️ 401 Unauthorized (erwartet, API erfordert Auth-Token)

---

## 2. Frontend-Architektur (Vanilla JS)

### Bestehende Patterns (Referenz)

#### Auth-Pattern (app.js)

```javascript
const API_BASE_URL = "http://127.0.0.1:8001";
const token = localStorage.getItem('auth_token');

const response = await fetch(`${API_BASE_URL}/api/endpoint`, {
  method: "GET",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  }
});
```

#### Modal-System (MCL)

- `frontend/js/modal-api.js` — Modal öffnen/schließen
- `frontend/js/dock.js` — Dock-Icons und Click-Handler
- `frontend/index.html` — Modal Container (`#modal-container`)
- `frontend/src/styles.css` — Modal Styles

#### Toast-Notifications (app.js)

```javascript
showToast("Erfolg", "success");
showToast("Fehler", "error");
```

---

## 3. Frontend-Implementierung (Phase 1)

### 3.1 Dateistruktur

```
frontend/
├── js/
│   ├── calendar-modal.js       (NEU)
│   ├── modal-api.js            (MODIFIZIEREN)
│   ├── dock.js                 (MODIFIZIEREN)
│   └── app.js                  (REFERENZ für Auth)
├── css/
│   └── calendar.css            (NEU)
└── index.html                  (MODIFIZIEREN für Calendar Icon)
```

### 3.2 Aufgaben (TODO)

#### Aufgabe 1: Fetch Engine

**Datei:** `frontend/js/calendar-modal.js`

```javascript
async function apiFetchCalendar(method, endpoint, body = null) {
  const API_BASE_URL = "http://127.0.0.1:8001";
  const token = localStorage.getItem('auth_token');

  const options = {
    method: method,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    }
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}/api/calendar${endpoint}`, options);
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}
```

#### Aufgabe 2: Initial Load

**Datei:** `frontend/js/calendar-modal.js`

```javascript
async function loadCalendarEvents() {
  const today = new Date();
  const nextWeek = new Date(today);
  nextWeek.setDate(today.getDate() + 7);

  const startDate = today.toISOString().split('T')[0];
  const endDate = nextWeek.toISOString().split('T')[0];

  const data = await apiFetchCalendar('GET', `/events?start_date=${startDate}&end_date=${endDate}`);
  return data.events;
}
```

#### Aufgabe 3: Agenda Rendering

**Datei:** `frontend/js/calendar-modal.js`

```javascript
function renderAgendaView(events) {
  const container = document.getElementById('calendar-agenda');
  container.innerHTML = '';

  // Gruppiere Events nach Datum
  const grouped = {};
  events.forEach(event => {
    const date = new Date(event.start).toLocaleDateString('de-DE', {
      weekday: 'long',
      day: 'numeric',
      month: 'long'
    });
    if (!grouped[date]) grouped[date] = [];
    grouped[date].push(event);
  });

  // Render
  for (const [date, dayEvents] of Object.entries(grouped)) {
    const dateHeader = document.createElement('div');
    dateHeader.className = 'calendar-date-header';
    dateHeader.textContent = date;
    container.appendChild(dateHeader);

    dayEvents.forEach(event => {
      const card = document.createElement('div');
      card.className = 'calendar-event-card';
      card.innerHTML = `
        <div class="event-title">${event.summary}</div>
        <div class="event-time">${formatTime(event.start)} - ${formatTime(event.end)}</div>
        <div class="event-location">${event.location || 'Kein Ort'}</div>
        <button class="event-delete-btn" data-id="${event.id}">Löschen</button>
      `;
      container.appendChild(card);
    });
  }
}

function formatTime(isoString) {
  return new Date(isoString).toLocaleTimeString('de-DE', {
    hour: '2-digit',
    minute: '2-digit'
  });
}
```

#### Aufgabe 4: Create Flow

**Datei:** `frontend/js/calendar-modal.js`

```javascript
async function createCalendarEvent(eventData) {
  try {
    // Optimistic UI
    const tempId = 'temp-' + Date.now();
    const tempEvent = { ...eventData, id: tempId };
    addEventToUI(tempEvent);

    // API Call
    const result = await apiFetchCalendar('POST', '/events', eventData);
    
    // Replace temp with real
    replaceEventInUI(tempId, result);
    showToast("Termin erstellt", "success");
  } catch (error) {
    // Rollback
    removeEventFromUI(tempId);
    showToast("Fehler beim Erstellen", "error");
  }
}
```

#### Aufgabe 5: Delete Flow

**Datei:** `frontend/js/calendar-modal.js`

```javascript
async function deleteCalendarEvent(eventId) {
  if (!confirm("Termin wirklich löschen?")) return;

  try {
    // Optimistic UI
    const event = getEventFromUI(eventId);
    removeEventFromUI(eventId);

    // API Call
    await apiFetchCalendar('DELETE', `/events/${eventId}`);
    showToast("Termin gelöscht", "success");
  } catch (error) {
    // Rollback
    restoreEventInUI(event);
    showToast("Fehler beim Löschen", "error");
  }
}
```

#### Aufgabe 6: MCL-Integration

**Datei:** `frontend/js/dock.js`

```javascript
// Calendar Icon hinzufügen
const calendarIcon = document.getElementById('dock-calendar');
calendarIcon.addEventListener('click', () => {
  openModal('calendar-modal');
  loadCalendarEvents().then(events => renderAgendaView(events));
});
```

**Datei:** `frontend/js/modal-api.js`

```javascript
// Modal öffnen
function openCalendarModal() {
  const modal = document.createElement('div');
  modal.id = 'calendar-modal';
  modal.className = 'modal-content';
  modal.innerHTML = `
    <div class="modal-header">
      <h2>Kalender</h2>
      <button class="modal-close">×</button>
    </div>
    <div class="calendar-toolbar">
      <button id="create-event-btn">Neuer Termin</button>
    </div>
    <div id="calendar-agenda"></div>
  `;
  
  document.getElementById('modal-container').appendChild(modal);
}
```

#### Aufgabe 7: CSS

**Datei:** `frontend/css/calendar.css`

```css
.calendar-event-card {
  background: #f5f5f5;
  border-left: 4px solid #4285f4; /* Google Blue */
  padding: 12px;
  margin: 8px 0;
  border-radius: 4px;
}

.event-title {
  font-weight: bold;
  margin-bottom: 4px;
}

.event-time {
  font-size: 0.9em;
  color: #666;
}

.event-location {
  font-size: 0.85em;
  color: #888;
}

.event-delete-btn {
  float: right;
  background: #dc3545;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
}

.calendar-date-header {
  font-weight: bold;
  margin: 16px 0 8px 0;
  color: #333;
}
```

---

## 4. Test-Szenario

1. **Modal öffnen:** Klick auf Calendar-Icon in Sidebar
2. **Events laden:** Automatischer Fetch für heute + 7 Tage
3. **Agenda anzeigen:** Gruppierte Events pro Tag
4. **Termin erstellen:** Button "Neuer Termin" → Formular → POST
5. **Termin löschen:** Button auf Event-Card → Bestätigung → DELETE
6. **Optimistic UI:** Sofortige UI-Update, Rollback bei Fehler

---

## 5. Fehlerbehandlung

| Fehler | Aktion |
|--------|--------|
| 401 Unauthorized | Token refresh (siehe app.js `attemptSilentLogin()`) |
| 400 Bad Request | Validierungs-Fehler anzeigen |
| 500 Internal Error | Toast mit "Server-Fehler" |
| Network Error | Toast mit "Verbindungsfehler" |

---

## 6. Backward-Referencing

- Backend-Schemas: `backend/data/schemas_calendar.py`
- Backend-Service: `backend/services/calendar/calendar_service.py`
- Backend-Router: `backend/api/routers/calendar.py`
- Auth-Pattern: `frontend/js/app.js`
- Modal-System: `frontend/js/modal-api.js`

---

## 7. Completion Gate (Frontend Phase 1)

- [x] Fetch Engine mit Auth
- [x] Initial Load beim Modal-Öffnen
- [x] Agenda Rendering mit Datum-Gruppierung
- [x] Create Flow mit Optimistic UI
- [x] Delete Flow mit Bestätigung
- [x] MCL-Integration (Dock + Modal)
- [x] CSS für Calendar Modal

---

## 8. Nächste Phasen

**Phase 2:** Inline Editing, Sidebar Filter, Conflict UI
**Phase 3:** Day/Week Views, Sync Status
**Phase 4:** AI Calendar Engine, Quick Actions

---

**Handover erstellt:** 2026-05-01 02:30
**Backend-Implementer:** Kimi K2.6
**Frontend-Implementer:** Cursor Auto-Mode / SWE-1.6
