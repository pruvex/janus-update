/**
 * Janus Calendar Modal — MCL Dock-Modul "calendar" (TASK-058 Phase 1).
 * Öffnen: openModal({ type: "calendar" }) oder window.dockOpen("calendar") (modal-api).
 */

import {
  dockClose,
  dockMinimize,
  getDockModuleState,
  subscribeWindowState,
} from "./window-state.js";
import { bringToFront } from "./modal-api.js";

const MODULE_ID = "calendar";
const API_BASE_URL = "http://127.0.0.1:8001";

// Local state for optimistic UI
let localEvents = [];

function isCalendarPanelVisible() {
  const m = getDockModuleState(MODULE_ID);
  return !!(m?.isOpen && !m?.minimized);
}

// ============================================================================
// API Fetch Engine
// ============================================================================

async function apiFetchCalendar(method, endpoint, body = null) {
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

  if (response.status === 401) {
    // Try silent login refresh
    if (window.attemptSilentLogin) {
      await window.attemptSilentLogin();
      const newToken = localStorage.getItem('auth_token');
      options.headers.Authorization = `Bearer ${newToken}`;
      return await fetch(`${API_BASE_URL}/api/calendar${endpoint}`, options);
    }
    throw new Error('Unauthorized: Please login again');
  }

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// ============================================================================
// Calendar Events
// ============================================================================

async function loadCalendarEvents() {
  try {
    const today = new Date();
    const nextWeek = new Date(today);
    nextWeek.setDate(today.getDate() + 7);

    const startDate = today.toISOString().split('T')[0];
    const endDate = nextWeek.toISOString().split('T')[0];

    const data = await apiFetchCalendar('GET', `/events?start_date=${startDate}&end_date=${endDate}`);
    localEvents = data.events || [];
    renderAgendaView(localEvents);
    return localEvents;
  } catch (error) {
    console.error('Failed to load calendar events:', error);
    showToast('Fehler beim Laden der Termine', 'error');
    return [];
  }
}

function formatTime(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleTimeString('de-DE', {
    hour: '2-digit',
    minute: '2-digit'
  });
}

function formatDate(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('de-DE', {
    weekday: 'long',
    day: 'numeric',
    month: 'long'
  });
}

function renderAgendaView(events) {
  const container = document.getElementById('calendar-agenda');
  if (!container) return;

  container.innerHTML = '';

  if (!events || events.length === 0) {
    container.innerHTML = '<div class="calendar-empty">Keine Termine in den nächsten 7 Tagen</div>';
    return;
  }

  // Gruppiere Events nach Datum
  const grouped = {};
  events.forEach(event => {
    const date = formatDate(event.start);
    if (!grouped[date]) grouped[date] = [];
    grouped[date].push(event);
  });

  // Sortiere Datums-Gruppen
  const sortedDates = Object.keys(grouped).sort((a, b) => {
    const dateA = new Date(grouped[a][0].start);
    const dateB = new Date(grouped[b][0].start);
    return dateA - dateB;
  });

  // Render
  sortedDates.forEach(date => {
    const dateHeader = document.createElement('div');
    dateHeader.className = 'calendar-date-header';
    dateHeader.textContent = date;
    container.appendChild(dateHeader);

    const dayEvents = grouped[date];
    dayEvents.forEach(event => {
      const card = document.createElement('div');
      card.className = 'calendar-event-card';
      card.dataset.eventId = event.id;

      card.innerHTML = `
        <div class="event-title">${event.summary || 'Ohne Titel'}</div>
        <div class="event-time">${formatTime(event.start)} - ${formatTime(event.end)}</div>
        ${event.location ? `<div class="event-location">📍 ${event.location}</div>` : ''}
        <button class="event-delete-btn" data-id="${event.id}" title="Termin löschen">×</button>
      `;

      container.appendChild(card);
    });
  });

  // Event Listeners für Delete-Buttons
  container.querySelectorAll('.event-delete-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const eventId = btn.dataset.id;
      deleteCalendarEvent(eventId);
    });
  });
}

// ============================================================================
// Create Flow
// ============================================================================

async function createCalendarEvent(eventData) {
  const tempId = 'temp-' + Date.now();
  const tempEvent = {
    id: tempId,
    summary: eventData.summary,
    start: eventData.start_time,
    end: eventData.end_time,
    location: eventData.location || null,
    description: eventData.description || null,
    color: '#4285f4',
    source: 'local'
  };

  try {
    // Optimistic UI
    localEvents.push(tempEvent);
    renderAgendaView(localEvents);

    // API Call
    const result = await apiFetchCalendar('POST', '/events', eventData);

    // Replace temp with real
    const index = localEvents.findIndex(e => e.id === tempId);
    if (index !== -1) {
      localEvents[index] = result;
      renderAgendaView(localEvents);
    }

    showToast('Termin erstellt', 'success');
    return result;
  } catch (error) {
    // Rollback
    localEvents = localEvents.filter(e => e.id !== tempId);
    renderAgendaView(localEvents);
    console.error('Failed to create calendar event:', error);
    showToast('Fehler beim Erstellen des Termins', 'error');
    throw error;
  }
}

// ============================================================================
// Delete Flow
// ============================================================================

async function deleteCalendarEvent(eventId) {
  if (!confirm('Termin wirklich löschen?')) return;

  const event = localEvents.find(e => e.id === eventId);
  if (!event) return;

  try {
    // Optimistic UI
    localEvents = localEvents.filter(e => e.id !== eventId);
    renderAgendaView(localEvents);

    // API Call
    await apiFetchCalendar('DELETE', `/events/${eventId}`);

    showToast('Termin gelöscht', 'success');
  } catch (error) {
    // Rollback
    localEvents.push(event);
    renderAgendaView(localEvents);
    console.error('Failed to delete calendar event:', error);
    showToast('Fehler beim Löschen des Termins', 'error');
    throw error;
  }
}

// ============================================================================
// Toast Helper
// ============================================================================

function showToast(message, type = 'info') {
  // Use existing toast system if available
  if (window.showToast) {
    window.showToast(message, type);
    return;
  }

  // Fallback: Simple toast
  const toast = document.createElement('div');
  toast.className = `calendar-toast calendar-toast--${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 24px;
    background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
    color: white;
    border-radius: 4px;
    z-index: 10000;
    animation: slideIn 0.3s ease-out;
  `;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease-out';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ============================================================================
// Create Event Form
// ============================================================================

function showCreateEventForm() {
  const container = document.getElementById('calendar-agenda');
  if (!container) return;

  // Check if form already exists
  if (document.getElementById('create-event-form')) return;

  const form = document.createElement('div');
  form.id = 'create-event-form';
  form.className = 'calendar-create-form';
  form.innerHTML = `
    <div class="form-header">
      <h3>Neuer Termin</h3>
      <button class="form-close-btn">×</button>
    </div>
    <form id="event-form">
      <div class="form-group">
        <label for="event-summary">Titel</label>
        <input type="text" id="event-summary" required placeholder="Termin-Titel">
      </div>
      <div class="form-group">
        <label for="event-start">Startzeit</label>
        <input type="datetime-local" id="event-start" required>
      </div>
      <div class="form-group">
        <label for="event-end">Endzeit</label>
        <input type="datetime-local" id="event-end" required>
      </div>
      <div class="form-group">
        <label for="event-location">Ort (optional)</label>
        <input type="text" id="event-location" placeholder="Ort">
      </div>
      <div class="form-group">
        <label for="event-description">Beschreibung (optional)</label>
        <textarea id="event-description" rows="3" placeholder="Beschreibung"></textarea>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn-primary">Termin erstellen</button>
        <button type="button" class="btn-secondary cancel-btn">Abbrechen</button>
      </div>
    </form>
  `;

  container.appendChild(form);

  // Set default start time to now
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  document.getElementById('event-start').value = now.toISOString().slice(0, 16);

  // Set default end time to 1 hour from now
  const endTime = new Date(now.getTime() + 60 * 60 * 1000);
  document.getElementById('event-end').value = endTime.toISOString().slice(0, 16);

  // Event listeners
  form.querySelector('.form-close-btn').addEventListener('click', () => {
    form.remove();
  });

  form.querySelector('.cancel-btn').addEventListener('click', () => {
    form.remove();
  });

  document.getElementById('event-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const summary = document.getElementById('event-summary').value;
    const startTime = document.getElementById('event-start').value;
    const endTime = document.getElementById('event-end').value;
    const location = document.getElementById('event-location').value;
    const description = document.getElementById('event-description').value;

    if (!summary || !startTime || !endTime) {
      showToast('Bitte alle Pflichtfelder ausfüllen', 'error');
      return;
    }

    const eventData = {
      summary,
      start_time: new Date(startTime).toISOString(),
      end_time: new Date(endTime).toISOString(),
      location: location || null,
      description: description || null
    };

    try {
      await createCalendarEvent(eventData);
      form.remove();
    } catch (error) {
      // Error already handled in createCalendarEvent
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const calendarView = document.getElementById("calendar-view");
  const calendarHost = document.getElementById("calendar-modal");
  const navBtn = document.getElementById("sidebar-nav-calendar");
  const closeBtn = document.getElementById("close-calendar-btn");
  const minimizeBtn = document.getElementById("calendar-minimize-btn");
  const resetBtn = document.getElementById("calendar-reset-btn");
  const header = document.getElementById("calendar-header");
  const createEventBtn = document.getElementById("create-event-btn");

  let prevVisible = false;

  function syncNavActive() {
    if (!navBtn) return;
    const visible = isCalendarPanelVisible();
    navBtn.setAttribute("aria-pressed", visible ? "true" : "false");
    navBtn.classList.toggle("sidebar-nav-item--active", visible);
  }

  function syncFromDockState() {
    const visible = isCalendarPanelVisible();
    if (calendarView) {
      calendarView.style.display = visible ? "flex" : "none";
    }
    if (visible && !prevVisible && calendarHost) {
      try {
        bringToFront(MODULE_ID);
        // Load events when modal opens
        loadCalendarEvents();
      } catch {
        /* ignore */
      }
    }
    prevVisible = visible;
    syncNavActive();
  }

  subscribeWindowState(() => syncFromDockState());
  syncFromDockState();

  minimizeBtn?.addEventListener("click", () => {
    dockMinimize(MODULE_ID, true);
  });

  closeBtn?.addEventListener("click", () => {
    dockClose(MODULE_ID);
  });

  // Create Event Button Handler
  createEventBtn?.addEventListener("click", () => {
    showCreateEventForm();
  });

  if (resetBtn && calendarHost) {
    resetBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      calendarHost.style.left = "0px";
      calendarHost.style.top = "0px";
      calendarHost.style.width = "";
      calendarHost.style.height = "";
    });
  }

  let isDragging = false;
  let offsetX = 0;
  let offsetY = 0;

  if (header && calendarHost) {
    header.addEventListener("mousedown", (e) => {
      if (e.target.closest("button")) return;
      bringToFront(MODULE_ID);
      isDragging = true;
      offsetX = e.clientX - calendarHost.offsetLeft;
      offsetY = e.clientY - calendarHost.offsetTop;
      e.preventDefault();
    });
  }

  document.addEventListener("mousemove", (e) => {
    if (!isDragging || !calendarHost) return;
    let newX = e.clientX - offsetX;
    let newY = e.clientY - offsetY;
    const maxX = window.innerWidth - calendarHost.offsetWidth;
    const maxY = window.innerHeight - calendarHost.offsetHeight;
    newX = Math.max(0, Math.min(newX, maxX));
    newY = Math.max(0, Math.min(newY, maxY));
    calendarHost.style.left = `${newX}px`;
    calendarHost.style.top = `${newY}px`;
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
  });
});
