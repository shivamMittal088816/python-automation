import { useEffect, useRef, useState } from 'react';
import { NavLink, Outlet } from 'react-router';
import { Icon } from '../common/Presentation';

const navigation = [
  ['/admission_file_page', 'Admission mapping'],
  ['/bulk-reg', 'Bulk registration'],
  ['/rollback', 'Rollback'],
];

export function ServiceLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const menuButton = useRef(null);

  function closeSidebar() {
    setSidebarOpen(false);
    menuButton.current?.focus();
  }

  useEffect(() => {
    if (!sidebarOpen) return undefined;
    const onKeyDown = event => {
      if (event.key === 'Escape') closeSidebar();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [sidebarOpen]);

  return <div className="min-h-screen bg-slate-50 text-slate-900">
    <header className="sticky top-0 z-40 flex h-12 items-center border-b border-slate-300 bg-white px-4 shadow-sm sm:px-5 lg:px-6">
      <button ref={menuButton} type="button" aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'} aria-expanded={sidebarOpen} aria-controls="service-sidebar" onClick={() => setSidebarOpen(open => !open)} className="flex size-9 items-center justify-center rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-100">
        <Icon name="menu" />
      </button>
    </header>
    {sidebarOpen && <button type="button" aria-label="Dismiss sidebar" onClick={closeSidebar} className="fixed inset-x-0 bottom-0 top-12 z-20 bg-slate-900/30" />}
    <aside id="service-sidebar" hidden={!sidebarOpen} className="fixed bottom-0 left-0 top-12 z-30 w-56 max-w-[calc(100vw-3rem)] overflow-y-auto border-r border-slate-300 bg-white p-2.5 shadow-[4px_0_18px_-8px_#33415540]">
      <div className="mb-3 flex items-center gap-2 border-b border-slate-200 px-2 pb-3">
        <span className="rounded-lg bg-blue-700 p-2 text-white"><Icon name="grid" className="size-4" /></span>
        <div><h1 className="text-sm font-bold tracking-tight">Student Mapping</h1><p className="text-xs text-slate-500">Operations workspace</p></div>
      </div>
      <nav aria-label="Main navigation" className="space-y-0.5" onClick={event => { if (event.target.closest('a')) closeSidebar(); }}>
        {navigation.map(([path, label]) => <NavLink key={path} to={path} end={path === '/bulk-reg'} className={({ isActive }) => `flex items-center gap-2 rounded-lg px-2.5 py-2 text-xs transition-colors ${isActive ? 'bg-blue-50 font-semibold text-blue-800 ring-1 ring-inset ring-blue-100' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}`}><Icon name={path === '/admission_file_page' ? 'grid' : 'file'} className="size-4" />{label}</NavLink>)}
      </nav>
    </aside>
    <main className={sidebarOpen ? 'md:ml-56' : ''}><Outlet /></main>
  </div>;
}
