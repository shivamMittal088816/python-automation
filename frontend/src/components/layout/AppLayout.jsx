import { NavLink, Outlet, useLocation, useNavigate } from 'react-router';
import { useEffect, useRef, useState } from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { Alert, Loading } from '../common/Controls';
import { Icon } from '../common/Presentation';
import { SchoolIdentity } from '../common/SchoolIdentity';
import { SidebarDownloadButton } from './SidebarDownloadButton';
import { InviteWorkflowDialog } from '../invitations/InviteWorkflowDialog';
import { JoinWorkflowDialog } from '../invitations/JoinWorkflowDialog';
import { WorkspaceSelector } from '../workspaces/WorkspaceSelector';
import { AccountMenu } from '../auth/AccountMenu';
import './sidebar.css';

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [inviteWorkflow, setInviteWorkflow] = useState(null);
  const [joinOpen, setJoinOpen] = useState(() => new URLSearchParams(window.location.search).has('invite'));
  const menuButton = useRef(null);
  const closeSidebar = () => {
    setSidebarOpen(false);
    menuButton.current?.focus();
  };
  useEffect(() => {
    if (!sidebarOpen || inviteWorkflow || joinOpen) return;
    const onKeyDown = event => {
      if (event.key === 'Escape') {
        setSidebarOpen(false);
        menuButton.current?.focus();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [sidebarOpen, inviteWorkflow, joinOpen]);
  const { workspace, busy, notice } = useWorkspace(), location = useLocation();
  const school = workspace.files.dump?.school_index, navigate = useNavigate();
  const viewer = workspace.role === 'viewer';
  const closeJoin = () => {
    setJoinOpen(false);
    const params = new URLSearchParams(location.search);
    params.delete('invite');
    navigate({ pathname: location.pathname, search: params.toString() }, { replace: true });
  };
  useEffect(() => {
    // Let the root redirect finish before synchronizing the school query.
    if (location.pathname === '/') return;
    const params = new URLSearchParams(location.search);
    if (school) params.set('school', school); else params.delete('school');
    const search = params.toString();
    if (search !== location.search.replace(/^\?/, '')) {
      navigate({ pathname: location.pathname, search, hash: location.hash }, { replace: true });
    }
  }, [school, location.pathname, location.search, location.hash, navigate]);
  const link = (path, label) => <NavLink key={path} to={`${path}${school ? `?school=${encodeURIComponent(school)}` : ''}`} className={({ isActive }) => `sidebar-link${isActive ? ' is-active' : ''}`}><Icon name={path.includes('email') ? 'mail' : path.includes('mapping') ? 'grid' : 'file'} className="size-4" /><span>{label}</span></NavLink>;
  const group = (title, pages, icon) => <details key={`${title}-${location.pathname}`} open={pages.some(([path]) => path === location.pathname)} className="sidebar-group"><summary><Icon name={icon} className="size-4" /><span>{title}</span><svg className="sidebar-chevron" aria-hidden="true" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="m6 4 4 4-4 4" /></svg></summary><div className="sidebar-group-links">{pages.map(([path, title]) => link(path, title))}</div></details>;
  const inviteButton = () => <button type="button" aria-haspopup="dialog" onClick={() => setInviteWorkflow('mapping')} className="sidebar-invite"><span className="sidebar-invite-icon"><Icon name="mail" className="size-4" /></span><span><strong>Invite to workflow</strong><small>Share your workspace</small></span><span aria-hidden="true" className="sidebar-invite-arrow">&#8599;</span></button>;
  return <div className={`mapping-app min-h-screen bg-slate-50 text-slate-900${location.pathname === '/admission_file_page' ? ' mapping-home-page' : ''}`}>
    {inviteWorkflow && <InviteWorkflowDialog workflow={inviteWorkflow} onClose={() => setInviteWorkflow(null)} />}
    {joinOpen && <JoinWorkflowDialog onClose={closeJoin} initialCode={new URLSearchParams(location.search).get('invite') || ''} />}
    <header className="sticky top-0 z-40 flex h-14 items-center border-b border-slate-200 bg-white px-4 sm:px-5 lg:px-6">
      <button ref={menuButton} type="button" aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'} aria-expanded={sidebarOpen} aria-controls="mapping-sidebar" onClick={() => setSidebarOpen(open => !open)} className="flex size-9 items-center justify-center rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-100">
        <Icon name="menu" />
      </button>
      <div className="ml-3 min-w-0"><WorkspaceSelector role={workspace.role || 'owner'} /></div>
      <div className="ml-auto"><AccountMenu /></div>
    </header>
    {sidebarOpen && <button type="button" aria-label="Dismiss sidebar" onClick={closeSidebar} className="fixed inset-x-0 bottom-0 top-14 z-20 bg-slate-900/30 md:hidden" />}
    <aside id="mapping-sidebar" hidden={!sidebarOpen} className="workspace-sidebar fixed bottom-0 left-0 top-14 z-30 w-60 max-w-[calc(100vw-3rem)]">
      <div className="sidebar-brand"><span className="sidebar-brand-icon"><Icon name="grid" className="size-4" /></span><div><h1>Student Mapping</h1><p>Operations workspace</p></div><span className="sidebar-brand-dot" aria-hidden="true" /></div>
      <nav aria-label="Main navigation" onClick={event => { if (event.target.closest('a')) closeSidebar(); }}>
        <div className="sidebar-section"><p className="sidebar-section-label">Mapping</p>
          {group('Admission No. Mapping', [['/admission_file_page', 'Admission mapping'], ['/admission_preview_page', 'Mapping preview']], 'grid')}
          {group('Email mapping', [['/email_mapping_page', 'Email mapping'], ['/email_preview_page', 'Mapping preview'], ['/email_dump_page', 'E-mail dump file']], 'mail')}
          {group('Full name + class Number', [['/full_name_class_mapping_page', 'Concatenation mapping'], ['/full_name_class_preview_page', 'Mapping preview']], 'grid')}
        </div>
        <div className="sidebar-section"><p className="sidebar-section-label">Data files</p>{link('/school_file_page', 'School file')}{link('/dump_file_page', 'Dump file')}</div>
        <div className="sidebar-section"><p className="sidebar-section-label">Exports</p><SidebarDownloadButton /></div>
        <div className="sidebar-section"><p className="sidebar-section-label">Services</p><NavLink to="/bulk-reg" className="sidebar-link"><Icon name="file" className="size-4" /><span>Bulk registration</span><span aria-hidden="true" className="sidebar-service-arrow">&#8599;</span></NavLink></div>
        {(!workspace.role || workspace.role === 'owner') && inviteButton()}
        <button type="button" className="sidebar-join" aria-haspopup="dialog" onClick={() => setJoinOpen(true)}>
          <Icon name="link" className="size-4" /><span>Join with invitation code</span>
        </button>
      </nav>
      <div className="sidebar-footer"><span className="sidebar-footer-mark"><Icon name="file" className="size-3.5" /></span><div><p>Your workspace</p><span>Files and selections stay available as you move between pages.</span></div></div>
    </aside><main className={`min-w-0 px-4 py-4 sm:px-5 lg:px-6 lg:py-5 ${sidebarOpen ? 'md:ml-60' : ''}`}><div className="w-full"><SchoolIdentity />{viewer && <Alert type="info">Viewer access: you can view this shared workspace. Editing is disabled.</Alert>}{notice && <Alert type={notice.type}>{notice.text}</Alert>}{busy && <Loading>{busy}</Loading>}<fieldset disabled={viewer} className="min-w-0"><Outlet /></fieldset></div></main></div>;
}
