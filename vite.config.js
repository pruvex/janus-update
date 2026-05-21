import { defineConfig, loadEnv } from 'vite';
import { readFileSync } from 'fs';
import { resolve } from 'path';
import { sentryVitePlugin } from "@sentry/vite-plugin";

const securityHeaders = {
  'Content-Security-Policy': [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob: http://127.0.0.1:8001 http://localhost:8001 janus:",
    "font-src 'self' data:",
    "connect-src 'self' http://127.0.0.1:8001 http://localhost:8001 http://localhost:11434 ws://127.0.0.1:5173 ws://localhost:5173",
    "media-src 'self' data: blob: http://127.0.0.1:8001 http://localhost:8001",
    "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com",
    "object-src 'none'",
    "base-uri 'self'",
    "frame-ancestors 'self' janus:",
    "form-action 'self'",
  ].join('; '),
  'X-Frame-Options': 'SAMEORIGIN',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=()',
};

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
  const shouldUploadSourcemaps = process.env.JANUS_UPLOAD_SOURCEMAPS === "1" && Boolean(env.SENTRY_AUTH_TOKEN);
  const shouldEmitSourcemaps = process.env.JANUS_EMIT_SOURCEMAPS === "1" || shouldUploadSourcemaps;
  const plugins = [];

  if (shouldUploadSourcemaps) {
    plugins.push(
      sentryVitePlugin({
        org: "pruvex",
        project: "javascript-react",
        authToken: env.SENTRY_AUTH_TOKEN,
        release: {
          name: "janus-projekt@" + appVersion,
          deploy: { env: "production" }
        },
        sourcemaps: { assets: "./frontend/dist/**" }
      })
    );
  }

  return {
    root: 'frontend',
    base: './',
    
    // Globale Konstanten definieren (Text-Ersetzung im Code)
    define: {
      // WICHTIG: Der String muss nochmal in JSON.stringify gepackt werden!
      __APP_VERSION__: JSON.stringify(appVersion)
    },

    plugins,
    
    build: {
      outDir: 'dist',
      emptyOutDir: true,
      sourcemap: shouldEmitSourcemaps,
    },
    
    server: {
      host: '127.0.0.1',
      port: 5173,
      strictPort: true,
      headers: securityHeaders,
      proxy: {
        '/api': { target: 'http://127.0.0.1:8001', changeOrigin: true },
        '/user_images': { target: 'http://127.0.0.1:8001', changeOrigin: true }
      }
    }
  };
});
