import { defineConfig, loadEnv } from 'vite';
import { readFileSync } from 'fs';
import { resolve } from 'path';
import { sentryVitePlugin } from "@sentry/vite-plugin";

// --- VERSION ERMITTELN ---
let appVersion = "0.0.0";
try {
    // Versuche package.json im selben Verzeichnis wie vite.config.js zu lesen
    const packageJsonPath = resolve(__dirname, 'package.json');
    const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf8'));
    appVersion = packageJson.version;
    
    // LAUTE MELDUNG IM TERMINAL
    console.log("--------------------------------------------------");
    console.log(`✅ TERMINAL CHECK: Version ${appVersion} gefunden!`);
    console.log("--------------------------------------------------");
} catch (e) {
    console.error("❌ TERMINAL CHECK: package.json konnte NICHT gelesen werden!");
    console.error(e.message);
}
// -------------------------

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, resolve(__dirname, 'frontend'), "");

  return {
    root: 'frontend',
    base: './',
    
    // Globale Konstanten definieren (Text-Ersetzung im Code)
    define: {
      // WICHTIG: Der String muss nochmal in JSON.stringify gepackt werden!
      __APP_VERSION__: JSON.stringify(appVersion)
    },

    plugins: [
      sentryVitePlugin({
        org: "pruvex",
        project: "javascript-react",
        authToken: env.SENTRY_AUTH_TOKEN,
        release: {
          name: "janus-projekt@" + appVersion,
          deploy: { env: "production" }
        },
        sourcemaps: { assets: "./frontend/dist/**" }
      }),
    ],
    
    build: {
      outDir: 'dist',
      emptyOutDir: true,
      sourcemap: true,
    },
    
    server: {
      host: '127.0.0.1',
      port: 5173,
      strictPort: true,
      proxy: {
        '/api': { target: 'http://127.0.0.1:8001', changeOrigin: true },
        '/user_images': { target: 'http://127.0.0.1:8001', changeOrigin: true }
      }
    }
  };
});
