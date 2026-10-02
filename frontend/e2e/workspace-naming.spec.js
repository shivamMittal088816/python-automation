import { test, expect } from './fixtures/browser-audit';

const api = 'http://127.0.0.1:8123/api/v1';
const origin = 'http://127.0.0.1:5174';
const password = 'a memorable workspace naming passphrase!';

async function register(context, name = 'Alex Morgan') {
  const email = `naming-${crypto.randomUUID()}@example.com`;
  const response = await context.request.post(`${api}/auth/register`, {
    headers: { origin }, data: { name, email, password },
  });
  expect(response.status()).toBe(201);
  return email;
}

async function nameInitial(page, name) {
  const dialog = page.getByRole('dialog', { name: 'A space of your own' });
  await expect(dialog).toBeVisible();
  await dialog.getByRole('textbox', { name: /^Workspace name/ }).fill(name);
  await dialog.getByRole('button', { name: 'Save and continue' }).click();
  await expect(dialog).toHaveCount(0);
}

test('first login names the initial workspace; create, cancel and rename preserve existing files', async ({ page, context }) => {
  const email = await register(context);
  expect((await context.request.post(`${api}/auth/logout`, { headers: { origin } })).status()).toBe(204);
  await page.goto('/login');
  await page.getByLabel('Email address').fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  const setup = page.getByRole('dialog', { name: 'A space of your own' });
  await expect(setup).toBeVisible();
  await expect(setup.getByRole('textbox', { name: /^Workspace name/ })).toBeFocused();
  await expect(setup.getByRole('button', { name: 'Save and continue' })).toBeDisabled();
  await page.screenshot({ path: '../.test-temp/workspace-naming/setup-desktop.png' });
  await nameInitial(page, '  Greenfield Admissions  ');
  await expect(page.getByLabel('Workspace selector', { exact: true })).toContainText('Greenfield Admissions');
  const initial = await (await context.request.get(`${api}/workspaces?workflow=mapping`)).json();
  const uploaded = await context.request.post(`${api}/mapping/files/school`, {
    headers: { origin, 'X-Workspace-Revision': '0' },
    multipart: { file: { name: 'naming-school.csv', mimeType: 'text/csv', buffer: Buffer.from('admission_number,first_name\n001,Alice\n') } },
  });
  expect(uploaded.status()).toBe(200);
  await page.reload();
  await expect(page.getByLabel('Workspace selector', { exact: true })).toContainText('Greenfield Admissions');
  await expect(setup).toHaveCount(0);
  await page.getByLabel('Workspace selector', { exact: true }).click();
  await page.getByRole('button', { name: 'Create workspace', exact: true }).click();
  await page.getByRole('dialog').getByRole('textbox', { name: /^Workspace name/ }).fill('Cancelled');
  await page.getByRole('dialog').getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(page.getByLabel('Workspace selector', { exact: true })).toBeFocused();
  expect((await (await context.request.get(`${api}/workspaces?workflow=mapping`)).json()).workspaces).toHaveLength(1);
  await page.getByLabel('Workspace selector', { exact: true }).click();
  await page.getByRole('button', { name: 'Create workspace', exact: true }).click();
  const create = page.getByRole('dialog', { name: 'Create your workspace' });
  await create.getByRole('textbox', { name: /^Workspace name/ }).fill('Second School');
  await create.getByRole('button', { name: 'Create workspace', exact: true }).click();
  await expect(create).toHaveCount(0);
  await expect(page.getByLabel('Workspace selector', { exact: true })).toContainText('Second School');
  await page.getByLabel('Workspace selector', { exact: true }).click();
  await page.getByLabel('Rename Greenfield Admissions', { exact: true }).click();
  const rename = page.getByRole('dialog', { name: 'Rename workspace' });
  await expect(rename.getByRole('textbox', { name: /^Workspace name/ })).toHaveValue('Greenfield Admissions');
  await expect(rename.getByRole('textbox', { name: /^Workspace name/ })).toBeFocused();
  const dimensions = await rename.evaluate(element => ({ width: element.getBoundingClientRect().width,
    inputHeight: element.querySelector('input').getBoundingClientRect().height,
    background: getComputedStyle(element).backgroundImage }));
  expect(dimensions.width).toBeGreaterThanOrEqual(400);
  expect(dimensions.width).toBeLessThanOrEqual(440);
  expect(dimensions.inputHeight).toBe(44);
  expect(dimensions.background).toContain('linear-gradient');
  await rename.getByRole('textbox', { name: /^Workspace name/ }).press('Escape');
  await expect(rename).toHaveCount(0);
  await expect(page.getByLabel('Workspace selector', { exact: true })).toBeFocused();
  await page.getByLabel('Workspace selector', { exact: true }).click();
  await page.getByLabel('Rename Greenfield Admissions', { exact: true }).click();
  await rename.getByRole('textbox', { name: /^Workspace name/ }).fill('Greenfield 2027');
  await page.screenshot({ path: '../.test-temp/workspace-naming/rename-desktop.png' });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: '../.test-temp/workspace-naming/rename-mobile.png' });
  expect(await rename.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  await page.setViewportSize({ width: 1280, height: 720 });
  await rename.getByRole('button', { name: 'Save changes' }).click();
  await expect(rename).toHaveCount(0);
  const after = await (await context.request.get(`${api}/workspaces?workflow=mapping`)).json();
  expect(after.workspaces).toHaveLength(2);
  expect(after.workspaces.find(item => item.id === initial.active_workspace_id).name).toBe('Greenfield 2027');
  await page.getByLabel('Workspace selector', { exact: true }).click();
  await page.locator(`[data-workspace-id="${initial.active_workspace_id}"]`).click();
  await expect(page.getByText('naming-school.csv', { exact: false }).first()).toBeVisible();
  await expect(page.getByLabel('Workspace selector', { exact: true })).toContainText('Greenfield 2027');
});

test('invitees see the owner’s current workspace name and cannot rename it', async ({ page, context, browser }) => {
  await register(context);
  const created = await context.request.post(`${api}/workspaces`, {
    headers: { origin }, data: { workflow: 'mapping', name: 'Shared Admissions' },
  });
  expect(created.status()).toBe(201);
  const identifier = (await created.json()).active_workspace_id;
  const invitation = await context.request.post(`${api}/invitations`, {
    headers: { origin }, data: { workflow: 'mapping', permission: 'editor' },
  });
  expect(invitation.status()).toBe(201);
  const guest = await browser.newContext();
  try {
    await register(guest, 'Jamie');
    const token = (await invitation.json()).invitation_url.split('/').pop();
    expect((await guest.request.post(`${api}/invitations/join`, { headers: { origin }, data: { token } })).status()).toBe(200);
    const guestPage = await guest.newPage();
    await guestPage.goto(`${origin}/admission_file_page`);
    await expect(guestPage.getByLabel('Workspace selector', { exact: true })).toContainText('Shared Admissions');
    await expect(guestPage.getByRole('dialog')).toHaveCount(0);
    await guestPage.getByLabel('Workspace selector', { exact: true }).click();
    await expect(guestPage.getByRole('button', { name: /^Rename / })).toHaveCount(0);
    expect((await guest.request.patch(`${api}/workspaces/${identifier}`, { headers: { origin }, data: { name: 'Forbidden' } })).status()).toBe(403);
    expect((await context.request.patch(`${api}/workspaces/${identifier}`, { headers: { origin }, data: { name: 'Shared 2027' } })).status()).toBe(200);
    await guestPage.reload();
    await expect(guestPage.getByLabel('Workspace selector', { exact: true })).toContainText('Shared 2027');
  } finally { await guest.close(); }
});

test('mobile bulk workspace setup, long names, retry and keyboard cancellation', async ({ page, context }) => {
  await register(context);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/bulk-reg');
  const setup = page.getByRole('dialog', { name: 'A space of your own' });
  await expect(setup).toBeVisible();
  await setup.getByRole('textbox', { name: /^Workspace name/ }).fill('Mobile Registration');
  await page.screenshot({ path: '../.test-temp/workspace-naming/setup-mobile.png' });
  let failed = false;
  await page.route('**/api/v1/workspaces/*', route => {
    if (!failed && route.request().method() === 'PATCH') {
      failed = true;
      return route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Please try again.' }) });
    }
    return route.continue();
  });
  await setup.getByRole('button', { name: 'Save and continue' }).click();
  await expect(setup.getByRole('alert')).toContainText('Please try again.');
  await expect(setup.getByRole('textbox', { name: /^Workspace name/ })).toHaveValue('Mobile Registration');
  await setup.getByRole('button', { name: 'Save and continue' }).click();
  await expect(setup).toHaveCount(0);
  await page.getByLabel('Workspace selector', { exact: true }).click();
  await page.getByRole('button', { name: 'Create workspace', exact: true }).click();
  const create = page.getByRole('dialog', { name: 'Create your workspace' });
  await create.getByRole('textbox', { name: /^Workspace name/ }).fill('A'.repeat(100));
  expect(await create.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  await create.getByRole('textbox', { name: /^Workspace name/ }).press('Escape');
  await expect(create).toHaveCount(0);
  const spaces = await (await context.request.get(`${api}/workspaces?workflow=bulk_registration`)).json();
  expect(spaces.workspaces).toHaveLength(1);
  expect(spaces.workspaces[0].name).toBe('Mobile Registration');
});

test('first-time invitee sees one join dialog and keeps their unnamed personal workspace', async ({ page, context, browser }) => {
  await register(context);
  const created = await context.request.post(`${api}/workspaces`, {
    headers: { origin }, data: { workflow: 'mapping', name: 'Invited Admissions' },
  });
  expect(created.status()).toBe(201);
  const invitation = await context.request.post(`${api}/invitations`, {
    headers: { origin }, data: { workflow: 'mapping', permission: 'viewer' },
  });
  expect(invitation.status()).toBe(201);
  const token = (await invitation.json()).invitation_url.split('/').pop();
  const guest = await browser.newContext();
  try {
    await register(guest, 'New invitee');
    const guestPage = await guest.newPage();
    await guestPage.goto(`${origin}/admission_file_page?invite=${token}`);
    const join = guestPage.getByRole('dialog', { name: 'Join with invitation code' });
    await expect(join).toBeVisible();
    await expect(guestPage.getByRole('dialog')).toHaveCount(1);
    await join.getByRole('button', { name: 'Join workflow' }).click();
    await expect(guestPage.getByRole('dialog')).toHaveCount(0);
    await expect(guestPage.getByLabel('Workspace selector', { exact: true })).toContainText('Invited Admissions');
    await expect(guestPage.getByText('Viewer access: you can view this shared workspace. Editing is disabled.')).toBeVisible();
    const spaces = await (await guest.request.get(`${api}/workspaces?workflow=mapping`)).json();
    const personal = spaces.workspaces.find(item => item.owned);
    expect(personal.needs_name).toBe(true);
    expect(spaces.workspaces).toHaveLength(2);
    await guestPage.getByLabel('Workspace selector', { exact: true }).click();
    await guestPage.locator(`[data-workspace-id="${personal.id}"]`).click();
    await nameInitial(guestPage, 'My Personal School');
    await expect(guestPage.getByLabel('Workspace selector', { exact: true })).toContainText('My Personal School');
    await guestPage.screenshot({ path: '../.test-temp/workspace-naming/invitee-personal-desktop.png' });
  } finally { await guest.close(); }
});

test('rename stays usable at 320px and preserves input after a failed save before retry and logout', async ({ page, context }) => {
  await register(context, 'Visual QA reviewer');
  await page.goto('/admission_file_page');
  await nameInitial(page, 'QA School Admissions');
  const selector = page.getByLabel('Workspace selector', { exact: true });
  await selector.click();
  await page.getByLabel('Rename QA School Admissions', { exact: true }).click();
  const rename = page.getByRole('dialog', { name: 'Rename workspace' });
  const input = rename.getByRole('textbox', { name: /^Workspace name/ });
  await input.fill('A'.repeat(100));
  await page.setViewportSize({ width: 320, height: 700 });
  expect(await rename.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  await page.screenshot({ path: '../.test-temp/review-qa/rename-mobile-320.png' });
  await input.press('Escape');
  await expect(rename).toHaveCount(0);
  await expect(selector).toBeFocused();
  await page.setViewportSize({ width: 1280, height: 800 });
  await selector.click();
  await page.getByLabel('Rename QA School Admissions', { exact: true }).click();
  await input.fill('QA School 2027');
  let failed = false;
  await page.route('**/api/v1/workspaces/*', route => {
    if (!failed && route.request().method() === 'PATCH') {
      failed = true;
      return route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Please try again.' }) });
    }
    return route.continue();
  });
  await rename.getByRole('button', { name: 'Save changes' }).click();
  await expect(rename.getByRole('alert')).toContainText('Please try again.');
  await expect(input).toHaveValue('QA School 2027');
  await page.screenshot({ path: '../.test-temp/review-qa/rename-save-error-desktop.png' });
  await input.press('Enter');
  await expect(rename).toHaveCount(0);
  await expect(selector).toContainText('QA School 2027');
  await expect(selector).toBeFocused();
  await page.getByLabel('Account menu').click();
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
});
