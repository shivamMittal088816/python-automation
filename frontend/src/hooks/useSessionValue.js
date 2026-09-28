import { useCallback, useEffect, useState } from "react";

function readValue(key, initial) {
  try {
    const saved = sessionStorage.getItem(key);
    return saved === null ? initial : JSON.parse(saved);
  } catch {
    return initial;
  }
}

export function useSessionValue(key, initial) {
  const [entry, setEntry] = useState(() => ({
    key,
    value: readValue(key, initial),
  }));
  const value = entry.key === key ? entry.value : initial;
  useEffect(() => {
    setEntry({ key, value: readValue(key, initial) });
  }, [key]);
  const update = useCallback(
    (next) =>
      setEntry((previous) => {
        const current =
          previous.key === key ? previous.value : readValue(key, initial);
        const result = typeof next === "function" ? next(current) : next;
        try {
          sessionStorage.setItem(key, JSON.stringify(result));
        } catch {
          /* Keep the UI usable when browser storage is unavailable or full. */
        }
        return { key, value: result };
      }),
    [key],
  );
  return [value, update];
}

// This hook stores a UI value in React state and in this browser tab's sessionStorage.
// It restores the saved JSON value, or uses the initial value if storage is missing or unreadable.
// When the storage key changes, it loads the value belonging to the new key.
// Its update function accepts either a new value or a function that changes the current value.
// Updates still work on screen if the browser cannot save them to sessionStorage.
// It returns the value and updater so selections can survive reloads within the same tab.
// Used by FileViewer.jsx and ResultPreview.jsx for filters, worksheet choices, and pagination.
// EmailForm.jsx and FullNameClassMappingPage.jsx use it for mapping drafts and source selections.
