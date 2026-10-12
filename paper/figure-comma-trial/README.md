# Figure comma trial (copies only)

Partial result: the temporal PDF has four edited labels. All six convergence PDFs are copied but unchanged and unsupported by this bounded prototype. Originals, manuscript, plotting code and archived results are untouched.

## Inspect

- `before/`: byte-identical baseline copies, never overwritten by the script.
- `after/fig_temporal_diagnostics.pdf`: 23600, 23800, 24000 and 24200 now display as 23,600, 23,800, 24,000 and 24,200.
- `after/figures/*.pdf`: six unchanged copies, not successful edits.
- `hash-manifest.json`: SHA-256 for original, before and after, with per-asset status.
- `*-before.png`, `*-after.png`: 1400-pixel previews of all seven pairs.
- `verification.json`: box/rotation checks and image difference bounds.

## Reproduce from repository root

```sh
python -B paper/figure-comma-trial/trial.py
python -B -m unittest discover -s paper/figure-comma-trial -p test_trial.py
python -B paper/figure-comma-trial/verify.py
```

Uses Python standard library for PDF editing; verification uses existing Pillow, pdfinfo, pdftotext and pdftoppm. No installations or simulations. The parser is deliberately specific to this temporal PDF, not a general PDF editor.

## Method and limits

The temporal copy keeps the complete original byte prefix and appends an incremental replacement for content object 9. Only four UTF-16BE TJ literals and their horizontal translation change. Embedded DejaVuSerif and its existing comma CID are reused. Width object 20 declares CID 44 width 318/1000 em, so each 7.5-point label moves left 2.385 points to preserve its right anchor. No curves, backgrounds, legends, font objects, page objects or boxes are replaced. Four-digit labels stay unchanged. The formatting helper preserves signs and decimal suffixes, but no decimal label is edited in this temporal asset.

The bounded convergence inspection decompressed the first active composite's Form stream. Numerals are absolute-coordinate filled outlines, intermixed with axes and other paths; they are not TJ strings or individually named glyphs. A reliable glyph-to-label mapping and comma outline placement were not established. Editing these without that mapping would risk modifying plot geometry, so all six after copies remain byte-identical. No white-box overlays, raster replacements, font substitution or recomposition were used. The remaining 36/36/32/32/31/31 eligible convergence occurrences are not addressed.

## Observed checks

Four focused unit tests pass, covering formatting, right-anchor translation, non-text preservation and actual incremental stream decoding. Initial test-first failure was the missing implementation module. The first trial execution exposed an indirect stream Length reference; handling that reference fixed execution. An added parser test initially counted pre-existing commas too; it was narrowed to the four exact target strings.

Functional verification passed for all seven source/before byte comparisons, expected after bytes, page boxes and rotation, and fourteen Poppler renders. Six pairs have no pixel differences. Temporal differences are confined to the upper-left label region; extracted text includes all four formatted labels and unchanged four-digit ticks. Visual inspection of the temporal after preview shows readable commas with intact curves and legends. Independent verification and author approval are still pending.

Formatting purpose: improve large-number readability without changing the existing figure design. Applicable static-asset gate: authorized copies and source-backed numbers PASS; same font/colors/legend PASS; render and structural checks PASS. Interactive/mobile/theme rules are not applicable to this PDF-copy trial. No UI or new visual identity is introduced.
