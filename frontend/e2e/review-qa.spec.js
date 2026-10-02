import { test, expect } from './fixtures/browser-audit';

const api = 'http://127.0.0.1:8123/api/v1';
const origin = 'http://127.0.0.1:5174';

async function openInvite(page) {
  await page.getByRole('button', { name: 'Open sidebar', exact: true }).click();
  await page.getByRole('button', { name: /^Invite to workflow/ }).click();
  return page.getByRole('dialog');
}

test('stale mapping tab cannot issue invitations or read another workspace member list', async ({ page, context }) => {
  await page.goto('/admission_file_page');
  await expect(page.getByRole('button', { name: 'Open sidebar', exact: true })).toBeVisible();
  const created = await context.request.post(`${api}/workspaces`, { headers: { origin }, data: { workflow: 'mapping' } });
  expect(created.status()).toBe(201);
  const results = await page.evaluate(async () => {
    const { generateInvitation, getInvitedMembers } = await import('/src/services/invitations/api.js');
    const results = [];
    for (const action of [() => generateInvitation({ workflow: 'mapping', permission: 'viewer' }), () => getInvitedMembers('mapping')]) {
      try { await action(); results.push({ accepted: true }); }
      catch (error) { results.push({ status: error.status, conflict: error.selectionConflict }); }
    }
    return results;
  });
  expect(results).toEqual([{ status: 409, conflict: true }, { status: 409, conflict: true }]);
});

test('invitation options and copying are locked while generating a link', async ({ page }) => {
  await page.goto('/admission_file_page');
  const dialog = await openInvite(page);
  let release;
  const waiting = new Promise(resolve => { release = resolve; });
  await page.route('**/api/v1/invitations', async route => { await waiting; await route.continue(); });
  try {
    await dialog.getByRole('button', { name: 'Generate invitation link', exact: true }).click();
    await expect(dialog.getByRole('button', { name: 'Generating…', exact: true })).toBeDisabled();
    for (const radio of await dialog.getByRole('radio').all()) await expect(radio).toBeDisabled();
    await expect(dialog.getByRole('button', { name: 'Copy invitation link', exact: true })).toBeDisabled();
    await page.screenshot({ path: '../.test-temp/review-qa/invitation-pending-desktop.png' });
  } finally { release(); }
  await expect(dialog.getByLabel('Invitation link', { exact: true })).toHaveValue(/\/i\/[A-Za-z0-9_-]+$/);
  await expect(dialog.getByRole('radio').first()).toBeEnabled();
  await dialog.getByRole('button', { name: 'Cancel', exact: true }).click();
});

test('create workspace recovers when the dropdown list request fails', async ({ page, context }) => {
  await page.goto('/admission_file_page');
  await expect(page.getByLabel('Workspace selector', { exact: true })).toBeVisible();
  await page.route('**/api/v1/workspaces?workflow=mapping', route => route.fulfill({
    status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Temporary list failure.' }),
  }));
  await page.getByLabel('Workspace selector', { exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Could not load workspace details.');
  await page.unroute('**/api/v1/workspaces?workflow=mapping');
  const created = page.waitForResponse(response => response.url().endsWith('/api/v1/workspaces') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Create workspace', exact: true }).click();
  expect((await created).status()).toBe(201);
  await expect(page.getByRole('button', { name: 'Open sidebar', exact: true })).toBeVisible();
  const spaces = await (await context.request.get(`${api}/workspaces?workflow=mapping`)).json();
  expect(spaces.workspaces).toHaveLength(2);
});

test('bulk permission changes refresh the UI even without a file revision change', async ({ browser, context }, testInfo) => {
  expect((await context.request.post(`${api}/bulk-reg/workspace`, { headers: { origin } })).status()).toBe(200);
  const invitation = await context.request.post(`${api}/invitations`, {
    headers: { origin }, data: { workflow: 'bulk_registration', permission: 'editor' },
  });
  expect(invitation.status()).toBe(201);
  const token = (await invitation.json()).invitation_url.split('/').pop();
  const recipient = await browser.newContext();
  try {
    const me = await (await recipient.request.get(`${api}/auth/me`)).json();
    expect((await recipient.request.post(`${api}/invitations/join`, { headers: { origin }, data: { token } })).status()).toBe(200);
    const guest = await recipient.newPage();
    await guest.goto(`${origin}/bulk-reg`);
    await expect(guest.locator('input[type="file"]').first()).toBeEnabled();
    const changed = await context.request.post('http://127.0.0.1:8123/_test/membership', {
      data: { user_id: me.user.id, workflow: 'bulk_registration', role: 'viewer' },
    });
    expect(changed.status()).toBe(200);
    await guest.evaluate(() => window.dispatchEvent(new Event('focus')));
    await expect(guest.getByText('Viewer access: you can view this shared workspace. Editing is disabled.')).toBeVisible();
    await expect(guest.locator('input[type="file"]').first()).toBeDisabled();
    expect((await recipient.request.delete(`${api}/bulk-reg/file`, { headers: { origin, 'X-Workspace-Revision': '0' } })).status()).toBe(403);
    await guest.setViewportSize({ width: 390, height: 844 });
    await guest.screenshot({ path: '../.test-temp/review-qa/bulk-viewer-mobile.png' });
    await guest.getByLabel('Workspace selector', { exact: true }).click();
    await guest.screenshot({ path: '../.test-temp/review-qa/shared-viewer-mobile.png' });
    const layout = await guest.evaluate(() => ({ viewport: innerWidth, scroll: document.documentElement.scrollWidth,
      overflowing: [...document.querySelectorAll('body *')].map(element => ({
        tag: element.tagName, className: element.className, right: element.getBoundingClientRect().right,
        width: element.getBoundingClientRect().width,
      })).filter(item => item.right > innerWidth + 1).slice(0, 25) }));
    await testInfo.attach('mobile-layout', { body: JSON.stringify(layout, null, 2), contentType: 'application/json' });
    if (layout.scroll > layout.viewport) console.log('Mobile overflow:', JSON.stringify(layout));
    expect(await guest.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    expect((await context.request.post('http://127.0.0.1:8123/_test/membership', {
      data: { user_id: me.user.id, workflow: 'bulk_registration', revoked: true },
    })).status()).toBe(200);
    await guest.getByLabel('Workspace selector', { exact: true }).click();
    await guest.evaluate(() => window.dispatchEvent(new Event('focus')));
    await expect(guest.getByRole('alert')).toContainText('revoked');
    await guest.getByLabel('Workspace selector', { exact: true }).click();
    await guest.getByRole('button', { name: 'Create workspace', exact: true }).click();
    await expect(guest.getByRole('alert')).toHaveCount(0);
    await expect(guest.getByRole('button', { name: 'Invite to workflow', exact: true })).toBeVisible();
  } finally { await recipient.close(); }
});
