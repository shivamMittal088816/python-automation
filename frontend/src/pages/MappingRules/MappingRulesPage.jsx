import { Link, useLocation } from 'react-router';
import { PageHeader } from '../../components/common/Presentation';

const sections = [
  { id: 'start', title: 'Before you start', rules: [
    'Load the school file and the dump of existing student accounts. Check the school index, worksheets and selected columns.',
    'Run Admission mapping first. After changing either input file, run it again before Email mapping or Class concatenation.',
    'Mapping runs only when you click a Run button. Opening a page or changing a selection does not run it.',
    'Rerunning an earlier stage can clear later results. Download the results you need before starting again.',
  ] },
  { id: 'results', title: 'What the results mean', rules: [
    'Matched: the student meets the matching rules and account checks.',
    'Review: something needs checking, such as different names, repeated details or an account used more than once. Read the reason beside the student.',
    'Not matched: no match was found, or required details are missing under that stage’s rules. These students may continue to the next stage.',
    'Review students stay in their current stage. They are not automatically sent to the next stage.',
    'Previews are read-only. You can view and download results, but cannot manually move students between groups. Correct the input and rerun mapping.',
  ] },
  { id: 'admission', title: '1. Admission mapping', rules: [
    'Completely identical school rows are reduced to one copy before matching.',
    'Pass 1 looks for the admission number in the dump, then compares the selected first-name cells. Capital letters and spaces at the beginning or end are ignored.',
    'Keep leading zeros: admission numbers such as 00123 and 123 are different.',
    'One dump record with the same admission number and first name can be Matched if the name is longer than one character and the dump username is present.',
    'Matching one-letter names, including matching initials such as A., go to Review. Different or missing first names also need Review.',
    'An admission number repeated in the remaining school rows, or found more than once in the dump, goes to Review.',
    'A blank admission number goes to Not matched. An admission number not found in the dump also goes to Not matched, unless another check, such as a missing school first name, requires Review.',
    'Pass 2 retries eligible first-name mismatch reviews using the full name and the same unique admission number. Names must contain the same characters and counts, ignoring spaces and capital letters. For example, Mary Ann and Myra Nan compare equally.',
    'Pass 2 does not clear single-letter-name reviews, duplicate admissions or missing-name reviews.',
  ] },
  { id: 'email', title: '2. Email mapping', rules: [
    'Uses only the current Admission Not matched students. Select the email and first-name columns.',
    'Pass 1 searches existing accounts by email across schools and saves a separate email dump.',
    'A unique email with a matching first name can be Matched. A matching one-character first name goes to Review.',
    'The account must belong to the selected school. Missing or different school details send the student to Review, even when the email and name match.',
    'Repeated emails in the input, multiple accounts for an email, or missing/different names go to Review.',
    'Missing emails or emails not found go to Not matched.',
    'Pass 2 retries eligible reviews where the email was found but the first name differed. Select the school full-name column; it compares sorted full-name characters with the dump full name, ignoring spaces and capital letters. School and account checks still apply.',
  ] },
  { id: 'class', title: '3. Full name + class concatenation', rules: [
    'Choose one source: Admission Not matched or Email Not matched. Email mapping is optional before this stage.',
    'After running Email mapping, choose Email Not matched to work on the remaining students. Choosing Admission Not matched can include students already handled by Email mapping.',
    'This stage uses the admission dump, not the email dump. Dump records are considered even when their admission number is blank.',
    'Pass 1 joins the full name and class number and compares them with the dump’s prepared name-and-class value. For example, Alice Smith in class 3 is compared as alicesmith3.',
    'One matching dump record is eligible for Matched. Multiple records go to Review. No match, or a missing school name or class, goes to Not matched.',
    'Pass 2 retries only Pass 1’s Not matched students. It compares the characters in the full name, ignoring spaces and capital letters, and checks the class number.',
    'Pass 2 compares the stored dump class directly, without adding 1. Class values such as 04, 4 and 4.0 count as the same number in this pass.',
    'Rerunning Pass 2 replaces its earlier results using the original Pass 1 misses. Rerunning Pass 1 starts the two-pass process again.',
    'Students still in Review or Not matched need further checking. The app does not automatically create new student accounts.',
  ] },
  { id: 'accounts', title: 'Account checks and reviewing your work', rules: [
    'The same username or user ID must not be assigned to multiple matched students. Conflicting matches go to Review.',
    'These checks also apply across mapping stages. An earlier Matched result can become Review if a later stage finds an account conflict.',
    'Check the status and reason in each result group after mapping. Download Excel or CSV when ready; downloads include all rows in that group, not just the visible page.',
    'Refreshing restores saved work while the session is valid. Sessions expire after 24 hours without activity, so download results you need to keep.',
  ] },
];

export function MappingRulesPage() {
  const { search } = useLocation();
  return <div className="page-stack">
    <PageHeader title="Mapping rules" description="A practical guide to how students are matched and what to check next." showHelp={false} />
    <Link className="inline-flex rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50" to={`/admission_file_page${search}`}>Back to admission mapping</Link>
    <nav aria-label="Mapping rules sections" className="flex flex-wrap gap-2">{sections.map(section => <a key={section.id} href={`#${section.id}`} className="rounded-full border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 hover:border-blue-300 hover:text-blue-700">{section.title}</a>)}</nav>
    {sections.map(section => <section key={section.id} id={section.id} aria-labelledby={`${section.id}-title`} className="scroll-mt-6 rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
      <h3 id={`${section.id}-title`} className="mb-4 text-lg font-semibold text-slate-900">{section.title}</h3>
      <ul className="list-disc space-y-3 pl-5 text-sm leading-6 text-slate-600 marker:text-blue-600">{section.rules.map(rule => <li key={rule}>{rule}</li>)}</ul>
    </section>)}
  </div>;
}
