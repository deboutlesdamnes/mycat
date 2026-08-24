# -*- coding: utf-8 -*-
"""Render sample figures of every type and write them out for inspection."""
import os
import figure_lib as fl

OUT = r"c:\Users\jason\Documents\mycat\workspace\figures_demo"
os.makedirs(OUT, exist_ok=True)


def save(name, content):
    ext = "html" if content.lstrip().startswith("<table") else "svg"
    with open(os.path.join(OUT, f"{name}.{ext}"), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"{name}.{ext}: {len(content)} chars")


# Michaelis-Menten curve
mm = []
for s in range(0, 101, 2):
    mm.append([s, 100 * s / (15 + s)])
save("michaelis_menten", fl.render_figure({
    "type": "line", "title": "Michaelis-Menten kinetics",
    "xLabel": "[Substrate] (mM)", "yLabel": "Reaction rate (µmol/min)",
    "series": [{"name": "v0", "points": mm}],
}))

# Bar chart: hormone levels
save("bar_hormones", fl.render_figure({
    "type": "bar", "title": "LH levels in control vs treated rats",
    "xLabel": "Day", "yLabel": "LH (ng/mL)",
    "series": [
        {"name": "Control LH", "points": [[1, 5], [2, 8], [3, 20], [4, 6]]},
        {"name": "Treated LH", "points": [[1, 4], [2, 5], [3, 8], [4, 5]]},
    ],
}))

# Scatter: correlation
save("scatter", fl.render_figure({
    "type": "scatter", "title": "Study time vs. exam score",
    "xLabel": "Study hours", "yLabel": "Score (%)",
    "series": [{"name": "Students", "points": [[1, 52], [2, 60], [3, 58], [4, 71], [5, 74], [6, 80], [7, 83], [8, 90]]}],
}))

# Table
save("table", fl.render_figure({
    "type": "table",
    "columns": ["Diagnosis", "Men (n=500)", "Women (n=500)"],
    "rows": [["MDD", 50, 100], ["No MDD", 450, 400]],
}))

# NMR spectrum
save("nmr", fl.render_figure({
    "type": "spectrum", "kind": "1h-nmr", "title": "¹H NMR of ethanol",
    "ppmRange": [0, 6],
    "peaks": [
        {"ppm": 1.2, "multiplicity": "t", "integration": 3},
        {"ppm": 2.5, "multiplicity": "s", "integration": 1},
        {"ppm": 3.7, "multiplicity": "q", "integration": 2},
    ],
}))

# IR spectrum
save("ir", fl.render_figure({
    "type": "spectrum", "kind": "ir", "title": "IR spectrum (transmittance)",
    "wavenumberRange": [400, 4000],
    "peaks": [
        {"wavenumber": 3300, "intensity": 1, "label": "O-H"},
        {"wavenumber": 1700, "intensity": 0.7, "label": "C=O"},
        {"wavenumber": 1200, "intensity": 0.5, "label": "C-O"},
    ],
}))

# Diagram: glycolysis (abbreviated)
save("pathway", fl.render_figure({
    "type": "diagram", "title": "Glycolysis (abbreviated)", "width": 640, "height": 200,
    "nodes": [
        {"id": "g", "label": "Glucose", "x": 80, "y": 100},
        {"id": "g6p", "label": "Glucose-6-P", "x": 220, "y": 100},
        {"id": "f16", "label": "Fructose-1,6-bisP", "x": 380, "y": 100},
        {"id": "pyr", "label": "Pyruvate", "x": 540, "y": 100},
    ],
    "edges": [
        {"from": "g", "to": "g6p", "label": "hexokinase"},
        {"from": "g6p", "to": "f16", "label": "PFK-1"},
        {"from": "f16", "to": "pyr", "label": ""},
    ],
}))

# Molecule (RDKit)
save("molecule", fl.render_figure({"type": "molecule", "smiles": "CC(=O)O"}))

print("DONE")
