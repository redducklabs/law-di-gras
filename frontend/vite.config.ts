import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Ports per session (see docs/plans/2026-10-02-case-brief-dashboard.md):
//   PORT=5173 API_PORT=8000 npm run dev
const port = Number(process.env.PORT ?? 5173)
const apiPort = process.env.API_PORT ?? '8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port,
    strictPort: true,
    proxy: { '/api': `http://127.0.0.1:${apiPort}` },
  },
})
