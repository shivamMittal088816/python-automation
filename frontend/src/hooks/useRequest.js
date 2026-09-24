import { useEffect, useState } from 'react';

export function useRequest(load, dependencies) {
  const [state, setState] = useState({ data: null, loading: true, error: '' });
  useEffect(() => {
    const controller = new AbortController();
    setState({ data: null, loading: true, error: '' });
    load(controller.signal).then(data => {
      if (!controller.signal.aborted) setState({ data, loading: false, error: '' });
    }).catch(error => {
      if (!controller.signal.aborted) setState({ data: null, loading: false, error: error.message });
    });
    return () => controller.abort();
    // Callers supply all inputs that determine their HTTP request.
  }, dependencies);
  return state;
}
