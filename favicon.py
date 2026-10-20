"""Install the hostname favicon in complete HTML documents only."""
import re
from pathlib import Path
LINKS = '<link rel="icon" href="/ai-blog/favicon.ico" sizes="16x16 32x32 48x48" type="image/x-icon">\n<link rel="icon" href="/ai-blog/favicon-32x32.png" sizes="32x32" type="image/png">\n<link rel="icon" href="/ai-blog/favicon-192x192.png" sizes="192x192" type="image/png">\n<link rel="apple-touch-icon" href="/ai-blog/apple-touch-icon.png" sizes="180x180">'
def apply(html):
    match = re.search(r'<head\b[^>]*>.*?</head>', html, re.I | re.S)
    if not match:
        return html
    head = match.group(0)
    def keep(m):
        rel = re.search(r"rel\s*=\s*([\"'])(.*?)\1", m.group(0), re.I)
        return '' if rel and any(x in ('icon', 'apple-touch-icon', 'apple-touch-icon-precomposed', 'mask-icon') for x in rel[2].lower().split()) else m.group(0)
    head = re.sub(r'<link\b[^>]*>\n?', keep, head, flags=re.I)
    head = head.replace('</head>', LINKS + '\n</head>')
    return html[:match.start()] + head + html[match.end():]
if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
    for p in root.rglob('*.html'):
        if '.git' not in p.parts and '_site' not in p.parts:
            old = p.read_text(encoding='utf-8')
            new = apply(old)
            if old != new: p.write_text(new, encoding='utf-8')
