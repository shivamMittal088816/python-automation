import config from './playwright.config.js';

export default {
  ...config,
  testDir: './e2e/live',
  testIgnore: [],
  webServer: undefined,
  outputDir: 'test-results/live/artifacts',
  reporter: [['list'], ['html', { outputFolder: 'test-results/live/report', open: 'never' }]],
  use: { ...config.use, baseURL: process.env.LIVE_BASE_URL || 'http://127.0.0.1:5173', headless: false },
};
