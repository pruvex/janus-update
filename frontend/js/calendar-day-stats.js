/**
 * Gemeinsame Kennzahlen „Heute“ — gleiche Formeln wie Kalender-Rechtsrail (`updatePlanningSidebar`).
 * Auslastung = gebuchte Minuten heute / (8 h), gedeckelt bei 100 %.
 */

/** @param {{ title?: string }} ev */
export function eventTone(ev) {
  const title = String(ev.title || "").toLowerCase();
  if (title.includes("focus") || title.includes("fokus")) return "focus";
  if (title.includes("projekt") || title.includes("project")) return "project";
  if (title.includes("call") || title.includes("zoom") || title.includes("meeting")) return "meeting";
  if (title.includes("sport") || title.includes("pause") || title.includes("essen")) return "personal";
  return "default";
}

/** @param {{ start?: unknown, end?: unknown }} ev */
export function eventDurationMinutes(ev) {
  const s = new Date(String(ev.start));
  const e = new Date(String(ev.end));
  if (Number.isNaN(s.getTime()) || Number.isNaN(e.getTime())) return 0;
  return Math.max(0, Math.round((e.getTime() - s.getTime()) / 60000));
}

export function formatHourAmount(minutes) {
  if (minutes <= 0) return "0h";
  const hours = minutes / 60;
  return hours >= 1 ? `${hours.toLocaleString("de-DE", { maximumFractionDigits: 1 })}h` : `${minutes}m`;
}

/** @param {Date | string | number} midnightSeed */
function columnDayBounds(midnightSeed) {
  const d = midnightSeed instanceof Date ? midnightSeed : new Date(midnightSeed);
  const start = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const endExclusive = new Date(start);
  endExclusive.setDate(endExclusive.getDate() + 1);
  return { start, endExclusive };
}

/**
 * Alle Termine, die den lokalen Kalendertag `day` überlappen (wie `eventsForDay` im Kalender-Modal).
 * @param {Array<{ start?: unknown, end?: unknown }>} events
 * @param {Date} day
 */
export function eventsForLocalCalendarDay(events, day) {
  const bounds = columnDayBounds(day);
  return events.filter((ev) => {
    const s = new Date(String(ev.start));
    const e = new Date(String(ev.end));
    return (
      !Number.isNaN(s.getTime()) && !Number.isNaN(e.getTime()) && e > bounds.start && s < bounds.endExclusive
    );
  });
}

/**
 * @param {Array<{ start?: unknown, end?: unknown, title?: string }>} events
 * @param {Date} [referenceDay]
 * @returns {{
 *   todayEvents: typeof events,
 *   eventCount: number,
 *   focusMinutes: number,
 *   busyMinutes: number,
 *   loadPercent: number,
 * }}
 */
export function computePlanningStatsForDay(events, referenceDay = new Date()) {
  const todayEvents = eventsForLocalCalendarDay(events, referenceDay).sort(
    (a, b) => new Date(String(a.start)) - new Date(String(b.start))
  );
  const focusMinutes = todayEvents
    .filter((ev) => eventTone(ev) === "focus")
    .reduce((sum, ev) => sum + eventDurationMinutes(ev), 0);
  const busyMinutes = todayEvents.reduce((sum, ev) => sum + eventDurationMinutes(ev), 0);
  const loadPercent = Math.min(100, Math.round((busyMinutes / (8 * 60)) * 100));
  return {
    todayEvents,
    eventCount: todayEvents.length,
    focusMinutes,
    busyMinutes,
    loadPercent,
  };
}
