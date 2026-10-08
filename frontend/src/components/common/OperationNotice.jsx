import { Alert } from './Controls';

function eventTime(event) {
  const value = event.finished_at || event.started_at;
  if (!value) return '';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? '' : parsed.toLocaleString();
}

export function OperationNotice({ notice }) {
  if (!notice) return null;
  const events = Array.isArray(notice.events) ? notice.events : [];
  return <Alert type={notice.type}>
    <p>{notice.text}</p>
    {events.length > 1 && <details className="mt-1.5">
      <summary className="cursor-pointer font-semibold">View operation details</summary>
      <ul className="mt-1 list-disc space-y-1 pl-5">
        {events.map(event => <li key={`${event.operation_id}:${event.status}`}>
          {event.message}{eventTime(event) && <span className="ml-1 opacity-75">({eventTime(event)})</span>}
        </li>)}
      </ul>
    </details>}
  </Alert>;
}

