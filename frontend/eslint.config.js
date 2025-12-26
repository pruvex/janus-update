import globals from "globals";
import pluginJs from "@eslint/js";

export default [
  {
    // We ignore build folders and external libraries
    ignores: ["node_modules/**", "dist/**", "coverage/**"],
  },
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
        // Global variables that are available in the browser context
        marked: "readonly",
        fetchCostData: "readonly",
        InterAct: "readonly",
      },
      ecmaVersion: "latest",
      sourceType: "module",
    },
  },
  pluginJs.configs.recommended,
  {
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "warn", // Warn instead of error as we're cleaning up legacy code
      "no-console": "off", // Console logs are okay in the Electron client
      semi: ["error", "always"], // Enforce semicolons (Goldstandard)
      quotes: ["error", "double"], // Consistent quotes
    },
  },
];
