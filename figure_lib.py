# -*- coding: utf-8 -*-
"""Render structured "figure specs" into inline SVG (or HTML for tables).

This is the renderer behind MCAT-style figures. The LLM only ever produces
structured specs (data points, labels, SMILES, peak lists); this module turns
them into valid, deterministic SVG. Nothing here trusts arbitrary markup.
"""
import html

COLORS = ["#e07a3f", "#2f9e57", "#3b82c4", "#d1453b", "#8b5cf6", "#0891b2"]
INK = "#2b2320"
GRID = "#e8e2da"


def _esc(s):
    return html.escape(str(s), quote=True)


def _fmt(v):
    if v == 0:
        return "0"
    if abs(v) >= 1000 or abs(v) < 0.01:
        return f"{v:.2g}"
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.4g}".rstrip("0").rstrip(".")


def _scale(v, lo, hi, out_lo, out_hi):
    if hi == lo:
        return (out_lo + out_hi) / 2
    return out_lo + (v - lo) * (out_hi - out_lo) / (hi - lo)


def _num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace(",", "").rstrip("%").strip()
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _normalize_series(series):
    """Coerce point values to floats; categorical x -> index; skip non-numeric y."""
    out = []
    for s in series:
        pts = []
        for i, p in enumerate(s.get("points", [])):
            if not isinstance(p, (list, tuple)) or len(p) < 2:
                continue
            x = _num(p[0])
            y = _num(p[1])
            if y is None:
                continue
            if x is None:
                x = float(i)
            pts.append([x, y])
        out.append({**s, "points": pts})
    return out


def _empty_svg(msg="(no data)"):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 120" width="100%" '
        'style="max-width:300px" role="img">'
        f'<rect width="300" height="120" fill="#f5f1ea" rx="8"/>'
        f'<text x="150" y="60" text-anchor="middle" font-family="Arial" font-size="13" fill="#999">{_esc(msg)}</text>'
        "</svg>"
    )


def _chart(spec, kind):
    w, h = 640, 400
    ml, mr, mt, mb = 72, 24, 58, 66
    pw = w - ml - mr
    ph = h - mt - mb

    series = _normalize_series(spec.get("series", []))
    all_x = [p[0] for s in series for p in s.get("points", [])]
    all_y = [p[1] for s in series for p in s.get("points", [])]
    if not all_x:
        return _empty_svg()

    xmin, xmax = min(all_x), max(all_x)
    ymin, ymax = min(all_y), max(all_y)
    if xmin == xmax:
        xmax = xmin + 1
    if ymin == ymax:
        ymax = ymin + 1
    xpad = (xmax - xmin) * 0.05
    ypad = (ymax - ymin) * 0.1
    xmin, xmax = xmin - xpad, xmax + xpad
    if kind == "bar":
        ymin = 0
    else:
        ymin = max(0, ymin - ypad)
    ymax = ymax + ypad
    if ymin == ymax:
        ymax += 1

    X = lambda v: ml + _scale(v, xmin, xmax, 0, pw)
    Y = lambda v: mt + ph - _scale(v, ymin, ymax, 0, ph)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" '
        f'style="max-width:{w}px" role="img" aria-label="{_esc(spec.get("title", ""))}">',
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff"/>',
    ]
    if spec.get("title"):
        parts.append(
            f'<text x="{w / 2:.0f}" y="26" text-anchor="middle" font-family="Arial" '
            f'font-size="15" font-weight="bold" fill="{INK}">{_esc(spec["title"])}</text>'
        )

    # grid + y ticks
    for i in range(6):
        val = ymin + (ymax - ymin) * i / 5
        y = Y(val)
        parts.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{ml + pw}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(
            f'<text x="{ml - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="Arial" '
            f'font-size="11" fill="#777">{_fmt(val)}</text>'
        )

    # x ticks
    for i in range(6):
        val = xmin + (xmax - xmin) * i / 5
        x = X(val)
        parts.append(
            f'<text x="{x:.1f}" y="{mt + ph + 18:.1f}" text-anchor="middle" font-family="Arial" '
            f'font-size="11" fill="#777">{_fmt(val)}</text>'
        )

    # axes
    parts.append(f'<line x1="{ml}" y1="{mt + ph}" x2="{ml + pw}" y2="{mt + ph}" stroke="{INK}" stroke-width="1.5"/>')
    parts.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt + ph}" stroke="{INK}" stroke-width="1.5"/>')

    # data
    n_series = len(series)
    for si, s in enumerate(series):
        pts = s.get("points", [])
        color = s.get("color") or COLORS[si % len(COLORS)]
        if kind == "line":
            coords = " ".join(f"{X(p[0]):.1f},{Y(p[1]):.1f}" for p in pts)
            parts.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>')
            for p in pts:
                parts.append(f'<circle cx="{X(p[0]):.1f}" cy="{Y(p[1]):.1f}" r="3.5" fill="{color}"/>')
        elif kind == "scatter":
            for p in pts:
                parts.append(f'<circle cx="{X(p[0]):.1f}" cy="{Y(p[1]):.1f}" r="4.5" fill="{color}"/>')
        elif kind == "bar":
            bw = (pw / max(len(pts), 1)) * 0.72 / n_series
            for pi, p in enumerate(pts):
                x0 = X(p[0]) - bw * n_series / 2 + si * bw
                bar_top = Y(p[1])
                parts.append(
                    f'<rect x="{x0:.1f}" y="{bar_top:.1f}" width="{bw * 0.9:.1f}" '
                    f'height="{(Y(ymin) - bar_top):.1f}" fill="{color}"/>'
                )

    # axis labels
    if spec.get("xLabel"):
        parts.append(
            f'<text x="{ml + pw / 2:.0f}" y="{h - 18}" text-anchor="middle" font-family="Arial" '
            f'font-size="13" fill="{INK}">{_esc(spec["xLabel"])}</text>'
        )
    if spec.get("yLabel"):
        parts.append(
            f'<text x="20" y="{mt + ph / 2:.0f}" text-anchor="middle" font-family="Arial" '
            f'font-size="13" fill="{INK}" transform="rotate(-90 20 {mt + ph / 2:.0f})">{_esc(spec["yLabel"])}</text>'
        )

    # legend
    if n_series > 1:
        lx, ly = ml + 10, mt + 10
        for si, s in enumerate(series):
            color = s.get("color") or COLORS[si % len(COLORS)]
            parts.append(f'<rect x="{lx}" y="{ly}" width="13" height="13" rx="2" fill="{color}"/>')
            parts.append(
                f'<text x="{lx + 20}" y="{ly + 11}" font-family="Arial" font-size="12" '
                f'fill="{INK}">{_esc(s.get("name", ""))}</text>'
            )
            ly += 20

    parts.append("</svg>")
    return "\n".join(parts)


def line(spec):
    return _chart(spec, "line")


def bar(spec):
    return _chart(spec, "bar")


def scatter(spec):
    return _chart(spec, "scatter")

def table(spec):
    columns = spec.get("columns", [])
    rows = spec.get("rows", [])
    if not columns:
        return '<p style="color:#999">(empty table)</p>'
    head = "".join(f"<th>{_esc(c)}</th>" for c in columns)
    body = ""
    for r in rows:
        body += "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in r) + "</tr>"
    return (
        '<table class="mcat-table" role="table">'
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    )


def spectrum(spec):
    """NMR ('1h-nmr'/'13c-nmr') or IR ('ir') spectrum as SVG."""
    kind = spec.get("kind", "1h-nmr")
    peaks = spec.get("peaks", [])
    w, h = 640, 320
    ml, mr, mt, mb = 56, 18, 46, 62
    pw = w - ml - mr
    ph = h - mt - mb

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" '
        f'style="max-width:{w}px" role="img">',
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
    ]
    if spec.get("title"):
        parts.append(
            f'<text x="{w / 2:.0f}" y="24" text-anchor="middle" font-family="Arial" '
            f'font-size="14" font-weight="bold" fill="{INK}">{_esc(spec["title"])}</text>'
        )

    if kind == "ir":
        # wavenumber axis, 4000 -> 400 left to right
        lo, hi = spec.get("wavenumberRange", [400, 4000])
        xmin, xmax = lo, hi
        X = lambda v: ml + _scale(v, xmin, xmax, 0, pw)
        parts.append(f'<line x1="{ml}" y1="{mt + ph}" x2="{ml + pw}" y2="{mt + ph}" stroke="{INK}" stroke-width="1.5"/>')
        for wv in [4000, 3000, 2000, 1500, 1000, 500]:
            x = X(wv)
            parts.append(f'<text x="{x:.1f}" y="{mt + ph + 16}" text-anchor="middle" font-family="Arial" font-size="10" fill="#777">{wv}</text>')
            parts.append(f'<line x1="{x:.1f}" y1="{mt + ph}" x2="{x:.1f}" y2="{mt + ph - 6}" stroke="{INK}" stroke-width="1"/>')
        # baseline near top
        base_y = mt + 30
        parts.append(f'<line x1="{ml}" y1="{base_y}" x2="{ml + pw}" y2="{base_y}" stroke="{INK}" stroke-width="1"/>')
        for pk in peaks:
            wv = _num(pk.get("wavenumber"))
            if wv is None:
                continue
            x = X(wv)
            intensity = _num(pk.get("intensity", 1)) or 1
            depth = 30 + intensity * 50
            parts.append(
                f'<path d="M {x:.1f} {base_y} L {x:.1f} {base_y + depth:.1f}" '
                f'stroke="#2f9e57" stroke-width="3" fill="none"/>'
            )
            if pk.get("label"):
                parts.append(
                    f'<text x="{x:.1f}" y="{base_y + depth + 14:.1f}" text-anchor="middle" '
                    f'font-family="Arial" font-size="10" fill="{INK}">{_esc(pk["label"])}</text>'
                )
        parts.append(
            f'<text x="{ml + pw / 2:.0f}" y="{h - 14}" text-anchor="middle" font-family="Arial" '
            f'font-size="12" fill="{INK}">Wavenumber (cm⁻¹)</text>'
        )
    else:
        # NMR: ppm axis (higher ppm on the LEFT, 0 on the right)
        hi, lo = spec.get("ppmRange", [0, 12])
        xmin, xmax = lo, hi  # reverse for display
        X = lambda v: ml + _scale(v, xmin, xmax, 0, pw)
        parts.append(f'<line x1="{ml}" y1="{mt + ph}" x2="{ml + pw}" y2="{mt + ph}" stroke="{INK}" stroke-width="1.5"/>')
        for ppm in range(int(lo), int(hi) + 1):
            x = X(ppm)
            parts.append(f'<text x="{x:.1f}" y="{mt + ph + 16}" text-anchor="middle" font-family="Arial" font-size="10" fill="#777">{ppm}</text>')
            parts.append(f'<line x1="{x:.1f}" y1="{mt + ph}" x2="{x:.1f}" y2="{mt + ph - 5}" stroke="{INK}" stroke-width="1"/>')
        base_y = mt + ph
        for pk in peaks:
            ppm = _num(pk.get("ppm"))
            if ppm is None:
                continue
            x = X(ppm)
            integration = _num(pk.get("integration", 1)) or 1
            height = 20 + integration * 16
            parts.append(
                f'<line x1="{x:.1f}" y1="{base_y}" x2="{x:.1f}" y2="{base_y - height:.1f}" '
                f'stroke="#3b82c4" stroke-width="2.5"/>'
            )
            if pk.get("multiplicity") or pk.get("label"):
                lab = pk.get("label") or pk.get("multiplicity", "")
                parts.append(
                    f'<text x="{x:.1f}" y="{base_y - height - 6:.1f}" text-anchor="middle" '
                    f'font-family="Arial" font-size="10" fill="{INK}">{_esc(lab)}</text>'
                )
        parts.append(
            f'<text x="{ml + pw / 2:.0f}" y="{h - 14}" text-anchor="middle" font-family="Arial" '
            f'font-size="12" fill="{INK}">Chemical shift (ppm)</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)

def diagram(spec):
    nodes = spec.get("nodes", [])
    edges = spec.get("edges", [])
    w = spec.get("width", 640)
    h = spec.get("height", 360)
    node_map = {n["id"]: n for n in nodes}

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" '
        f'style="max-width:{w}px" role="img">',
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" '
        'orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="#2b2320"/></marker></defs>',
    ]
    if spec.get("title"):
        parts.append(
            f'<text x="{w / 2:.0f}" y="24" text-anchor="middle" font-family="Arial" '
            f'font-size="14" font-weight="bold" fill="{INK}">{_esc(spec["title"])}</text>'
        )

    for e in edges:
        a = node_map.get(e["from"])
        b = node_map.get(e["to"])
        if not a or not b:
            continue
        x1 = a["x"] + a.get("w", 120) / 2
        y1 = a["y"]
        x2 = b["x"] - b.get("w", 120) / 2
        y2 = b["y"]
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{INK}" stroke-width="1.5" marker-end="url(#arrow)"/>'
        )
        if e.get("label"):
            parts.append(
                f'<text x="{(x1 + x2) / 2:.1f}" y="{(y1 + y2) / 2 - 7:.1f}" text-anchor="middle" '
                f'font-family="Arial" font-size="11" fill="#666">{_esc(e["label"])}</text>'
            )

    for n in nodes:
        nw = n.get("w", 120)
        nh = n.get("h", 40)
        x, y = n["x"], n["y"]
        parts.append(
            f'<rect x="{x - nw / 2:.1f}" y="{y - nh / 2:.1f}" width="{nw}" height="{nh}" rx="8" '
            f'fill="#ffffff" stroke="{INK}" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{x}" y="{y + 4}" text-anchor="middle" font-family="Arial" '
            f'font-size="12" fill="{INK}">{_esc(n["label"])}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def molecule(spec):
    smiles = spec if isinstance(spec, str) else spec.get("smiles", "")
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
        from rdkit.Chem.Draw import rdMolDraw2D
    except ImportError:
        return _empty_svg("(RDKit unavailable)")
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return _empty_svg("(invalid SMILES)")
    AllChem.Compute2DCoords(mol)
    d = rdMolDraw2D.MolDraw2DSVG(400, 300)
    rdMolDraw2D.PrepareAndDrawMolecule(d, mol)
    d.FinishDrawing()
    svg = d.GetDrawingText()
    # strip a leading XML/DOCTYPE declaration if present
    start = svg.find("<svg")
    if start > 0:
        svg = svg[start:]
    return svg


def render_figure(spec):
    if not spec:
        return None
    t = (spec.get("type") or "line").lower()
    if t == "line":
        return line(spec)
    if t == "bar":
        return bar(spec)
    if t == "scatter":
        return scatter(spec)
    if t == "table":
        return table(spec)
    if t in ("spectrum", "nmr", "ir"):
        return spectrum(spec)
    if t == "diagram":
        return diagram(spec)
    if t == "molecule":
        return molecule(spec)
    return line(spec)


