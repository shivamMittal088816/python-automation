import { test, expect } from '@playwright/test';
import { fileURLToPath } from 'node:url';

const school = fileURLToPath(new URL('./fixtures/school.csv', import.meta.url));

test('same-session tabs refresh and stale writes receive 409', async ({ page, context }) => {
  await page.goto('/admission_file_page');
  const second = await context.newPage();
  await second.goto('/admission_file_page');
  const staleRevision = await second.evaluate(async () => {
    const response = await fetch('http://127.0.0.1:8123/api/v1/mapping/session', {
      credentials: 'include',
    });
    return (await response.json()).revision;
  });

  await page.getByLabel('Add school file').setInputFiles(school);
  await expect(page.getByText('Loaded: school.csv', { exact: true })).toBeVisible();
  await expect(second.getByText('Loaded: school.csv', { exact: true })).toBeVisible();

  const conflict = await second.evaluate(async revision => {
    const response = await fetch('http://127.0.0.1:8123/api/v1/mapping/school', {
      method: 'PATCH',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-Workspace-Revision': String(revision),
      },
      body: JSON.stringify({ school_index: '914' }),
    });
    return { status: response.status, body: await response.json() };
  }, staleRevision);

  expect(conflict.status).toBe(409);
  expect(conflict.body.detail).toContain('changed');
});
