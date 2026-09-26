import config from './playwright.config.js';

export default {
  ...config,
  outputDir: 'test-results/site-audit/browser-artifacts',
  reporter: [['list'], ['html', { outputFolder: 'test-results/site-audit/browser-report', open: 'never' }]],
  use: { ...config.use, baseURL: 'http://127.0.0.1:5178', headless: false },
  webServer: [
    { ...config.webServer[0], env: { ...config.webServer[0].env, CORS_ORIGINS: 'http://127.0.0.1:5178' } },
    { ...config.webServer[1], command: 'npm run start -- --port 5178 --strictPort', url: 'http://127.0.0.1:5178' },
  ],
};
