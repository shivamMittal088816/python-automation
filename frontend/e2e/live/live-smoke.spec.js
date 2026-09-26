import { test, expect } from '../fixtures/browser-audit';
import { fileURLToPath } from 'node:url';
import { readFile } from 'node:fs/promises';

const schoolIndex = process.env.LIVE_SCHOOL_INDEX || '914';

test('live SQL verification, conversion, download, errors and cross-tab clearing', async ({ page, context }) => {
  await page.goto('/bulk-reg');
  await page.getByLabel('School index', { exact: true }).fill(schoolIndex);
  const verified = page.waitForResponse(response => response.url().includes(`/bulk-reg/schools/${schoolIndex}`));
  await page.getByRole('button', { name: 'Verify school index' }).click();
  const response = await verified;
  expect(response.status()).toBe(200);
  expect(response.headers()['x-request-id']).toBeTruthy();
  await expect(page.getByLabel('School name fetched')).not.toHaveValue('');
  await page.getByLabel('Upload registration file').setInputFiles({ name: 'synthetic-live-audit.csv',
    mimeType: 'text/csv', buffer: Buffer.from('FIRST NAME,admission_number\nAuditSynthetic,0001') });
  await page.getByRole('button', { name: 'Generate preview' }).click();
  const output = page.getByRole('region', { name: 'Output preview', exact: true });
  await expect(output.getByRole('cell', { name: 'AuditSynthetic', exact: true })).toBeVisible();
  const second = await context.newPage();
  await second.goto('/bulk-reg');
  await expect(second.getByRole('region', { name: 'Output preview', exact: true })).toBeVisible();
  const download = second.waitForEvent('download');
  await second.getByRole('button', { name: 'Download CSV' }).click();
  expect(await readFile(await (await download).path(), 'utf8')).toContain('AuditSynthetic');
  await second.getByRole('button', { name: 'Clear file', exact: true }).click();
  await second.getByRole('dialog').getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(output).toBeVisible();
  await second.getByRole('button', { name: 'Clear file', exact: true }).click();
  await second.getByRole('dialog').getByRole('button', { name: 'Confirm', exact: true }).click();
  await expect(output).toHaveCount(0);
  const invalid = page.waitForResponse(response => response.url().endsWith('/bulk-reg/files'));
  await page.getByLabel('Upload registration file').setInputFiles({ name: 'empty.csv', mimeType: 'text/csv', buffer: Buffer.alloc(0) });
  expect((await invalid).status()).toBe(400);
  await expect(page.getByRole('alert')).toContainText('HTTP 400; request');
  await page.getByRole('button', { name: 'Reset bulk registration' }).click();
});

test('live mapping with synthetic files, page navigation and cross-tab invalidation', async ({ page, context }) => {
  await page.goto('/admission_file_page');
  await page.getByLabel('Add school file').setInputFiles(fileURLToPath(new URL('../fixtures/school.csv', import.meta.url)));
  await expect(page.getByText('Loaded: school.csv', { exact: true })).toBeVisible();
  await page.getByLabel('Add dump file').setInputFiles(fileURLToPath(new URL('../fixtures/dump.csv', import.meta.url)));
  await page.getByLabel('School index', { exact: true }).fill(schoolIndex);
  await page.getByRole('button', { name: 'Save school index', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Run mapping', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: 'Run mapping', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Preview matched', exact: true })).toBeVisible();
  const second = await context.newPage();
  await second.goto('/admission_file_page');
  await expect(second.getByRole('link', { name: 'Preview matched', exact: true })).toBeVisible();
  for (const route of ['/school_file_page', '/dump_file_page', '/admission_preview_page',
    '/email_mapping_page', '/full_name_class_mapping_page', '/mapping_rules_page']) {
    await page.goto(route);
    await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible();
    await expect(page.getByRole('alert')).toHaveCount(0);
  }
  await page.goto('/admission_file_page');
  await page.getByRole('button', { name: 'Clear school file', exact: true }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Confirm', exact: true }).click();
  await expect(second.getByRole('link', { name: 'Preview matched', exact: true })).toHaveCount(0);
  await expect(second.getByText('Loaded: school.csv', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Clear dump file', exact: true }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Confirm', exact: true }).click();
});
