import { test, expect } from './fixtures/browser-audit';

test('generate and copy a workflow link, and regenerate when options change', async ({ page }) => {
  const requests = [];
  await page.route('**/api/v1/invitations', async route => {
    const payload = route.request().postDataJSON();
    requests.push(payload);
    const path = payload.workflow === 'bulk_registration' ? '/i/b' : '/i';
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ invitation_url: `http://127.0.0.1:5173${path}/test-token-${requests.length}`, expires_at: '2026-10-04T00:00:00Z' }),
    });
  });
  await page.setViewportSize({ width: 1366, height: 633 });
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: async value => { window.copiedInvitationLink = value; } },
    });
  });
  await page.goto('/admission_file_page');
  await page.getByRole('button', { name: 'Open sidebar', exact: true }).click();
  await page.getByRole('button', { name: 'Invite to workflow' }).click();
  const dialog = page.getByRole('dialog');
  const generate = dialog.getByRole('button', { name: 'Generate invitation link' });
  const copy = dialog.getByRole('button', { name: 'Copy invitation link' });
  const input = dialog.getByLabel('Invitation link', { exact: true });
  await expect(dialog.locator('input[type=email]')).toHaveCount(0);
  await expect(dialog.getByRole('checkbox')).toHaveCount(0);
  await expect(copy).toBeDisabled();
  expect(await generate.evaluate(element => {
    const bounds = element.getBoundingClientRect();
    return bounds.top >= 0 && bounds.bottom <= innerHeight;
  })).toBe(true);
  await generate.click();
  const link = new URL(await input.inputValue());
  expect(link.pathname).toBe('/i/test-token-1');
  expect(requests[0]).toEqual({ workflow: 'mapping', permission: 'editor' });
  await copy.click();
  await expect(dialog.getByRole('status')).toHaveText('Link copied');
  expect(await page.evaluate(() => window.copiedInvitationLink)).toBe(link.href);
  await dialog.getByRole('radio', { name: /Viewer/ }).check();
  await expect(input).toHaveValue('');
  await expect(copy).toBeDisabled();
  await expect(generate).toBeEnabled();
  await generate.click();
  const viewerLink = new URL(await input.inputValue());
  expect(viewerLink.pathname).toBe('/i/test-token-2');
  expect(requests[1]).toEqual({ workflow: 'mapping', permission: 'viewer' });
  await dialog.getByRole('radio', { name: /Bulk registration/ }).check();
  await generate.click();
  const bulkLink = new URL(await input.inputValue());
  expect(bulkLink.pathname).toBe('/i/b/test-token-3');
  expect(requests[2]).toEqual({ workflow: 'bulk_registration', permission: 'viewer' });
  await page.setViewportSize({ width: 390, height: 650 });
  expect(await generate.evaluate(element => element.getBoundingClientRect().bottom <= innerHeight)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.evaluate(() => {
    navigator.clipboard.writeText = async () => { throw new Error('Clipboard unavailable'); };
  });
  await copy.click();
  await expect(dialog.getByRole('status')).toContainText('Copy the selected link manually');
  await expect(input).toBeFocused();
  await dialog.getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(dialog).toHaveCount(0);
});

test('short invitation links preserve the token and open the correct workflow', async ({ page }) => {
  await page.goto('/i/test-mapping-token');
  await expect(page).toHaveURL(/\/admission_file_page\?invite=test-mapping-token$/);
  await page.goto('/i/b/test-bulk-token');
  await expect(page).toHaveURL(/\/bulk-reg\?invite=test-bulk-token$/);
});
