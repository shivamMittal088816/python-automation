import { test, expect } from './fixtures/browser-audit';

const api = 'http://127.0.0.1:8123/api/v1';
const origin = 'http://127.0.0.1:5174';
const password = 'a memorable student mapping passphrase!';

test('unauthenticated access requires login and preserves the requested destination', async ({ page, context }) => {
  await page.goto('/admission_file_page?invite=test-invitation-code');
  await expect(page).toHaveURL(/\/login\?next=/);
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  const apiResponse = await context.request.get(`${api}/mapping/session`);
  expect(apiResponse.status()).toBe(401);
});

test('account creation, persistent cookie sign-in, logout, and sign-in validation', async ({ page, context, browser }) => {
  const email = `alex-${Date.now()}@example.com`;
  await page.goto('/register');
  await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible();
  await page.getByLabel('Full name').fill('Alex Morgan');
  await page.getByLabel('Email address').fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Show password', exact: true }).click();
  await expect(page.getByLabel('Password', { exact: true })).toHaveAttribute('type', 'text');
  await page.getByRole('button', { name: 'Hide password', exact: true }).click();
  await page.getByRole('button', { name: 'Create account', exact: true }).click();
  await expect(page.getByLabel('Account menu')).toBeVisible();
  const setup = page.getByRole('dialog', { name: 'A space of your own' });
  await expect(setup).toBeVisible();
  await setup.getByRole('textbox', { name: /^Workspace name/ }).fill('Alex’s school');
  await setup.getByRole('button', { name: 'Save and continue' }).click();
  await expect(setup).toHaveCount(0);
  const selected = await (await context.request.get(`${api}/workspaces?workflow=mapping`)).json();
  const uploaded = await context.request.post(`${api}/mapping/files/school`, {
    headers: { origin, 'X-Workspace-Revision': '0' },
    multipart: { file: { name: 'persistent-school.csv', mimeType: 'text/csv', buffer: Buffer.from('admission_number,first_name\n001,Alice\n') } },
  });
  expect(uploaded.status()).toBe(200);
  const cookie = (await context.cookies()).find(item => item.name === 'auth-session');
  expect(cookie.httpOnly).toBe(true);
  expect(cookie.sameSite).toBe('Lax');
  expect(await page.evaluate(() => document.cookie)).not.toContain('auth-session');
  await page.reload();
  await page.getByLabel('Account menu').click();
  await expect(page.locator('.account-panel')).toContainText(email);
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  await expect(page.getByRole('status')).toContainText('signed out');
  expect((await context.cookies()).some(item => item.name === 'auth-session')).toBe(false);
  const replay = await context.request.get(`${api}/auth/me`, { headers: { cookie: `auth-session=${cookie.value}` } });
  expect((await replay.json()).user).toBeNull();
  await page.getByLabel('Email address').fill(email);
  await page.getByLabel('Password', { exact: true }).fill('wrong password');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Email or password is incorrect');
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByLabel('Password', { exact: true }).press('Enter');
  await expect(page.getByLabel('Account menu')).toBeVisible();
  expect((await context.cookies()).find(item => item.name === 'auth-session').value).not.toBe(cookie.value);
  await expect(page.getByText('persistent-school.csv', { exact: false }).first()).toBeVisible();
  const restored = await (await context.request.get(`${api}/workspaces?workflow=mapping`)).json();
  expect(restored.active_workspace_id).toBe(selected.active_workspace_id);
  expect(restored.workspaces).toHaveLength(1);
  const device = await browser.newContext();
  try {
    const signedIn = await device.request.post(`${api}/auth/login`, { headers: { origin }, data: { email, password } });
    expect(signedIn.status()).toBe(200);
    const devicePage = await device.newPage();
    await devicePage.goto(`${origin}/admission_file_page`);
    await expect(devicePage.getByText('persistent-school.csv', { exact: false }).first()).toBeVisible();
    const deviceSpaces = await (await device.request.get(`${api}/workspaces?workflow=mapping`)).json();
    expect(deviceSpaces.active_workspace_id).toBe(selected.active_workspace_id);
    expect((await device.cookies()).map(item => item.name)).toEqual(['auth-session']);
  } finally {
    await device.close();
  }
});

test('login and registration layouts fit mobile and preserve invitation return path', async ({ page }) => {
  await page.goto('/login?next=%2Fi%2Ftest-invitation-code');
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  await page.screenshot({ path: '../.test-temp/auth-qa/login-desktop.png' });
  await page.getByRole('link', { name: 'Create an account', exact: true }).click();
  await expect(page).toHaveURL(/register\?next=/);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole('button', { name: 'Create account', exact: true })).toBeVisible();
  await page.screenshot({ path: '../.test-temp/auth-qa/register-mobile.png' });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole('link', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  await page.screenshot({ path: '../.test-temp/auth-qa/login-mobile.png' });
});

test('login rejects an external return destination', async ({ page, context }) => {
  const email = `return-${Date.now()}@example.com`;
  const created = await context.request.post(`${api}/auth/register`, { headers: { origin }, data: { name: 'Jamie', email, password } });
  expect(created.status()).toBe(201);
  await page.goto('/login?next=https%3A%2F%2Funtrusted.example%2F');
  await page.getByLabel('Email address').fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page).toHaveURL(/127\.0\.0\.1:5174\/admission_file_page/);
});
