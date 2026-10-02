import { test, expect } from './fixtures/browser-audit';

test('a delayed bulk refresh cannot replace the reset selection or hide a new upload', async ({ page, context }) => {
  await page.goto('/bulk-reg');
  await expect(page.getByLabel('Upload registration file')).toBeEnabled();
  const second = await context.newPage();
  await second.goto('/bulk-reg');
  await expect(second.getByLabel('Upload registration file')).toBeEnabled();
  let release, intercepted, completed;
  const held = new Promise(resolve => { release = resolve; });
  const captured = new Promise(resolve => { intercepted = resolve; });
  const done = new Promise(resolve => { completed = resolve; });
  let first = true;
  let staleStatus, staleCookie;
  await page.route('**/bulk-reg/workspace', async route => {
    if (!first || route.request().method() !== 'GET') return route.continue();
    first = false;
    const headers = await route.request().allHeaders();
    intercepted();
    await held;
    const response = await route.fetch({ headers });
    staleStatus = response.status();
    staleCookie = response.headers()['set-cookie'];
    await route.fulfill({ response });
    completed();
  });
  try {
    await page.evaluate(() => window.dispatchEvent(new Event('focus')));
    await captured;
    await second.getByRole('button', { name: 'Reset bulk registration', exact: true }).click();
    await second.getByRole('dialog').getByRole('button', { name: 'Confirm', exact: true }).click();
    await expect(second.getByRole('dialog')).toHaveCount(0);
    await expect(second.getByLabel('Upload registration file')).toBeEnabled();
    await second.getByLabel('Upload registration file').setInputFiles({
      name: 'after-reset.csv', mimeType: 'text/csv', buffer: Buffer.from('FIRST NAME\nSavedAfterReset'),
    });
    await expect(second.getByText('File ready', { exact: true })).toBeVisible();
    release(); await done;
    expect(staleStatus).toBe(409);
    expect(staleCookie).toBeUndefined();
    await page.evaluate(() => window.dispatchEvent(new Event('focus')));
    await expect(page.getByRole('alert').first()).toContainText('active workspace changed');
    await expect(page.getByLabel('Upload registration file')).toBeDisabled();
    await page.reload();
    await second.reload();
    for (const tab of [page, second]) {
      await expect(tab.getByText('after-reset.csv', { exact: true }).first()).toBeVisible();
      await expect(tab.getByText('File ready', { exact: true })).toBeVisible();
    }
  } finally { release(); }
});

test('mapping startup rechecks changes broadcast while its snapshot is delayed', async ({ page, context }) => {
  await page.goto('/admission_file_page');
  await expect(page.getByLabel(/^(Add|Replace) school file$/)).toBeVisible();
  const second = await context.newPage();
  await second.goto('/admission_file_page');
  await expect(second.getByLabel(/^(Add|Replace) school file$/)).toBeVisible();
  let release, intercepted;
  const gate = new Promise(resolve => { release = resolve; });
  const captured = new Promise(resolve => { intercepted = resolve; });
  let first = true;
  await page.route('**/mapping/session', async route => {
    if (!first || route.request().method() !== 'GET') return route.continue();
    first = false;
    const response = await route.fetch();
    intercepted(); await gate;
    await route.fulfill({ response });
  });
  try {
    await page.reload({ waitUntil: 'domcontentloaded' });
    await captured;
    await page.evaluate(() => {
      window.qaUpdateReceived = new Promise(resolve => {
        const channel = new BroadcastChannel('student-mapping-workspace');
        channel.onmessage = () => { channel.close(); resolve(); };
      });
    });
    await expect(second.getByLabel(/^(Add|Replace) school file$/)).toBeEnabled();
    await second.getByLabel(/^(Add|Replace) school file$/).setInputFiles({
      name: 'new-from-tab-b.csv', mimeType: 'text/csv', buffer: Buffer.from('admission_number,first_name\n001,Ada'),
    });
    await expect(second.getByText('new-from-tab-b.csv', { exact: true }).first()).toBeVisible();
    await page.evaluate(() => window.qaUpdateReceived);
    release();
    // No focus/reload should be needed to repair the initial snapshot.
    await expect(page.getByText('new-from-tab-b.csv', { exact: true }).first()).toBeVisible();
  } finally { release(); }
});
