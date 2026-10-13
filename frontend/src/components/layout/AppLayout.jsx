import { NavLink, Outlet, useLocation, useNavigate } from 'react-router';
import { useEffect, useRef, useState } from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { Loading } from '../common/Controls';
import { OperationNotice } from '../common/OperationNotice';
import { Icon } from '../common/Presentation';
import { SchoolIdentity } from '../common/SchoolIdentity';
import { SidebarDownloadButton } from './SidebarDownloadButton';

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const menuButton = useRef(null);
  const closeSidebar = () => {
    setSidebarOpen(false);
    menuButton.current?.focus();
  };
  useEffect(() => {
    if (!sidebarOpen) return;
    const onKeyDown = event => {
      if (event.key === 'Escape') {
        setSidebarOpen(false);
        menuButton.current?.focus();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [sidebarOpen]);
  const { workspace, busy, notice } = useWorkspace(), location = useLocation();
  const school = workspace.files.dump?.school_index, navigate = useNavigate();
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
  const link = (path, label) => <NavLink key={path} to={`${path}${school ? `?school=${encodeURIComponent(school)}` : ''}`} className={({ isActive }) => `flex items-center gap-2 rounded-lg px-2.5 py-2 text-xs transition-colors ${isActive ? 'bg-blue-50 font-semibold text-blue-800 ring-1 ring-inset ring-blue-100' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}`}><Icon name={path.includes('email') ? 'mail' : path.includes('mapping') ? 'grid' : 'file'} className="size-4" />{label}</NavLink>;
  const group = (title, pages) => <details key={`${title}-${location.pathname}`} open={pages.some(([path]) => path === location.pathname)} className="mb-1"><summary className="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-slate-500 hover:bg-slate-50">{title}</summary><div className="ml-2 space-y-0.5 border-l border-slate-200 py-1 pl-1.5">{pages.map(([path, title]) => link(path, title))}</div></details>;
  return <div className="mapping-app min-h-screen bg-slate-50 text-slate-900">
    <header className="sticky top-0 z-40 flex h-12 items-center border-b border-slate-300 bg-white shadow-sm px-4 sm:px-5 lg:px-6">
      <button ref={menuButton} type="button" aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'} aria-expanded={sidebarOpen} aria-controls="mapping-sidebar" onClick={() => setSidebarOpen(open => !open)} className="flex size-9 items-center justify-center rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-100">
        <Icon name="menu" />
      </button>
    </header>
    {sidebarOpen && <button type="button" aria-label="Dismiss sidebar" onClick={closeSidebar} className="fixed inset-x-0 bottom-0 top-12 z-20 bg-slate-900/30 md:hidden" />}
    <aside id="mapping-sidebar" hidden={!sidebarOpen} className="fixed bottom-0 left-0 top-12 z-30 w-56 max-w-[calc(100vw-3rem)] overflow-y-auto border-r border-slate-300 bg-white p-2.5 shadow-[4px_0_18px_-8px_#33415540]"><div className="mb-3 flex items-center gap-2 border-b border-slate-200 px-2 pb-3"><span className="rounded-lg bg-blue-700 p-2 text-white"><Icon name="grid" className="size-4" /></span><div><h1 className="text-sm font-bold tracking-tight">Student Mapping</h1><p className="text-xs text-slate-500">Operations workspace</p></div></div><nav aria-label="Main navigation" onClick={event => { if (event.target.closest('a')) closeSidebar(); }}><p className="mb-1 px-2.5 text-[10px] font-semibold uppercase tracking-widest text-slate-400">Mapping</p>{group('Admission No. Mapping', [['/admission_file_page', 'Admission mapping'], ['/admission_preview_page', 'Mapping preview']])}{group('Email mapping', [['/email_mapping_page', 'Email mapping'], ['/email_preview_page', 'Mapping preview'], ['/email_dump_page', 'E-mail dump file']])}{group('Full name + class Number', [['/full_name_class_mapping_page', 'Concatenation mapping'], ['/full_name_class_preview_page', 'Mapping preview']])}<p className="mb-1 mt-3 px-2.5 text-[10px] font-semibold uppercase tracking-widest text-slate-400">Data files</p>{link('/school_file_page', 'School file')}{link('/dump_file_page', 'Dump file')}<p className="mb-1 mt-3 px-2.5 text-[10px] font-semibold uppercase tracking-widest text-slate-400">Exports</p><SidebarDownloadButton /><p className="mb-1 mt-3 px-2.5 text-[10px] font-semibold uppercase tracking-widest text-slate-400">Services</p><NavLink to="/bulk-reg" className="block rounded-lg px-2.5 py-2 text-xs text-slate-600 hover:bg-slate-50">Bulk registration</NavLink><NavLink to="/rollback" className="block rounded-lg px-2.5 py-2 text-xs text-slate-600 hover:bg-slate-50">Rollback</NavLink></nav><div className="mt-3 hidden border-t border-slate-200 px-2.5 pt-3 md:block"><p className="text-xs font-medium text-slate-600">Your workspace</p><p className="mt-1 text-xs leading-4 text-slate-400">Files and selections stay available as you move between pages.</p></div></aside><main className={`min-w-0 px-3 py-3 sm:px-4 lg:px-5 ${sidebarOpen ? 'md:ml-56' : ''}`}><div className="w-full"><SchoolIdentity /><OperationNotice notice={notice} />{busy && <Loading>{busy}</Loading>}<Outlet /></div></main></div>;
}
