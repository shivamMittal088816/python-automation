import { test, expect } from './fixtures/browser-audit';

test('reopening the root restores the session and displays the mapping page', async ({ page, context }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Admission File Mapping' })).toBeVisible();
  await page.getByLabel('Fetch from SQL', { exact: true }).check();
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Fetch dump data' }).click();
  await expect(page).toHaveURL(/\/admission_file_page\?school=914$/);
  await expect(page.getByText('Test School', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByLabel('School index', { exact: true })).toHaveValue('914');
  // An unsubmitted search must not replace the last successfully fetched index.
  await page.getByLabel('School index', { exact: true }).fill('999');
  await page.reload();
  await expect(page.getByLabel('School index', { exact: true })).toHaveValue('914');
  await page.close();

  const reopened = await context.newPage();
  for (const url of ['/', '/?school=914']) {
    await reopened.goto(url);
    await expect(reopened).toHaveURL(/\/admission_file_page\?school=914$/);
    await expect(reopened.getByRole('heading', { name: 'Admission File Mapping' })).toBeVisible();
    await expect(reopened.getByText('Test School', { exact: true })).toBeVisible();
  }
  await reopened.goto('/?page=admission-preview&school=914');
  await expect(reopened.getByRole('heading', { name: 'Admission Results Preview' })).toBeVisible();
});
