# -*- coding: utf-8 -*-
"""Table reconstruction (OCR coordinate rows) and markdown rendering."""
import re


def _row_is_junk(cells):
    texts = [t.strip() for _, t in cells if t.strip()]
    if not texts:
        return True
    return all(len(t) <= 3 and not re.search(r"\d", t) for t in texts)


class TableReconstructor:
    """Turn OCR'd text blocks (with x/y coordinates) into a markdown table.

    Rows are a list of {"text", "cx", "cy", "top", "left", "h"} dicts.
    """

    def _filtered_rows(self, rows):
        ordered = sorted(rows, key=lambda r: (r["top"], r["left"]))
        vrows = []
        cur = [ordered[0]]
        for r in ordered[1:]:
            avg_cy = sum(x["cy"] for x in cur) / len(cur)
            if abs(r["cy"] - avg_cy) <= 0.7 * max(r["h"], 8):
                cur.append(r)
            else:
                vrows.append(cur)
                cur = [r]
        vrows.append(cur)

        kept = []
        for cl in vrows:
            cells = sorted([(c["cx"], c["text"]) for c in cl if c["text"].strip()], key=lambda x: x[0])
            if not cells or _row_is_junk(cells):
                continue
            texts = [t for _, t in cells]
            if kept and [t for _, t in kept[-1]] == texts:
                continue
            kept.append(cells)
        return kept

    def _rows_to_markdown(self, cell_rows):
        all_x = sorted(set(round(x) for row in cell_rows for x, _ in row))
        cols = []
        for x in all_x:
            if cols and x - cols[-1][-1] <= 25:
                cols[-1].append(x)
            else:
                cols.append([x])
        col_centers = [sum(c) / len(c) for c in cols]
        ncols = len(col_centers)

        grid = []
        for cells in cell_rows:
            row = [""] * ncols
            for x, t in cells:
                j = min(range(ncols), key=lambda j: abs(col_centers[j] - x))
                row[j] = (row[j] + " " + t).strip() if row[j] else t
            grid.append(row)

        trans = [[grid[r][c] for r in range(len(grid))] for c in range(ncols)]
        keep_cols = [c for c in range(ncols) if any(trans[c][r].strip() for r in range(len(grid)))]
        grid2 = [[grid[r][c] for c in keep_cols] for r in range(len(grid))]

        def esc(s):
            return s.replace("|", "\\|")

        header = grid2[0]
        out = ["| " + " | ".join(esc(c) for c in header) + " |"]
        out.append("|" + "|".join(["---"] * len(header)) + "|")
        for r in grid2[1:]:
            out.append("| " + " | ".join(esc(c) for c in r) + " |")
        return "\n".join(out)

    def reconstruct(self, rows):
        """Return (markdown_or_None, filtered_reading_order_lines)."""
        if not rows:
            return None, []
        kept = self._filtered_rows(rows)
        if not kept:
            return None, []

        seen = set()
        reading_lines = []
        for cells in kept:
            line = " ".join(t for _, t in cells)
            if line in seen:
                continue
            seen.add(line)
            reading_lines.append(line)

        md = self._rows_to_markdown(kept)
        if md:
            header_cells = md.splitlines()[0].strip("|").split("|")
            if len(header_cells) > 6:
                md = None
        return md, reading_lines


def table_to_markdown(caption, rows):
    """Render a caption + list-of-rows (each a list of cells) as markdown."""
    if not rows:
        return ""
    out = []
    if caption:
        out.append(f"**{caption}**\n")
    ncols = max(len(r) for r in rows)
    norm = [list(r) + [""] * (ncols - len(r)) for r in rows]

    def esc(s):
        return str(s).replace("|", "\\|")

    out.append("| " + " | ".join(esc(c) for c in norm[0]) + " |")
    out.append("|" + "|".join(["---"] * ncols) + "|")
    for r in norm[1:]:
        out.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(out)
