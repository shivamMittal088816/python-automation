import { test, expect } from '@playwright/test';
import { fileURLToPath } from 'node:url';

const school = fileURLToPath(new URL('./fixtures/school.csv', import.meta.url));
const dump = fileURLToPath(new URL('./fixtures/dump.csv', import.meta.url));

test('all active pages remain readable at desktop, tablet and mobile widths', async ({ page }) => {
  test.setTimeout(120000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  async function capture(name) {
    await expect(page.locator('main h2')).toBeVisible();
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`${name}.png`), fullPage: true });
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/school_file_page');
  await expect(page.getByRole('heading', { name: 'No school file loaded' })).toBeVisible();
  await capture('empty-school');
  await page.goto('/admission_file_page');
  await capture('admission-empty');
  await page.getByLabel('Add school file').setInputFiles({ name: 'School_records_with_a_very_long_filename_for_operations_review_September_2026.csv', mimeType: 'text/csv', buffer: await (await import('node:fs/promises')).readFile(school) });
  await expect(page.getByText(/^Loaded: School_records/)).toBeVisible();
  await page.getByLabel('Add dump file').setInputFiles(dump);
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Save school index', exact: true }).click();
  await expect(page.getByText('Saved school index: 914', { exact: true })).toBeVisible();
  await expect(page.getByLabel('School admission number column')).toBeVisible();
  await capture('admission-configured');
  await page.getByRole('button', { name: 'Run pass 1', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Preview matched', exact: true })).toBeVisible();
  await capture('admission-results');
  await page.goto('/email_mapping_page');
  await page.getByRole('button', { name: 'Run pass 1', exact: true }).click();
  await expect(page.getByLabel('Email result group')).toBeVisible();
  await capture('email-results');
  await page.goto('/full_name_class_mapping_page');
  await page.getByRole('button', { name: 'Run pass 1', exact: true }).click();
  await expect(page.getByLabel('Result group', { exact: true })).toBeVisible();
  await capture('full-name-results');
  for (const width of [1440, 820, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const route of ['admission_file', 'admission_preview', 'school_file', 'dump_file', 'email_mapping', 'email_dump', 'full_name_class_mapping']) {
      await page.goto(`/${route}_page`);
      await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible();
      await expect(page.getByRole('status').filter({ hasText: /Reading|Checking/ })).toHaveCount(0);
      await capture(`${route}-${width}`);
    }
  }
  await page.route('**/table-previews/school?**', async route => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Could not load school records. Please try again.' }) });
  });
  await page.goto('/school_file_page');
  await expect(page.getByRole('status').filter({ hasText: 'Reading file' })).toBeVisible();
  await capture('loading-mobile');
  await expect(page.getByRole('alert')).toBeVisible();
  await capture('error-mobile');
  expect(errors).toEqual([]);
});
