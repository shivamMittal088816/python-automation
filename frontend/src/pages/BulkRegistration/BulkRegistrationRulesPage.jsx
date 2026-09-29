import { Link } from 'react-router';
import './bulk-registration.css';

const columnRules = [
  ['FIRST NAME', ['Required for every record.', 'Only uppercase and lowercase English letters (A–Z and a–z) are allowed.', 'Spaces, numbers, punctuation, symbols, and non-English letters are not allowed.']],
  ['LAST NAME', ['Optional.', 'When supplied, only A–Z, a–z, and spaces are allowed.']],
  ['FULL NAME', ['Required for every record; blank or whitespace-only values fail.', 'Only A–Z, a–z, and spaces are allowed.']],
  ['Section', ['Required for every record.', 'The value must match a section stored in the database and resolve to a valid section index.', 'Blank sections and sections not found in the database appear in Review records.']],
  ['Class Number', ['Required for every record.', 'The class name must match a class stored in the server-side class mapping.', 'Blank or unknown classes appear in Review records.']],
  ['GENDER', ['Required for every record.', 'Accepted values are Male, Female, and Others; matching is case-insensitive.', 'Blank or non-predefined values appear in Review records.']],
  ['EMAIL', ['Blank input emails are allowed and are generated during preview creation.', 'A supplied email must follow local-part@domain.suffix, such as name@domain.com.', 'The domain suffix must contain at least two letters.', 'Common local-part characters such as dots, underscores, plus signs, and hyphens are allowed.', 'Duplicate nonblank input emails fail; comparison ignores case and surrounding whitespace.', 'Invalid email formats and duplicate input emails appear in generated-preview Review records.']],
  ['user_name', ['Must be blank in the input file because bulk registration generates usernames.', 'Any input record that already contains a username fails input sanity.', 'If a generated username conflicts in the final file or database, Bulk-reg verify assigns another available username.']],
];

const finalRuleGroups = [
  ['Student details', [
    'First name: required, A–Z and a–z only, without spaces.',
    'Last name: optional; letters and spaces only when supplied.',
    'Full name: required; letters and spaces only.',
  ]],
  ['Mapped values', [
    'Section must have a valid database index.',
    'Class Number must have a valid stored class index.',
    'Gender must be Male, Female, or Others and have a valid index.',
  ]],
  ['Username and email', [
    'Username and email cannot be blank.',
    'Every email must follow local-part@domain.suffix with a suffix of at least two letters.',
    'Username and email must be unique in the final file.',
    'Username and email must not already exist in the database.',
    'Username without trailing digits must match the lowercase first name.',
  ]],
  ['Automatic correction', [
    'Only usernames that are duplicated in the final file or already exist in the database are regenerated; valid usernames remain unchanged.',
    'Replacement usernames are checked again against both the final file and the database.',
    'Verification makes at most 10 repair attempts, then reports an error instead of continuing indefinitely.',
    'Corrected usernames are saved to the preview and downloadable file.',
    'When a corrected username belongs to a student whose input email was blank, the generated email is updated to use the corrected username. Supplied input emails are not changed.',
    'Previous and newly assigned usernames are shown for affected students.',
    'Only failed checks are listed; a clean file shows All checks passed.',
  ]],
];

export function BulkRegistrationRulesPage() {
  return <main className="bulk-page">
    <div className="bulk-shell bulk-rules-shell">
      <header className="bulk-header">
        <div><p className="bulk-eyebrow">OPERATIONS GUIDE</p><h1>Bulk-registration sanity rules</h1><p className="bulk-subtitle">Use this checklist to prepare files that pass preview and final verification.</p></div>
        <Link to="/bulk-reg" className="bulk-back">Back to bulk registration <span aria-hidden="true">&#8592;</span></Link>
      </header>
      <section className="bulk-card bulk-rules-intro">
        <h2>Before the checks run</h2>
        <ul><li>Leading and trailing whitespace is removed from every input value.</li></ul>
      </section>
      <section className="bulk-rules-grid" aria-label="Rules by column">
        {columnRules.map(([column, rules]) => <article className="bulk-card bulk-rule-card" key={column}><h2>{column}</h2><ul>{rules.map(rule => <li key={rule}>{rule}</li>)}</ul></article>)}
      </section>
      <section className="bulk-card bulk-final-rules">
        <div className="bulk-final-rules-heading"><div><p className="bulk-card-eyebrow">SAVED GENERATED FILE</p><h2>Bulk-reg verify rules</h2></div><span>Final safety check</span></div>
        <div className="bulk-final-rules-grid">{finalRuleGroups.map(([group, rules], index) => <article className="bulk-final-rule-group" key={group}>
          <span className="bulk-rule-number">{String(index + 1).padStart(2, '0')}</span><div><h3>{group}</h3><ul>{rules.map(rule => <li key={rule}>{rule}</li>)}</ul></div>
        </article>)}</div>
      </section>
    </div>
  </main>;
}
