import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

// One self-contained index.html: scripts, styles, fonts and the drill data all
// inlined. It opens from the filesystem with no server and no network, which is
// what the venue allows, and the same file can be hosted anywhere unchanged.
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: { target: "es2022", cssCodeSplit: false, assetsInlineLimit: 100_000_000 },
});
