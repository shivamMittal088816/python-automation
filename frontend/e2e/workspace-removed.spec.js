import { test, expect } from './fixtures/browser-audit';

const api = 'http://127.0.0.1:8123/api/v1';
const headers = { origin: 'http://127.0.0.1:5174' };

async function create(context, workflow, name) {
  const response = await context.request.post(`${api}/workspaces`, { headers, data: { workflow, name } });
  expect(response.status()).toBe(201);
  return (await response.json()).active_workspace_id;
}

async function share(owner, member, workflow, permission = 'editor') {
  const created = await owner.request.post(`${api}/invitations`, { headers, data: { workflow, permission } });
  expect(created.status()).toBe(201);
  const token = (await created.json()).invitation_url.split('/').pop();
  expect((await member.request.post(`${api}/invitations/join`, { headers, data: { token } })).status()).toBe(200);
}

for (const workflow of ['mapping', 'bulk_registration']) {
  const path = workflow === 'mapping' ? '/admission_file_page' : '/bulk-reg';
  for (const detection of ['refresh', 'operation']) {
    test(`${workflow}: member recovers from owner deletion detected by ${detection}`, async ({ page, context, browser }, testInfo) => {
      const owner = await browser.newContext();
      try {
        const personal = detection === 'refresh' ? await create(context, workflow, 'My remaining workspace') : null;
        if (personal) await create(context, workflow, 'Another workspace');
        const shared = await create(owner, workflow, 'Shared school');
        await share(owner, context, workflow, detection === 'refresh' ? 'viewer' : 'editor');
        await page.goto(path);
        await expect(page.getByLabel('Workspace selector', { exact: true })).toContainText('Shared school');
        expect((await owner.request.delete(`${api}/workspaces/${shared}`, { headers })).status()).toBe(200);
        if (detection === 'refresh') {
          await page.evaluate(() => window.dispatchEvent(new Event('focus')));
        } else if (workflow === 'mapping') {
          await expect(page.getByLabel(/^(Add|Replace) school file$/)).toBeEnabled();
          await page.getByLabel(/^(Add|Replace) school file$/).setInputFiles({ name: 'school.csv', mimeType: 'text/csv', buffer: Buffer.from('admission_number,first_name\n001,Alice\n') });
        } else {
          await expect(page.getByLabel('Upload registration file')).toBeEnabled();
          await page.getByLabel('Upload registration file').setInputFiles({ name: 'students.csv', mimeType: 'text/csv', buffer: Buffer.from('FIRST NAME\nAda') });
        }
        const removed = page.getByRole('heading', { name: 'Workspace removed', exact: true });
        await expect(removed).toBeVisible();
        await expect(page.getByText('The owner deleted this workspace. Select another workspace to continue.', { exact: true })).toBeVisible();
        await expect(page.locator('input[type=file]')).toHaveCount(0);
        await expect(page.getByText(/HTTP 410/)).toHaveCount(0);
        // The same recovery screen also appears on initial page load.
        await page.reload();
        await expect(removed).toBeVisible();
        await page.getByLabel('Select workspace', { exact: true }).click();
        if (personal) {
          for (const [label, width, height] of [['desktop', 1366, 640], ['mobile', 390, 640]]) {
            await page.setViewportSize({ width, height });
            const bounds = await page.evaluate(() => {
              const card = document.querySelector('.workspace-removed-card').getBoundingClientRect();
              const panel = document.querySelector('.workspace-selector-panel').getBoundingClientRect();
              return { cardBottom: card.bottom, panelBottom: panel.bottom, panelLeft: panel.left,
                panelRight: panel.right, cardLeft: card.left, cardRight: card.right,
                scrollHeight: document.documentElement.scrollHeight, viewportHeight: innerHeight };
            });
            expect(bounds.panelBottom).toBeLessThanOrEqual(bounds.cardBottom);
            expect(bounds.panelLeft).toBeGreaterThanOrEqual(bounds.cardLeft);
            expect(bounds.panelRight).toBeLessThanOrEqual(bounds.cardRight);
            expect(bounds.scrollHeight).toBeLessThanOrEqual(bounds.viewportHeight + 1);
            await page.screenshot({ path: testInfo.outputPath(`compact-${label}.png`) });
          }
        }
        await expect(page.locator(`[data-workspace-id="${shared}"]`)).toHaveCount(0);
        if (personal) {
          await page.locator(`[data-workspace-id="${personal}"]`).click();
        } else {
          await page.getByRole('button', { name: 'Create workspace', exact: true }).click();
          const dialog = page.getByRole('dialog', { name: 'Create your workspace' });
          await dialog.getByRole('textbox', { name: /^Workspace name/ }).fill('New personal workspace');
          await dialog.getByRole('button', { name: 'Create workspace', exact: true }).click();
        }
        await expect(removed).toHaveCount(0);
        await expect(page.getByLabel('Workspace selector', { exact: true })).toContainText(personal ? 'My remaining workspace' : 'New personal workspace');
      } finally { await owner.close(); }
    });
  }

  test(`${workflow}: deleting an inactive shared workspace leaves current work usable`, async ({ page, context, browser }) => {
    const owner = await browser.newContext();
    try {
      const personal = await create(context, workflow, 'Current workspace');
      const shared = await create(owner, workflow, 'Other shared workspace');
      await share(owner, context, workflow);
      expect((await context.request.post(`${api}/workspaces/select`, { headers, data: { workflow, workspace_id: personal } })).status()).toBe(200);
      await page.goto(path);
      await expect(page.getByLabel('Workspace selector', { exact: true })).toContainText('Current workspace');
      expect((await owner.request.delete(`${api}/workspaces/${shared}`, { headers })).status()).toBe(200);
      await page.evaluate(() => window.dispatchEvent(new Event('focus')));
      await page.getByLabel('Workspace selector', { exact: true }).click();
      await expect(page.locator(`[data-workspace-id="${shared}"]`)).toHaveCount(0);
      await expect(page.locator(`[data-workspace-id="${personal}"]`)).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Workspace removed', exact: true })).toHaveCount(0);
    } finally { await owner.close(); }
  });
}
