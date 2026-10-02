import { useState } from 'react';
import { AccountMenu } from '../../components/auth/AccountMenu';
import { Link, useLocation, useNavigate } from 'react-router';
import { JoinWorkflowDialog } from '../../components/invitations/JoinWorkflowDialog';
import { InviteWorkflowDialog } from '../../components/invitations/InviteWorkflowDialog';
import { WorkspaceSelector } from '../../components/workspaces/WorkspaceSelector';
import { useBulkRegistration } from './useBulkRegistration';
import { SchoolVerification } from './components/SchoolVerification';
import { RegistrationFileInput } from './components/RegistrationFileInput';
import { RegistrationDefaults } from './components/RegistrationDefaults';
import { RegistrationActions } from './components/RegistrationActions';
import { RegistrationSanityCheck } from './components/RegistrationSanityCheck';
import { RegistrationPreviews } from './components/RegistrationPreviews';
import { ConfirmResetBulkRegistration } from './components/ConfirmResetBulkRegistration';
import './bulk-registration.css';

export function BulkRegistrationPage() {
  const workflow = useBulkRegistration();
  const { error, storageError, working, ready, busy, edit } = workflow;
  const location = useLocation();
  const navigate = useNavigate();
  const [joinOpen, setJoinOpen] = useState(() => new URLSearchParams(window.location.search).has('invite'));
  const [inviteOpen, setInviteOpen] = useState(false);
  const viewer = workflow.role === 'viewer';
  function closeJoin() {
    setJoinOpen(false);
    const params = new URLSearchParams(location.search);
    params.delete('invite');
    navigate({ pathname: location.pathname, search: params.toString() }, { replace: true });
  }

  return (
    <main className="bulk-page">
      {joinOpen && <JoinWorkflowDialog onClose={closeJoin} initialCode={new URLSearchParams(location.search).get('invite') || ''} />}
      {inviteOpen && <InviteWorkflowDialog workflow="bulk" onClose={() => setInviteOpen(false)} />}
      <div className="bulk-shell">
        <div className="mb-4 flex items-center justify-between">{ready || storageError ? <WorkspaceSelector role={workflow.role} workflow="bulk_registration" /> : <span className="text-sm text-slate-500" role="status">Opening workspace…</span>}<AccountMenu /></div>
        <header className="bulk-header">
          <div>
            <p className="bulk-eyebrow">FILE CONVERSION</p>
            <h1>Bulk registration</h1>
            <p className="bulk-subtitle">Your student data, ready for registration.</p>
          </div>
          <Link to="/admission_file_page" className="bulk-back">
            Back to mapping <span aria-hidden="true">&#8599;</span>
          </Link>
          <Link to="/bulk-reg/rules" className="bulk-help-link" aria-label="Open bulk-registration sanity rules">
            <span className="bulk-help-icon" aria-hidden="true">?</span> Sanity rules
          </Link>
        </header>
        <div className="bulk-collaboration">
          <button type="button" className="bulk-button bulk-secondary" aria-haspopup="dialog" onClick={() => setJoinOpen(true)}>Join with invitation code</button>
          {workflow.role === 'owner' && <button type="button" className="bulk-button bulk-secondary" aria-haspopup="dialog" onClick={() => setInviteOpen(true)}>Invite to workflow</button>}
        </div>
        {viewer && <p className="bulk-notice">Viewer access: you can view this shared workspace. Editing is disabled.</p>}
        {(error || storageError) && (
          <p role="alert" className="bulk-error bulk-top-error">{error || storageError}</p>
        )}
        <fieldset disabled={viewer} className="bulk-workspace-fields">
        <div className="bulk-grid">
          <div className="bulk-setup">
            <SchoolVerification
              schoolIndex={workflow.schoolIndex} school={workflow.school}
              schoolValid={workflow.schoolValid} busy={busy}
              verifySchool={workflow.verifySchool} edit={edit}
            />
            <RegistrationFileInput
              path={workflow.path} file={workflow.file} busy={busy}
              load={workflow.load} upload={workflow.upload}
              selectSheet={workflow.selectSheet} edit={edit} clearFile={workflow.clearWorkspace}
            />
          </div>
          <RegistrationDefaults />
        </div>
        {(working || (!ready && !storageError)) && (
          <p role="status" className="bulk-notice">Working...</p>
        )}
        <RegistrationSanityCheck source={workflow.source} busy={busy} result={workflow.sanity} onCheck={workflow.runSanityCheck} />
        <RegistrationActions
          sanity={workflow.sanity}
          schoolValid={workflow.schoolValid} source={workflow.source}
          busy={busy} output={workflow.output} outputVerified={workflow.outputVerified}
          convert={workflow.convert}
        />
        <RegistrationPreviews
          file={workflow.file} output={workflow.output} busy={busy}
          onOutputPage={workflow.showOutputPage}
          onInputPage={workflow.showInputPage}
          outputVerification={workflow.outputVerification}
          usernameChanges={workflow.usernameChanges}
          onVerifyOutput={workflow.verifyOutput}
        />
        <footer className="bulk-footer">
          <ConfirmResetBulkRegistration disabled={busy} onConfirm={() => workflow.clearWorkspace(true)} />
          <span>Shared across tabs on this browser</span>
          <span>File conversion only &middot; No registrations submitted</span>
        </footer>
        </fieldset>
      </div>
    </main>
  );
}
