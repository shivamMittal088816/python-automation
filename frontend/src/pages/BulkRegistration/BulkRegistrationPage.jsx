import { Link } from 'react-router';
import { useBulkRegistration } from './useBulkRegistration';
import { SchoolVerification } from './components/SchoolVerification';
import { RegistrationFileInput } from './components/RegistrationFileInput';
import { RegistrationDefaults } from './components/RegistrationDefaults';
import { RegistrationActions } from './components/RegistrationActions';
import { RegistrationPreviews } from './components/RegistrationPreviews';
import './bulk-registration.css';

export function BulkRegistrationPage() {
  const workflow = useBulkRegistration();
  const { error, storageError, working, ready, busy, edit } = workflow;

  function reset() {
    edit({ path: '', file: null, source: null, schoolIndex: '', school: null, output: null });
  }

  return (
    <main className="bulk-page">
      <div className="bulk-shell">
        <header className="bulk-header">
          <div>
            <p className="bulk-eyebrow">FILE CONVERSION</p>
            <h1>Bulk registration</h1>
            <p className="bulk-subtitle">Your student data, ready for registration.</p>
          </div>
          <Link to="/admission_file_page" className="bulk-back">
            Back to mapping <span aria-hidden="true">&#8599;</span>
          </Link>
        </header>
        {(error || storageError) && (
          <p role="alert" className="bulk-error bulk-top-error">{error || storageError}</p>
        )}
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
              selectSheet={workflow.selectSheet} edit={edit}
            />
          </div>
          <RegistrationDefaults />
        </div>
        {(working || (!ready && !storageError)) && (
          <p role="status" className="bulk-notice">Working...</p>
        )}
        <RegistrationActions
          schoolValid={workflow.schoolValid} source={workflow.source}
          busy={busy} output={workflow.output} convert={workflow.convert}
        />
        <RegistrationPreviews file={workflow.file} output={workflow.output} />
        <footer className="bulk-footer">
          <button className="bulk-text-button" disabled={busy} onClick={reset}>Reset bulk registration</button>
          <span>Shared across tabs on this browser</span>
          <span>File conversion only &middot; No registrations submitted</span>
        </footer>
      </div>
    </main>
  );
}
