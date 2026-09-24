import { test, expect } from '@playwright/test';

test('startup shimmer matches the responsive shell and disappears after session loading', async ({ page }) => {
  let release;
  const pending = new Promise(resolve => { release = resolve; });
  await page.route('**/mapping/session', async route => {
    await pending;
    await route.continue();
  });
  await page.goto('/admission_file_page');
  const skeleton = page.getByRole('status', { name: 'Loading workspace' });
  await expect(skeleton).toBeVisible();
  await expect(skeleton.getByRole('button')).toHaveCount(0);
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`startup-${width}.png`), fullPage: true });
  }
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await expect.poll(() => page.locator('.workspace-placeholder').first().evaluate(element => getComputedStyle(element, '::after').animationName)).toBe('none');
  release();
  await expect(page.getByRole('heading', { name: 'Admission File Mapping' })).toBeVisible();
  await expect(skeleton).toHaveCount(0);
});

test('session failure replaces shimmer with an error and retry restores loading', async ({ page }) => {
  await page.route('**/mapping/session', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Session unavailable' }) }));
  await page.goto('/');
  await expect(page.getByRole('alert')).toHaveText('Session unavailable');
  await expect(page.getByRole('status', { name: 'Loading workspace' })).toHaveCount(0);
  await page.unroute('**/mapping/session');
  await page.getByRole('button', { name: 'Retry', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Admission File Mapping' })).toBeVisible();
});
