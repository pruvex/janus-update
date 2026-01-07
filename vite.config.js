import { defineConfig } from 'vite';
import { readFileSync } from 'fs';
import { resolve } from 'path';

// package.json einlesen, um die Version zu bekommen
const packageJson = JSON.parse(readFileSync(resolve(__dirname, 'package.json'), 'utf8'));

// https://vitejs.dev/config/
export default defineConfig({
  // Definiert das Hauptverzeichnis des Projekts. Alle Pfade werden relativ hierzu aufgelöst.
  root: 'frontend',
  
  // Wichtig für Electron: Verwendet relative Pfade für die Asset-Ladung
  base: './',
  
  // Konfiguriert, wohin die gebaute ('production') Version der App gespeichert wird.
  build: {
    // Output-Verzeichnis relativ zum 'root' (frontend)
    outDir: 'dist',
    // Leert das 'dist' Verzeichnis vor jedem Build.
    emptyOutDir: true,
    // Sourcemaps für besseres Debugging in der Produktion
    sourcemap: process.env.NODE_ENV !== 'production',
  },
  
  // Definiert globale Konstanten, die zur Build-Zeit ersetzt werden
  define: {
    'import.meta.env.APP_VERSION': JSON.stringify(packageJson.version)
  },
  
  server: {
    // Wichtig für HMR in Electron
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    
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
