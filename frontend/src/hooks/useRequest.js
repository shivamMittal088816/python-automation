import { useEffect, useState } from "react";

export function useRequest(load, dependencies) {
  const [state, setState] = useState({ data: null, loading: true, error: "" });
  useEffect(() => {
    // Let superseded reads finish normally so browsers do not report an
    // intentional AbortController cancellation as a failed network request.
    // The active flag still prevents an older response from replacing newer
    // component state.
    let active = true;
    setState(
      { data: null, 
        loading: true, 
        error: "" }
    );
    
    Promise.resolve()
      .then(() => load(undefined))
      .then((data) => {
        if (active) setState({ data, loading: false, error: "" });
      })
      .catch((error) => {
        if (active)
          setState({ data: null, loading: false, error: error.message });
      });
    return () => {
      active = false;
    };
    // Callers supply all inputs that determine their HTTP request.
  }, dependencies);
  return state;
}

// This hook loads data when the component first appears and when its dependencies change.
// Each request clears the previous data and error, then sets loading to true.
// It calls the supplied load function and stores its returned data when the request succeeds.
// If loading fails, it stores the error message and turns off the loading indicator.
// Old requests can finish, but their results are ignored after dependencies change or the component is removed.
// It returns data, loading, and error so the component can display the current request state.
// Used by FileViewer.jsx and ResultPreview.jsx to load file rows and mapping results.
// EmailMappingPage.jsx and FullNameClassMappingPage.jsx also use it to load mapping information.
