// dashboard/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/telegram-bot/', // نام مخزن شما
  build: {
    emptyOutDir: true, // پاک کردن فایل‌های بیلد قبلی قبل از ساخت جدید
  }
})