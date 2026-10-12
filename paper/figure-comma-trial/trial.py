"""Bounded copy-only PDF trial, using an incremental stream update."""
import hashlib
import json
import re
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / '6a59435558644210a6934a74'
ASSETS = ['figures/mknapcb1_binary_simple.pdf', 'figures/mknapcb1_binary_complex.pdf', 'fig_temporal_diagnostics.pdf', 'figures/mknapcb5_binary_simple.pdf', 'figures/mknapcb5_binary_complex.pdf', 'figures/mknapcb9_binary_simple.pdf', 'figures/mknapcb9_binary_complex.pdf']

def format_number(value):
    m = re.fullmatch(r'([+-]?)(\d+)(\.\d+)?', value)
    if not m or len(m[2]) < 5:
        return value
    digits = m[2]
    groups = []
    while digits:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    return m[1] + ','.join(groups) + (m[3] or '')

def edit_temporal(stream):
    pattern = rb'1 0 -0 1 ([\d.]+) ([\d.]+) cm\nBT\n/F1 7\.5 Tf\n0 0 Td\n\[ \(([^()]*)\) \] TJ'
    count = 0
    def replace(m):
        nonlocal count
        label = m[3].decode('utf-16-be')
        if label not in {'23600','23800','24000','24200'}:
            return m[0]
        count += 1
        x = f'{float(m[1])-2.385:.6f}'.encode()
        return b'1 0 -0 1 '+x+b' '+m[2]+b' cm\nBT\n/F1 7.5 Tf\n0 0 Td\n[ ('+format_number(label).encode('utf-16-be')+b') ] TJ'
    return re.sub(pattern, replace, stream), count

def temporal_pdf(data):
    m = re.search(rb'(?m)^9 0 obj\s*(<<.*?>>)\s*stream\r?\n', data, re.S)
    if not m or b'/FlateDecode' not in m[1]:
        raise ValueError('Unsupported content object')
    length_ref = re.search(rb'/Length (\d+) 0 R', m[1])
    if length_ref:
        length = int(re.search(rb'(?m)^'+length_ref[1]+rb' 0 obj\s+(\d+)', data)[1])
    else:
        length = int(re.search(rb'/Length (\d+)', m[1])[1])
    payload = data[m.end():m.end()+length]
    stream = zlib.decompress(payload)
    changed, count = edit_temporal(stream)
    if count != 4:
        raise ValueError(f'Expected four labels, found {count}')
    compressed = zlib.compress(changed)
    dictionary = re.sub(rb'/Length \d+(?: 0 R)?', b'/Length '+str(len(compressed)).encode(), m[1])
    previous = re.findall(rb'startxref\s+(\d+)', data)[-1]
    trailer = re.findall(rb'trailer\s*(<<.*?>>)', data, re.S)[-1]
    trailer = re.sub(rb'/Prev\s+\d+', b'', trailer)
    trailer = trailer[:-2]+b' /Prev '+previous+b' >>'
    prefix = data+b'\n'
    offset = len(prefix)
    prefix += b'9 0 obj\n'+dictionary+b'\nstream\n'+compressed+b'\nendstream\nendobj\n'
    xref = len(prefix)
    return prefix+b'xref\n9 1\n'+f'{offset:010d} 00000 n \n'.encode()+b'trailer\n'+trailer+b'\nstartxref\n'+str(xref).encode()+b'\n%%EOF\n'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    manifest = []
    for asset in ASSETS:
        original = (SOURCE / asset).read_bytes()
        before = HERE / 'before' / asset
        after = HERE / 'after' / asset
        before.parent.mkdir(parents=True, exist_ok=True)
        after.parent.mkdir(parents=True, exist_ok=True)
        if before.exists() and before.read_bytes() != original:
            raise ValueError(f'Immutable baseline mismatch: {asset}')
        if not before.exists():
            before.write_bytes(original)
        output = temporal_pdf(original) if asset == 'fig_temporal_diagnostics.pdf' else original
        after.write_bytes(output)
        assert (SOURCE / asset).read_bytes() == original
        manifest.append(dict(asset=asset, original=digest(original), before=digest(before.read_bytes()), after=digest(output), status='edited: four labels' if output != original else 'unsupported: outlined labels, unchanged'))
    (HERE / 'hash-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')

if __name__ == '__main__':
    main()
