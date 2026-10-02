export function invitationToken(value) {
  const text = value.trim();
  if (/^[A-Za-z0-9_-]{20,64}$/.test(text)) return text;
  try {
    const url = new URL(text, window.location.origin);
    if (!['http:', 'https:'].includes(url.protocol)) return '';
    const shortLink = url.pathname.match(/^\/i\/(?:b\/)?([A-Za-z0-9_-]{20,64})\/?$/);
    if (shortLink) return shortLink[1];
    const legacyPaths = ['/admission_file_page', '/email_mapping_page', '/full_name_class_mapping_page', '/bulk-reg'];
    const token = url.searchParams.get('invite') || '';
    if (legacyPaths.includes(url.pathname) && /^[A-Za-z0-9_-]{20,64}$/.test(token)) return token;
  } catch { /* Invalid links are handled by the inline validation message. */ }
  return '';
}
