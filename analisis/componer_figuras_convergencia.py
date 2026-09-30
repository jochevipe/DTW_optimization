#!/usr/bin/env python3
"""Compose vector convergence previews from the archived one-page PDFs."""
from __future__ import print_function

import copy
import hashlib
import shutil
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "paper" / "figures" / "convergence"
GROUPS = (1, 5, 9)
INDICES = (0, 15, 29)
REGIMES = (
    ("binary_simple", "binary_simple", "Binary-Simple"),
    ("binary_hysteresis", "binary_complex", "Binary-Complex"),
)
RUN_STAMPS = {
    1: {0: "20260929_141958", 15: "20260929_142952", 29: "20260929_143610"},
    5: {0: "20260929_144048", 15: "20260929_150543", 29: "20260929_152024"},
    9: {0: "20260929_153821", 15: "20260929_163949", 29: "20260929_171252"},
}
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
PANEL_WIDTH = 721.234063
# Includes edge tick glyphs (y=17..232) while stopping before lower-panel titles (y>=236).
MAIN_TOP = 12.0
MAIN_BOTTOM = 234.5
MAIN_HEIGHT = MAIN_BOTTOM - MAIN_TOP
PANEL_HEIGHT = MAIN_HEIGHT + 2.0 + 39.434141


def source_path(regime, group, index):
    stamp = RUN_STAMPS[group][index]
    return ROOT / "results" / regime / "todos" / ("mknapcb%d_%d" % (group, index)) / (
        "comparacion_mhs_%s" % stamp
    ) / ("%s_mknapcb%d.pdf" % (regime, group))


def panel_pdf_path(group, regime, index):
    return OUTPUT / ("panel_mknapcb%d_%s_%d.pdf" % (group, regime, index))


def figure_stem(group, output_regime):
    return "mknapcb%d_%s" % (group, output_regime)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def crop_svg(source_svg):
    original = ET.parse(str(source_svg)).getroot()
    definitions = original.find("{%s}defs" % SVG_NS)
    content = original.find("{%s}g[@id='surface1']" % SVG_NS)
    if definitions is None or content is None:
        raise RuntimeError("Unexpected Poppler SVG structure in %s" % source_svg)

    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)
    result = ET.Element("{%s}svg" % SVG_NS, {
        "width": "%.6fpt" % PANEL_WIDTH,
        "height": "%.6fpt" % PANEL_HEIGHT,
        "viewBox": "0 0 %.6f %.6f" % (PANEL_WIDTH, PANEL_HEIGHT),
    })
    result.append(copy.deepcopy(definitions))
    crops = (
        (0, 0, PANEL_WIDTH, MAIN_HEIGHT,
         "-5 %.1f %.6f %.1f" % (MAIN_TOP, PANEL_WIDTH, MAIN_HEIGHT)),
        (80, MAIN_HEIGHT + 2.0, 621.234063, 39.434141,
         "75 419 621.234063 39.434141"),
    )
    for crop_index, (x, y, width, height, viewbox) in enumerate(crops):
        viewport = ET.SubElement(result, "{%s}svg" % SVG_NS, {
            "x": str(x), "y": str(y), "width": "%.6f" % width,
            "height": "%.6f" % height, "viewBox": viewbox, "overflow": "hidden",
        })
        drawing = copy.deepcopy(content)
        drawing.attrib.pop("id", None)
        if crop_index == 0:
            removed_title = 0
            for parent in drawing.iter():
                for child in list(parent):
                    if not child.tag.endswith("use"):
                        continue
                    x = float(child.attrib.get("x", "-1"))
                    baseline = float(child.attrib.get("y", "-1"))
                    if 100 <= x <= 650 and 10 <= baseline <= 25:
                        parent.remove(child)
                        removed_title += 1
            if removed_title < 10:
                raise RuntimeError("Could not identify the original seed-bearing title glyphs")
        viewport.append(drawing)
    return ET.tostring(result, encoding="utf-8")


def tex_for(group, regime, version):
    panels = []
    for index in INDICES:
        image = panel_pdf_path(group, regime, index).relative_to(ROOT).as_posix()
        panels.append(
            r"\noindent\makebox[\textwidth][c]{\textbf{Instance %d}}\par" % index
            + "\n\\vspace{1pt}\n"
            + r"\noindent\makebox[\textwidth][c]{\includegraphics[width=6.8in]{%s}}\par" % image
            + "\n\\vspace{2pt}"
        )
    return r"""\documentclass[10pt]{article}
\usepackage[paperwidth=7.4in,paperheight=9.2in,margin=0.2in]{geometry}
\usepackage{graphicx}
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\begin{document}
\begin{center}
{\Large\bfseries Convergence fitness: mknapcb%(group)d -- %(version)s\par}
\end{center}
\vspace{-0.04in}
%(panels)s
\end{document}
""" % {"group": group, "version": version, "panels": "\n".join(panels)}


def main():
    tools = ("pdflatex", "pdftoppm", "pdftocairo", "rsvg-convert")
    missing_tools = [name for name in tools if shutil.which(name) is None]
    if missing_tools:
        raise RuntimeError("Required local composition tools unavailable: %s" % ", ".join(missing_tools))

    sources = [source_path(regime, group, index)
               for group in GROUPS for index in INDICES for regime, _, _ in REGIMES]
    missing_sources = [str(path.relative_to(ROOT)) for path in sources if not path.is_file()]
    if missing_sources:
        raise RuntimeError("Expected source PDFs are missing: %s" % ", ".join(missing_sources))
    initial_hashes = {path: sha256(path) for path in sources}

    OUTPUT.mkdir(parents=True, exist_ok=True)
    source_svg = OUTPUT / ".source-panel.svg"
    for group in GROUPS:
        for index in INDICES:
            for regime, _, _ in REGIMES:
                source = source_path(regime, group, index)
                subprocess.run(
                    ["pdftocairo", "-svg", "-f", "1", "-l", "1", str(source), str(source_svg)],
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                subprocess.run(
                    ["rsvg-convert", "-f", "pdf", "-o",
                     str(panel_pdf_path(group, regime, index))],
                    input=crop_svg(source_svg), check=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
    print("Created 18 cropped vector panels")

    for group in GROUPS:
        for regime, output_regime, version in REGIMES:
            name = figure_stem(group, output_regime)
            texfile = OUTPUT / (name + ".tex")
            texfile.write_text(tex_for(group, regime, version), encoding="utf-8")
            build = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
                 "-jobname=" + name, "-output-directory=" + str(OUTPUT), str(texfile)],
                cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            if build.returncode:
                raise RuntimeError("pdflatex failed for %s:\n%s" % (name, build.stdout.decode("utf-8", "replace")))
            pdf = OUTPUT / (name + ".pdf")
            subprocess.run(
                ["pdftoppm", "-png", "-r", "180", "-singlefile", str(pdf), str(OUTPUT / name)],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            print("Created %s.pdf and %s.png" % (name, name))

    changed = [str(path.relative_to(ROOT)) for path, old_hash in initial_hashes.items()
               if sha256(path) != old_hash]
    if changed:
        raise RuntimeError("Source PDFs changed during composition: %s" % ", ".join(changed))

    manifest = [
        "# Convergence figure source manifest",
        "",
        "Six additional figures: mknapcb1, mknapcb5, and mknapcb9, each in Binary-Simple and Binary-Complex.",
        "Each figure stacks instances 0, 15, and 29 vertically in that top-to-bottom order.",
        "Titles identify the mknapcb group and Binary-Simple or Binary-Complex version; each panel is individually labeled.",
        "The earlier horizontal previews remain under the unsuffixed mknapcb{1,5,9}.pdf and .png names.",
        "Panels are vector crops of the fitness/convergence axes, original legends, and Iteration axis.",
        "Main crop spans y=12..234.5, retaining boundary ticks while omitting original title glyphs and lower control axes.",
        "Selection caveat: each MH curve is the selected best-of-31 run, not a mean or a typical run.",
        "SHA-256 values identify the exact source PDFs used; Binary-Complex sources are archived under binary_hysteresis.",
        "",
        "| Output figure | Group | Version | Panel order | Instance | Source PDF | SHA-256 |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for group in GROUPS:
        for regime, output_regime, version in REGIMES:
            for panel_order, index in enumerate(INDICES, 1):
                path = source_path(regime, group, index)
                manifest.append("| `%s` | mknapcb%d | %s | %d of 3 | %d | `%s` | `%s` |" % (
                    figure_stem(group, output_regime), group, version, panel_order, index,
                    path.relative_to(ROOT).as_posix(), initial_hashes[path]))
    (OUTPUT / "source_manifest.md").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print("Verified %d source hashes unchanged; wrote source_manifest.md" % len(sources))


if __name__ == "__main__":
    main()
