import { ActionLink, Card } from './Controls';
import { Badge, SectionHeader } from './Presentation';
import { useWorkspace } from '../../context/WorkspaceContext';

const groups = [
  ['matched', 'Matched'],
  ['review', 'Review'],
  ['not_matched', 'Not matched'],
];

const descriptions = {
  email: {
    matched: 'Email matches uniquely and the selected first name matches the account.',
    review: 'Duplicate emails, missing or different names, and duplicate accounts require review.',
    not_matched: 'The email is blank or was not found in the email lookup.',
  },
  full_name_class: {
    matched: 'Full name and class number match one account using the concatenated value.',
    review: 'Multiple matches or duplicate usernames and user IDs require review.',
    not_matched: 'No account matches the concatenated full name and class number.',
  },
};

export function MappingResultCards({ stage, previewPath, title }) {
  const prefix = stage === 'email' ? 'email_' : 'full_name_class_';
  return <section className="space-y-3">
    <SectionHeader title={title} description="Saved results from the last run. Open a group on the dedicated preview page." />
    <div className="grid gap-3 sm:grid-cols-3">
      {groups.map(([group, label]) => {
        const filename = `${prefix}${group}.xlsx`;
        return <ResultCard key={filename} stage={stage} filename={filename} group={group} label={label} previewPath={previewPath} />;
      })}
    </div>
  </section>;
}

function ResultCard({ stage, filename, group, label, previewPath }) {
  const { workspace } = useWorkspace();
  const count = workspace.exports[stage]?.[filename] || 0;
  return <Card>
    <Badge>{label}</Badge>
    <p className="my-2 text-2xl font-semibold tabular-nums">{count.toLocaleString()}</p>
    <p className="mb-3 caption">{descriptions[stage][group]}</p>
    <ActionLink to={`${previewPath}?file=${encodeURIComponent(filename)}`}>Preview {label.toLowerCase()}</ActionLink>
  </Card>;
}
