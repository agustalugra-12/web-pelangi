// Builds the Node-target SSR bundle (frontend/ssr/dist/render.cjs) from ssr/cli.mjs.
// Kept entirely separate from CRA/craco - this is the ONLY place esbuild is used in
// this project. Run via `npm run build:ssr` (frontend/package.json).
import * as esbuild from "esbuild";
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const srcDir = path.resolve(__dirname, "../src");

// jsconfig.json maps "@/*" -> "src/*" for webpack/craco; esbuild needs its own
// resolution for the same alias. Recurses into esbuild's own resolve algorithm
// (extension probing, index files, etc.) instead of hand-rolling it.
const atAliasPlugin = {
  name: "at-alias",
  setup(build) {
    build.onResolve({ filter: /^@\// }, async (args) => {
      const result = await build.resolve("./" + args.path.slice(2), {
        resolveDir: srcDir,
        kind: args.kind,
      });
      if (result.errors.length > 0) return { errors: result.errors };
      return { path: result.path };
    });
  },
};

// Only frontend/src/App.js contains JSX under a plain .js extension (confirmed via
// source audit - every other src file with JSX is already .jsx). Scope the jsx loader
// to just our own src tree so node_modules/**/*.js keeps its default (js) loader -
// deliberately not a blanket --loader:.js=jsx across third-party code we don't control.
const srcJsxLoaderPlugin = {
  name: "src-js-as-jsx",
  setup(build) {
    build.onLoad({ filter: /\.js$/, namespace: "file" }, async (args) => {
      if (!args.path.startsWith(srcDir + path.sep)) return null;
      const contents = await fs.promises.readFile(args.path, "utf8");
      return { contents, loader: "jsx" };
    });
  },
};

await esbuild.build({
  entryPoints: [path.join(__dirname, "cli.mjs")],
  outfile: path.join(__dirname, "dist", "render.cjs"),
  bundle: true,
  platform: "node",
  format: "cjs",
  target: "node20",
  // CRA/react-scripts 5 uses the automatic JSX runtime (no explicit `import React`
  // needed in component files) - match that here or unimported-React components crash.
  jsx: "automatic",
  // No CSS import exists in Home's render path itself, but App.js pulls in App.css -
  // irrelevant to SSR text output, so stub it out entirely rather than parse it.
  loader: { ".css": "empty" },
  define: { "process.env.NODE_ENV": '"production"' },
  plugins: [atAliasPlugin, srcJsxLoaderPlugin],
  logLevel: "info",
});
