#!/usr/bin/env python3
"""
build-standalone.py — folds the multi-file project into one index-standalone.html
for immediate preview (opens straight off the file system, no server).

  * css/styles.css      -> inline <style>
  * assets/*.webp       -> data: URLs on each page's `image`
  * assets/text/*.txt   -> inlined as `pageText` on each page
  * js/lease-data.js    -> inline module
  * js/app.js           -> inline module (the import line is dropped)

Run from the project root:  python3 build-standalone.py
"""
import base64, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
p = lambda *a: os.path.join(ROOT, *a)

html = open(p('index.html'), encoding='utf-8').read()
css = open(p('css', 'styles.css'), encoding='utf-8').read()
data_js = open(p('js', 'lease-data.js'), encoding='utf-8').read()
app_js = open(p('js', 'app.js'), encoding='utf-8').read()

# ---- fold the assets into the data model -----------------------------------
m = re.search(r'export const LEASE = (\[.*?\]);\n', data_js, re.S)
if not m:
    sys.exit('could not find the LEASE export in js/lease-data.js')
lease = json.loads(m.group(1))

total = 0
for pg in lease:
    img = p(pg['image'])
    raw = open(img, 'rb').read()
    total += len(raw)
    pg['image'] = 'data:image/webp;base64,' + base64.b64encode(raw).decode('ascii')
    pg['pageText'] = open(p(pg['pageTextUrl']), encoding='utf-8').read()

data_js = data_js[:m.start(1)] + json.dumps(lease, ensure_ascii=False) + data_js[m.end(1):]

# ---- stitch --------------------------------------------------------------
app_js = re.sub(r"^import .*?from '\./lease-data\.js';\s*$", '', app_js, flags=re.M)

html = html.replace('<link rel="stylesheet" href="css/styles.css">',
                    '<style>\n' + css + '\n</style>')
html = html.replace('<link rel="preload" as="image" href="assets/lease-page-01-sanitized.webp">', '')
html = html.replace('<script type="module" src="js/app.js"></script>',
                    '<script type="module">\n' + data_js + '\n' + app_js + '\n</script>')
html = html.replace('<title>Understanding Your Lease — Interactive Guide</title>',
                    '<title>Understanding Your Lease — Interactive Guide (standalone)</title>')

out = p('index-standalone.html')
open(out, 'w', encoding='utf-8').write(html)
print(f'wrote {os.path.relpath(out, ROOT)}  '
      f'({os.path.getsize(out)/1024/1024:.2f} MB; {total/1024:.0f} KB of images inlined)')
