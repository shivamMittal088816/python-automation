import { test as base, expect } from '@playwright/test';

// Capture browser evidence for every scenario, including additional tabs.
export const test = base.extend({
  browserAudit: [async ({ context, browser }, use, testInfo) => {
    const originalNewContext = browser.newContext;
    const seedAccount = async target => {
      const response = await target.request.post('http://127.0.0.1:8123/_test/sign-in', { data: {} });
      expect(response.status()).toBe(200);
    };
    const needsAccount = !testInfo.file.endsWith('auth.spec.js') && !testInfo.file.endsWith('workspace-naming.spec.js');
    if (needsAccount) {
      await seedAccount(context);
      browser.newContext = async options => {
        const target = await originalNewContext.call(browser, options);
        await seedAccount(target);
        target.on('page', watch);
        return target;
      };
    }
    const errors = [], consoleErrors = [], requests = [], failedRequests = [];
    const watch = async page => {
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => {
        if (message.type() === 'error') consoleErrors.push(message.text());
      });
      // Existing workflow scenarios complete the new first-use naming step.
      // Naming and auth scenarios exercise this dialog explicitly instead.
      if (needsAccount) await page.addLocatorHandler(page.getByRole('dialog', { name: 'A space of your own' }), async dialog => {
        await dialog.getByRole('textbox', { name: /^Workspace name/ }).fill('My workspace');
        await dialog.getByRole('button', { name: 'Save and continue' }).click();
        await expect(dialog).toHaveCount(0);
      });
    };
    await Promise.all(context.pages().map(watch));
    context.on('page', watch);
    context.on('response', response => {
      const path = new URL(response.url()).pathname;
      if (!path.includes('/api/')) return;
      const headers = response.headers();
      requests.push({ method: response.request().method(), path, status: response.status(),
        requestId: headers['x-request-id'] || null, timing: headers['server-timing'] || null });
    });
    context.on('requestfailed', request => failedRequests.push({
      path: new URL(request.url()).pathname, error: request.failure()?.errorText,
    }));
    try { await use(); }
    finally { browser.newContext = originalNewContext; }
    await testInfo.attach('browser-diagnostics', {
      body: JSON.stringify({ errors, consoleErrors, requests, failedRequests }, null, 2),
      contentType: 'application/json',
    });
    expect(errors, 'Uncaught browser errors').toEqual([]);
    // Failed resources are expected in negative/offline tests; keep them in evidence.
    expect(consoleErrors.filter(message => !/Failed to load resource|net::ERR_/i.test(message)),
      'Unexpected browser console errors').toEqual([]);
  }, { auto: true }],
});

export { expect };
