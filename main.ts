// Entry point for the news-image-20261124 competition entry.
//
// The finished front-page image ships in this repository as entry.png.
// This program copies it, byte for byte, into the output directory, so
// every run writes exactly the same bytes: the image the judges see is
// always the one committed beside this file.

import { copyFileSync, mkdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, "entry.png");
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const target = join(outDir, "entry.png");

mkdirSync(outDir, { recursive: true });
copyFileSync(source, target);
console.log(`wrote ${target} (${statSync(target).size} bytes)`);
