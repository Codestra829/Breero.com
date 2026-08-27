#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { extname } from "node:path";

const ROOT = process.cwd();
const REQUIRED_FILES = [
  "apps/web/app/enterprise-design-system.css",
  "docs/design-system.md",
  "docs/design-system-migration.md",
  ".github/CODEOWNERS",
  ".github/pull_request_template.md",
];

const ALLOWED_STYLE_AUTHORITIES = new Set([
  "packages/ui/src/styles.css",
  "apps/web/app/globals.css",
  "apps/web/app/marketplace.css",
  "apps/web/app/brand.css",
  "apps/web/app/enterprise-design-system.css",
]);

const CODE_EXTENSIONS = new Set([".tsx", ".ts", ".jsx", ".js", ".css", ".scss"]);
const errors = [];

function git(args) {
  return execFileSync("git", args, { cwd: ROOT, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
}

function read(path) {
  return readFileSync(path, "utf8");
}

function fail(message) {
  errors.push(message);
}

for (const path of REQUIRED_FILES) {
  if (!existsSync(path)) fail(`missing required governance file: ${path}`);
}

const layout = existsSync("apps/web/app/layout.tsx") ? read("apps/web/app/layout.tsx") : "";
if (!layout.includes('import "./enterprise-design-system.css";')) {
  fail("RootLayout must import enterprise-design-system.css after the existing shared styles");
}
if (!layout.includes("Manrope")) {
  fail("RootLayout must keep the approved Manrope font authority");
}

const shell = existsSync("apps/web/components/app-shell.tsx") ? read("apps/web/components/app-shell.tsx") : "";
if (!shell.includes("<SiteHeader") || !shell.includes("<SiteFooter")) {
  fail("AppShell must retain the shared SiteHeader and SiteFooter");
}

const header = existsSync("apps/web/components/site-header.tsx") ? read("apps/web/components/site-header.tsx") : "";
if (!header.includes("<Logo") || !header.includes('data-cta="header-book"')) {
  fail("SiteHeader must retain the shared BREERO logo and primary header CTA");
}

let base = process.argv[2]?.trim();
if (!base || /^0+$/.test(base)) {
  try {
    base = git(["merge-base", "HEAD", "origin/main"]);
  } catch {
    base = "";
  }
}

let diff = "";
if (base) {
  try {
    diff = git(["diff", "--unified=0", `${base}...HEAD`, "--"]);
  } catch {
    diff = "";
  }
}

if (!diff) {
  console.log("DESIGN_GUARD_RANGE=STRUCTURAL_ONLY");
} else {
  console.log(`DESIGN_GUARD_BASE=${base}`);
  let currentFile = "";

  for (const line of diff.split("\n")) {
    if (line.startsWith("+++ b/")) {
      currentFile = line.slice(6);
      continue;
    }
    if (!line.startsWith("+") || line.startsWith("+++")) continue;
    if (!CODE_EXTENSIONS.has(extname(currentFile))) continue;

    const added = line.slice(1);

    if (/\bstyle\s*=\s*\{\{/.test(added)) {
      fail(`${currentFile}: inline visual style is prohibited`);
    }

    if (/font-family\s*:/.test(added) && !ALLOWED_STYLE_AUTHORITIES.has(currentFile)) {
      fail(`${currentFile}: font-family must be controlled by the shared design system`);
    }

    const rawColor = /#[0-9a-fA-F]{3,8}\b|\brgba?\s*\(|\bhsla?\s*\(/;
    if (rawColor.test(added) && !ALLOWED_STYLE_AUTHORITIES.has(currentFile)) {
      fail(`${currentFile}: literal color added outside approved style/token authority`);
    }

    if (/\b(?:bg|text|border|ring)-(?:red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}\b/.test(added)) {
      fail(`${currentFile}: random palette utility added; use BREERO tokens/shared components`);
    }

    if (/\b(?:m|p|gap|w|h|top|right|bottom|left)-\[[^\]]+\]/.test(added)) {
      fail(`${currentFile}: arbitrary utility value added; use shared spacing/layout tokens`);
    }

    if (/\brounded-full\b/.test(added) && /apps\/web\/app\/.*page\.(t|j)sx?$|apps\/web\/components\//.test(currentFile)) {
      fail(`${currentFile}: new decorative pill geometry requires a design-system exception`);
    }

    if ((currentFile.startsWith("apps/web/") || currentFile.startsWith("packages/ui/")) &&
        /\.(css|scss)$/.test(currentFile) &&
        !ALLOWED_STYLE_AUTHORITIES.has(currentFile)) {
      fail(`${currentFile}: new/changed parallel stylesheet is outside approved authorities`);
    }
  }
}

if (errors.length) {
  console.error("DESIGN_SYSTEM_GUARD=FAIL");
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log("DESIGN_SYSTEM_GUARD=PASS");
