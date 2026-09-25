import { useEffect, useState } from 'react';

export function useRequest(load, dependencies) {
  const [state, setState] = useState({ data: null, loading: true, error: '' });
  useEffect(() => {
    // Let superseded reads finish normally so browsers do not report an
    // intentional AbortController cancellation as a failed network request.
    // The active flag still prevents an older response from replacing newer
    // component state.
    let active = true;
    setState({ data: null, loading: true, error: '' });
    load(undefined).then(data => {
      if (active) setState({ data, loading: false, error: '' });
    }).catch(error => {
      if (active) setState({ data: null, loading: false, error: error.message });
    });
    return () => { active = false; };
    // Callers supply all inputs that determine their HTTP request.
  }, dependencies);
  return state;
}
