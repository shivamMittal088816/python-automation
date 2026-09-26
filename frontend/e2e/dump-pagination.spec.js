import { test, expect } from './fixtures/browser-audit';

test('dump pages all rows and searches beyond the visible page', async ({ page }) => {
  const csv = 'admission_number,user_firstname,user_name,user_edu_class,user_edu_major\n' +
    Array.from({ length: 120 }, (_, i) => `${i + 1},Student${i + 1},user${i + 1},3,A`).join('\n');
  await page.goto('/admission_file_page');
  await page.getByLabel('Add dump file').setInputFiles({ name: 'large-dump.csv', mimeType: 'text/csv', buffer: Buffer.from(csv) });
  await expect(page.getByText('Loaded: large-dump.csv', { exact: true })).toBeVisible();
  const response = page.waitForResponse(r => r.url().includes('/table-previews/dump?') && r.status() === 200);
  await page.getByRole('link', { name: 'Dump file', exact: true }).click();
  const data = await (await response).json();
  expect(data.rows).toHaveLength(50);
  expect(data.total).toBe(120);
  await expect(page.getByLabel('Rows per page')).toHaveValue('50');
  await expect(page.getByText('Page 1 of 3', { exact: true })).toBeVisible();
  await page.getByLabel('Page', { exact: true }).fill('3');
  await expect(page.getByRole('cell', { name: 'Student120', exact: true })).toBeVisible();
  await page.getByLabel('Rows per page').selectOption('25');
  await expect(page.getByText('Page 1 of 5', { exact: true })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Student120', exact: true })).toHaveCount(0);
  await page.getByLabel('Search all columns').fill('Student120');
  await expect(page.getByRole('cell', { name: 'Student120', exact: true })).toBeVisible();
  await expect(page.getByText('Student records · 1 of 120', { exact: true })).toBeVisible();
  await page.getByLabel('Search all columns').fill('');
  await expect(page.getByText('Page 1 of 5', { exact: true })).toBeVisible();
});
