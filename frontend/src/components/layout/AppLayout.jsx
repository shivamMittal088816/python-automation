import { NavLink, Outlet, useLocation, useNavigate } from 'react-router';
import { useEffect } from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { Alert, Loading } from '../common/Controls';
import { Icon } from '../common/Presentation';
import { SchoolIdentity } from '../common/SchoolIdentity';
import { SidebarDownloadButton } from './SidebarDownloadButton';

export function AppLayout() {
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
  const link = (path, label) => <NavLink key={path} to={`${path}${school ? `?school=${encodeURIComponent(school)}` : ''}`} className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${isActive ? 'bg-blue-50 font-semibold text-blue-800 ring-1 ring-inset ring-blue-100' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}`}><Icon name={path.includes('email') ? 'mail' : path.includes('mapping') ? 'grid' : 'file'} className="size-4" />{label}</NavLink>;
  const group = (title, pages) => <details key={`${title}-${location.pathname}`} open={pages.some(([path]) => path === location.pathname)} className="mb-2"><summary className="rounded-lg px-3 py-2.5 text-xs font-semibold text-slate-500 hover:bg-slate-50">{title}</summary><div className="ml-3 space-y-1 border-l border-slate-200 py-1 pl-2">{pages.map(([path, title]) => link(path, title))}</div></details>;
  return <div className="min-h-screen bg-slate-50 text-slate-900 md:flex"><aside className="border-b border-slate-200 bg-white p-4 md:fixed md:inset-y-0 md:w-64 md:overflow-y-auto md:border-r"><div className="mb-7 flex items-center gap-3 px-2"><span className="rounded-xl bg-blue-700 p-2.5 text-white"><Icon name="grid" /></span><div><h1 className="text-sm font-bold tracking-tight">Student Mapping</h1><p className="mt-0.5 text-xs text-slate-500">Operations workspace</p></div></div><nav aria-label="Main navigation"><p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-400">Mapping</p>{group('Admission No. Mapping', [['/admission_file_page', 'Admission mapping'], ['/admission_preview_page', 'Mapping preview']])}{group('Email mapping', [['/email_mapping_page', 'Email mapping'], ['/email_preview_page', 'Mapping preview'], ['/email_dump_page', 'E-mail dump file']])}{group('Full name + class Number', [['/full_name_class_mapping_page', 'Concatenation mapping'], ['/full_name_class_preview_page', 'Mapping preview']])}<p className="mb-2 mt-7 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-400">Data files</p>{link('/school_file_page', 'School file')}{link('/dump_file_page', 'Dump file')}<p className="mb-2 mt-7 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-400">Exports</p><SidebarDownloadButton /></nav><div className="mt-8 hidden border-t border-slate-100 px-3 pt-5 md:block"><p className="text-xs font-medium text-slate-600">Your workspace</p><p className="mt-1 text-xs leading-5 text-slate-400">Files and selections stay available as you move between pages.</p></div></aside><main className="min-w-0 flex-1 px-4 py-6 sm:px-6 md:ml-64 lg:px-8 lg:py-8"><div className="mx-auto max-w-7xl"><SchoolIdentity />{notice && <Alert type={notice.type}>{notice.text}</Alert>}{busy && <Loading>{busy}</Loading>}<Outlet /></div></main></div>;
}
