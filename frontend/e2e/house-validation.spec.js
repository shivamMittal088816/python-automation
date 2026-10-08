import { test, expect } from './fixtures/browser-audit';

test('unresolved houses block final export; corrected houses export as IDs', async ({ page }) => {
  await page.goto('/bulk-reg');
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Verify school index', exact: true }).click();
  await expect(page.getByLabel('School name fetched')).toBeVisible();
  const input = house => ({ name: 'houses.csv', mimeType: 'text/csv',
    buffer: Buffer.from(`FIRST NAME,FULL NAME,Section,Class Number,GENDER,house\nBob,Bob Smith,A,Class I,Male,${house}`) });
  await page.getByLabel('Upload registration file').setInputFiles(input('Unknown'));
  // Intentionally skip optional input sanity: final verification must still protect downloads.
  await page.getByRole('button', { name: 'Generate preview', exact: true }).click();
  await page.getByRole('button', { name: 'Bulk-reg verify', exact: true }).click();
  await expect(page.getByText('Every supplied house resolves to a database index', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Download CSV', exact: true })).toBeDisabled();
  await page.reload();
  await page.getByRole('button', { name: 'Bulk-reg verify', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Download CSV', exact: true })).toBeDisabled();
  await page.getByLabel('Upload registration file').setInputFiles(input('Blue'));
  await page.getByRole('button', { name: 'Generate preview', exact: true }).click();
  await page.getByRole('button', { name: 'Bulk-reg verify', exact: true }).click();
  const downloadButton = page.getByRole('button', { name: 'Download CSV', exact: true });
  await expect(downloadButton).toBeEnabled();
  const downloaded = page.waitForEvent('download');
  await downloadButton.click();
  const download = await downloaded;
  const { readFile } = await import('node:fs/promises');
  const csv = await readFile(await download.path(), 'utf8');
  const [header, row] = csv.trim().split(/\r?\n/).map(line => line.split(','));
  expect(row[header.indexOf('house')]).toBe('12');
});
