#!/usr/bin/env python3
"""Generate Chicago bibliography citations from the catalogue's recorded evidence.

Unknown dates, authors, editors, and publishers must never be supplied by guess.
The author registry and exceptional print sources are reviewed explicitly.
"""
import calendar
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
AUTHORS = json.loads((ROOT / 'citation-authors.json').read_text())


def text(s):
    return html.unescape(re.sub('<[^>]+>', '', s))


def sentence(s):
    s = s.strip()
    if not s:
        return ''
    if s.endswith('”'):
        body = s[:-1]
        return body + ('' if text(body).endswith(('.', '?', '!', '…')) else '.') + '”'
    return s + ('' if text(s).endswith(('.', '?', '!', '…')) else '.')


def date_value(raw):
    """Only convert dates explicitly identified by the record."""
    if re.match(r'(?i)about|approximately|undated|date not|exact |individual', raw):
        return ''
    if raw == '2025/2026':
        return ''
    raw = re.sub(r'^(Published|Online|Opened|Republished)\s+', '', raw, flags=re.I)
    if raw.startswith('Updated '):
        return 'Last modified ' + date_value(raw[8:])
    if raw.startswith('Last homepage revision '):
        return 'Last modified ' + raw[23:]
    m = re.fullmatch(r'(\d{4})[–-](\d{4})', raw)
    if m:
        return raw
    m = re.match(r'^(\d{4})-(\d{2})/(\d{2})', raw)
    if m:
        return f'{calendar.month_name[int(m[2])]}–{calendar.month_name[int(m[3])]} {m[1]}'
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2}) to (\d{4})-(\d{2})-(\d{2})', raw)
    if m:
        if (m[1], m[2]) == (m[4], m[5]):
            return f'{calendar.month_name[int(m[2])]} {int(m[3])}–{int(m[6])}, {m[1]}'
        return date_value(raw.split(' to ')[0]) + '–' + date_value(raw.split(' to ')[1])
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})[–-](\d{2})(?!\d)', raw)
    if m:
        return f'{calendar.month_name[int(m[2])]} {int(m[3])}–{int(m[4])}, {m[1]}'
    m = re.match(r'^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?(?=$|[ ;,(])', raw)
    if m:
        year, month, day = m.groups()
        if month and day:
            return f'{calendar.month_name[int(month)]} {int(day)}, {year}'
        if month:
            return f'{calendar.month_name[int(month)]} {year}'
        if raw == '2022 autumn':
            return 'Autumn 2022'
        return year
    m = re.match(r'((?:January|February|March|April|May|June|July|August|September|October|November|December|Spring|Summer|Fall|Winter)(?:[–-](?:January|February|March|April|May|June|July|August|September|October|November|December))? \d{4})', raw)
    return m[1] if m else ''


def pages(value):
    def shorten(m):
        a, b = int(m[1]), int(m[2])
        if b <= a or a < 100 or a % 100 == 0 or len(str(a)) != len(str(b)):
            return m[0]
        if 1 <= a % 100 <= 9 and a // 100 == b // 100:
            return str(a) + '–' + str(b % 100)
        common = 0
        for x, y in zip(str(a), str(b)):
            if x != y:
                break
            common += 1
        return str(a) + '–' + str(b)[-max(2, len(str(b)) - common):]
    return re.sub(r'(\d+)[–-](\d+)', shorten, value)


INTERVIEWS = {
    'L020': ('Lafferty, R. A.', 'Darrell Schweitzer'),
    'L044': ('Lafferty, R. A.', 'Paul Walker'),
    'L047': ('Lafferty, R. A.', 'Robert Whitaker Sirignano'),
    'L089': ('Ellison, Harlan', 'Andrew Mass'),
    'L156': ('Pelan, John', 'John Owen'),
    'L190': ('Cheek, Kevin', 'Science Fiction Book Club participants'),
    'L239': ('Lafferty, R. A.', 'Tom Jackson'),
    'L334': ('Nat', 'Kevin Cheek'),
    'L359': ('Swanwick, Michael', 'Stephen Case'),
    'L677': ('Evenson, Brian', 'Gauraa Shekhar'),
}

# These select the identified edition, not a mixture of original and reprint.
SOURCE_OVERRIDES = {
    'L028': ('<em>THATTA ONLINE</em>, no. 458 (July 2026).', 'The catalogue also records the column number as 336.'),
    'L384': ('Ktistec Press, 2014–2020.', 'This entry covers volumes 1–5; editorial roles are not fully recorded.'),
    'L394': ('Springer Nature, n.d.', 'Book title, editors, page range, and publication year are not established in this record. Verify them before using this chapter citation.'),
    'L502': ('Arno Press, 1975.', 'This cites the published book. The original dissertation was submitted to East Texas State University in 1971.'),
    'L503': ('In <em>Clockwork Worlds: Mechanized Environments in SF</em>, 105–13. 1983.', 'This cites the original chapter. Editors and publisher are not recorded; the link describes a later reprint.'),
    'L504': ('<em>The Journal of American Culture</em> 2, no. 2 (1979): 279–87.', 'This cites the original journal article, not its later reprints.'),
    'L505': ('Bloomsbury Academic, 2020.', 'The catalogue directs readers to chapter 3. This is a citation to the whole book.'),
    'L506': ('In <em>Imagining Apocalypse: Studies in Cultural Crisis</em>, edited by David Seed. Palgrave Macmillan, 2000.', 'The chapter occupies pages 27–44. Chicago’s eighteenth edition does not require a chapter page range in a bibliography.'),
    'L507': ('In <em>Twentieth-Century American Science-Fiction Writers</em>, part 1 (A–L), 250–55. Vol. 8 of <em>Dictionary of Literary Biography</em>. Gale, 1981.', 'The volume editor is not recorded. The link is a bibliographic record, not the full entry.'),
    'L508': ('In <em>Supernatural Fiction Writers</em>, 1045–52. 1985.', 'This cites the original version. Editors and publisher are not recorded; a revised 2003 version has a different title and page range.'),
    'L509': ('In <em>Survey of Science Fiction Literature</em>, edited by Frank N. Magill, 2:574–78. Salem Press, 1979.', 'The link is a bibliographic record, not the full entry.'),
    'L644': ('<em>eI</em>, no. 36 (February 2008).', 'This cites the linked reprint of the December 1973 interview in Vertex. The reprint page range is not recorded.'),
}

VENUE_OVERRIDES = {
    'L258': '<em>SIGMA Review</em>', 'L366': 'Terry Bisson',
    'L423': 'Homo Magi', 'L455': 'WEB本の雑誌', 'L456': 'WEB本の雑誌',
    'L457': '<em>Мир фантастики</em>', 'L458': '<em>Мир фантастики</em>',
    'L513': '<em>Nemonymous Night</em>', 'L566': '<em>The Pickup</em>',
    'L606': '<em>The Colin McEnroe Show</em>. Connecticut Public',
    'L680': 'Conceptual Fiction', 'L690': 'Lost Books',
}


def citation(e):
    if e['author'] not in AUTHORS:
        raise ValueError(e['id'] + ': review this author in citation-authors.json')
    author = AUTHORS[e['author']]
    title = e['titleHtml']
    date = date_value(e['date'])
    venue = VENUE_OVERRIDES.get(e['id'], e['venueHtml'])
    notes = []
    if not re.fullmatch(r'\d{4}(?:-\d{2}(?:-\d{2})?)?|Undated', e['date']):
        notes.append('Recorded date: ' + e['date'] + '.')
    if not author:
        notes.append('No verified author is recorded; the citation begins with the title.')
    if e['titleKind'] == 'description':
        notes.append('The catalogue uses a descriptive label for this source. Check the original title before formal submission.')
    attribution = ''
    if e['id'] in INTERVIEWS:
        author, interviewer = INTERVIEWS[e['id']]
        attribution = 'Interview by ' + html.escape(interviewer) + '.'
    elif '; translated by ' in e['author']:
        attribution = 'Translated by ' + html.escape(e['author'].split('; translated by ')[1]) + '.'
    if e['id'] == 'L401':
        title = '“Mapping Planet Auschwitz: Non-Mimetic Writing and the Holocaust in Anglo-American Fiction”'
        notes.append('The catalogue directs readers to section 2.2; the thesis date is 2016, not the 2017 repository date.')
    source = ''
    needs_access = False
    # The linked PDFs are the reprinted issues, with issue-specific pagination.
    fol = re.search(r'<em>Feast of Laughter</em> (\d), pp\. ([\d–-]+)', venue)
    if fol and 'drive.google.com/' in e['url']:
        year = {'1': '2014', '2': '2015', '3': '2015', '4': '2017', '5': '2020'}[fol[1]]
        source = f'<em>Feast of Laughter</em>, no. {fol[1]} ({year}): {pages(fol[2])}.'
        if 'reprint' in e['date'].lower() or not e['date'].startswith(year):
            notes.append('This cites the linked Feast of Laughter edition and its page range.')
    elif e['id'] in SOURCE_OVERRIDES:
        source, note = SOURCE_OVERRIDES[e['id']]
        notes.append(note)
    elif re.search(r'(MA|PhD|DPhil) (?:thesis|dissertation)', venue):
        m = re.match(r'(.*?) (MA|PhD|DPhil) (?:thesis|dissertation)', venue)
        degree = 'Master’s thesis' if m[2] == 'MA' else 'PhD diss.' if m[2] == 'PhD' else 'DPhil thesis'
        source = f'{degree}, {m[1]}, {date or "n.d."}.'
    else:
        periodical = re.match(r'^(<em>[^<]+</em>)\s+(\d+(?:[–/-]\d+)*)(?:\.(\d+(?:[–-]\d+)*)|\((\d+(?:[–-]\d+)*)\))?(?=$|[,; ])', venue)
        if periodical:
            container, number, issue1, issue2 = periodical.groups()
            issue = issue1 or issue2
            source = container + (f' {number}, no. {issue}' if issue else f', no. {number}')
            source += f' ({html.escape(date or "n.d.")})'
            page = re.search(r'\bpp?\.\s*([\d–-]+)', venue)
            source += (': ' + pages(page[1]) if page else '') + '.'
        else:
            source = venue
            if date:
                source += ', ' + html.escape(date)
            needs_access = not bool(date)
            source = sentence(source)
    lead = ' '.join(s for s in [sentence(html.escape(author)), sentence(title), attribution, source] if s)
    return {'html': lead, 'plain': text(lead), 'url': e['url'],
            'needsAccessDate': needs_access, 'notes': notes}


def build(records):
    data = {e['id']: citation(e) for e in records}
    serialized = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return '/* Generated by scripts/build_catalogue.py. Do not edit by hand. */\nwindow.CATALOGUE_CITATIONS=' + serialized + ';\n'


if __name__ == '__main__':
    from build_catalogue import DATA, PAGE
    records = json.loads(DATA.search(PAGE.read_text())[2])
    (ROOT / 'citations-data.js').write_text(build(records))
    print(f'Built {len(records)} Chicago bibliography citations.')
