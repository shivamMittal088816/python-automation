import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Keep Vite 7's browser targets when upgrading the build tool.
  build: { target: ['chrome107', 'edge107', 'firefox104', 'safari16'] },
  server: { port: 5173, strictPort: true },
});
