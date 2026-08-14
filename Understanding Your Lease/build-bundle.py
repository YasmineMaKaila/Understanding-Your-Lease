#!/usr/bin/env python3
"""
build-bundle.py — regenerates js/bundle-standalone.js from the canonical sources.

js/bundle-standalone.js is the non-module build consumed by standalone-src.html
(the Claude Design publish path). It used to be maintained as a hand-kept copy of
js/lease-data.js + js/app.js, which meant every content or logic edit had to be
made twice; the two builds had silently diverged. This script derives it instead,
so there is exactly one source of truth.

Run from the project root, after any edit to js/lease-data.js or js/app.js:

    python3 build-bundle.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
p = lambda *a: os.path.join(ROOT, *a)

data_js = open(p('js', 'lease-data.js'), encoding='utf-8').read()
app_js = open(p('js', 'app.js'), encoding='utf-8').read()

# --- lease-data.js: strip ES module exports, keep plain declarations ----------
data_js = re.sub(r'^export const ', 'const ', data_js, flags=re.M)
data_js = re.sub(r'^export function ', 'function ', data_js, flags=re.M)
data_js = re.sub(r'^export default \w+;\s*$', '', data_js, flags=re.M)
if 'export ' in data_js:
    sys.exit('unhandled `export` remains in lease-data.js — check by hand')

# --- the resource shim: standalone-src.html injects the webp/txt payloads as
#     window.__resources, keyed pageNNimg / pageNNtxt ------------------------
SHIM = """

(function () {
  var R = window.__resources || {};
  LEASE.forEach(function (p, i) {
    var n = String(i + 1).padStart(2, '0');
    if (R['page' + n + 'img']) p.image = R['page' + n + 'img'];
    if (R['page' + n + 'txt']) p.pageTextUrl = R['page' + n + 'txt'];
  });
})();
"""

# --- app.js: drop the import line, it is concatenated instead ----------------
app_js = re.sub(r"^import .*?from '\./lease-data\.js';\s*$", '', app_js, flags=re.M)
if re.search(r'^\s*import\s', app_js, flags=re.M):
    sys.exit('unhandled `import` remains in app.js — check by hand')

out = p('js', 'bundle-standalone.js')
open(out, 'w', encoding='utf-8').write(data_js + SHIM + app_js)
print(f'wrote {os.path.relpath(out, ROOT)} ({os.path.getsize(out) / 1024:.0f} KB) '
      f'from js/lease-data.js + js/app.js')
