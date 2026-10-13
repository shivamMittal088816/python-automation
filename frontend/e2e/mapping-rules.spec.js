import { test, expect } from './fixtures/browser-audit';

test('header help opens readable mapping rules without running mapping', async ({ page }) => {
  const runs = [];
  page.on('request', request => {
    if (request.method() === 'POST' && /\/run$/.test(new URL(request.url()).pathname)) runs.push(request.url());
  });
  await page.goto('/admission_file_page');
  await page.getByRole('link', { name: 'Mapping rules / Help', exact: true }).click();
  await expect(page).toHaveURL(/\/bulk-reg\/rules\?from=mapping/);
  await expect(page.getByRole('heading', { name: 'Complete student mapping rules', exact: true })).toBeVisible();
  for (const title of ['Admission Mapping Rules', 'Email Mapping Rules', 'Full Name + Class Concatenation Rules']) {
    await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
  }
  await expect(page.getByRole('region', { name: 'Sanity Check Rules', exact: true })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Complete student mapping rules', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Back to mapping' }).click();
  await expect(page.getByRole('heading', { name: 'Admission File Mapping' })).toBeVisible();
  expect(runs).toEqual([]);
});
