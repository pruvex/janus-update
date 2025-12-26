import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
  // Definiert das Hauptverzeichnis des Projekts. Alle Pfade werden relativ hierzu aufgelöst.
  root: 'frontend',
  
  // Konfiguriert, wohin die gebaute ('production') Version der App gespeichert wird.
  build: {
    // Der Output-Pfad ist relativ zum 'root'. Wir gehen einen Ordner zurück ('..')
    // und speichern alles im 'dist' Ordner im Hauptverzeichnis.
    outDir: '../dist',
    // Leert das 'dist' Verzeichnis vor jedem Build.
    emptyOutDir: true
  },
  
  server: {
    proxy: {
      // Leitet alle Anfragen, die mit '/api' beginnen, an den Python-Backend-Server weiter
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      // Weiterleitung für Benutzerbilder
      '/user_images': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      }
    }
  }
});
