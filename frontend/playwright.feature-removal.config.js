import config from './playwright.config.js';
export default {
  ...config,
  use: { ...config.use, baseURL: 'http://127.0.0.1:5174' },
  webServer: [
    { ...config.webServer[0], env: { CORS_ORIGINS: 'http://127.0.0.1:5174,http://localhost:5174' } },
    { ...config.webServer[1], command: 'npm run dev -- --port 5174', url: 'http://127.0.0.1:5174' },
  ],
};
