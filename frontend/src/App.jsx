import { BrowserRouter, Navigate, Route, Routes } from 'react-router';
import { MappingRulesPage } from './pages/MappingRules/MappingRulesPage';
import { WorkspaceProvider } from './context/WorkspaceContext';
import { AppLayout } from './components/layout/AppLayout';
import { AdmissionMappingPage } from './pages/AdmissionMapping/AdmissionMappingPage';
import { AdmissionPreviewPage } from './pages/AdmissionPreview/AdmissionPreviewPage';
import { SchoolFilePage } from './pages/SchoolFile/SchoolFilePage';
import { DumpFilePage } from './pages/DumpFile/DumpFilePage';
import { EmailMappingPage } from './pages/EmailMapping/EmailMappingPage';
import { EmailDumpPage } from './pages/EmailDump/EmailDumpPage';
import { FullNameClassMappingPage } from './pages/FullNameClassMapping/FullNameClassMappingPage';
import { ErrorBoundary } from './components/common/ErrorBoundary';

export function App() {
  const legacy = new URLSearchParams(location.search);
  const initial = legacy.get('page') === 'admission-preview' ? '/admission_preview_page' : '/admission_file_page';
  return <ErrorBoundary><BrowserRouter><WorkspaceProvider><Routes><Route element={<AppLayout />}><Route path="/" element={<Navigate replace to={`${initial}${location.search}`} />} /><Route path="/admission_file_page" element={<AdmissionMappingPage />} /><Route path="/admission_preview_page" element={<AdmissionPreviewPage />} /><Route path="/school_file_page" element={<SchoolFilePage />} /><Route path="/dump_file_page" element={<DumpFilePage />} /><Route path="/email_mapping_page" element={<EmailMappingPage />} /><Route path="/email_dump_page" element={<EmailDumpPage />} /><Route path="/full_name_class_mapping_page" element={<FullNameClassMappingPage />} /><Route path="/mapping_rules_page" element={<MappingRulesPage />} /><Route path="*" element={<Navigate replace to="/admission_file_page" />} /></Route></Routes></WorkspaceProvider></BrowserRouter></ErrorBoundary>;
}
