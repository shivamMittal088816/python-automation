import { test, expect } from './fixtures/browser-audit';
import { fileURLToPath } from 'node:url';

const school = fileURLToPath(new URL('./fixtures/school.csv', import.meta.url));

test('clear mapping inputs removes dependent results across tabs and permits reloading', async ({ page, context }) => {
  await page.goto('/admission_file_page');
  await page.getByLabel('Add school file').setInputFiles(school);
  await page.getByRole('radio', { name: 'Fetch from SQL', exact: true }).check();
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Fetch dump data', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Run mapping', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: 'Run mapping', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Preview matched', exact: true })).toBeVisible();
  const second = await context.newPage();
  await second.goto('/dump_file_page');
  await expect(second.getByRole('button', { name: 'Clear dump file' })).toBeVisible();
  await page.getByRole('button', { name: 'Clear dump file' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('dialog').getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(page.getByText('Loaded: school.csv', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Clear dump file' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Confirm', exact: true }).click();
  await expect(second.getByText('No student dump loaded', { exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Preview matched', exact: true })).toHaveCount(0);
  await expect(page.getByText('Loaded: school.csv', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Clear school file' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Confirm', exact: true }).click();
  await expect(page.getByText('Loaded: school.csv', { exact: true })).toHaveCount(0);
  await page.getByLabel('Add school file').setInputFiles(school);
  await expect(page.getByText('Loaded: school.csv', { exact: true })).toBeVisible();
  await page.goto('/school_file_page');
  await page.getByRole('button', { name: 'Clear school file' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Confirm', exact: true }).click();
  await expect(page.getByText('No school file loaded', { exact: true })).toBeVisible();
});
