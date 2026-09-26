import { test, expect } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import { readFileSync } from 'node:fs';
const school = fileURLToPath(new URL('./fixtures/school.csv', import.meta.url));
const dump = fileURLToPath(new URL('./fixtures/dump.csv', import.meta.url));

test('mapping runs only after an explicit start action, never on navigation or reload', async ({ page }) => {
  const actions = [];
  page.on('request', request => {
    if (request.method() === 'POST' && /\/(?:admission-mapping\/run|email-mapping\/run|full-name-class-mapping\/run|duplicate-accounts\/reconcile)$/.test(new URL(request.url()).pathname)) actions.push(new URL(request.url()).pathname.split('/').slice(-2).join('/'));
  });
  await page.goto('/admission_file_page');
  await page.getByLabel('Add school file').setInputFiles(school);
  await expect(page.getByText('Loaded: school.csv', { exact: true })).toBeVisible();
  await page.getByLabel('Add dump file').setInputFiles(dump);
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Save school index', exact: true }).click();
  await expect(page.getByText('Saved school index: 914', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Run mapping', exact: true })).toBeEnabled();
  expect(actions).toEqual([]);
  await page.getByRole('button', { name: 'Run mapping', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Preview matched', exact: true })).toBeVisible();
  expect(actions).toEqual(['admission-mapping/run']);
  await page.goto('/email_mapping_page');
  await expect(page.getByRole('button', { name: 'Run mapping', exact: true })).toBeEnabled();
  expect(actions).toEqual(['admission-mapping/run']);
  await page.getByRole('button', { name: 'Run mapping', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Preview matched', exact: true })).toBeVisible();
  expect(actions).toEqual(['admission-mapping/run', 'email-mapping/run']);
  await page.goto('/full_name_class_mapping_page');
  await expect(page.getByRole('button', { name: 'Run mapping', exact: true })).toBeEnabled();
  expect(actions).toEqual(['admission-mapping/run', 'email-mapping/run']);
  await page.getByRole('button', { name: 'Run mapping', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Preview matched', exact: true })).toBeVisible();
  for (const route of ['/admission_file_page', '/email_mapping_page', '/full_name_class_mapping_page']) {
    await page.goto(route);
    await page.reload();
    await expect(page.getByRole('button', { name: 'Run mapping', exact: true })).toBeEnabled();
  }
  expect(actions).toEqual(['admission-mapping/run', 'email-mapping/run', 'full-name-class-mapping/run']);
});

async function mapAdmission(page) {
  await page.goto('/admission_file_page');
  await page.getByLabel('Add school file').setInputFiles(school);
  await expect(page.getByText('Loaded: school.csv', { exact: true })).toBeVisible();
  await page.getByLabel('Add dump file').setInputFiles(dump);
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Save school index', exact: true }).click();
  await expect(page.getByText('Saved school index: 914', { exact: true })).toBeVisible();
  await expect(page.getByLabel('School admission number column')).toBeVisible();
  await page.getByRole('button', { name: 'Run mapping', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Preview not matched', exact: true })).toBeVisible();
}

test('email metadata is cached across navigation and refreshed after admission runs and reload', async ({ page }) => {
  let requests = 0;
  page.on('request', request => {
    if (new URL(request.url()).pathname.endsWith('/table-previews/school')) requests++;
  });
  async function openSidebar(group, link) {
    await page.locator('summary').filter({ hasText: group }).click();
    await page.getByRole('link', { name: link, exact: true }).click();
  }
  await mapAdmission(page);
  await openSidebar('Email mapping', 'Email mapping');
  await expect(page.getByLabel('School email column')).toBeVisible();
  expect(requests).toBe(1);
  await openSidebar('Admission No. Mapping', 'Admission mapping');
  await openSidebar('Email mapping', 'Email mapping');
  await expect(page.getByLabel('School email column')).toBeVisible();
  expect(requests).toBe(1);
  await openSidebar('Admission No. Mapping', 'Admission mapping');
  await page.getByRole('button', { name: 'Run mapping', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Run mapping', exact: true })).toBeEnabled();
  await openSidebar('Email mapping', 'Email mapping');
  await expect(page.getByLabel('School email column')).toBeVisible();
  expect(requests).toBe(1);
  await page.reload();
  await expect(page.getByLabel('School email column')).toBeVisible();
  expect(requests).toBe(2);
  await openSidebar('Admission No. Mapping', 'Admission mapping');
  await page.getByLabel('Add school file').setInputFiles({
    name: 'changed-school.csv', mimeType: 'text/csv',
    buffer: Buffer.from(readFileSync(school, 'utf8') + '\n'),
  });
  await expect(page.getByText('Loaded: changed-school.csv', { exact: true })).toBeVisible();
  await openSidebar('Email mapping', 'Email mapping');
  await expect(page.getByLabel('School email column')).toBeVisible();
  expect(requests).toBe(3);
});

test('class concatenation caches both sources and dump metadata across navigation', async ({ page }) => {
  const requests = { school: 0, email_source: 0, dump: 0 };
  page.on('request', request => {
    const path = new URL(request.url()).pathname;
    for (const kind of Object.keys(requests)) if (path.endsWith(`/table-previews/${kind}`)) requests[kind]++;
  });
  async function navigate(group, link) {
    await page.locator('summary').filter({ hasText: group }).click();
    await page.getByRole('link', { name: link, exact: true }).click();
  }
  await mapAdmission(page);
  await navigate('Email mapping', 'Email mapping');
  await expect(page.getByLabel('School email column')).toBeVisible();
  await navigate('Full name + class Number', 'Concatenation mapping');
  await expect(page.getByLabel('Full name', { exact: true })).toBeVisible();
  expect(requests).toEqual({ school: 1, email_source: 0, dump: 1 });
  await navigate('Email mapping', 'Email mapping');
  await navigate('Full name + class Number', 'Concatenation mapping');
  await expect(page.getByLabel('Full name', { exact: true })).toBeVisible();
  expect(requests).toEqual({ school: 1, email_source: 0, dump: 1 });
  await navigate('Email mapping', 'Email mapping');
  await page.getByRole('button', { name: 'Run mapping', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Preview matched', exact: true })).toBeVisible();
  await navigate('Full name + class Number', 'Concatenation mapping');
  await expect(page.getByLabel('Full name', { exact: true })).toBeVisible();
  expect(requests.email_source).toBe(0);
  await page.getByRole('radio', { name: /Admission mapping/ }).check();
  await expect(page.getByLabel('Full name', { exact: true })).toBeVisible();
  const cachedCounts = { ...requests };
  await page.getByRole('radio', { name: /Email mapping/ }).check();
  await expect(page.getByLabel('Full name', { exact: true })).toBeVisible();
  await navigate('Email mapping', 'Email mapping');
  await navigate('Full name + class Number', 'Concatenation mapping');
  await expect(page.getByLabel('Full name', { exact: true })).toBeVisible();
  expect(requests).toEqual(cachedCounts);
  await page.reload();
  await expect(page.getByLabel('Full name', { exact: true })).toBeVisible();
  expect(requests.email_source).toBe(cachedCounts.email_source);
  expect(requests.school).toBe(cachedCounts.school + 1);
  expect(requests.dump).toBe(cachedCounts.dump + 1);
});

test('admission upload, locked preview, workbook downloads and refresh', async ({ page }) => {
  const failures=[]; page.on('pageerror',error=>failures.push(error.message));
  await mapAdmission(page);
  await page.getByRole('link', { name: 'Preview matched', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Admission Results Preview' })).toBeVisible();
  await expect(page.getByRole('cell', { name: '0001', exact: true })).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download Excel', exact: true }).click();
  expect((await download).suggestedFilename()).toBe('matched.xlsx');
  await expect(page.getByRole('checkbox', { name: /Select row/ })).toHaveCount(0);
  await expect(page.getByRole('button', { name: /Move selected/ })).toHaveCount(0);
  await expect(page.getByText(/Student previews are locked/)).toBeVisible();
  await page.getByLabel('Choose result group').selectOption('review.xlsx');
  await expect(page.getByRole('button', { name: 'Download Excel', exact: true })).toBeVisible();
  await page.getByLabel('Choose result group').selectOption('matched.xlsx');
  await page.reload();
  await expect(page.getByRole('cell', { name: '0001', exact: true })).toBeVisible();
  await page.screenshot({ path: test.info().outputPath('admission-preview.png'), fullPage: true });
  expect(failures).toEqual([]);
});

for (const kind of ['school', 'dump']) {
  test(`${kind} changes clear stale results while direct mapping remains available`, async ({ page }) => {
    await mapAdmission(page);
    await page.getByLabel(kind === 'school' ? 'Add school file' : 'Add dump file').setInputFiles({
      name: `changed-${kind}.csv`, mimeType: 'text/csv',
      buffer: Buffer.from(readFileSync(kind === 'school' ? school : dump, 'utf8') + '\n'),
    });
    await expect(page.getByText(`Loaded: changed-${kind}.csv`, { exact: true })).toBeVisible();
    await page.goto('/admission_preview_page');
    await expect(page.getByText('No results available in this session. Map your files first to preview the results.', { exact: true })).toBeVisible();
    await page.goto('/admission_file_page');
    if (kind === 'dump') {
      await page.getByLabel('School index', { exact: true }).fill('914');
      await page.getByRole('button', { name: 'Save school index', exact: true }).click();
      await expect(page.getByText('Saved school index: 914', { exact: true })).toBeVisible();
    }
    for (const route of ['/email_mapping_page', '/full_name_class_mapping_page']) {
      await page.goto(route);
      await expect(page.getByRole('button', { name: 'Run mapping', exact: true })).toBeEnabled();
    }
  });
}

test('email handoff, separate dump, full-name/class mapping, search and downloads', async ({ page }) => {
  await mapAdmission(page);
  await expect(page.getByRole('button', { name: 'Download mapping results', exact: true })).toBeEnabled();
  const admissionResults = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download mapping results', exact: true }).click();
  expect((await admissionResults).suggestedFilename()).toBe('automation-914-school.xlsx');
  await page.goto('/email_mapping_page');
  await expect(page.getByLabel('School email column')).toBeVisible();
  await expect(page.getByLabel('School first name column')).toHaveValue('first_name');
  await page.getByRole('button', { name: 'Run mapping', exact: true }).click();
  await page.getByRole('link', { name: 'Preview matched', exact: true }).click();
  await expect(page.getByRole('button', { name: /Move selected/ })).toHaveCount(0);
  await expect(page.getByRole('checkbox', { name: /Select row/ })).toHaveCount(0);
  await expect(page.getByRole('cell', { name: '0002', exact: true })).toBeVisible();
  await page.goto('/email_dump_page');
  await expect(page.getByRole('heading', { name: 'E-mail dump file', exact: true })).toBeVisible();
  await page.getByLabel('Search email dump').fill('bob@example.test');
  await expect(page.locator('mark').first()).toHaveText('bob@example.test');
  await page.goto('/full_name_class_mapping_page');
  await page.getByRole('radio', { name: /Email mapping/ }).check();
  await page.getByRole('button', { name: 'Run mapping', exact: true }).click();
  await page.getByRole('link', { name: 'Preview matched', exact: true }).click();
  await expect(page.getByRole('button', { name: /Move selected/ })).toHaveCount(0);
  await expect(page.getByRole('checkbox', { name: /Select row/ })).toHaveCount(0);
  await expect(page.getByRole('cell', { name: '0003', exact: true })).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download CSV', exact: true }).click();
  expect((await download).suggestedFilename()).toBe('full_name_class_matched.csv');
  const finalDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download mapping results', exact: true }).click();
  expect((await finalDownload).suggestedFilename()).toBe('automation-914-school.xlsx');
  await page.goto('/school_file_page');
  await expect(page.getByLabel('Search all columns')).toBeVisible();
  await page.getByLabel('Class column', { exact: true }).selectOption('classNumber');
  await page.getByLabel('Section column', { exact: true }).selectOption('section');
  await page.getByLabel('Search all columns').fill('Carol');
  await expect(page.getByText('School students · 1 of 5', { exact: true })).toBeVisible();
  await page.getByText('Selected columns', { exact: true }).click();
  await expect(page.getByLabel('Selected columns', { exact: true })).toBeChecked();
  await page.getByText('Choose columns', { exact: true }).click();
  await page.getByRole('checkbox', { name: 'email', exact: true }).check();
  await page.getByRole('checkbox', { name: 'full_name', exact: true }).check();
  await expect(page.getByText('2 selected', { exact: true })).toBeVisible();
  await page.getByLabel('Search selected columns').fill('dave@example.test');
  await expect(page.locator('mark').first()).toHaveText('dave@example.test');
  await page.goto('/dump_file_page');
  await expect(page.getByRole('heading', { name: 'Dump file', exact: true })).toBeVisible();
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByLabel('School name', { exact: true }).fill('Test School');
  await page.getByRole('button', { name: 'Save details', exact: true }).click();
  await expect(page.getByText('School details saved with this dump.', { exact: true })).toBeVisible();
  await page.reload();
  const identity = page.getByRole('region', { name: 'Current school' });
  await expect(identity.getByText('914', { exact: true })).toBeVisible();
  await expect(identity.getByText('Test School', { exact: true })).toBeVisible();
});

test('removed Jobs and Review links, routes and APIs are unavailable', async ({ page, request }) => {
  await page.goto('/admission_file_page');
  const sidebar = page.getByRole('navigation', { name: 'Main navigation' });
  await expect(sidebar.getByRole('link', { name: 'Jobs', exact: true })).toHaveCount(0);
  await expect(sidebar.getByRole('link', { name: 'Review', exact: true })).toHaveCount(0);
  for (const path of ['/jobs_page', '/review_page']) {
    await page.goto(path);
    await expect(page).toHaveURL(/admission_file_page/);
    await expect(page.getByRole('heading', { name: 'Admission File Mapping' })).toBeVisible();
  }
  for (const path of ['/mapping/jobs', '/mapping/results']) {
    const response = await request.get(`http://127.0.0.1:8123/api/v1${path}`);
    expect(response.status()).toBe(404);
  }
});

test('file path inputs, SQL dump loading, loading/error states and responsive navigation', async ({ page }) => {
  await page.goto('/admission_file_page');
  await page.getByTestId('school-input').getByRole('tab', { name: 'File path', exact: true }).click();
  await page.getByTestId('school-input').getByLabel('File path', { exact: true }).fill(school);
  await page.getByRole('button', { name: 'Use file path', exact: true }).click();
  await expect(page.getByText('Loaded: school.csv', { exact: true })).toBeVisible();
  await page.getByLabel('Fetch from SQL', { exact: true }).check();
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Fetch dump data', exact: true }).click();
  await expect(page.getByText('Fetched 4 student records for 914-Test School.', { exact: true })).toBeVisible();
  await page.route('**/table-previews/school?**', async route => {
    await new Promise(resolve => setTimeout(resolve, 700));
    await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Fixture API unavailable' }) });
  });
  await page.goto('/school_file_page');
  await expect(page.getByRole('status').filter({ hasText: /Reading file/ })).toBeVisible();
  await expect(page.getByRole('alert')).toHaveText('Fixture API unavailable');
  await page.unroute('**/table-previews/school?**');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/school_file_page');
  await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'School file', exact: true })).toBeVisible();
});

test('SQL dump replacement preserves results on failure and invalidates them on success', async ({ page }) => {
  await mapAdmission(page);
  await expect(page.getByRole('link', { name: 'Preview matched', exact: true })).toBeVisible();

  await page.getByLabel('Fetch from SQL', { exact: true }).check();
  await page.getByLabel('School index', { exact: true }).fill('999999');
  await page.getByRole('button', { name: 'Fetch dump data', exact: true }).click();
  await expect(page.getByRole('alert')).toHaveText('No school found for index 999999.');
  await expect(page.getByText('Loaded: dump.csv', { exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Preview matched', exact: true })).toBeVisible();

  await page.goto('/admission_preview_page');
  await expect(page.getByRole('heading', { name: 'Admission Results Preview' })).toBeVisible();
  await expect(page.getByRole('cell', { name: '0001', exact: true })).toBeVisible();

  await page.goto('/admission_file_page');
  await page.getByLabel('Fetch from SQL', { exact: true }).check();
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Fetch dump data', exact: true }).click();
  await expect(page.getByText('Fetched 4 student records for 914-Test School.', { exact: true })).toBeVisible();
  await expect(page.getByText('Loaded: school_914_dump.csv', { exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Preview matched', exact: true })).toHaveCount(0);

  await page.goto('/admission_preview_page');
  await expect(page.getByText('No results available in this session. Map your files first to preview the results.', { exact: true })).toBeVisible();
  await page.goto('/email_mapping_page');
  await expect(page.getByLabel('School email column')).toBeVisible();
  await page.goto('/full_name_class_mapping_page');
  await expect(page.getByLabel('Full name', { exact: true })).toBeVisible();
});
