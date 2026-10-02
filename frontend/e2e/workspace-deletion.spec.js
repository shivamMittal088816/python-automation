import { test, expect } from './fixtures/browser-audit';

const api = 'http://127.0.0.1:8123/api/v1';
const origin = 'http://127.0.0.1:5174';

for (const workflow of ['mapping', 'bulk_registration']) {
  test(`deleting the last ${workflow} workspace opens a fresh workspace`, async ({ page, context }) => {
    const registered = await context.request.post(`${api}/auth/register`, {
      headers: { origin }, data: { name: 'Workspace Owner', email: `last-deletion-${crypto.randomUUID()}@example.com`, password: 'a memorable workspace deletion passphrase!' },
    });
    expect(registered.status()).toBe(201);
    const created = await context.request.post(`${api}/workspaces`, {
      headers: { origin }, data: { workflow, name: 'Last workspace' },
    });
    expect(created.status()).toBe(201);
    const oldId = (await created.json()).active_workspace_id;
    await page.goto(workflow === 'mapping' ? '/admission_file_page' : '/bulk-reg');
    const selector = page.getByLabel('Workspace selector', { exact: true });
    await expect(selector).toContainText('Last workspace');
    await selector.click();
    await page.getByRole('button', { name: 'Delete Last workspace', exact: true }).click();
    await page.getByRole('dialog', { name: 'Delete workspace?' }).getByRole('button', { name: 'Delete workspace', exact: true }).click();
    // The browser fixture completes first-use naming for newly created workspaces.
    await expect(selector).toContainText('My workspace');
    const listed = await context.request.get(`${api}/workspaces?workflow=${workflow}`);
    const spaces = await listed.json();
    expect(spaces.workspaces).toHaveLength(1);
    expect(spaces.active_workspace_id).not.toBe(oldId);
  });
}

test('owner can cancel, retry, and soft-delete inactive and active workspaces', async ({ page, context }, testInfo) => {
  const registered = await context.request.post(`${api}/auth/register`, {
    headers: { origin }, data: { name: 'Workspace Owner', email: `deletion-${crypto.randomUUID()}@example.com`, password: 'a memorable workspace deletion passphrase!' },
  });
  expect(registered.status()).toBe(201);
  for (const name of ['Keep workspace', 'Delete workspace']) {
    expect((await context.request.post(`${api}/workspaces`, { headers: { origin }, data: { workflow: 'mapping', name } })).status()).toBe(201);
  }
  await page.goto('/admission_file_page');
  const selector = page.getByLabel('Workspace selector', { exact: true });
  await expect(selector).toContainText('Delete workspace');
  await selector.click();
  for (const [label, width, height] of [['desktop', 1366, 640], ['mobile', 390, 640]]) {
    await page.setViewportSize({ width, height });
    await page.screenshot({ path: testInfo.outputPath(`switcher-${label}.png`) });
  }
  await page.getByRole('button', { name: 'Delete Keep workspace', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Delete workspace?' });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('button', { name: 'Cancel', exact: true })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(selector).toBeFocused();
  await selector.click();
  await page.getByRole('button', { name: 'Delete Keep workspace', exact: true }).click();
  await dialog.getByRole('button', { name: 'Delete workspace', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await selector.click();
  await expect(page.getByRole('button', { name: 'Delete Keep workspace', exact: true })).toHaveCount(0);
  await expect(selector).toContainText('Delete workspace');
  await page.getByRole('button', { name: 'Create workspace', exact: true }).click();
  const createDialog = page.getByRole('dialog', { name: 'Create your workspace' });
  await createDialog.getByRole('textbox', { name: /^Workspace name/ }).fill('Replacement');
  await createDialog.getByRole('button', { name: 'Create workspace', exact: true }).click();
  await expect(selector).toContainText('Replacement');
  await selector.click();
  await page.getByRole('button', { name: 'Delete Replacement', exact: true }).click();
  let failed = false;
  await page.route('**/api/v1/workspaces/*', route => {
    if (!failed && route.request().method() === 'DELETE') {
      failed = true;
      return route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Please try again.' }) });
    }
    return route.continue();
  });
  await dialog.getByRole('button', { name: 'Delete workspace', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('Please try again.');
  await dialog.getByRole('button', { name: 'Delete workspace', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await expect(selector).toContainText('Delete workspace');
  await selector.click();
  await expect(page.getByRole('button', { name: 'Delete Replacement', exact: true })).toHaveCount(0);
});
