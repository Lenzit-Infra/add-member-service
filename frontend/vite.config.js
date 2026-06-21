// dashboard/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Served from the custom domain root (lenzit.ir), not a GitHub Pages
  // project subpath — so base is "/", not "/<repo-name>/".
  base: '/',
  build: {
    emptyOutDir: true, // پاک کردن فایل‌های بیلد قبلی قبل از ساخت جدید
  }
})