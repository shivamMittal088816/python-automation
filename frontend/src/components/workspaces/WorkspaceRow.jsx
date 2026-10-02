import { Icon } from '../common/Presentation';

export function WorkspaceRow({ item, current, switching, onSelect, onRename }) {
    const name = item.name, access = item.role === 'owner' ? 'Owner' : item.role === 'viewer' ? 'Viewer' : 'Editor';
    return <div className="workspace-selector-row-wrap"><button key={item.id} type="button" data-workspace-id={item.id} onClick={() => onSelect(item)} disabled={switching || item.status !== 'active'} aria-current={current ? 'true' : undefined} className={`workspace-selector-row${current ? ' is-current' : ''}`}>
    <span className={`workspace-selector-row-icon${access !== 'Owner' ? ' is-shared' : ''}`}><Icon name={access === 'Owner' ? 'grid' : 'link'} className="size-4" /></span>
    <div className="workspace-selector-row-copy"><strong>{name}</strong><span>{item.status !== 'active' ? `Access ${item.status}` : access === 'Owner' ? 'Your personal space' : item.owner_email || 'Shared with you'}</span></div>
    <span className={`workspace-selector-role role-${access.toLowerCase()}`}>{access}</span>
    <span className="workspace-selector-selection">{current && <Icon name="check" className="size-3" />}</span>
  </button>{item.owned && item.status === 'active' && <button type="button" className="workspace-selector-rename" aria-label={`Rename ${item.name}`} title="Rename workspace" disabled={switching} onClick={() => onRename(item)}><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="m14 5 5 5M4 20l5-1L20 8a2 2 0 0 0-5-5L4 14z" /></svg></button>}</div>;
  }
