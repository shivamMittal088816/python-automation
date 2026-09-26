export const normalizeColumnName = value => String(value).toLowerCase().replace(/[^a-z0-9]/g, '');

export function suggestedColumn(columns, suggestion, matches) {
  if (columns.includes(suggestion)) return suggestion;
  return columns.find(column => matches(normalizeColumnName(column)));
}
