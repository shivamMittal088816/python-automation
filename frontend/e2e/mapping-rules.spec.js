import { test, expect } from '@playwright/test';

test('header help opens readable mapping rules without running mapping', async ({ page }) => {
  const runs = [];
  page.on('request', request => {
    if (request.method() === 'POST' && /\/run$/.test(new URL(request.url()).pathname)) runs.push(request.url());
  });
  await page.goto('/admission_file_page');
  await page.getByRole('link', { name: 'Mapping rules / Help', exact: true }).click();
  await expect(page).toHaveURL(/\/mapping_rules_page/);
  await expect(page.getByRole('heading', { name: 'Mapping rules', exact: true })).toBeVisible();
  for (const title of ['1. Admission mapping', '2. Email mapping', '3. Full name + class concatenation']) {
    await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
  }
  await expect(page.locator('main ul')).toHaveCount(6);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Mapping rules', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Back to admission mapping' }).click();
  await expect(page.getByRole('heading', { name: 'Admission File Mapping' })).toBeVisible();
  expect(runs).toEqual([]);
});
