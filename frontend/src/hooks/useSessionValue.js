import { useState } from 'react';

export function useSessionValue(key, initial) {
  const [value, setValue] = useState(() => {
    try { const saved = sessionStorage.getItem(key); return saved === null ? initial : JSON.parse(saved); }
    catch { return initial; }
  });
  const update = next => setValue(previous => {
    const result = typeof next === 'function' ? next(previous) : next;
    try { sessionStorage.setItem(key, JSON.stringify(result)); }
    catch { /* Keep the UI usable when browser storage is unavailable or full. */ }
    return result;
  });
  return [value, update];
}
