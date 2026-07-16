/**
 * Regenerates src/vendor/fontawesome/fontawesome-subset.css.
 *
 * The full @fortawesome/fontawesome-free "all.css" ships every icon in the
 * library (~90KB minified) even though this site only uses ~30 of them.
 * This script runs PurgeCSS against the actual source tree so the shipped
 * CSS only contains the icons/classes that are really referenced.
 *
 * Re-run this (`node scripts/build-fontawesome-subset.js`) whenever a new
 * `fa-*` icon class is added anywhere in src/, then commit the updated
 * fontawesome-subset.css.
 */
const fs = require("fs");
const path = require("path");
const { PurgeCSS } = require("purgecss");

const ROOT = path.resolve(__dirname, "..");
const SRC_CSS = path.join(
  ROOT,
  "node_modules/@fortawesome/fontawesome-free/css/all.css"
);
const OUT_DIR = path.join(ROOT, "src/vendor/fontawesome");
const OUT_CSS = path.join(OUT_DIR, "fontawesome-subset.css");
const WEBFONTS_SRC = path.join(
  ROOT,
  "node_modules/@fortawesome/fontawesome-free/webfonts"
);
const WEBFONTS_OUT = path.join(OUT_DIR, "webfonts");
const NEEDED_FONTS = ["fa-solid-900.woff2", "fa-regular-400.woff2", "fa-brands-400.woff2"];

async function main() {
  const result = await new PurgeCSS().purge({
    content: [path.join(ROOT, "src/**/*.{js,jsx}")],
    css: [SRC_CSS],
    safelist: [
      // Base/shared rules PurgeCSS's selector-matching can miss because
      // they're combined selectors (.fa,.fa-solid,.fab,... {...}).
      /^\.fa$/,
      /^\.fa-solid$/,
      /^\.fa-regular$/,
      /^\.fa-brands$/,
      /^\.fa-classic$/,
      /^\.fas$/,
      /^\.far$/,
      /^\.fab$/,
    ],
  });

  // PurgeCSS only drops unused *selectors*; it leaves @font-face at-rules
  // alone even when nothing references that font-family. The package ships
  // legacy v4/v5-compat @font-face blocks ("Font Awesome 5 Free/Brands",
  // "FontAwesome") that we don't use (all icons here use the v6/v7 "fa-solid
  // / fa-regular / fa-brands" classes) — strip them so we don't ship or
  // reference webfont files we didn't copy.
  const KEEP_FAMILIES = ["Font Awesome 7 Free", "Font Awesome 7 Brands"];
  const css = result[0].css
    .replace(
      /@font-face\s*\{[^}]*\}/g,
      (block) => (KEEP_FAMILIES.some((f) => block.includes(`"${f}"`)) ? block : "")
    )
    // Output CSS + its webfonts/ dir are siblings (both directly under
    // OUT_DIR), unlike the source package's css/ + webfonts/ layout.
    .replace(/\.\.\/webfonts\//g, "./webfonts/");

  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(OUT_CSS, css, "utf8");

  fs.mkdirSync(WEBFONTS_OUT, { recursive: true });
  for (const font of NEEDED_FONTS) {
    fs.copyFileSync(path.join(WEBFONTS_SRC, font), path.join(WEBFONTS_OUT, font));
  }

  const before = fs.statSync(SRC_CSS).size;
  const after = fs.statSync(OUT_CSS).size;
  console.log(
    `fontawesome-subset.css: ${(before / 1024).toFixed(1)}KB -> ${(after / 1024).toFixed(1)}KB`
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
