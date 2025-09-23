import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  root: 'frontend',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      // Leitet alle Anfragen, die mit '/api' beginnen,
      // an Ihren Python-Backend-Server weiter.
      '/api': {
        target: 'http://127.0.0.1:8001', // Die Adresse Ihres FastAPI-Servers
        changeOrigin: true, // Notwendig für virtuelle Hosts
      },
      // HINWEIS: /user_images muss ebenfalls weitergeleitet werden,
      // damit die Bilder in der Galerie und im Chat angezeigt werden können!
      '/user_images': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      }
    }
  }
});
