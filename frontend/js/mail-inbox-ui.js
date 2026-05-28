export function filterMailThreads(threads, query) {
  const list = Array.isArray(threads) ? threads : [];
  const q = String(query || "")
    .trim()
    .toLowerCase();
  if (!q) return list;
  return list.filter((thread) => {
    const subject = String(thread?.subject || "").toLowerCase();
    const from = String(thread?.from_display || thread?.from || "").toLowerCase();
    const snippet = String(thread?.snippet || "").toLowerCase();
    return subject.includes(q) || from.includes(q) || snippet.includes(q);
  });
}
