import { defineConfig } from "vite";

// HA serves this bundle from the integration's static path (see panel.py /
// const.py PANEL_STATIC_PATH); `base` must match so any future chunk/asset
// imports resolve correctly.
export default defineConfig({
  base: "/home_upkeep_static/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    lib: {
      entry: "src/entrypoint.ts",
      formats: ["es"],
      fileName: () => "entrypoint.js",
    },
  },
});
