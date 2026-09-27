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
  await page.getByLabel('Upload registration file').setInputFiles({ name: 'students.csv', mimeType: 'text/csv', buffer: Buffer.from('id,name\n001,Student') });
  await expect(page.getByText('File uploaded successfully', { exact: true })).toBeVisible();
  await expect(page.getByText('students.csv', { exact: true }).first()).toBeVisible();
  await page.locator('summary').filter({ hasText: 'Input preview' }).click();
  await expect(page.getByRole('cell', { name: '001' })).toBeVisible();
  await page.getByRole('button', { name: 'Clear file' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  // Returning to the tab refreshes shared browser metadata without changing the loaded file.
  const focused = page.waitForResponse('**/bulk-reg/workspace');
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await (await focused).finished();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('dialog').getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(page.getByRole('cell', { name: '001' })).toBeVisible();
  await page.getByRole('button', { name: 'Clear file' }).click();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(page.getByRole('cell', { name: '001' })).toBeVisible();
  await page.getByRole('button', { name: 'Clear file' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Confirm', exact: true }).click();
  await page.getByLabel('File path', { exact: true }).fill(resolve('e2e/fixtures/school.csv'));
  await page.getByRole('button', { name: 'Load file', exact: true }).click();
  await page.locator('summary').filter({ hasText: 'Input preview' }).click();
  await expect(page.getByRole('cell', { name: '001' }).first()).toBeVisible();
  expect(mappingRequests).toEqual([]);
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
  await expect(page.getByText('File loaded', { exact: false })).toBeVisible();
  const second = await context.newPage();
  await second.goto('/bulk-reg');
  await expect(second.getByLabel('School index', { exact: true })).toHaveValue('914');
  await expect(second.getByLabel('School name fetched')).toHaveValue('Test School');
  await expect(second.getByText('File loaded', { exact: false })).toBeVisible();
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
  await expect(second.getByText('File uploaded successfully', { exact: true })).toBeVisible();
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
  await expect(page.getByText('File uploaded successfully', { exact: true })).toBeVisible();
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
  await expect(page.getByText('File uploaded successfully', { exact: true })).toBeVisible();
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
