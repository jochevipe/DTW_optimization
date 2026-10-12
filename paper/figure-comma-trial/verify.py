"""Functional checks and previews; no scientific experiments."""
import json
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageChops
from trial import HERE, SOURCE, ASSETS, digest, temporal_pdf

report = []
for asset in ASSETS:
    original = (SOURCE / asset).read_bytes()
    before = HERE / 'before' / asset
    after = HERE / 'after' / asset
    assert original == before.read_bytes()
    expected = temporal_pdf(original) if asset == 'fig_temporal_diagnostics.pdf' else original
    assert after.read_bytes() == expected
    infos = [subprocess.check_output(['pdfinfo', '-box', str(p)]).decode(errors='replace') for p in (before, after)]
    boxes = [[line for line in info.splitlines() if re.search(r'(Box:|Page size:|Page rot:)', line)] for info in infos]
    assert boxes[0] == boxes[1]
    previews = []
    for tag,path in [('before',before),('after',after)]:
        prefix = HERE / (Path(asset).stem+'-'+tag)
        subprocess.run(['pdftoppm','-scale-to','1400','-png','-singlefile',str(path),str(prefix)],check=True)
        previews.append(str(prefix)+'.png')
    diff = ImageChops.difference(Image.open(previews[0]).convert('RGB'), Image.open(previews[1]).convert('RGB'))
    bbox = diff.getbbox()
    if asset == 'fig_temporal_diagnostics.pdf':
        assert bbox and bbox[2] < 150 and bbox[3] < 270, bbox
        text = subprocess.check_output(['pdftotext',str(after),'-']).decode()
        assert all(n in text for n in ['23,600','23,800','24,000','24,200'])
        assert all(n in text for n in ['1000','1250','1500','1750','2000'])
    else:
        assert bbox is None
    report.append(dict(asset=asset,source_sha256=digest(original),boxes_rotation_identical=True,pixel_difference_bbox=bbox,previews=previews))
(HERE / 'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: seven source/before hashes; exact expected after bytes; all boxes/rotation; 14 renders; temporal text and bounded pixel changes; six identical pairs')
