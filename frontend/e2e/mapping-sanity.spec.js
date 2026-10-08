import { test, expect } from './fixtures/browser-audit';
import { resolve } from 'node:path';

test('mapping headers detect duplicate emails without false missing-field errors', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Add school file', { exact: true }).setInputFiles(resolve('e2e/fixtures/school.csv'));
  await page.getByRole('button', { name: 'Sanity check', exact: true }).click();
  const panel = page.getByRole('region', { name: 'Input sanity check', exact: true });
  await expect(panel.getByRole('status')).toHaveAccessibleName('5 records checked · 2 with issues · 3 passed');
  await expect(panel.getByText('Duplicate email in input file', { exact: true })).toHaveCount(2);
  await expect(panel.getByText('First name missing', { exact: true })).toHaveCount(0);
  await expect(panel.getByText('Section missing', { exact: true })).toHaveCount(0);
});

test('mapping sanity follows unsaved first-name column selection', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Add school file', { exact: true }).setInputFiles({
    name: 'selected.csv', mimeType: 'text/csv',
    buffer: Buffer.from('admission_number,first_name,Chosen\n001,Bad1,Ada'),
  });
  await page.getByLabel('Fetch from SQL', { exact: true }).check();
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Fetch dump data', exact: true }).click();
  const check = page.getByRole('button', { name: 'Sanity check', exact: true });
  await check.click();
  const panel = page.getByRole('region', { name: 'Input sanity check', exact: true });
  await expect(panel.getByRole('status')).toHaveAccessibleName('1 records checked · 1 with issues · 0 passed');
  await page.getByLabel('First name column in school file', { exact: true }).selectOption('Chosen');
  await expect(panel.getByRole('status')).toHaveCount(0);
  await check.click();
  await expect(panel.getByText('All students passed', { exact: true })).toBeVisible();
});

test('mapping sanity checks school records and clears results after replacement', async ({ page }) => {
  await page.goto('/');
  const check = page.getByRole('button', { name: 'Sanity check', exact: true });
  await expect(check).toBeDisabled();
  await page.getByLabel('Add school file', { exact: true }).setInputFiles({
    name: 'school.csv', mimeType: 'text/csv',
    buffer: Buffer.from('FIRST NAME,FULL NAME,Section,Class Number,GENDER,EMAIL\nAda,Ada Lovelace,A,Class I,Female,ada@example.com\nBob1,Bob Smith,,Unknown,M,invalid'),
  });
  await check.click();
  const panel = page.getByRole('region', { name: 'Input sanity check', exact: true });
  await expect(panel.getByRole('status')).toHaveAccessibleName('2 records checked · 1 with issues · 1 passed');
  await expect(panel.locator('tbody tr')).toHaveCount(1);
  await expect(panel.getByText('Section missing', { exact: true })).toBeVisible();
  await page.getByLabel('Replace school file', { exact: true }).setInputFiles({
    name: 'clean.csv', mimeType: 'text/csv',
    buffer: Buffer.from('FIRST NAME,FULL NAME,Section,Class Number,GENDER\nAda,Ada Lovelace,A,Class I,Female'),
  });
  await expect(panel.getByRole('table')).toHaveCount(0);
  await check.click();
  await expect(panel.getByText('All students passed', { exact: true })).toBeVisible();
});
