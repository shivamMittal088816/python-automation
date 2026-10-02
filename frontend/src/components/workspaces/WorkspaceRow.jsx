import { Icon } from '../common/Presentation';

export function WorkspaceRow({ item, current, switching, onSelect }) {
    const name = item.name, access = item.role === 'owner' ? 'Owner' : item.role === 'viewer' ? 'Viewer' : 'Editor';
    return <button key={item.id} type="button" data-workspace-id={item.id} onClick={() => onSelect(item)} disabled={switching || item.status !== 'active'} aria-current={current ? 'true' : undefined} className={`workspace-selector-row${current ? ' is-current' : ''}`}>
    <span className={`workspace-selector-row-icon${access !== 'Owner' ? ' is-shared' : ''}`}><Icon name={access === 'Owner' ? 'grid' : 'link'} className="size-4" /></span>
    <div className="workspace-selector-row-copy"><strong>{name}</strong><span>{item.status !== 'active' ? `Access ${item.status}` : access === 'Owner' ? 'Your personal space' : item.owner_email || 'Shared with you'}</span></div>
    <span className={`workspace-selector-role role-${access.toLowerCase()}`}>{access}</span>
    <span className="workspace-selector-selection">{current && <Icon name="check" className="size-3" />}</span>
  </button>;
  }
