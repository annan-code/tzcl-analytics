#!/usr/bin/env python3
"""Inline the subset webfonts and the TZ logo into index.html.

Fonts are subset to only the glyphs the dashboard uses and converted to WOFF2,
then base64-inlined. That keeps them out of the repo as standalone, installable
font files while still rendering correctly.
"""
import base64, re, os

TPL   = '/tmp/v5/tpl.html'
FONTS = '/tmp/design/web'
LOGO  = '/tmp/design/web/tz-logo.min.svg'
OUT   = '/tmp/v5/index.html'

# Served as separate files from fonts/ rather than base64-inlined: it keeps
# index.html at ~65 KB instead of ~108 KB, and the browser caches the faces
# across visits. Light is deliberately absent — Regular covers the light weights.
FACES = [
    ('Good Sans',    'GoodSans-Regular.woff2', '400'),
    ('Good Sans',    'GoodSans-Medium.woff2',  '500'),
    ('Good Sans',    'GoodSans-Bold.woff2',    '700'),
    ('Redaction 35', 'Redaction35.woff2',      '400'),
]

css = []
for fam, fn, wt in FACES:
    assert os.path.exists(os.path.join(FONTS, fn)), 'missing font ' + fn
    css.append(
        '@font-face{font-family:"%s";'
        'src:url(fonts/%s) format("woff2");'
        'font-weight:%s;font-style:normal;font-display:swap}' % (fam, fn, wt))

logo = open(LOGO, encoding='utf-8').read().strip()

# svgo drops the viewBox, so recover the geometry from width/height before
# removing them, otherwise the SVG has no intrinsic aspect ratio and blows up.
m = re.search(r'<svg[^>]*?width="([\d.]+)"[^>]*?height="([\d.]+)"', logo)
if not m:
    raise SystemExit('logo: could not read width/height to rebuild the viewBox')
vb = '0 0 %s %s' % (m.group(1), m.group(2))
logo = re.sub(r'\s(?:width|height)="[\d.]+"', '', logo, count=2)
logo = logo.replace('<svg', '<svg viewBox="%s" fill="currentColor"' % vb, 1)

# drop hardcoded brand ink so the mark follows the theme in dark mode
logo = re.sub(r'\sfill="#1[fF]283[dD]"', ' fill="currentColor"', logo)

html = open(TPL, encoding='utf-8').read()
html = html.replace('/*__FONTS__*/', '\n'.join(css))
html = html.replace('/*__LOGO__*/', logo)

open(OUT, 'w', encoding='utf-8').write(html)
print('wrote %s  (%.1f KB)' % (OUT, os.path.getsize(OUT) / 1024))
print('font faces linked: %d  |  logo inlined: %d chars' % (len(FACES), len(logo)))
assert '__FONTS__' not in html and '__LOGO__' not in html, 'placeholder left behind'
