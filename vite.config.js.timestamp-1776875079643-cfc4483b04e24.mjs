// vite.config.js
import { defineConfig, loadEnv } from "file:///C:/KI/Janus-Projekt/node_modules/vite/dist/node/index.js";
import { readFileSync } from "fs";
import { resolve } from "path";
import { sentryVitePlugin } from "file:///C:/KI/Janus-Projekt/node_modules/@sentry/vite-plugin/dist/esm/index.mjs";
var __vite_injected_original_dirname = "C:\\KI\\Janus-Projekt";
var appVersion = "0.0.0";
try {
  const packageJsonPath = resolve(__vite_injected_original_dirname, "package.json");
  const packageJson = JSON.parse(readFileSync(packageJsonPath, "utf8"));
  appVersion = packageJson.version;
  console.log("--------------------------------------------------");
  console.log(`\u2705 TERMINAL CHECK: Version ${appVersion} gefunden!`);
  console.log("--------------------------------------------------");
} catch (e) {
  console.error("\u274C TERMINAL CHECK: package.json konnte NICHT gelesen werden!");
  console.error(e.message);
}
var vite_config_default = defineConfig(({ mode }) => {
  const env = loadEnv(mode, resolve(__vite_injected_original_dirname, "frontend"), "");
  return {
    root: "frontend",
    base: "./",
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
      })
    ],
    build: {
      outDir: "dist",
      emptyOutDir: true,
      sourcemap: true
    },
    server: {
      host: "127.0.0.1",
      port: 5173,
      strictPort: true,
      proxy: {
        "/api": { target: "http://127.0.0.1:8001", changeOrigin: true },
        "/user_images": { target: "http://127.0.0.1:8001", changeOrigin: true }
      }
    }
  };
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxLSVxcXFxKYW51cy1Qcm9qZWt0XCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCJDOlxcXFxLSVxcXFxKYW51cy1Qcm9qZWt0XFxcXHZpdGUuY29uZmlnLmpzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9DOi9LSS9KYW51cy1Qcm9qZWt0L3ZpdGUuY29uZmlnLmpzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnLCBsb2FkRW52IH0gZnJvbSAndml0ZSc7XG5pbXBvcnQgeyByZWFkRmlsZVN5bmMgfSBmcm9tICdmcyc7XG5pbXBvcnQgeyByZXNvbHZlIH0gZnJvbSAncGF0aCc7XG5pbXBvcnQgeyBzZW50cnlWaXRlUGx1Z2luIH0gZnJvbSBcIkBzZW50cnkvdml0ZS1wbHVnaW5cIjtcblxuLy8gLS0tIFZFUlNJT04gRVJNSVRURUxOIC0tLVxubGV0IGFwcFZlcnNpb24gPSBcIjAuMC4wXCI7XG50cnkge1xuICAgIC8vIFZlcnN1Y2hlIHBhY2thZ2UuanNvbiBpbSBzZWxiZW4gVmVyemVpY2huaXMgd2llIHZpdGUuY29uZmlnLmpzIHp1IGxlc2VuXG4gICAgY29uc3QgcGFja2FnZUpzb25QYXRoID0gcmVzb2x2ZShfX2Rpcm5hbWUsICdwYWNrYWdlLmpzb24nKTtcbiAgICBjb25zdCBwYWNrYWdlSnNvbiA9IEpTT04ucGFyc2UocmVhZEZpbGVTeW5jKHBhY2thZ2VKc29uUGF0aCwgJ3V0ZjgnKSk7XG4gICAgYXBwVmVyc2lvbiA9IHBhY2thZ2VKc29uLnZlcnNpb247XG4gICAgXG4gICAgLy8gTEFVVEUgTUVMRFVORyBJTSBURVJNSU5BTFxuICAgIGNvbnNvbGUubG9nKFwiLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cIik7XG4gICAgY29uc29sZS5sb2coYFx1MjcwNSBURVJNSU5BTCBDSEVDSzogVmVyc2lvbiAke2FwcFZlcnNpb259IGdlZnVuZGVuIWApO1xuICAgIGNvbnNvbGUubG9nKFwiLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cIik7XG59IGNhdGNoIChlKSB7XG4gICAgY29uc29sZS5lcnJvcihcIlx1Mjc0QyBURVJNSU5BTCBDSEVDSzogcGFja2FnZS5qc29uIGtvbm50ZSBOSUNIVCBnZWxlc2VuIHdlcmRlbiFcIik7XG4gICAgY29uc29sZS5lcnJvcihlLm1lc3NhZ2UpO1xufVxuLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuXG5leHBvcnQgZGVmYXVsdCBkZWZpbmVDb25maWcoKHsgbW9kZSB9KSA9PiB7XG4gIGNvbnN0IGVudiA9IGxvYWRFbnYobW9kZSwgcmVzb2x2ZShfX2Rpcm5hbWUsICdmcm9udGVuZCcpLCBcIlwiKTtcblxuICByZXR1cm4ge1xuICAgIHJvb3Q6ICdmcm9udGVuZCcsXG4gICAgYmFzZTogJy4vJyxcbiAgICBcbiAgICAvLyBHbG9iYWxlIEtvbnN0YW50ZW4gZGVmaW5pZXJlbiAoVGV4dC1FcnNldHp1bmcgaW0gQ29kZSlcbiAgICBkZWZpbmU6IHtcbiAgICAgIC8vIFdJQ0hUSUc6IERlciBTdHJpbmcgbXVzcyBub2NobWFsIGluIEpTT04uc3RyaW5naWZ5IGdlcGFja3Qgd2VyZGVuIVxuICAgICAgX19BUFBfVkVSU0lPTl9fOiBKU09OLnN0cmluZ2lmeShhcHBWZXJzaW9uKVxuICAgIH0sXG5cbiAgICBwbHVnaW5zOiBbXG4gICAgICBzZW50cnlWaXRlUGx1Z2luKHtcbiAgICAgICAgb3JnOiBcInBydXZleFwiLFxuICAgICAgICBwcm9qZWN0OiBcImphdmFzY3JpcHQtcmVhY3RcIixcbiAgICAgICAgYXV0aFRva2VuOiBlbnYuU0VOVFJZX0FVVEhfVE9LRU4sXG4gICAgICAgIHJlbGVhc2U6IHtcbiAgICAgICAgICBuYW1lOiBcImphbnVzLXByb2pla3RAXCIgKyBhcHBWZXJzaW9uLFxuICAgICAgICAgIGRlcGxveTogeyBlbnY6IFwicHJvZHVjdGlvblwiIH1cbiAgICAgICAgfSxcbiAgICAgICAgc291cmNlbWFwczogeyBhc3NldHM6IFwiLi9mcm9udGVuZC9kaXN0LyoqXCIgfVxuICAgICAgfSksXG4gICAgXSxcbiAgICBcbiAgICBidWlsZDoge1xuICAgICAgb3V0RGlyOiAnZGlzdCcsXG4gICAgICBlbXB0eU91dERpcjogdHJ1ZSxcbiAgICAgIHNvdXJjZW1hcDogdHJ1ZSxcbiAgICB9LFxuICAgIFxuICAgIHNlcnZlcjoge1xuICAgICAgaG9zdDogJzEyNy4wLjAuMScsXG4gICAgICBwb3J0OiA1MTczLFxuICAgICAgc3RyaWN0UG9ydDogdHJ1ZSxcbiAgICAgIHByb3h5OiB7XG4gICAgICAgICcvYXBpJzogeyB0YXJnZXQ6ICdodHRwOi8vMTI3LjAuMC4xOjgwMDEnLCBjaGFuZ2VPcmlnaW46IHRydWUgfSxcbiAgICAgICAgJy91c2VyX2ltYWdlcyc6IHsgdGFyZ2V0OiAnaHR0cDovLzEyNy4wLjAuMTo4MDAxJywgY2hhbmdlT3JpZ2luOiB0cnVlIH1cbiAgICAgIH1cbiAgICB9XG4gIH07XG59KTtcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBaVAsU0FBUyxjQUFjLGVBQWU7QUFDdlIsU0FBUyxvQkFBb0I7QUFDN0IsU0FBUyxlQUFlO0FBQ3hCLFNBQVMsd0JBQXdCO0FBSGpDLElBQU0sbUNBQW1DO0FBTXpDLElBQUksYUFBYTtBQUNqQixJQUFJO0FBRUEsUUFBTSxrQkFBa0IsUUFBUSxrQ0FBVyxjQUFjO0FBQ3pELFFBQU0sY0FBYyxLQUFLLE1BQU0sYUFBYSxpQkFBaUIsTUFBTSxDQUFDO0FBQ3BFLGVBQWEsWUFBWTtBQUd6QixVQUFRLElBQUksb0RBQW9EO0FBQ2hFLFVBQVEsSUFBSSxrQ0FBNkIsVUFBVSxZQUFZO0FBQy9ELFVBQVEsSUFBSSxvREFBb0Q7QUFDcEUsU0FBUyxHQUFHO0FBQ1IsVUFBUSxNQUFNLGtFQUE2RDtBQUMzRSxVQUFRLE1BQU0sRUFBRSxPQUFPO0FBQzNCO0FBR0EsSUFBTyxzQkFBUSxhQUFhLENBQUMsRUFBRSxLQUFLLE1BQU07QUFDeEMsUUFBTSxNQUFNLFFBQVEsTUFBTSxRQUFRLGtDQUFXLFVBQVUsR0FBRyxFQUFFO0FBRTVELFNBQU87QUFBQSxJQUNMLE1BQU07QUFBQSxJQUNOLE1BQU07QUFBQTtBQUFBLElBR04sUUFBUTtBQUFBO0FBQUEsTUFFTixpQkFBaUIsS0FBSyxVQUFVLFVBQVU7QUFBQSxJQUM1QztBQUFBLElBRUEsU0FBUztBQUFBLE1BQ1AsaUJBQWlCO0FBQUEsUUFDZixLQUFLO0FBQUEsUUFDTCxTQUFTO0FBQUEsUUFDVCxXQUFXLElBQUk7QUFBQSxRQUNmLFNBQVM7QUFBQSxVQUNQLE1BQU0sbUJBQW1CO0FBQUEsVUFDekIsUUFBUSxFQUFFLEtBQUssYUFBYTtBQUFBLFFBQzlCO0FBQUEsUUFDQSxZQUFZLEVBQUUsUUFBUSxxQkFBcUI7QUFBQSxNQUM3QyxDQUFDO0FBQUEsSUFDSDtBQUFBLElBRUEsT0FBTztBQUFBLE1BQ0wsUUFBUTtBQUFBLE1BQ1IsYUFBYTtBQUFBLE1BQ2IsV0FBVztBQUFBLElBQ2I7QUFBQSxJQUVBLFFBQVE7QUFBQSxNQUNOLE1BQU07QUFBQSxNQUNOLE1BQU07QUFBQSxNQUNOLFlBQVk7QUFBQSxNQUNaLE9BQU87QUFBQSxRQUNMLFFBQVEsRUFBRSxRQUFRLHlCQUF5QixjQUFjLEtBQUs7QUFBQSxRQUM5RCxnQkFBZ0IsRUFBRSxRQUFRLHlCQUF5QixjQUFjLEtBQUs7QUFBQSxNQUN4RTtBQUFBLElBQ0Y7QUFBQSxFQUNGO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
