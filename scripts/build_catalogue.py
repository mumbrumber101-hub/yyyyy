#!/usr/bin/env python3
"""Build and validate the About catalogue's reviewed Chicago-style markup.

Edit the embedded JSON in index.html, then run this file. --check validates
without writing. The source strings remain available for search and CSV.
This deliberately does not guess whether an ambiguous title names a story,
collection, character, website, or series; that is an editorial decision.
"""
import argparse
import collections
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'index.html'
DATA = re.compile(r'(<script id="data"[^>]*>)(.*?)(</script>)', re.S)
TABLE = re.compile(r'(<tbody id="entries">)(.*?)(</tbody>)', re.S)


class Fragment(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag != 'em' or attrs:
            raise ValueError('Rich fields allow only <em> with no attributes')
        if self.stack:
            raise ValueError('Nested emphasis is not allowed')
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            raise ValueError('Unbalanced rich-text markup')

    def handle_data(self, text):
        self.text.append(text)


def words(s):
    return ''.join(c for c in s.casefold() if c.isalnum())


def validate(records):
    seen = set()
    for e in records:
        identity = e.get('id', '<missing ID>')
        if not re.fullmatch(r'L\d+', identity) or identity in seen:
            raise ValueError(f'Invalid or duplicate ID: {identity}')
        seen.add(identity)
        if e.get('titleKind') not in ('short', 'book', 'description'):
            raise ValueError(f'{identity}: choose titleKind before publishing')
        for key in ('title', 'venue', 'annotation'):
            rich = e.get(key + 'Html')
            if not isinstance(rich, str) or not rich:
                raise ValueError(f'{identity}: {key}Html needs editorial review')
            parser = Fragment()
            parser.feed(rich)
            parser.close()
            if parser.stack:
                raise ValueError(f'{identity}: unclosed emphasis in {key}')
            if words(''.join(parser.text)) != words(e[key]):
                raise ValueError(f'{identity}: {key}Html differs from its source words')
            if any(t in rich for t in ('““', '””', '‘‘', '<em></em>')):
                raise ValueError(f'{identity}: duplicated delimiters in {key}')
        if e['titleKind'] == 'short' and not (e['titleHtml'].startswith('“') and e['titleHtml'].endswith('”')):
            raise ValueError(f'{identity}: a short-work title needs outer quotation marks')
        if e['titleKind'] == 'book' and '<em>' not in e['titleHtml']:
            raise ValueError(f'{identity}: a book title needs italics')
        for key in ('url', 'alternate'):
            if e.get(key) and not re.match(r'^https?://', e[key]):
                raise ValueError(f'{identity}: invalid {key}')


def row(e):
    esc = html.escape
    alternate = ('<p><a href="' + esc(e['alternate'], quote=True) +
                 '" target="_blank" rel="noopener">Alternate source</a></p>') if e.get('alternate') and e.get('alternateVisible', True) else ''
    annotation_link = alternate if e.get('alternatePlacement') == 'annotation' else ''
    source_link = '' if annotation_link else alternate
    return (f'<tr id="{esc(e["id"])}" data-id="{esc(e["id"])}">'
            f'<td class="who"><span class="entry-id">{esc(e["id"])}</span>'
            f'<strong>{esc(e["author"])}</strong><span>{esc(e["date"])}</span>'
            f'<span class="language">{esc(e["language"])}</span></td>'
            f'<td class="what"><a class="title" href="{esc(e["url"], quote=True)}" target="_blank" rel="noopener">{e["titleHtml"]}</a>'
            f'<span class="venue">{e["venueHtml"]}</span>'
            f'<span class="subject">{esc(e["category"])}</span>{source_link}</td>'
            f'<td class="annotation">{e["annotationHtml"]}{annotation_link}</td>'
            f'<td class="status"><span class="priority">{esc(e["priority"])}</span></td></tr>')


def build(source):
    match = DATA.search(source)
    if not match:
        raise ValueError('Missing catalogue data')
    records = json.loads(match[2])
    validate(records)
    totals = collections.Counter(e['section'] for e in records)
    replacement = ''.join(row(e) for e in records)
    output, n = TABLE.subn(lambda m: m[1] + replacement + m[3], source)
    if n != 1:
        raise ValueError('Expected exactly one catalogue table')
    labels = {'selected': f'Criticism and resources ({totals["Criticism and resources"]})',
              'posts': f'Posts and conversations ({totals["Posts and conversations"]})',
              'all': f'Everything ({len(records)})'}
    for value, label in labels.items():
        output = re.sub(r'(<option value="' + value + r'">)[^<]*(</option>)',
                        lambda m: m[1] + label + m[2], output)
    output = re.sub(r'(<span class="count" id="count"[^>]*>)\d+ entries',
                    lambda m: m[1] + f'{len(records)} entries', output)
    output = re.sub(r'JavaScript is disabled\. All \d+ entries',
                    f'JavaScript is disabled. All {len(records)} entries', output)
    return output, records


if __name__ == '__main__':
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--check', action='store_true')
    opts = args.parse_args()
    original = PAGE.read_text()
    result, records = build(original)
    if opts.check and result != original:
        raise SystemExit('Static rows or counts are stale. Run scripts/build_catalogue.py.')
    if not opts.check:
        PAGE.write_text(result)
    print(f'Validated {len(records)} records: reviewed markup, source words, links, rows, and counts.')
