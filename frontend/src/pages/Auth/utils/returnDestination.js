export function returnDestination(search) {
  const candidate = new URLSearchParams(search).get('next') || '/admission_file_page';
  let target;
  try { target = new URL(candidate, window.location.origin); }
  catch { return '/admission_file_page'; }
  return target.origin === window.location.origin && !['/login', '/register'].includes(target.pathname)
    ? target.pathname + target.search + target.hash : '/admission_file_page';
}
