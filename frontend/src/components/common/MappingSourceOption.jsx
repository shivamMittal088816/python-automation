export function MappingSourceOption({ name, value, label, selected, disabled, detail, onSelect }) {
  return <label className={`flex items-start gap-2 rounded-lg border p-3 text-sm ${selected ? 'border-blue-400 bg-blue-50 text-blue-900' : 'border-slate-200'}`}>
    <input
      type="radio"
      name={name}
      value={value}
      checked={selected}
      disabled={disabled}
      onChange={() => onSelect(value)}
    />
    <span>{label}{detail && <span className="mt-1 block text-xs text-slate-500">{detail}</span>}</span>
  </label>;
}
