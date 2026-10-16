import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In dev the UI runs on 5173 and the API on 8000, so proxy /api through vite.
// In Docker and Kubernetes nginx / the ingress does the same job.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});
