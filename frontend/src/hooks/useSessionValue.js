import { useCallback, useState } from 'react';

function readValue(key, initial) {
  try { const saved = sessionStorage.getItem(key); return saved === null ? initial : JSON.parse(saved); }
  catch { return initial; }
}

export function useSessionValue(key, initial) {
  const [entry, setEntry] = useState(() => ({ key, value: readValue(key, initial) }));
  const value = entry.key === key ? entry.value : readValue(key, initial);
  if (entry.key !== key) setEntry({ key, value });
  const update = useCallback(next => setEntry(previous => {
    const current = previous.key === key ? previous.value : readValue(key, initial);
    const result = typeof next === 'function' ? next(current) : next;
    try { sessionStorage.setItem(key, JSON.stringify(result)); }
    catch { /* Keep the UI usable when browser storage is unavailable or full. */ }
    return { key, value: result };
  }), [key]);
  return [value, update];
}
