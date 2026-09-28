import { test, expect } from './fixtures/browser-audit';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { readFile } from 'node:fs/promises';

test('bulk registration loads files independently of mapping', async ({ page }) => {
  const mappingRequests = [];
  page.on('request', request => { if (request.url().includes('/mapping/')) mappingRequests.push(request.url()); });
  await page.goto('/bulk-reg');
  await expect(page.getByRole('heading', { name: 'Bulk registration', exact: true })).toBeVisible();
  await expect(page.getByLabel('Upload registration file')).toBeEnabled();
  const rows = Array.from({ length: 25 }, (_, index) => `${String(index + 1).padStart(3, '0')},Student ${index + 1}`).join('\n');
  await page.getByLabel('Upload registration file').setInputFiles({ name: 'students.csv', mimeType: 'text/csv', buffer: Buffer.from(`id,name\n${rows}`) });
  await expect(page.getByText('File ready', { exact: true })).toBeVisible();
  await expect(page.getByText('students.csv', { exact: true }).first()).toBeVisible();
  await page.locator('summary').filter({ hasText: 'Input preview' }).click();
  await expect(page.getByRole('cell', { name: '001' })).toBeVisible();
  const inputPages = page.getByRole('navigation', { name: 'Input preview pages' });
  await expect(inputPages).toContainText('Rows 1–20 of 25');
  await inputPages.getByRole('button', { name: 'Next' }).click();
  await expect(page.getByRole('cell', { name: '021' })).toBeVisible();
  await expect(inputPages).toContainText('Rows 21–25 of 25');
  await page.getByRole('button', { name: 'Clear file' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  // Returning to the tab refreshes shared browser metadata without changing the loaded file.
  const focused = page.waitForResponse('**/bulk-reg/workspace');
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await (await focused).finished();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('dialog').getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(page.getByRole('cell', { name: '021' })).toBeVisible();
  await page.getByRole('button', { name: 'Clear file' }).click();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(page.getByRole('cell', { name: '021' })).toBeVisible();
  await page.getByRole('button', { name: 'Clear file' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Confirm', exact: true }).click();
  await page.locator('summary').filter({ hasText: 'Use a file path instead' }).click();
  await page.getByLabel('File path', { exact: true }).fill(resolve('e2e/fixtures/school.csv'));
  await page.getByRole('button', { name: 'Load file', exact: true }).click();
  await page.locator('summary').filter({ hasText: 'Input preview' }).click();
  await expect(page.getByRole('cell', { name: '001' }).first()).toBeVisible();
  expect(mappingRequests).toEqual([]);
});

test('email verification reports preview and database duplicates and clears on regeneration', async ({ page }) => {
  await page.goto('/bulk-reg');
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await expect(page.getByLabel('School name fetched')).toBeVisible();
  await page.getByLabel('Upload registration file').setInputFiles({
    name: 'emails.csv', mimeType: 'text/csv',
    buffer: Buffer.from('FIRST NAME,EMAIL\nAda,duplicate@testschool.com\nBob,duplicate@testschool.com\nCara,existing@testschool.com'),
  });
  await page.getByRole('button', { name: 'Generate preview' }).click();
  await page.getByRole('button', { name: 'Verify emails', exact: true }).click();
  const verification = page.locator('details').filter({ has: page.getByRole('heading', { name: 'Email verification', exact: true }) });
  await expect(verification).toContainText('3 student records');
  await expect(verification.locator('article')).toHaveCount(3);
  await expect(verification.locator('article').nth(0)).toContainText('duplicate@testschool.com');
  await expect(verification.locator('article').nth(1)).toContainText('existing@testschool.com');
  await expect(verification.getByText('Failed', { exact: true })).toHaveCount(2);
  const duplicateStage = verification.locator('article').nth(0);
  await duplicateStage.getByText('Preview students who failed (2)', { exact: true }).click();
  await expect(duplicateStage.getByRole('columnheader')).toHaveCount(25);
  await expect(duplicateStage.getByRole('cell', { name: 'Ada', exact: true })).toBeVisible();
  await expect(duplicateStage.getByRole('cell', { name: 'Bob', exact: true })).toBeVisible();
  await expect(duplicateStage.getByRole('cell', { name: 'Cara', exact: true })).toHaveCount(0);
  const databaseStage = verification.locator('article').nth(1);
  await databaseStage.getByText('Preview students who failed (1)', { exact: true }).click();
  await expect(databaseStage.getByRole('cell', { name: 'Cara', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Verify usernames', exact: true }).click();
  const usernames = page.locator('details.bulk-username-verification').filter({ has: page.getByRole('heading', { name: 'Username verification', exact: true }) });
  await usernames.getByText('Preview students who failed (1)', { exact: true }).click();
  await expect(usernames.getByRole('columnheader')).toHaveCount(25);
  await expect(usernames.getByRole('cell', { name: 'Ada', exact: true })).toBeVisible();
  await expect(usernames.getByRole('cell', { name: 'Bob', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Generate preview' }).click();
  await expect(verification).toHaveCount(0);
  await expect(usernames).toHaveCount(0);
});

test('unknown classes show student records and status after reload', async ({ page }) => {
  await page.goto('/bulk-reg');
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await expect(page.getByLabel('School name fetched')).toBeVisible();
  await page.getByLabel('Upload registration file').setInputFiles({
    name: 'classes.csv', mimeType: 'text/csv',
    buffer: Buffer.from('FIRST NAME,LAST NAME,Class Number,admission_number\nZoe,Smith,Class XIII,001\nAda,Jones,Class I,002'),
  });
  await page.getByRole('button', { name: 'Generate preview' }).click();
  const missing = page.getByRole('region', { name: 'Classes not found in the built-in mapping', exact: true });
  await expect(missing.getByRole('cell', { name: 'Zoe Smith', exact: true })).toBeVisible();
  await expect(missing.getByRole('cell', { name: 'Class not exist', exact: true })).toBeVisible();
  await expect(missing.getByRole('cell', { name: '001', exact: true })).toBeVisible();
  await expect(missing.getByRole('cell', { name: 'Ada Jones', exact: true })).toHaveCount(0);
  await page.reload();
  await expect(missing.getByRole('cell', { name: 'Class XIII', exact: true })).toBeVisible();
});

test('unknown genders show student records and status after reload', async ({ page }) => {
  await page.goto('/bulk-reg');
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await expect(page.getByLabel('School name fetched')).toBeVisible();
  await page.getByLabel('Upload registration file').setInputFiles({
    name: 'genders.csv', mimeType: 'text/csv',
    buffer: Buffer.from('FIRST NAME,LAST NAME,GENDER,admission_number\nZoe,Smith,Unknown,001\nAda,Jones,Female,002\nBob,Brown, ,003'),
  });
  await page.getByRole('button', { name: 'Generate preview' }).click();
  const missing = page.getByRole('region', { name: 'Genders not found in the predefined mapping', exact: true });
  await expect(missing.getByRole('cell', { name: 'Zoe Smith', exact: true })).toBeVisible();
  await expect(missing.getByRole('cell', { name: 'Gender not exist', exact: true })).toBeVisible();
  await expect(missing.getByRole('cell', { name: 'Gender is blank', exact: true })).toBeVisible();
  await expect(missing.getByRole('cell', { name: 'Bob Brown', exact: true })).toBeVisible();
  for (const [label, status] of [
    ['Classes not found in the built-in mapping', 'Class is blank'],
    ['Sections not found in the database', 'Section is blank'],
  ]) {
    const table = page.getByRole('region', { name: label, exact: true });
    await expect(table.getByRole('cell', { name: status, exact: true })).toHaveCount(3);
    await expect(table.getByRole('cell', { name: 'Blank', exact: true })).toHaveCount(3);
  }
  await expect(missing.getByRole('cell', { name: '001', exact: true })).toBeVisible();
  await expect(missing.getByRole('cell', { name: 'Ada Jones', exact: true })).toHaveCount(0);
  await page.reload();
  await expect(missing.getByRole('cell', { name: 'Unknown', exact: true })).toBeVisible();
});

test('blank full names show source rows and student details after reload', async ({ page }) => {
  await page.goto('/bulk-reg');
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await expect(page.getByLabel('School name fetched')).toBeVisible();
  await page.getByLabel('Upload registration file').setInputFiles({
    name: 'names.csv', mimeType: 'text/csv',
    buffer: Buffer.from('FIRST NAME,LAST NAME,FULL NAME,admission_number\nZoe,Smith,,001\nAda,Jones,Ada Jones,002'),
  });
  await page.getByRole('button', { name: 'Generate preview' }).click();
  const missing = page.getByRole('region', { name: 'Records with blank full names', exact: true });
  await expect(missing.getByRole('cell', { name: 'Zoe', exact: true })).toBeVisible();
  await expect(missing.getByRole('cell', { name: 'Needs full name', exact: true })).toBeVisible();
  await expect(missing.getByRole('cell', { name: '2', exact: true })).toBeVisible();
  await expect(missing.getByRole('cell', { name: 'Ada', exact: true })).toHaveCount(0);
  await page.reload();
  await expect(missing.getByRole('cell', { name: '001', exact: true })).toBeVisible();
});

test('blank usernames and emails fail verification and show student records', async ({ page }) => {
  await page.goto('/bulk-reg');
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await expect(page.getByLabel('School name fetched')).toBeVisible();
  await page.getByLabel('Upload registration file').setInputFiles({
    name: 'blank-values.csv', mimeType: 'text/csv',
    buffer: Buffer.from('FIRST NAME,FULL NAME,admission_number\n,Missing Name,001'),
  });
  await page.getByRole('button', { name: 'Generate preview' }).click();
  for (const kind of ['usernames', 'emails']) {
    await page.getByRole('button', { name: `Verify ${kind}`, exact: true }).click();
    const stage = page.locator('article').filter({ has: page.getByRole('heading', { name: `No blank ${kind} in preview`, exact: true }) });
    await expect(stage.getByText('Failed', { exact: true })).toBeVisible();
    await stage.getByText('Preview students who failed (1)', { exact: true }).click();
    await expect(stage.getByRole('cell', { name: 'Missing Name', exact: true })).toBeVisible();
    await expect(stage.getByRole('columnheader')).toHaveCount(25);
  }
});

test('bulk registration recovers after a temporary storage read failure', async ({ page }) => {
  await page.goto('/bulk-reg');
  await expect(page.getByLabel('School index', { exact: true })).toBeEnabled();
  await page.route('**/bulk-reg/workspace', route => route.fulfill({ status: 503, json: { detail: 'Unavailable' } }));
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await expect(page.getByRole('alert')).toContainText('Could not load');
  await expect(page.getByLabel('School index', { exact: true })).toBeDisabled();
  await page.unroute('**/bulk-reg/workspace');
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.getByLabel('School index', { exact: true })).toBeEnabled();
});

test('verified school details, preview fixed output and download', async ({ page }) => {
  const unrelated = [];
  page.on('request', request => { if (/\/mapping\//.test(request.url())) unrelated.push(request.url()); });
  await page.goto('/bulk-reg');
  await expect(page.getByRole('button', { name: 'Generate preview' })).toBeDisabled();
  await page.screenshot({ path: 'test-results/bulk-registration-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole('button', { name: 'Verify school index' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/bulk-registration-mobile.png', fullPage: true });
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await expect(page.getByText('School index verified', { exact: true })).toBeVisible();
  await expect(page.getByLabel('School name fetched')).toHaveValue('Test School');
  await expect(page.getByLabel('School name fetched')).toHaveAttribute('readonly', '');
  await page.getByLabel('Upload registration file').setInputFiles({ name: 'students.csv', mimeType: 'text/csv', buffer: Buffer.from('FIRST NAME\nAda') });
  await page.getByRole('button', { name: 'Generate preview' }).click();
  await expect(page.getByRole('region', { name: 'Output preview', exact: true }).getByRole('cell', { name: '2026', exact: true })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Output preview', exact: true }).getByRole('cell', { name: 'ada001@testschool.com', exact: true })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Test School', exact: true })).toBeVisible();
  await expect(page.getByRole('cell', { name: '914', exact: true })).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download XLSX' }).click();
  expect((await download).suggestedFilename()).toBe('bulk-registration-914.xlsx');
  expect(unrelated).toEqual([]);
  await page.getByLabel('School index', { exact: true }).fill('999');
  await expect(page.getByText('School index verified', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await expect(page.getByRole('alert')).toContainText('No school found');
  await expect(page.getByLabel('School name fetched')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Download XLSX' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Generate preview' })).toBeDisabled();
});

test('bulk registration syncs files, verification and output across tabs and reloads', async ({ page, context }) => {
  await page.goto('/bulk-reg');
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await expect(page.getByLabel('School name fetched')).toHaveValue('Test School');
  await page.getByLabel('Upload registration file').setInputFiles({ name: 'shared.csv', mimeType: 'text/csv', buffer: Buffer.from('FIRST NAME\nAda') });
  await expect(page.getByText('File ready', { exact: true })).toBeVisible();
  const second = await context.newPage();
  await second.goto('/bulk-reg');
  await expect(second.getByLabel('School index', { exact: true })).toHaveValue('914');
  await expect(second.getByLabel('School name fetched')).toHaveValue('Test School');
  await expect(second.getByText('File ready', { exact: true })).toBeVisible();
  await second.getByRole('button', { name: 'Generate preview' }).click();
  await expect(page.getByRole('region', { name: 'Output preview', exact: true })).toBeVisible();
  await second.reload();
  await expect(second.getByRole('region', { name: 'Output preview', exact: true })).toBeVisible();
  const download = second.waitForEvent('download');
  await second.getByRole('button', { name: 'Download XLSX' }).click();
  expect((await download).suggestedFilename()).toBe('bulk-registration-914.xlsx');
  await page.getByRole('button', { name: 'Clear file', exact: true }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Confirm', exact: true }).click();
  await expect(second.getByRole('region', { name: 'Output preview', exact: true })).toHaveCount(0);
  await expect(second.getByRole('button', { name: 'Generate preview' })).toBeDisabled();
  await second.locator('summary').filter({ hasText: 'Use a file path instead' }).click();
  await second.getByLabel('File path', { exact: true }).fill('C:\\data\\shared.csv');
  // Unsubmitted drafts belong to the editing tab; persisted files are shared.
  await expect(page.getByLabel('File path', { exact: true })).toHaveValue('');
  await second.getByRole('button', { name: 'Reset bulk registration' }).click();
  await expect(second.getByRole('dialog')).toContainText('Reset bulk registration?');
  await second.getByRole('dialog').getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(second.getByRole('dialog')).not.toBeVisible();
  await expect(second.getByLabel('School index', { exact: true })).toHaveValue('914');
  await second.getByRole('button', { name: 'Reset bulk registration' }).click();
  await second.getByRole('dialog').getByRole('button', { name: 'Confirm', exact: true }).click();
  await expect(page.getByLabel('School index', { exact: true })).toHaveValue('');
  await expect(page.getByLabel('File path', { exact: true })).toHaveValue('');
  await expect(page.getByLabel('School name fetched')).toHaveCount(0);
});

test('a delayed verification cannot restore a workspace reset in another tab', async ({ page, context }) => {
  let release, captured;
  const gate = new Promise(resolve => { release = resolve; });
  const completed = new Promise(resolve => { captured = resolve; });
  await page.route('**/bulk-reg/school', async route => {
    const response = await route.fetch();
    captured();
    await gate;
    await route.fulfill({ response });
  });
  await page.goto('/bulk-reg');
  const second = await context.newPage();
  await second.goto('/bulk-reg');
  await page.getByLabel('School index', { exact: true }).fill('914');
  const started = page.waitForRequest('**/bulk-reg/school');
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await started;
  await completed;
  await second.reload();
  await expect(second.getByLabel('School name fetched')).toHaveValue('Test School');
  await second.getByRole('button', { name: 'Reset bulk registration' }).click();
  await second.getByRole('dialog').getByRole('button', { name: 'Confirm', exact: true }).click();
  await expect(page.getByLabel('School index', { exact: true })).toHaveValue('');
  release();
  await expect(page.getByRole('alert')).toContainText('changed in another tab');
  await expect(page.getByLabel('School name fetched')).toHaveCount(0);
  await expect(second.getByLabel('School name fetched')).toHaveCount(0);
});

test('focus preserves drafts and restores committed changes without BroadcastChannel', async ({ page, context }) => {
  await context.addInitScript(() => { window.BroadcastChannel = class { constructor() { throw new Error('Unavailable'); } }; });
  await page.goto('/bulk-reg');
  await page.getByLabel('School index', { exact: true }).pressSequentially('1234567890');
  await expect(page.getByLabel('School index', { exact: true })).toHaveValue('1234567890');
  await page.locator('summary').filter({ hasText: 'Use a file path instead' }).click();
  await page.getByLabel('File path', { exact: true }).pressSequentially('C:\\data\\students.csv');
  await expect(page.getByLabel('File path', { exact: true })).toHaveValue('C:\\data\\students.csv');
  const refreshed = page.waitForResponse('**/bulk-reg/workspace');
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await refreshed;
  await expect(page.getByLabel('School index', { exact: true })).toHaveValue('1234567890');
  await expect(page.getByLabel('File path', { exact: true })).toHaveValue('C:\\data\\students.csv');
  const second = await context.newPage();
  await second.goto('/bulk-reg');
  await expect(second.getByLabel('School index', { exact: true })).toHaveValue('');
  await second.getByLabel('School index', { exact: true }).fill('914');
  await second.getByRole('button', { name: 'Verify school index' }).click();
  await expect(second.getByLabel('School name fetched')).toHaveValue('Test School');
  // Reload deliberately discards this tab's drafts and restores committed state.
  await page.reload();
  await expect(page.getByLabel('School index', { exact: true })).toHaveValue('914');
  await second.getByLabel('Upload registration file').setInputFiles({ name: 'shared.csv', mimeType: 'text/csv', buffer: Buffer.from('FIRST NAME\nAda') });
  await expect(second.getByText('File ready', { exact: true })).toBeVisible();
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await expect(page.getByText('shared.csv', { exact: true }).first()).toBeVisible();
});

test('blocked browser storage produces an actionable error', async ({ page }) => {
  await page.route('**/api/v1/bulk-reg/workspace', route => route.abort());
  await page.goto('/bulk-reg');
  await expect(page.getByRole('alert')).toContainText('Could not load the bulk registration workspace');
  await expect(page.getByRole('button', { name: 'Generate preview' })).toBeDisabled();
});

test('a delayed workspace refresh cannot undo successful verification', async ({ page }) => {
  await page.goto('/bulk-reg');
  await expect(page.getByLabel('School index', { exact: true })).toBeEnabled();
  let release, captured;
  const gate = new Promise(resolve => { release = resolve; });
  const completed = new Promise(resolve => { captured = resolve; });
  await page.route('**/bulk-reg/workspace', async route => {
    const response = await route.fetch();
    captured();
    await gate;
    await route.fulfill({ response });
  });
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await completed;
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await expect(page.getByLabel('School name fetched')).toHaveValue('Test School');
  const refreshed = page.waitForResponse('**/bulk-reg/workspace');
  release();
  await (await refreshed).finished();
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  await expect(page.getByLabel('School index', { exact: true })).toHaveValue('914');
  await expect(page.getByLabel('School name fetched')).toHaveValue('Test School');
  // The revision must also remain current, otherwise this mutation receives 409.
  await page.getByLabel('Upload registration file').setInputFiles({ name: 'students.csv', mimeType: 'text/csv', buffer: Buffer.from('FIRST NAME\nAda') });
  await expect(page.getByText('File ready', { exact: true })).toBeVisible();
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test('successful verification recovers from an overlapping failed refresh', async ({ page }) => {
  await page.goto('/bulk-reg');
  const index = page.getByLabel('School index', { exact: true });
  await expect(index).toBeEnabled();
  let release, captured;
  const gate = new Promise(resolve => { release = resolve; });
  const completed = new Promise(resolve => { captured = resolve; });
  await page.route('**/bulk-reg/school', async route => {
    const response = await route.fetch();
    captured();
    await gate;
    await route.fulfill({ response });
  });
  await index.fill('914');
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await completed;
  await page.route('**/bulk-reg/workspace', route => route.fulfill({
    status: 503, json: { detail: 'Temporary refresh failure' },
  }));
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await expect(page.getByRole('alert')).toContainText('Could not load');
  release();
  await expect(page.getByLabel('School name fetched')).toHaveValue('Test School');
  await expect(index).toBeEnabled();
  await expect(page.getByRole('alert')).toHaveCount(0);
  // No reload or extra refresh should be needed to use the workspace again.
  await page.getByLabel('Upload registration file').setInputFiles({
    name: 'students.csv', mimeType: 'text/csv', buffer: Buffer.from('FIRST NAME\nAda'),
  });
  await expect(page.getByText('File ready', { exact: true })).toBeVisible();
});

test('Excel working sheet controls preview, download and cross-tab state', async ({ page, context }) => {
  const buffer = execFileSync(resolve('../backend/.venv/Scripts/python.exe'), ['-c',
    "import sys; from io import BytesIO; from openpyxl import Workbook; w=Workbook(); w.active.title='Empty'; s=w.create_sheet('Students'); s.append(['FIRST NAME']); s.append(['Ada']); t=w.create_sheet('Other'); t.append(['FIRST NAME']); t.append(['Grace']); b=BytesIO(); w.save(b); sys.stdout.buffer.write(b.getvalue())"]);
  await page.goto('/bulk-reg');
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await expect(page.getByLabel('School name fetched')).toBeVisible();
  await page.getByLabel('Upload registration file').setInputFiles({ name: 'sheets.xlsx', mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', buffer });
  await expect(page.getByLabel('Working sheet')).toHaveValue('Empty');
  await page.getByLabel('Working sheet').selectOption('Students');
  await expect(page.getByLabel('Working sheet')).toHaveValue('Students');
  await page.getByRole('button', { name: 'Generate preview' }).click();
  await expect(page.getByRole('region', { name: 'Output preview', exact: true }).getByRole('cell', { name: 'Ada', exact: true })).toBeVisible();
  const second = await context.newPage();
  await second.goto('/bulk-reg');
  await expect(second.getByLabel('Working sheet')).toHaveValue('Students');
  const download = second.waitForEvent('download');
  await second.getByRole('button', { name: 'Download CSV' }).click();
  const downloaded = await download;
  expect(downloaded.suggestedFilename()).toBe('bulk-registration-914.csv');
  expect(await readFile(await downloaded.path(), 'utf8')).toContain('Ada');
  await second.getByLabel('Working sheet').selectOption('Empty');
  await expect(page.getByLabel('Working sheet')).toHaveValue('Empty');
  await expect(page.getByRole('region', { name: 'Output preview', exact: true }).getByRole('cell', { name: 'Ada', exact: true })).toBeVisible();
  await second.getByRole('button', { name: 'Generate preview' }).click();
  await expect(second.getByRole('alert')).toContainText('no data rows');
  await expect(page.getByRole('region', { name: 'Output preview', exact: true }).getByRole('cell', { name: 'Ada', exact: true })).toBeVisible();
  const oldDownload = second.waitForEvent('download');
  await second.getByRole('button', { name: 'Download CSV' }).click();
  expect(await readFile(await (await oldDownload).path(), 'utf8')).toContain('Ada');
  await second.getByLabel('Working sheet').selectOption('Other');
  await expect(second.getByLabel('Working sheet')).toHaveValue('Other');
  await second.getByRole('button', { name: 'Generate preview' }).click();
  await expect(page.getByRole('region', { name: 'Output preview', exact: true }).getByRole('cell', { name: 'Grace', exact: true })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Output preview', exact: true }).getByRole('cell', { name: 'Ada', exact: true })).toHaveCount(0);
});
