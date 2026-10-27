"""Build-time identifier minification; no decoder or application data outside the seed."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / 'compact-config.json').read_text())


def rename(text, mapping, properties=True):
    pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, mapping)) + r')\b')
    def replacement(match):
        before = text[:match.start()]
        if not properties and before.endswith('.') and not before.endswith('...'):
            return match[0]
        return mapping[match[0]]
    return pattern.sub(replacement, text)


def minify(source):
    text = re.sub(r'//[^\n]*', '', source)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s*([{}();,=+*<>?:])\s*', r'\1', text)
    # The templates have no ${...}; quoted strings are never renamed as JS.
    parts = re.split(r'''(`[^`]*`|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")''', text)
    text = ''.join(part if i % 2 else rename(part, CONFIG['js_identifiers'], properties=False)
                   for i, part in enumerate(parts))
    start, end = text.index('precision highp float;'), text.index('}`.replace')
    shader = rename(text[start:end], CONFIG['glsl_identifiers'])
    text = text[:start] + shader + text[end:]
    options = CONFIG['syntax_options']
    if options['operator_whitespace']:
        text = re.sub(r'\s*([/!&|\-])\s*', r'\1', text)
    if options['boolean_literals']:
        text = re.sub(r'\btrue\b', '!0', text)
        text = re.sub(r'\bfalse\b', '!1', text)
    if options['implicit_public_globals']:
        text = re.sub(r'window\.(planet|camera|draw)=', r'\1=', text)
    for name, value in CONFIG['webgl_constants'].items():
        text = text.replace('g.' + name, str(value))
    return text
