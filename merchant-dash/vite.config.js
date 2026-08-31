import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'

export default defineConfig({
  plugins: [
    frappeui({
      frappeProxy: false,
      jinjaBootData: false,
      buildConfig: false,
    }),
    vue(),
  ],
  optimizeDeps: {
    exclude: ['frappe-ui'],
    include: [
      'feather-icons',
      'tippy.js',
      'engine.io-client',
      'socket.io-client',
      'debug',
    ],
  },
})
