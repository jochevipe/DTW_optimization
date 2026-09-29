"""Focused regression checks for historical campaign reconstruction."""
import csv
import io
import unittest
from pathlib import Path

from analisis.generar_tablas_wilcoxon import CAMPAIGNS, COLUMNS, ROOT, render, select_sources


class HistoricalTables(unittest.TestCase):
    def test_base_reference(self):
        config = CAMPAIGNS['base_50']
        result = render(select_sources(ROOT / config[0], config))
        reference = (ROOT / 'results/tabla_wilcoxon/tabla_wilcoxon1.csv').read_text()
        self.assertEqual(list(csv.reader(io.StringIO(result))),
                         list(csv.reader(io.StringIO(reference))))

    def test_all_campaigns_have_complete_schema(self):
        for name, config in CAMPAIGNS.items():
            with self.subTest(name=name):
                rows = list(csv.reader(io.StringIO(render(select_sources(ROOT / config[0], config)))))
                self.assertEqual(rows[0], list(COLUMNS))
                self.assertEqual(len(rows), 37)
                self.assertTrue(all(len(row) == 12 for row in rows))

    def test_missing_campaign_fails_closed(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'no complete validated campaign'):
                select_sources(Path(directory), CAMPAIGNS['base_50'])

    def test_wrong_budget_rejected(self):
        from analisis.generar_tablas_wilcoxon import source_valid
        import json
        config = CAMPAIGNS['200-40-60']
        path = next((ROOT / config[0] / 'binary_hysteresis').rglob('PSO_mknapcb1_0.json'))
        data = json.loads(path.read_text())
        data['info']['dtw_window'] = 100
        self.assertFalse(source_valid(data, path, 'binary_hysteresis', 'mknapcb1', 'PSO', config))


if __name__ == '__main__':
    unittest.main()
