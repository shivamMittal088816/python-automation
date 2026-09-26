import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  expect: { timeout: 10000 },
  use: { baseURL: 'http://127.0.0.1:5174', browserName: 'chromium', channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge', headless: true, trace: 'retain-on-failure' },
  webServer: [
    { command: '..\\backend\\.venv\\Scripts\\python.exe -B ..\\backend\\tests\\browser_fixture_server.py', url: 'http://127.0.0.1:8123/api/v1/mapping/health', timeout: 30000, reuseExistingServer: false, env: { CORS_ORIGINS: 'http://127.0.0.1:5174', SESSION_COOKIE_SECURE: 'false' } },
    { command: 'npm run start -- --port 5174 --strictPort', url: 'http://127.0.0.1:5174', timeout: 30000, reuseExistingServer: false, env: { VITE_API_BASE_URL: 'http://127.0.0.1:8123' } },
  ],
});
