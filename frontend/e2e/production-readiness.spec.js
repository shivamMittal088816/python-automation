import { test, expect } from './fixtures/browser-audit';

const file = (name = 'students.csv', text = 'FIRST NAME\nAda') => ({
  name, mimeType: 'text/csv', buffer: Buffer.from(text),
});
const output = page => page.getByRole('region', { name: 'Output preview', exact: true });

async function readyBulk(page) {
  await page.goto('/bulk-reg');
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await expect(page.getByLabel('School name fetched')).toBeVisible();
  await page.getByLabel('Upload registration file').setInputFiles(file());
  await expect(page.getByText('File loaded', { exact: false })).toBeVisible();
}

test('simultaneous fresh mapping tabs create one shared session', async ({ page, context }) => {
  let creates = 0;
  await context.route('**/mapping/session', async route => {
    if (route.request().method() === 'POST') {
      creates += 1;
      // Keep creation in flight while the other tab begins initialization.
      await new Promise(resolve => setTimeout(resolve, 400));
    }
    await route.continue();
  });
  const second = await context.newPage();
  await Promise.all([page.goto('/admission_file_page'), second.goto('/admission_file_page')]);
  await expect(page.getByLabel('Add school file')).toBeVisible();
  await expect(second.getByLabel('Add school file')).toBeVisible();
  expect(creates).toBe(1);
  await page.getByLabel('Add school file').setInputFiles(file('shared.csv', 'admission_number,first_name\n001,Ada'));
  await expect(second.getByText('Loaded: shared.csv', { exact: true })).toBeVisible();
  await second.reload();
  await expect(second.getByText('Loaded: shared.csv', { exact: true })).toBeVisible();
});

test('failed replacement and offline conversion preserve output and recover', async ({ page, context }) => {
  await readyBulk(page);
  await page.getByRole('button', { name: 'Generate preview' }).click();
  await expect(output(page)).toBeVisible();
  const failedUpload = page.waitForResponse(response => response.url().endsWith('/bulk-reg/files'));
  await page.getByLabel('Upload registration file').setInputFiles(file('empty.csv', ''));
  expect((await failedUpload).status()).toBe(400);
  await expect(page.getByRole('alert')).toContainText('HTTP 400; request');
  await expect(output(page).getByRole('cell', { name: 'Ada', exact: true })).toBeVisible();
  await context.setOffline(true);
  await page.getByRole('button', { name: 'Generate preview' }).click();
  await expect(page.getByRole('alert')).toContainText('Could not reach the API');
  await expect(output(page)).toBeVisible();
  await context.setOffline(false);
  await page.getByRole('button', { name: 'Generate preview' }).click();
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Generate preview' })).toBeEnabled();
  await expect(output(page)).toBeVisible();
});

test('delayed generation and double clicks cannot restore a file cleared in another tab', async ({ page, context }) => {
  await readyBulk(page);
  const second = await context.newPage();
  await second.goto('/bulk-reg');
  await expect(second.getByRole('button', { name: 'Clear file', exact: true })).toBeVisible();
  let release, calls = 0;
  const gate = new Promise(resolve => { release = resolve; });
  await page.route('**/bulk-reg/convert', async route => {
    calls += 1;
    const response = await route.fetch();
    await gate;
    await route.fulfill({ response });
  });
  const started = page.waitForRequest('**/bulk-reg/convert');
  await page.getByRole('button', { name: 'Generate preview' }).evaluate(button => { button.click(); button.click(); });
  await started;
  await second.getByRole('button', { name: 'Clear file', exact: true }).click();
  await second.getByRole('dialog').getByRole('button', { name: 'Confirm', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Clear file', exact: true })).toHaveCount(0);
  release();
  await expect(page.getByRole('alert')).toContainText('changed in another tab');
  await expect(output(page)).toHaveCount(0);
  await expect(output(second)).toHaveCount(0);
  expect(calls).toBe(1);
});

test('confirmation dismisses when another tab replaces the file', async ({ page, context }) => {
  await readyBulk(page);
  const second = await context.newPage();
  await second.goto('/bulk-reg');
  await expect(second.getByRole('button', { name: 'Clear file', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Clear file', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await second.getByLabel('Upload registration file').setInputFiles(file('replacement.csv', 'FIRST NAME\nGrace'));
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(page.getByText('replacement.csv', { exact: true }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Generate preview' }).click();
  await expect(output(second).getByRole('cell', { name: 'Grace', exact: true })).toBeVisible();
});

test('server errors display HTTP status and request ID and permit retry', async ({ page }) => {
  await page.goto('/bulk-reg');
  await page.getByLabel('School index', { exact: true }).fill('914');
  for (const status of [400, 404, 413, 422, 500, 503]) {
    await page.route('**/bulk-reg/schools/914', route => route.fulfill({
      status, headers: { 'X-Request-ID': `audit-${status}`, 'Access-Control-Expose-Headers': 'X-Request-ID' },
      json: { detail: 'Verification unavailable' },
    }));
    await page.getByRole('button', { name: 'Verify school index' }).click();
    await expect(page.getByRole('alert')).toContainText(`HTTP ${status}; request audit-${status}`);
    await expect(page.getByLabel('School name fetched')).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Generate preview' })).toBeDisabled();
    await page.unroute('**/bulk-reg/schools/914');
  }
  await page.getByRole('button', { name: 'Verify school index' }).click();
  await expect(page.getByLabel('School name fetched')).toHaveValue('Test School');
});

test('real API status codes and diagnostic headers are readable in the browser', async ({ page }) => {
  await page.goto('/bulk-reg');
  const results = await page.evaluate(async () => {
    const paths = [
      ['/mapping/health', 'GET', undefined],
      ['/mapping/session', 'GET', undefined],
      ['/bulk-reg/schools/999', 'GET', undefined],
      ['/bulk-reg/files/path', 'POST', '{}'],
    ];
    const results = [];
    for (const [path, method, body] of paths) {
      const response = await fetch(`http://127.0.0.1:8123/api/v1${path}`, {
        method, body, credentials: 'include', headers: { 'Content-Type': 'application/json' },
      });
      results.push({ status: response.status, id: response.headers.get('X-Request-ID'),
        cache: response.headers.get('Cache-Control'), timing: response.headers.get('Server-Timing') });
    }
    return results;
  });
  expect(results.map(result => result.status)).toEqual([200, 401, 404, 422]);
  for (const result of results) {
    expect(result.id).toMatch(/^[a-f0-9-]{36}$/);
    expect(result.cache).toBe('no-store');
    expect(result.timing).toMatch(/^app;dur=/);
  }
});
