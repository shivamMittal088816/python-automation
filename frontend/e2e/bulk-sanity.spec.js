import { test, expect } from './fixtures/browser-audit';

test('sanity check scans all input rows and clears when the file changes', async ({ page }) => {
  await page.goto('/bulk-reg');
  const check = page.getByRole('button', { name: 'Sanity check', exact: true });
  await expect(check).toBeDisabled();
  await expect(page.getByLabel('Upload registration file')).toBeEnabled();
  const rows = Array.from({ length: 25 }, (_, i) => `Ada,Ada Lovelace,A,Class I,Female,ada${i}@example.com`);
  rows[24] = ' ,,,, , ADA0@EXAMPLE.COM ';
  await page.getByLabel('Upload registration file').setInputFiles({
    name: 'sanity.csv', mimeType: 'text/csv',
    buffer: Buffer.from(`FIRST NAME,FULL NAME,Section,Class Number,GENDER,EMAIL\n${rows.join('\n')}`),
  });
  await expect(page.getByText('File ready', { exact: true })).toBeVisible();
  await check.click();
  const panel = page.getByRole('region', { name: 'Input sanity check', exact: true });
  await expect(panel.getByRole('status')).toHaveAccessibleName('25 records checked · 2 with issues · 23 passed');
  await expect(panel.locator('.bulk-sanity-icon.is-failed')).toHaveCount(6);
  await expect(panel.locator('tbody tr')).toHaveCount(2);
  await expect(panel.getByRole('columnheader')).toHaveText([
    'Row number', 'FIRST NAME', 'FULL NAME', 'Section', 'Class Number', 'GENDER', 'EMAIL', 'Status',
  ]);
  await expect(panel.getByRole('cell', { name: 'ada1@example.com', exact: true })).toHaveCount(0);
  await expect(panel.getByRole('cell', { name: '26', exact: true })).toBeVisible();
  await expect(panel.getByRole('cell').filter({ hasText: 'First name missing' })).toContainText('Duplicate email in input file');
  await expect(panel.getByRole('button', { name: 'Download trimmed CSV' })).toHaveCount(0);
  await page.getByLabel('Upload registration file').setInputFiles({
    name: 'clean.csv', mimeType: 'text/csv',
    buffer: Buffer.from('FIRST NAME,FULL NAME,Section,Class Number,GENDER,EMAIL\nAda,Ada Lovelace,A,Class I,Female,ada@example.com'),
  });
  await expect(panel.getByRole('table')).toHaveCount(0);
  await check.click();
  await expect(panel.locator('.bulk-sanity-icon.is-passed')).toHaveCount(11);
  await expect(panel.getByRole('status')).toHaveAccessibleName('1 records checked · 0 with issues · 1 passed');
  await expect(panel.locator('tbody tr')).toHaveCount(0);
  await expect(panel.getByText('No records with issues.', { exact: true })).toBeVisible();
});
