"""Recreate the historical paired Wilcoxon tables without mixing protocols."""
import csv
import io
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGNS = {
    'base_50': ('results_base_50', 50, None, None, 1000),
    '200-40-60': ('results-200-40-60', 200, 40, 60, 2000),
    '200-20-80': ('results-200-20-80', 200, 20, 80, 2000),
    '100-50-60': ('results-100-50-60', 100, 50, 60, 2000),
    '100-20-80': ('results-100-20-80', 100, 20, 80, 2000),
}
STRATEGIES = ('binary_hysteresis', 'vanilla_explotacion', 'vanilla_exploracion', 'binary_simple')
MHS = ('PSO', 'GA', 'GWO', 'DE')
LABELS = ('BPSO', 'GA', 'BGWO', 'BDE')
COLUMNS = ('instance', 'mh_raw', 'mh', 'vs_exploit_p', 'vs_exploit_sign', 'vs_exploit_diff',
           'vs_explore_p', 'vs_explore_sign', 'vs_explore_diff',
           'vs_simple_p', 'vs_simple_sign', 'vs_simple_diff')
A4 = 'A4 fire sustained (plateau+constant+ramp) -> explore; improvement -> exploit'


def source_valid(data, path, strategy, instance, mh, config):
    _, window, low, high, iterations = config
    info = data['info']
    expected = {'estrategia': strategy, 'instancia': f'instances/{instance}.txt',
                'idx': 0, 'poblacion': 20, 'iteraciones': iterations}
    if strategy in ('binary_hysteresis', 'binary_simple'):
        expected['dtw_window'] = window
    if any(info.get(k) != v for k, v in expected.items()):
        return False
    if data.get('mh') != mh or data.get('epochs') != 31 or len(data.get('fitness', [])) != 31:
        return False
    if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in data['fitness']):
        return False
    if low is None:
        if 'campaign_id' in info or 'dtw_p_low' in info or 'dtw_p_high' in info:
            return False
        rule = {'binary_hysteresis': 'hysteresis on delta', 'binary_simple': 'D2 <= theta_c'}
    else:
        if strategy in ('binary_hysteresis', 'binary_simple') and (info.get('dtw_p_low') != low or info.get('dtw_p_high') != high):
            return False
        if info.get('campaign_id') != path.parent.name.removeprefix('comparacion_mhs_'):
            return False
        rule = {'binary_hysteresis': A4, 'binary_simple': 'D2 <= theta_c'}
    return info.get('decision_rule') == rule[strategy] if strategy in rule else 'decision_rule' not in info


def select_sources(root, config):
    selected = {}
    for number in range(1, 10):
        instance = f'mknapcb{number}'
        candidates = {}
        for directory in sorted(directory for strategy in STRATEGIES
                                for directory in (root / strategy / 'todos' / f'{instance}_0').glob('comparacion_mhs_*')):
            strategy = directory.parents[2].name
            campaign = directory.name.removeprefix('comparacion_mhs_')
            entries = candidates.setdefault(campaign, {})
            for mh in MHS:
                path = directory / f'{mh}_{instance}_0.json'
                if path.exists():
                    data = json.loads(path.read_text())
                    if source_valid(data, path, strategy, instance, mh, config):
                        entries[(strategy, mh)] = data['fitness']
        complete = [(key, value) for key, value in candidates.items() if len(value) == 16]
        if not complete:
            raise ValueError(f'{root}: no complete validated campaign for {instance}')
        complete.sort(key=lambda pair: pair[0])
        if any(value != complete[0][1] for _, value in complete[1:]):
            raise ValueError(f'{root}: conflicting complete campaigns for {instance}')
        selected[instance] = complete[-1][1]
    return selected


def render(sources):
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(COLUMNS)
    for instance, records in sources.items():
        for mh, label in zip(MHS, LABELS):
            focal = np.asarray(records['binary_hysteresis', mh])
            row = [instance, mh, label]
            for strategy in STRATEGIES[1:]:
                other = np.asarray(records[strategy, mh])
                p = wilcoxon(focal, other, zero_method='wilcox', alternative='two-sided', mode='auto').pvalue
                diff = np.mean(focal - other)
                sign = '$\\approx$' if p >= .05 else ('$+$' if diff > 0 else '$-$')
                row.extend((p, sign, diff))
            writer.writerow(row)
    return output.getvalue()


def generate(base=ROOT):
    # Resolve and render every campaign before writing any output.
    tables = {name: render(select_sources(base / config[0], config))
              for name, config in CAMPAIGNS.items()}
    destination = base / 'results/tabla_wilcoxon/by_campaign'
    destination.mkdir(parents=True, exist_ok=True)
    for name, text in tables.items():
        folder = destination / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'tabla_wilcoxon.csv').write_bytes(text.encode())


if __name__ == '__main__':
    generate()
