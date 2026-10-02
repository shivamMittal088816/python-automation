import { test, expect } from './fixtures/browser-audit';

const api = 'http://127.0.0.1:8123/api/v1';
const origin = 'http://127.0.0.1:5174';

async function dropdown(page) {
  await page.getByLabel('Workspace selector', { exact: true }).click();
  return page.locator('.workspace-selector-panel');
}

async function ownedInvitation(context, permission, filename) {
  const initialized = await context.request.post(`${api}/mapping/session`, { headers: { origin }, data: { school_index: '914' } });
  expect(initialized.status()).toBe(200);
  const uploaded = await context.request.post(`${api}/mapping/files/school`, {
    headers: { origin, 'X-Workspace-Revision': '0' },
    multipart: { file: { name: filename, mimeType: 'text/csv', buffer: Buffer.from('admission_number,first_name\n001,Alice\n') } },
  });
  expect(uploaded.status()).toBe(200);
  const invitation = await context.request.post(`${api}/invitations`, { headers: { origin }, data: { workflow: 'mapping', permission } });
  expect(invitation.status()).toBe(201);
  return (await invitation.json()).invitation_url;
}

async function joinFromDropdown(page, invitation) {
  const panel = await dropdown(page);
  await panel.getByRole('button', { name: 'Join with invitation code', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByLabel('Invitation code', { exact: true }).fill(invitation);
  await dialog.getByRole('button', { name: 'Join workflow' }).click();
  await expect(dialog).toHaveCount(0);
}

test('dropdown joins multiple workspaces, restores own files, and creates a personal workspace from shared access', async ({ page, browser }) => {
  const viewerOwner = await browser.newContext();
  const editorOwner = await browser.newContext();
  try {
    const viewerInvite = await ownedInvitation(viewerOwner, 'viewer', 'viewer-school.csv');
    const editorInvite = await ownedInvitation(editorOwner, 'editor', 'editor-school.csv');
    await page.goto('/admission_file_page');
    await expect(page.getByRole('button', { name: 'Open sidebar', exact: true })).toBeVisible();
    const own = await (await page.context().request.get(`${api}/workspaces?workflow=mapping`)).json();
    const uploaded = await page.context().request.post(`${api}/mapping/files/school`, {
      headers: { origin, 'X-Workspace-Revision': '0' },
      multipart: { file: { name: 'my-school.csv', mimeType: 'text/csv', buffer: Buffer.from('admission_number,first_name\n002,Bob\n') } },
    });
    expect(uploaded.status()).toBe(200);
    await page.reload();
    await expect(page.getByText('my-school.csv', { exact: false }).first()).toBeVisible();
    const identityBefore = (await page.context().cookies()).find(cookie => cookie.name === 'auth-session').value;
    await joinFromDropdown(page, viewerInvite);
    await expect(page.getByText('viewer-school.csv', { exact: false }).first()).toBeVisible();
    await expect(page.getByText('Viewer access: you can view this shared workspace. Editing is disabled.')).toBeVisible();
    const viewer = await (await page.context().request.get(`${api}/workspaces?workflow=mapping`)).json();
    let panel = await dropdown(page);
    await expect(panel.getByRole('region', { name: 'Shared with me' }).getByRole('button')).toHaveCount(1);
    await panel.getByRole('button', { name: /^My workspace Your personal space Owner$/ }).click();
    await expect(page.getByText('my-school.csv', { exact: false }).first()).toBeVisible();
    const ownAgain = await (await page.context().request.get(`${api}/workspaces?workflow=mapping`)).json();
    expect(ownAgain.active_workspace_id).toBe(own.active_workspace_id);
    await joinFromDropdown(page, editorInvite);
    await expect(page.getByText('editor-school.csv', { exact: false }).first()).toBeVisible();
    await expect(page.getByText('Viewer access: you can view this shared workspace. Editing is disabled.')).toHaveCount(0);
    panel = await dropdown(page);
    await expect(panel.getByRole('region', { name: 'Shared with me' }).getByRole('button')).toHaveCount(2);
    await panel.locator(`[data-workspace-id="${viewer.active_workspace_id}"]`).click();
    await expect(page.getByText('viewer-school.csv', { exact: false }).first()).toBeVisible();
    panel = await dropdown(page);
    await panel.getByRole('button', { name: 'Create workspace', exact: true }).click();
    await page.getByRole('dialog').getByRole('textbox', { name: /^Workspace name/ }).fill('My workspace 2');
    await page.getByRole('dialog').getByRole('button', { name: 'Create workspace', exact: true }).click();
    await expect(page.getByRole('dialog')).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Open sidebar', exact: true })).toBeVisible();
    await expect(page.getByText('viewer-school.csv', { exact: false })).toHaveCount(0);
    const created = await (await page.context().request.get(`${api}/workspaces?workflow=mapping`)).json();
    expect(created.workspaces).toHaveLength(4);
    expect(created.workspaces.find(item => item.id === created.active_workspace_id).role).toBe('owner');
    expect((await page.context().cookies()).find(cookie => cookie.name === 'auth-session').value).toBe(identityBefore);
    panel = await dropdown(page);
    await expect(panel.getByRole('region', { name: 'Shared with me' }).getByRole('button')).toHaveCount(2);
    await page.screenshot({ path: '../.test-temp/invitation-qa/workspace-switching-desktop.png' });
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(panel.getByRole('button', { name: 'Create workspace', exact: true })).toBeVisible();
    await page.screenshot({ path: '../.test-temp/invitation-qa/workspace-switching-mobile.png' });
  } finally {
    await viewerOwner.close();
    await editorOwner.close();
  }
});

test('bulk workspace creation and selection preserve previous workspace', async ({ page }) => {
  await page.goto('/bulk-reg');
  const panel = await dropdown(page);
  await expect(panel.getByRole('button', { name: /^My workspace Your personal space Owner$/ })).toBeVisible();
  const initial = await (await page.context().request.get(`${api}/workspaces?workflow=bulk_registration`)).json();
  await panel.getByRole('button', { name: 'Create workspace', exact: true }).click();
  await page.getByRole('dialog').getByRole('textbox', { name: /^Workspace name/ }).fill('My workspace 2');
  await page.getByRole('dialog').getByRole('button', { name: 'Create workspace', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByLabel('Workspace selector', { exact: true })).toBeVisible();
  const next = await dropdown(page);
  await expect(next.getByRole('button', { name: /^My workspace 2 / })).toBeVisible();
  await next.getByRole('button', { name: /^My workspace Your personal space Owner$/ }).click();
  await expect(page.getByLabel('Workspace selector', { exact: true })).toBeVisible();
  const restored = await (await page.context().request.get(`${api}/workspaces?workflow=bulk_registration`)).json();
  expect(restored.active_workspace_id).toBe(initial.active_workspace_id);
});

test('an older tab cannot initialize or mutate the newly selected workspace', async ({ page, context }) => {
  await page.goto('/bulk-reg');
  const panel = await dropdown(page);
  await expect(panel.getByRole('button', { name: /^My workspace Your personal space Owner$/ })).toBeVisible();
  await page.getByLabel('Workspace selector', { exact: true }).click();
  const otherTab = await context.newPage();
  await otherTab.goto('/bulk-reg');
  const otherPanel = await dropdown(otherTab);
  await expect(otherPanel.getByRole('button', { name: 'Create workspace', exact: true })).toBeEnabled();
  await otherPanel.getByRole('button', { name: 'Create workspace', exact: true }).click();
  await otherTab.getByRole('dialog').getByRole('textbox', { name: /^Workspace name/ }).fill('My workspace 2');
  await otherTab.getByRole('dialog').getByRole('button', { name: 'Create workspace', exact: true }).click();
  await expect(otherTab.getByRole('dialog')).toHaveCount(0);
  await expect(otherTab.getByLabel('Workspace selector', { exact: true })).toBeVisible();
  const selected = await (await context.request.get(`${api}/workspaces?workflow=bulk_registration`)).json();
  const result = await page.evaluate(async () => {
    const { bulkRegistrationApi } = await import('/src/services/bulkRegistrationApi.js');
    const errors = [];
    for (const call of [() => bulkRegistrationApi.getWorkspace(), () => bulkRegistrationApi.clearFile(0)]) {
      try { await call(); errors.push(null); }
      catch (error) { errors.push({ status: error.status, selectionConflict: error.selectionConflict }); }
    }
    return errors;
  });
  expect(result).toEqual([{ status: 409, selectionConflict: true }, { status: 409, selectionConflict: true }]);
  const after = await (await context.request.get(`${api}/workspaces?workflow=bulk_registration`)).json();
  expect(after.active_workspace_id).toBe(selected.active_workspace_id);
  expect(after.workspaces).toHaveLength(2);
  await page.reload();
  await expect(page.getByLabel('Workspace selector', { exact: true })).toBeVisible();
  await otherTab.close();
});
