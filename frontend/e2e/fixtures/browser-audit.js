import { test as base, expect } from '@playwright/test';

// Capture browser evidence for every scenario, including additional tabs.
export const test = base.extend({
  browserAudit: [async ({ context }, use, testInfo) => {
    const errors = [], consoleErrors = [], requests = [], failedRequests = [];
    const watch = page => {
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => {
        if (message.type() === 'error') consoleErrors.push(message.text());
      });
    };
    context.pages().forEach(watch);
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
    await use();
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
