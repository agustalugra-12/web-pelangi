// Thin CLI wrapper around render.jsx's renderHome(): reads {content, lang, origin} JSON
// from stdin, prints ONLY the rendered HTML string to stdout (diagnostics go to stderr
// so the Python caller can treat stdout as a pure payload).
import { renderHome } from "./render.jsx";

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    process.stdin.on("error", reject);
  });
}

async function main() {
  const raw = await readStdin();
  const { content, lang, origin, path, blogList, blogDetail } = JSON.parse(raw);
  const html = await renderHome({ content, lang, origin, path, blogList, blogDetail });
  process.stdout.write(html);
}

main().catch((err) => {
  console.error(err.stack || err.message || String(err));
  process.exit(1);
});
