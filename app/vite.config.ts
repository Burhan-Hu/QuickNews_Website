import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vite.dev/config/
export default defineConfig({
  base: './',
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/sru': 'http://localhost:5000',
      '/api': 'http://localhost:5000',
      '/health': 'http://localhost:5000',
    },
  },
});
