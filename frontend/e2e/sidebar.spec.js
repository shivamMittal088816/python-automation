import { test, expect } from './fixtures/browser-audit';

for (const width of [1440, 390]) {
  test(`mapping sidebar toggles without reserving space at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/admission_file_page');
    const open = page.getByRole('button', { name: 'Open sidebar', exact: true });
    const navigation = page.getByRole('navigation', { name: 'Main navigation' });
    await expect(open).toHaveAttribute('aria-expanded', 'false');
    await expect(navigation).toBeHidden();
    const closedBounds = await page.locator('main').boundingBox();
    expect(closedBounds.x).toBe(0);
    expect(closedBounds.width).toBe(width);
    await expect(page.getByLabel(/^(Add|Replace) school file$/)).toBeEnabled();
    await page.getByLabel(/^(Add|Replace) school file$/).setInputFiles({
      name: 'sidebar-check.csv', mimeType: 'text/csv',
      buffer: Buffer.from('admission_number,first_name\n001,Ada'),
    });
    await expect(page.getByText('sidebar-check.csv', { exact: true }).first()).toBeVisible();
    await open.click();
    const close = page.getByRole('button', { name: 'Close sidebar', exact: true });
    await expect(close).toHaveAttribute('aria-expanded', 'true');
    await expect(navigation).toBeVisible();
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`sidebar-open-${width}.png`) });
    await close.click();
    await expect(navigation).toBeHidden();
    await expect(page.getByText('sidebar-check.csv', { exact: true }).first()).toBeVisible();
    expect((await page.locator('main').boundingBox()).width).toBe(width);
    await page.screenshot({ path: test.info().outputPath(`sidebar-closed-${width}.png`) });
    await open.click();
    await page.keyboard.press('Escape');
    await expect(open).toBeFocused();
    await expect(navigation).toBeHidden();
    if (width < 768) {
      await open.click();
      await page.getByRole('button', { name: 'Dismiss sidebar', exact: true }).click({ position: { x: width - 10, y: 100 } });
      await expect(navigation).toBeHidden();
    }
    await open.click();
    await navigation.getByRole('link', { name: 'School file', exact: true }).click();
    await expect(page).toHaveURL(/school_file_page/);
    await expect(navigation).toBeHidden();
    await expect(open).toBeFocused();
  });
}
