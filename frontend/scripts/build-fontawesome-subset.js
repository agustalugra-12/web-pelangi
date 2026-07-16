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
const { execFileSync } = require("child_process");
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

// Which style each non-solid icon uses (checked against src/**/*.{js,jsx}
// via `fa-regular fa-xxx` / `fa-brands fa-xxx` pairs in className strings).
// Everything not listed here is assumed fa-solid. Update this if a new
// fa-regular/fa-brands icon is added anywhere in the app.
const REGULAR_ICONS = ["fa-clock"];
const BRANDS_ICONS = ["fa-whatsapp"];

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

  // The CSS subset above only trims *selectors* — the @font-face src still
  // points at the full webfont, which contains every glyph in that style
  // (~1500+ for solid, ~500+ for brands) even though we use ~30 total. Pull
  // the exact codepoints this subset actually references out of the CSS and
  // use fonttools (pyftsubset) to cut real glyph-level font files.
  const codepoints = [...css.matchAll(/--fa:\s*"\\([0-9a-fA-F]+)"/g)].map((m) => `0x${m[1]}`);
  // fa-plus's glyph is the literal "+" character, not a private-use codepoint.
  if (css.includes(".fa-plus")) codepoints.push("0x2B");

  const iconOf = (line) => (line.match(/\.(fa-[a-z0-9-]+)\s*\{/) || [])[1];
  const byFamily = { regular: [], brands: [], solid: [] };
  for (const block of css.split("}")) {
    const icon = iconOf(block);
    const cp = block.match(/--fa:\s*"\\([0-9a-fA-F]+)"/);
    if (!icon || !cp) continue;
    const family = REGULAR_ICONS.includes(icon)
      ? "regular"
      : BRANDS_ICONS.includes(icon)
        ? "brands"
        : "solid";
    byFamily[family].push(`0x${cp[1]}`);
  }
  if (css.includes(".fa-plus")) byFamily.solid.push("0x2B");

  fs.mkdirSync(WEBFONTS_OUT, { recursive: true });
  const FONT_FAMILY_FILE = {
    solid: "fa-solid-900.woff2",
    regular: "fa-regular-400.woff2",
    brands: "fa-brands-400.woff2",
  };
  for (const [family, file] of Object.entries(FONT_FAMILY_FILE)) {
    const src = path.join(WEBFONTS_SRC, file);
    const dest = path.join(WEBFONTS_OUT, file);
    const unicodes = byFamily[family];
    if (unicodes.length === 0) {
      fs.copyFileSync(src, dest);
      continue;
    }
    execFileSync("pyftsubset", [
      src,
      `--output-file=${dest}`,
      `--unicodes=${unicodes.join(",")}`,
      "--flavor=woff2",
      "--no-layout-closure",
    ]);
  }

  const before = fs.statSync(SRC_CSS).size;
  const after = fs.statSync(OUT_CSS).size;
  console.log(
    `fontawesome-subset.css: ${(before / 1024).toFixed(1)}KB -> ${(after / 1024).toFixed(1)}KB`
  );
  for (const file of NEEDED_FONTS) {
    const b = fs.statSync(path.join(WEBFONTS_SRC, file)).size;
    const a = fs.statSync(path.join(WEBFONTS_OUT, file)).size;
    console.log(`${file}: ${(b / 1024).toFixed(1)}KB -> ${(a / 1024).toFixed(1)}KB`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
