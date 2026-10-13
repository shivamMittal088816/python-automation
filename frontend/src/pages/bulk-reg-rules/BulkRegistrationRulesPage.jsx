import { Link, useLocation } from 'react-router';
import paragraphs from './completeStudentMappingRules.json';
import '../BulkRegistration/bulk-registration.css';
import './student-mapping-rules.css';

// Preserve the source document's section order and nested bullet lists.
const sections = [];
for (const paragraph of paragraphs) {
  if (paragraph.style === 'Title') {
    sections.push({ title: paragraph.text, blocks: [] });
    continue;
  }
  const blocks = sections.at(-1).blocks;
  if (paragraph.style.startsWith('ListBullet')) {
    if (blocks.at(-1)?.type !== 'list') blocks.push({ type: 'list', items: [] });
    const items = blocks.at(-1).items;
    if (paragraph.style === 'ListBullet2' && items.length) {
      items.at(-1).children.push(paragraph.text);
    } else {
      items.push({ text: paragraph.text, children: [] });
    }
  } else {
    blocks.push({ type: paragraph.style === 'Heading1' || paragraph.text === 'Meaning of the results' ? 'heading' : 'paragraph', text: paragraph.text });
  }
}

export function BulkRegistrationRulesPage() {
  const { search } = useLocation();
  const returnParams = new URLSearchParams(search);
  const fromMapping = returnParams.get('from') === 'mapping';
  returnParams.delete('from');
  const returnSearch = returnParams.toString();
  const returnPath = fromMapping ? '/admission_file_page' : '/bulk-reg';
  const returnTo = `${returnPath}${returnSearch ? `?${returnSearch}` : ''}`;
  return <main className="bulk-page student-rules-page">
    <div className="bulk-shell bulk-rules-shell">
      <header className="bulk-header">
        <div><p className="bulk-eyebrow">OPERATIONS GUIDE</p><h1>Complete student mapping rules</h1><p className="bulk-subtitle">Admission mapping, email mapping, full name and class matching, and sanity checks.</p></div>
        <Link to={returnTo} className="bulk-back">{fromMapping ? 'Back to mapping' : 'Back to bulk registration'} <span aria-hidden="true">&#8592;</span></Link>
      </header>
      <nav className="bulk-card student-rules-contents" aria-label="Rule sections">
        {sections.map((section, index) => <a key={section.title} href={`#mapping-rules-${index}`}>{section.title}</a>)}
      </nav>
      {sections.map((section, index) => <section className="bulk-card student-rules-section" id={`mapping-rules-${index}`} key={section.title} aria-labelledby={`mapping-rules-title-${index}`}>
        <h2 id={`mapping-rules-title-${index}`}>{section.title}</h2>
        {section.blocks.map((block, blockIndex) => {
          if (block.type === 'heading') return <h3 key={blockIndex}>{block.text}</h3>;
          if (block.type === 'paragraph') return <p key={blockIndex}>{block.text}</p>;
          return <ul key={blockIndex}>{block.items.map((item, itemIndex) => <li key={itemIndex}>{item.text}{item.children.length > 0 && <ul>{item.children.map((text, childIndex) => <li key={childIndex}>{text}</li>)}</ul>}</li>)}</ul>;
        })}
      </section>)}
    </div>
  </main>;
}
