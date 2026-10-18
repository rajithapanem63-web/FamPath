#!/usr/bin/env node
/**
 * Verify that en.json, te.json, and hi.json all have identical key sets.
 * Exits with code 1 if there are mismatches (used in CI).
 */
const fs = require("fs");
const path = require("path");

const MESSAGES_DIR = path.join(
  __dirname,
  "..",
  "frontend",
  "src",
  "i18n",
  "messages"
);

const LOCALES = ["en", "te", "hi"];

/** Recursively extract all dot-notation keys from a nested object. */
function getKeys(obj, prefix = "") {
  const keys = [];
  for (const [k, v] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${k}` : k;
    if (typeof v === "object" && v !== null && !Array.isArray(v)) {
      keys.push(...getKeys(v, fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

let hasErrors = false;
const messages = {};

// Load all locale files
for (const locale of LOCALES) {
  const filePath = path.join(MESSAGES_DIR, `${locale}.json`);
  if (!fs.existsSync(filePath)) {
    console.error(`❌ Missing locale file: ${filePath}`);
    hasErrors = true;
    continue;
  }
  try {
    messages[locale] = JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (e) {
    console.error(`❌ Parse error in ${locale}.json:`, e.message);
    hasErrors = true;
  }
}

if (!messages["en"]) {
  console.error("❌ en.json is the source of truth and must exist");
  process.exit(1);
}

const enKeys = new Set(getKeys(messages["en"]));
console.log(`✓ en.json has ${enKeys.size} keys`);

// Compare each non-English locale against English
for (const locale of LOCALES.filter((l) => l !== "en")) {
  if (!messages[locale]) continue;

  const lKeys = new Set(getKeys(messages[locale]));
  const missing = [...enKeys].filter((k) => !lKeys.has(k));
  const extra = [...lKeys].filter((k) => !enKeys.has(k));

  if (missing.length === 0 && extra.length === 0) {
    console.log(`✓ ${locale}.json key parity: OK (${lKeys.size} keys)`);
  } else {
    if (missing.length > 0) {
      console.error(
        `❌ ${locale}.json missing ${missing.length} keys:\n  ${missing.slice(0, 10).join("\n  ")}${missing.length > 10 ? "\n  …" : ""}`
      );
      hasErrors = true;
    }
    if (extra.length > 0) {
      console.warn(
        `⚠️  ${locale}.json has ${extra.length} extra keys not in en.json:\n  ${extra.slice(0, 5).join("\n  ")}`
      );
      // Extra keys are a warning, not an error
    }
  }
}

if (hasErrors) {
  console.error("\n❌ i18n key parity check FAILED");
  process.exit(1);
} else {
  console.log("\n✅ i18n key parity check passed");
  process.exit(0);
}
