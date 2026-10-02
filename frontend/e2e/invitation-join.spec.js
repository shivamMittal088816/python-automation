import { test, expect } from './fixtures/browser-audit';

const api = 'http://127.0.0.1:8123/api/v1';
const origin = 'http://127.0.0.1:5174';

test('workspace dropdown shows accepted invitees and dummy edit access controls', async ({ page, browser }) => {
  await page.goto('/admission_file_page');
  await expect(page.getByRole('button', { name: 'Open sidebar', exact: true })).toBeVisible();
  const token = await generate(page.context(), 'mapping', 'viewer');
  await page.getByLabel('Workspace selector', { exact: true }).click();
  const people = page.getByRole('region', { name: 'People with access' });
  await expect(people).toContainText('Accepted invitees will appear here.');
  await page.getByLabel('Workspace selector', { exact: true }).click();
  const recipient = await browser.newContext();
  try {
    const joined = await recipient.request.post(`${api}/invitations/join`, { headers: { origin }, data: { token } });
    expect(joined.status(), await joined.text()).toBe(200);
    await page.getByLabel('Workspace selector', { exact: true }).click();
    await expect(people).toContainText('Test member');
    await expect(people).toContainText('Mapping · View only');
    await expect(people).toContainText('Viewer');
    await expect(people.getByRole('button', { name: /Edit access for Test member/ })).toBeDisabled();
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(people).toBeVisible();
    await page.screenshot({ path: '../.test-temp/invitation-qa/workspace-members-mobile.png' });
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.screenshot({ path: '../.test-temp/invitation-qa/workspace-members-desktop.png' });
  } finally { await recipient.close(); }
});

test('owner cannot accept their own invitation and another recipient can still use it', async ({ page, browser }) => {
  await page.goto('/admission_file_page');
  await expect(page.getByRole('button', { name: 'Open sidebar', exact: true })).toBeVisible();
  const token = await generate(page.context());
  const dialog = await openJoin(page);
  await dialog.getByLabel('Invitation code', { exact: true }).fill(`${origin}/i/${token}`);
  await dialog.getByRole('button', { name: 'Join workflow' }).click();
  await expect(dialog.getByRole('alert')).toContainText('You cannot accept an invitation to your own workspace.');
  await expect(dialog.getByRole('button', { name: 'Join workflow' })).toBeEnabled();
  const recipient = await browser.newContext();
  try {
    const guest = await recipient.newPage();
    await guest.goto(`${origin}/i/${token}`);
    await guest.getByRole('dialog').getByRole('button', { name: 'Join workflow' }).click();
    await expect(guest.getByRole('dialog')).toHaveCount(0);
    const ownerState = await (await page.context().request.get(`${api}/mapping/session`)).json();
    const shared = await (await recipient.request.get(`${api}/mapping/session`)).json();
    expect(shared.workspace_id).toBe(ownerState.workspace_id);
    expect(ownerState.role).toBe('owner');
    expect(shared.role).toBe('editor');
  } finally { await recipient.close(); }
});

async function generate(context, workflow = 'mapping', permission = 'editor') {
  const result = await context.request.post(`${api}/invitations`, {
    headers: { origin }, data: { workflow, permission },
  });
  expect(result.status(), await result.text()).toBe(201);
  return (await result.json()).invitation_url.split('/').pop();
}

async function openJoin(page) {
  await page.getByRole('button', { name: 'Open sidebar', exact: true }).click();
  await page.getByRole('button', { name: 'Join with invitation code', exact: true }).click();
  return page.getByRole('dialog');
}

test('join by code shares owner files, editor changes, and rejects reused codes', async ({ page, browser }) => {
  await page.goto('/admission_file_page');
  await expect(page.getByRole('button', { name: 'Open sidebar', exact: true })).toBeVisible();
  const owner = page.context();
  const initial = await (await owner.request.get(`${api}/mapping/session`)).json();
  const upload = await owner.request.post(`${api}/mapping/files/school`, {
    headers: { origin, 'X-Workspace-Revision': String(initial.revision) },
    multipart: { file: { name: 'shared-school.csv', mimeType: 'text/csv', buffer: Buffer.from('admission_number,first_name\n001,Alice\n') } },
  });
  expect(upload.status()).toBe(200);
  const token = await generate(owner);
  const recipient = await browser.newContext();
  try {
    const guest = await recipient.newPage();
    await guest.goto(`${origin}/admission_file_page`);
    const dialog = await openJoin(guest);
    await expect(dialog.getByRole('button', { name: 'Join workflow' })).toBeDisabled();
    await dialog.getByLabel('Invitation code', { exact: true }).fill(` ${origin}/i/${token} `);
    await dialog.getByLabel('Invitation code', { exact: true }).press('Enter');
    await expect(guest.getByRole('dialog')).toHaveCount(0);
    await expect(guest.getByText('shared-school.csv', { exact: false }).first()).toBeVisible();
    const shared = await (await recipient.request.get(`${api}/mapping/session`)).json();
    expect(shared.workspace_id).toBe(initial.workspace_id);
    expect(shared.role).toBe('editor');
    const clear = await recipient.request.post(`${api}/mapping/files/school/clear`, {
      headers: { origin, 'X-Workspace-Revision': String(shared.revision) },
    });
    expect(clear.status()).toBe(200);
    expect((await (await owner.request.get(`${api}/mapping/session`)).json()).files.school).toBeUndefined();
    const reused = await owner.request.post(`${api}/invitations/join`, { headers: { origin }, data: { token } });
    expect(reused.status()).toBe(409);
  } finally { await recipient.close(); }
});

test('viewer sees read-only UI and cannot bypass it through the API', async ({ page, browser }) => {
  await page.goto('/admission_file_page');
  await expect(page.getByRole('button', { name: 'Open sidebar', exact: true })).toBeVisible();
  const token = await generate(page.context(), 'mapping', 'viewer');
  const recipient = await browser.newContext();
  try {
    const guest = await recipient.newPage();
    await guest.goto(`${origin}/i/${token}`);
    const dialog = guest.getByRole('dialog');
    await expect(dialog.getByLabel('Invitation code', { exact: true })).toHaveValue(token);
    await dialog.getByRole('button', { name: 'Join workflow' }).click();
    await expect(guest.getByText('Viewer access: you can view this shared workspace. Editing is disabled.')).toBeVisible();
    await expect(guest.locator('main input[type="file"]').first()).toBeDisabled();
    const result = await recipient.request.post(`${api}/mapping/files/school/clear`, {
      headers: { origin, 'X-Workspace-Revision': '0' },
    });
    expect(result.status()).toBe(403);
  } finally { await recipient.close(); }
});

test('invalid input, unknown codes, keyboard close, focus return, and mobile layout', async ({ page }) => {
  await page.goto('/admission_file_page');
  const dialog = await openJoin(page);
  const input = dialog.getByLabel('Invitation code', { exact: true });
  await expect(input).toBeFocused();
  await input.fill('short');
  await dialog.getByRole('button', { name: 'Join workflow' }).click();
  await expect(dialog.getByRole('alert')).toContainText('Enter a valid invitation code');
  await input.fill('unknown-code-123456789012');
  await dialog.getByRole('button', { name: 'Join workflow' }).click();
  await expect(dialog.getByRole('alert')).toContainText('Invitation code was not found');
  await page.setViewportSize({ width: 390, height: 650 });
  expect(await dialog.evaluate(element => element.getBoundingClientRect().width <= innerWidth)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Join with invitation code', exact: true })).toBeFocused();
});

test('both workflows and bulk-only invitations restore the intended workspace', async ({ page, browser }) => {
  await page.goto('/admission_file_page');
  await expect(page.getByRole('button', { name: 'Open sidebar', exact: true })).toBeVisible();
  for (const workflow of ['both', 'bulk_registration']) {
    const token = await generate(page.context(), workflow, 'editor');
    const ownerBulk = await (await page.context().request.get(`${api}/bulk-reg/workspace`)).json();
    const recipient = await browser.newContext();
    try {
      const guest = await recipient.newPage();
      await guest.goto(`${origin}${workflow === 'both' ? '/i' : '/i/b'}/${token}`);
      await guest.getByRole('dialog').getByRole('button', { name: 'Join workflow' }).click();
      await expect(guest.getByRole('dialog')).toHaveCount(0);
      if (workflow === 'both') await guest.goto(`${origin}/bulk-reg`);
      await expect(guest.getByRole('heading', { name: 'Bulk registration', exact: true })).toBeVisible();
      const joinedBulk = await (await recipient.request.get(`${api}/bulk-reg/workspace`)).json();
      expect(joinedBulk.workspace_id).toBe(ownerBulk.workspace_id);
      expect(joinedBulk.role).toBe('editor');
    } finally { await recipient.close(); }
  }
});

test('a new invitation can be entered when previous shared access is unavailable', async ({ page, browser }) => {
  await page.goto('/admission_file_page');
  await expect(page.getByRole('button', { name: 'Open sidebar', exact: true })).toBeVisible();
  const token = await generate(page.context());
  const recipient = await browser.newContext();
  try {
    const guest = await recipient.newPage();
    await guest.route('**/api/v1/mapping/session', route => route.fulfill({
      status: 403, contentType: 'application/json',
      body: JSON.stringify({ detail: 'Shared workflow access expired or was revoked.' }),
    }));
    await guest.goto(`${origin}/i/${token}`);
    const dialog = guest.getByRole('dialog');
    await expect(dialog.getByLabel('Invitation code', { exact: true })).toHaveValue(token);
    await guest.unroute('**/api/v1/mapping/session');
    await dialog.getByRole('button', { name: 'Join workflow' }).click();
    await expect(guest.getByRole('button', { name: 'Open sidebar', exact: true })).toBeVisible();
    expect((await (await recipient.request.get(`${api}/mapping/session`)).json()).role).toBe('editor');
  } finally { await recipient.close(); }
});
