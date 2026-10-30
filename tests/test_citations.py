import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_catalogue import DATA, PAGE
from build_citations import AUTHORS, citation, date_value, pages, sentence

RECORDS = {r['id']: r for r in json.loads(DATA.search(PAGE.read_text())[2])}


class CitationTests(unittest.TestCase):
    def test_uncertain_dates_are_not_invented(self):
        for raw in ['Undated', 'Approximately 2026-09-26; displayed 6d ago', '2025/2026', 'Exact date not exposed']:
            self.assertEqual(date_value(raw), '')
        self.assertEqual(date_value('2026-01-31 to 2026-02-01'), 'January 31, 2026–February 1, 2026')
        self.assertEqual(date_value('2002-07-16 to 2002-07-27'), 'July 16–27, 2002')
        self.assertEqual(date_value('1969-02/03'), 'February–March 1969')

    def test_reprint_keeps_one_edition(self):
        result = citation(RECORDS['L020'])
        self.assertIn('no. 4 (2017): 204–15.', result['plain'])
        self.assertNotIn('1982', result['plain'])
        self.assertTrue(result['plain'].startswith('Lafferty, R. A.'))
        self.assertIn('Interview by Darrell Schweitzer.', result['plain'])

    def test_dates_and_known_source_types(self):
        self.assertTrue(citation(RECORDS['L079'])['needsAccessDate'])
        self.assertFalse(citation(RECORDS['L001'])['needsAccessDate'])
        self.assertIn('PhD diss., University of Liverpool, 2016.', citation(RECORDS['L401'])['plain'])
        self.assertIn('Arno Press, 1975.', citation(RECORDS['L502'])['plain'])

    def test_incomplete_sources_are_flagged(self):
        self.assertTrue(any('not established' in n for n in citation(RECORDS['L394'])['notes']))
        unknown = dict(RECORDS['L001'], author='Future Unreviewed Author')
        with self.assertRaisesRegex(ValueError, 'review this author'):
            citation(unknown)

    def test_punctuation_and_pages(self):
        self.assertEqual(sentence('“A Title”'), '“A Title.”')
        self.assertEqual(sentence('“A Question?”'), '“A Question?”')
        self.assertEqual(sentence('<em>A Book</em>'), '<em>A Book</em>.')
        for start, end in [('204–215', '204–15'), ('101–109', '101–9'), ('100–104', '100–104'), ('107–110', '107–10'), ('1087–1089', '1087–89')]:
            self.assertEqual(pages(start), end)

    def test_every_record_preserves_source_link(self):
        for record in RECORDS.values():
            result = citation(record)
            self.assertEqual(result['url'], record['url'])
            self.assertNotIn('<em>', result['plain'])
            self.assertNotIn('</em>', result['plain'])
            self.assertTrue(result['plain'])


if __name__ == '__main__':
    unittest.main()
