import unittest
from trial import format_number, edit_temporal, temporal_pdf, HERE
import re
import zlib

class TrialTests(unittest.TestCase):
    def test_format(self):
        for a,b in [('10000','10,000'),('24381.0','24,381.0'),('-10000.00','-10,000.00'),('1000','1000'),('2000','2000'),('text','text')]:
            self.assertEqual(format_number(a), b)
    def test_fixture(self):
        stream=b'q\n1 0 -0 1 38.435875 506 cm\nBT\n/F1 7.5 Tf\n0 0 Td\n[ ('+'23600'.encode('utf-16-be')+b') ] TJ\nET\nQ'
        changed,count=edit_temporal(stream)
        self.assertEqual(count,1)
        self.assertIn('23,600'.encode('utf-16-be'),changed)
        self.assertIn(b'36.050875 506 cm',changed)
    def test_incremental_parser(self):
        data = (HERE / 'before' / 'fig_temporal_diagnostics.pdf').read_bytes()
        output = temporal_pdf(data)
        self.assertTrue(output.startswith(data))
        streams = list(re.finditer(rb'(?m)^9 0 obj\s*(<<.*?>>)\s*stream\r?\n', output, re.S))
        last = streams[-1]
        length = int(re.search(rb'/Length (\d+)', last[1])[1])
        changed = zlib.decompress(output[last.end():last.end()+length])
        for label in ['23,600', '23,800', '24,000', '24,200']:
            self.assertEqual(changed.count(label.encode('utf-16-be')), 1)

    def test_unrelated(self):
        self.assertEqual(edit_temporal(b'0 0 m 100 100 l S'),(b'0 0 m 100 100 l S',0))

if __name__=='__main__': unittest.main()
