import { BrowserRouter, Navigate, Outlet, Route, Routes, useParams } from "react-router";
import { MappingRulesPage } from "./pages/MappingRules/MappingRulesPage";
import { WorkspaceProvider } from "./context/WorkspaceContext";
import { AppLayout } from "./components/layout/AppLayout";
import { AdmissionMappingPage } from "./pages/AdmissionMapping/AdmissionMappingPage";
import { AdmissionPreviewPage } from "./pages/AdmissionPreview/AdmissionPreviewPage";
import { SchoolFilePage } from "./pages/SchoolFile/SchoolFilePage";
import { DumpFilePage } from "./pages/DumpFile/DumpFilePage";
import { EmailMappingPage } from "./pages/EmailMapping/EmailMappingPage";
import { EmailDumpPage } from "./pages/EmailDump/EmailDumpPage";
import { EmailPreviewPage } from "./pages/EmailPreview/EmailPreviewPage";
import { FullNameClassMappingPage } from "./pages/FullNameClassMapping/FullNameClassMappingPage";
import { FullNameClassPreviewPage } from "./pages/FullNameClassPreview/FullNameClassPreviewPage";
import { BulkRegistrationPage } from "./pages/BulkRegistration/BulkRegistrationPage";
import { BulkRegistrationRulesPage } from "./pages/BulkRegistration/BulkRegistrationRulesPage";
import { ErrorBoundary } from "./components/common/ErrorBoundary";
import { AuthProvider } from './context/AuthContext';
import { RequireAuth } from './components/auth/RequireAuth';
import { AuthPage } from './pages/Auth/AuthPage';

function InvitationRedirect({ bulk = false }) {
  const { token } = useParams();
  const destination = bulk ? '/bulk-reg' : '/admission_file_page';
  return <Navigate replace to={`${destination}?${new URLSearchParams({ invite: token })}`} />;
}

export function App() {
  const legacy = new URLSearchParams(location.search);
  const initial =
    legacy.get("page") === "admission-preview"
      ? "/admission_preview_page"
      : "/admission_file_page";
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
        <Routes>
          <Route path="/login" element={<AuthPage key="login" />} />
          <Route path="/register" element={<AuthPage key="register" register />} />
          <Route element={<RequireAuth />}>
          <Route path="/i/:token" element={<InvitationRedirect />} />
          <Route path="/i/b/:token" element={<InvitationRedirect bulk />} />
          <Route path="/bulk-reg" element={<BulkRegistrationPage />} />
          <Route path="/bulk-reg/rules" element={<BulkRegistrationRulesPage />} />
          <Route
            element={
              <WorkspaceProvider>
                <Outlet />
              </WorkspaceProvider>
            }
          >
            <Route element={<AppLayout />}> 
              <Route
                path="/"
                element={
                  <Navigate replace to={`${initial}${location.search}`} />
                }
              />
              <Route
                path="/admission_file_page"
                element={<AdmissionMappingPage />}
              />
              <Route
                path="/admission_preview_page"
                element={<AdmissionPreviewPage />}
              />
              <Route path="/school_file_page" element={<SchoolFilePage />} />
              <Route path="/dump_file_page" element={<DumpFilePage />} />
              <Route
                path="/email_mapping_page"
                element={<EmailMappingPage />}
              />
              <Route
                path="/email_preview_page"
                element={<EmailPreviewPage />}
              />
              <Route path="/email_dump_page" element={<EmailDumpPage />} />
              <Route
                path="/full_name_class_mapping_page"
                element={<FullNameClassMappingPage />}
              />
              <Route
                path="/full_name_class_preview_page"
                element={<FullNameClassPreviewPage />}
              />
              <Route
                path="/mapping_rules_page"
                element={<MappingRulesPage />}
              />
              <Route
                path="*"
                element={<Navigate replace to="/admission_file_page" />}
              />
            </Route>
          </Route>
          </Route>
        </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
