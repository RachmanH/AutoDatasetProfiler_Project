// import { defineConfig } from 'vite'
// import react from '@vitejs/plugin-react'
// import tailwindcss from '@tailwindcss/vite'

// export default defineConfig({
//   plugins: [react(), tailwindcss()],
//   server: {
//     port: 5173,
//     proxy: {
//       '/api': {
//         target: 'http://localhost:8000',
//         timeout: 180000,
//         proxyTimeout: 180000,
//       },
//     },
//   },
// })
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: [
      'strongman-kilometer-endpoint.ngrok-free.dev',
    ],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        timeout: 180000,
        proxyTimeout: 180000,
        changeOrigin: true,
      },
    },
  },
})