#!/usr/bin/env python3
"""Deterministic renderer for the JAMA-style ranked coloured-cell matrix figures
of Papanicolas, Woskie & Jha, JAMA 2018;319(10):1024-1039 (Figures 1, 4, 5, 7, 9, 10, 11).

Usage
-----
python3 scripts/viz/render_figures.py \
    --data outputs/validation/test_2018_data.csv \
    --meta spec/figure_meta.json \
    --outdir outputs/validation/figures_2018_reproduction \
    [--spec spec/indicators.csv] [--colors spec/country_colors.json] \
    [--figures 1,4,5] [--combined-name all_figures.pdf] [--dpi 300]

Inputs
------
* spec/indicators.csv : row order, figure, section, label, decimals per indicator.
* data CSV (long)     : indicator_id,country,value[,display_value]
                        value numeric or NA/empty; display_value (optional) overrides
                        the formatted text of that cell ("<blank>" = show nothing).
* meta JSON           : titles, footnotes, label/section overrides, markers, layout
                        (schema documented in the report / spec/figure_meta.json "_schema").

Outputs per figure: figure_<n>.png (300 dpi), .svg, .pdf  + combined multi-page PDF
(US Letter, one figure per page, order 1,4,5,7,9,10,11).

Everything is drawn in absolute inch coordinates with fonts loaded from files shipped
in scripts/viz/fonts (Fira Sans Condensed, SIL OFL), so output is reproducible.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_agg import RendererAgg  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FONT_DIR = os.path.join(HERE, "fonts")

COUNTRIES = ["USA", "GBR", "DEU", "SWE", "FRA", "NLD", "CHE", "DNK", "CAN", "JPN", "AUS"]
COUNTRY_LABELS = {
    "USA": "US", "GBR": "UK", "DEU": "Germany", "SWE": "Sweden", "FRA": "France",
    "NLD": "NLD", "CHE": "CHE", "DNK": "Denmark", "CAN": "Canada", "JPN": "Japan",
    "AUS": "Australia",
}
FIGURE_ORDER = [1, 4, 5, 7, 9, 10, 11]
THIN = " "  # thousands separator token (drawn as a fixed gap; font lacks the glyph)

# --------------------------------------------------------------------------------------
# Default style: all lengths in inches, font sizes / line widths in points.
# Measured from the 2018 article pages rendered at 400 dpi.
# --------------------------------------------------------------------------------------
DEFAULT_STYLE = {
    "table_width": 6.49,
    "label_col": 1.2988,
    "cell_col": 0.4387,
    # mean column = table_width - label_col - 11*cell_col
    "margin": 0.25,               # whitespace around stand-alone figure files
    "font_regular": "FiraSansCondensed-Regular.ttf",
    "font_bold": "FiraSansCondensed-Medium.ttf",
    "font_title": "FiraSansCondensed-Medium.ttf",
    "fs_cell": 6.5,
    "fs_label": 6.5,
    "fs_header": 6.5,
    "fs_section": 6.5,
    "fs_title": 7.6,
    "fs_foot": 6.85,
    "fs_mean_n": 5.6,
    "marker_scale": 0.66,          # superscript size relative to base
    "marker_rise": 0.36,           # superscript baseline rise (fraction of base size)
    "line_pitch_pt": 7.0,          # baseline-to-baseline inside cells/labels
    "foot_pitch_pt": 9.0,
    "foot_para_gap": 0.033,
    "foot_indent": 0.055,          # hanging indent of lettered footnotes
    "foot_col_gap": 0.25,
    "cap_ratio": 0.689,            # Fira cap height / em
    "pad_x": 0.0575,
    "label_pad_right": 0.086,       # label text width = label_col - pad_x - this
    "pad_top": 0.064,              # row top to cap top
    "row_h": 0.29,
    "row_h_extra_line": 0.0972,    # added per label line beyond the cell's 2 lines
    "section_h": 0.14,
    "header_h": 0.1275,
    "red_rule_lw": 1.6,
    "title_base_dy": 0.142,        # red-rule top -> title baseline
    "title_rule_dy": 0.211,        # red-rule top -> thin black rule
    "table_top_dy": 0.3275,        # red-rule top -> table top rule
    "lw_table_top": 0.55,
    "lw_header_bottom": 0.4,
    "lw_section_under": 0.4,
    "lw_row": 0.2,
    "lw_block_end": 0.55,
    "lw_vert": 0.2,
    "lw_vert_major": 0.4,
    "lw_title_rule": 0.4,
    "lw_foot_rule": 0.5,
    "foot_gap_above": 0.213,       # table bottom -> footnote top rule
    "foot_text_dy": 0.07,          # footnote rule -> first cap top
    "foot_bottom_dy": 0.095,       # last footnote baseline -> bottom rule
    "ink": "#231F20",
    "red": "#D91433",
    "mean_n_color": "#58595B",
    "section_band": None,          # e.g. "#EDEDED" to shade section divider rows
    "mean_align": "left",
    "bold_unsectioned": True,      # rows with empty section get a bold label (as in 2018)
    "show_mean_n": True,
}

DEFAULT_MEAN_NOTE = ("Mean is the unweighted arithmetic mean of the countries with data; "
                     "(n = x) under a mean gives the number of countries contributing when "
                     "data were not available (NA) for all 11.")

_RENDERER = RendererAgg(10, 10, 72)  # 72 dpi -> widths come back in points
_FP_CACHE: dict = {}


def fp(fname: str) -> FontProperties:
    if fname not in _FP_CACHE:
        path = fname if os.path.isabs(fname) else os.path.join(FONT_DIR, fname)
        if not os.path.exists(path):
            raise FileNotFoundError(f"font file missing: {path}")
        _FP_CACHE[fname] = FontProperties(fname=path)
    return _FP_CACHE[fname]


def text_width_pt(s: str, font: str, size: float) -> float:
    if not s:
        return 0.0
    p = fp(font).copy()
    p.set_size(size)
    w, _h, _d = _RENDERER.get_text_width_height_descent(s, p, ismath=False)
    return float(w)


# --------------------------------------------------------------------------------------
# Number formatting
# --------------------------------------------------------------------------------------
def is_na(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def parse_value(s):
    if s is None:
        return None
    s = str(s).strip()
    if s == "" or s.upper() in ("NA", "N/A", "NAN", "NONE", ".."):
        return None
    return float(s)


def fmt_number(v: float, decimals: int) -> str:
    """Round half-up to `decimals`; group thousands with a thin space only when |v| >= 10000
    (JAMA style: 9403 but 218 173)."""
    q = Decimal(repr(v)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
    if q == 0:
        q = abs(q)
    s = f"{q:f}"
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    intpart, _, frac = s.partition(".")
    if abs(v) >= 10000 or len(intpart) >= 5:
        groups = []
        while len(intpart) > 3:
            groups.insert(0, intpart[-3:])
            intpart = intpart[:-3]
        groups.insert(0, intpart)
        intpart = THIN.join(groups)
    out = intpart + ("." + frac if frac else "")
    return ("-" if neg else "") + out


# --------------------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------------------
def load_spec(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for i, r in enumerate(rows):
        r["_order"] = i
        r["figure"] = int(r["figure"])
        r["decimals"] = int(r["decimals"]) if str(r.get("decimals", "")).strip() != "" else 0
        r["section"] = (r.get("section") or "").strip()
    return rows


def load_data(path):
    data: dict = {}
    with open(path, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        need = {"indicator_id", "country", "value"}
        if not need.issubset(rd.fieldnames or []):
            raise ValueError(f"data CSV must have columns {sorted(need)}; got {rd.fieldnames}")
        has_disp = "display_value" in rd.fieldnames
        for r in rd:
            iid = r["indicator_id"].strip()
            c = r["country"].strip().upper()
            if c not in COUNTRIES:
                raise ValueError(f"unknown country code {c!r} for {iid}")
            key = (iid, c)
            if key in data:
                raise ValueError(f"duplicate data row for {key}")
            disp = r.get("display_value") if has_disp else None
            disp = disp if (disp is not None and disp.strip() != "") else None
            data[key] = {"value": parse_value(r["value"]), "display": disp}
    return data


def load_colors(path):
    with open(path, encoding="utf-8") as f:
        js = json.load(f)
    cols = js["colors"] if "colors" in js else js
    missing = [c for c in COUNTRIES if c not in cols]
    if missing:
        raise ValueError(f"colour mapping missing {missing}")
    return {c: (cols[c]["hex"] if isinstance(cols[c], dict) else cols[c]) for c in COUNTRIES}


# --------------------------------------------------------------------------------------
# Row model + QC
# --------------------------------------------------------------------------------------
def build_row(ind, data, fmeta, warnings):
    iid = ind["indicator_id"]
    dec = ind["decimals"]
    cells = []
    for c in COUNTRIES:
        rec = data.get((iid, c))
        if rec is None:
            warnings.append(f"{iid}: no data row for {c}; treated as NA")
            rec = {"value": None, "display": None}
        v = rec["value"]
        if rec["display"] is not None:
            disp = "" if rec["display"].strip() == "<blank>" else rec["display"]
            disp = disp.replace(" ", THIN)
        else:
            disp = "NA" if v is None else fmt_number(v, dec)
        cells.append({"country": c, "value": v, "display": disp})
    # sort: value descending, NA last; ties & NAs in the fixed country order (stable)
    fixed = {c: i for i, c in enumerate(COUNTRIES)}
    cells.sort(key=lambda d: (d["value"] is None, -(d["value"] or 0.0) if d["value"] is not None else 0.0,
                              fixed[d["country"]]))
    vals = [d["value"] for d in cells if d["value"] is not None]
    n = len(vals)
    mean_override = (fmeta.get("mean_overrides") or {}).get(iid)
    if mean_override is not None:
        mean_disp = mean_override
        mean_val = None
    elif n == 0:
        mean_disp, mean_val = "NA", None
    else:
        mean_val = math.fsum(vals) / n
        mean_disp = fmt_number(mean_val, dec)
    markers = (fmeta.get("cell_markers") or {}).get(iid, {})
    for d in cells:
        d["marker"] = markers.get(d["country"], "")
    return {"id": iid, "decimals": dec, "cells": cells, "n": n, "mean_val": mean_val,
            "mean_disp": mean_disp, "mean_overridden": mean_override is not None}


def qc_row(row):
    iid = row["id"]
    cells = row["cells"]
    assert len(cells) == 11, f"{iid}: expected 11 cells, got {len(cells)}"
    cs = [d["country"] for d in cells]
    assert len(set(cs)) == 11 and set(cs) == set(COUNTRIES), f"{iid}: duplicate/missing countries {cs}"
    seen_na = False
    fixed = {c: i for i, c in enumerate(COUNTRIES)}
    for a, b in zip(cells, cells[1:]):
        if a["value"] is None:
            seen_na = True
            assert b["value"] is None, f"{iid}: non-NA after NA in ranking"
            assert fixed[a["country"]] < fixed[b["country"]], f"{iid}: NA order not fixed"
        elif b["value"] is not None:
            assert a["value"] >= b["value"], f"{iid}: rank order violated {a} vs {b}"
            if a["value"] == b["value"]:
                assert fixed[a["country"]] < fixed[b["country"]], f"{iid}: tie order not stable"
    del seen_na
    if not row["mean_overridden"]:
        vals = [d["value"] for d in cells if d["value"] is not None]
        if vals:
            recomputed = sum(Decimal(repr(v)) for v in vals) / Decimal(len(vals))
            assert fmt_number(float(recomputed), row["decimals"]) == row["mean_disp"], \
                f"{iid}: displayed mean {row['mean_disp']} != recomputed {recomputed}"
        else:
            assert row["mean_disp"] == "NA"
    for d in cells:
        if d["value"] is None:
            continue
        if d["display"] and not d["display"].startswith("<"):
            pass
    return True


# --------------------------------------------------------------------------------------
# Drawing helpers (inch coordinates, y downwards; `S` scales everything)
# --------------------------------------------------------------------------------------
class Canvas:
    def __init__(self, ax, x0, y0, scale, style):
        self.ax, self.x0, self.y0, self.s, self.st = ax, x0, y0, scale, style

    def X(self, x):
        return self.x0 + x * self.s

    def Y(self, y):
        return self.y0 + y * self.s

    def rect(self, x, y, w, h, color):
        self.ax.add_patch(matplotlib.patches.Rectangle((self.X(x), self.Y(y)), w * self.s, h * self.s,
                                                       facecolor=color, edgecolor="none", lw=0, zorder=1))

    def hline(self, x1, x2, y, lw, color=None):
        self.ax.plot([self.X(x1), self.X(x2)], [self.Y(y), self.Y(y)], color=color or self.st["ink"],
                     lw=lw * self.s, solid_capstyle="butt", zorder=3)

    def vline(self, x, y1, y2, lw, color=None):
        self.ax.plot([self.X(x), self.X(x)], [self.Y(y1), self.Y(y2)], color=color or self.st["ink"],
                     lw=lw * self.s, solid_capstyle="butt", zorder=3)

    def runs(self, x, base, runs, ha="left", color=None):
        """Draw a sequence of runs [(text, font, size, rise_pt)] on one baseline.
        THIN characters are drawn as a fixed 0.2 em gap. Returns width in inches."""
        pieces = []
        for text, font, size, rise in runs:
            parts = text.split(THIN)
            for k, p in enumerate(parts):
                if k > 0:
                    pieces.append(("", font, size, rise, 0.2 * size))
                if p:
                    pieces.append((p, font, size, rise, text_width_pt(p, font, size)))
        total = sum(p[4] for p in pieces) / 72.0
        cx = x - total if ha == "right" else (x - total / 2 if ha == "center" else x)
        for text, font, size, rise, w in pieces:
            if text:
                self.ax.text(self.X(cx), self.Y(base - rise / 72.0), text, fontproperties=fp(font),
                             fontsize=size * self.s, color=color or self.st["ink"], ha="left",
                             va="baseline", zorder=4)
            cx += w / 72.0
        return total


def marker_runs(text, marker, font, size, st):
    r = [(text, font, size, 0.0)]
    if marker:
        r.append((marker, font, size * st["marker_scale"], size * st["marker_rise"]))
    return r


def wrap_words(text, font, size, width_in, first_extra=0.0):
    """Greedy wrap honouring explicit newlines, plus two small typesetting rules that
    mimic the 2018 figures (keep parentheticals together; no stranded '%' after a comma)."""
    out = []
    for para in text.split("\n"):
        words = para.split(" ")
        lines, cur = [], ""
        for w in words:
            cand = (cur + " " + w) if cur else w
            if text_width_pt(cand, font, size) / 72.0 <= width_in or not cur:
                cur = cand
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        if len(lines) >= 2:
            l1 = lines[0]
            # (a) do not split a parenthetical group: break before "(" instead
            if l1.count("(") > l1.count(")"):
                k = l1.rfind("(")
                if k > 0:
                    a, rest = l1[:k].rstrip(), l1[k:] + " " + " ".join(lines[1:])
                    if text_width_pt(rest, font, size) / 72.0 + first_extra <= width_in:
                        lines = [a, rest]
            # (b) do not strand a tiny fragment ("%") after a comma at the end of line 1
            l1 = lines[0]
            if len(lines) == 2 and "," in l1:
                k = l1.rfind(",")
                tail = l1[k + 1:].strip()
                if tail and len(tail) <= 3:
                    rest = tail + " " + lines[1]
                    if text_width_pt(rest, font, size) / 72.0 + first_extra <= width_in:
                        lines = [l1[:k + 1], rest]
        out.extend(lines)
    return out


# --------------------------------------------------------------------------------------
# Figure layout
# --------------------------------------------------------------------------------------
def figure_style(meta, fmeta):
    st = copy.deepcopy(DEFAULT_STYLE)
    st.update(meta.get("style") or {})
    st.update(fmeta.get("style") or {})
    return st


def layout_figure(fig_no, spec, data, meta, colors, warnings):
    fmeta = (meta.get("figures") or {}).get(str(fig_no), {})
    st = figure_style(meta, fmeta)
    inds = [r for r in spec if r["figure"] == fig_no]
    if not inds:
        raise ValueError(f"no indicators for figure {fig_no} in spec")
    inds.sort(key=lambda r: r["_order"])
    label_over = fmeta.get("label_overrides") or {}
    label_mark = fmeta.get("label_markers") or {}
    sec_over = fmeta.get("section_overrides") or {}
    sec_mark = fmeta.get("section_markers") or {}
    bold_set = set(fmeta.get("bold_label") or [])
    not_bold = set(fmeta.get("not_bold_label") or [])

    mean_col = st["table_width"] - st["label_col"] - 11 * st["cell_col"]
    assert mean_col > 0.15, f"figure {fig_no}: mean column too narrow ({mean_col:.3f} in)"
    label_w = st["label_col"] - st["pad_x"] - st["label_pad_right"]

    items = []  # sequence of ("section", text) and ("row", rowdict)
    prev_sec = object()
    for ind in inds:
        sec = ind["section"]
        if sec != prev_sec:
            if sec:
                disp = sec_over.get(sec, sec)
                items.append({"kind": "section", "text": disp, "marker": sec_mark.get(sec, sec_mark.get(disp, "")),
                              "block_start": True})
            prev_sec_changed = True
        else:
            prev_sec_changed = False
        row = build_row(ind, data, fmeta, warnings)
        qc_row(row)
        bold = (ind["indicator_id"] in bold_set) or (st["bold_unsectioned"] and not sec)
        if ind["indicator_id"] in not_bold:
            bold = False
        font = st["font_bold"] if bold else st["font_regular"]
        label = label_over.get(ind["indicator_id"], ind["label"])
        marker = label_mark.get(ind["indicator_id"], "")
        mw = text_width_pt(marker, font, st["fs_label"] * st["marker_scale"]) / 72.0 if marker else 0.0
        def wrap_label(width, slack=0.0):
            ls = wrap_words(label, font, st["fs_label"], width, first_extra=mw)
            if mw and text_width_pt(ls[-1], font, st["fs_label"]) / 72.0 + mw > width + slack:
                ls = wrap_words(label, font, st["fs_label"], width - mw, first_extra=mw)
            return ls
        wide = st["label_col"] - st["pad_x"] - 0.012
        lines = wrap_label(label_w)
        if len(lines) > 2 and "\n" not in label:
            # use the full column before accepting a 3rd line (taller row)
            lines2 = wrap_label(wide, slack=0.018)
            if len(lines2) < len(lines):
                lines = lines2
        for ln in lines:
            extra = mw if ln is lines[-1] else 0.0
            if text_width_pt(ln, font, st["fs_label"]) / 72.0 + extra > wide + 0.018 + 1e-6:
                warnings.append(f"{ind['indicator_id']}: label line overflows column: {ln!r}")
        row.update({"label_lines": lines, "label_font": font, "label_marker": marker,
                    "block_start": prev_sec_changed and not sec, "section": sec})
        items.append({"kind": "row", "row": row, "block_start": row["block_start"] if not sec else False})
        prev_sec = sec
    return fmeta, st, items, mean_col


def foot_paragraphs(fig_no, fmeta, rows_any_na, st):
    paras = []  # (marker, text)
    if fmeta.get("general_note"):
        paras.append(("", fmeta["general_note"]))
    src_pos = fmeta.get("source_note_position", "after_general")
    if fmeta.get("source_note") and src_pos == "after_general":
        paras.append(("", fmeta["source_note"]))
    mean_note = fmeta.get("mean_note", "auto")
    if mean_note == "auto":
        if rows_any_na and st["show_mean_n"]:
            paras.append(("", DEFAULT_MEAN_NOTE))
    elif mean_note:
        paras.append(("", mean_note))
    for fn in fmeta.get("footnotes") or []:
        if isinstance(fn, str):
            paras.append(("", fn))
        else:
            paras.append((fn.get("marker", ""), fn["text"]))
    if fmeta.get("source_note") and src_pos == "end":
        paras.append(("", fmeta["source_note"]))
    return paras


def foot_lines(paras, st, col_w):
    """Returns list of lines: dict(marker, text, indent, gap_before)."""
    out = []
    font, size = st["font_regular"], st["fs_foot"]
    for pi, (marker, text) in enumerate(paras):
        indent = st["foot_indent"] if marker else 0.0
        lines = _greedy(text, font, size, col_w - indent)
        for li, ln in enumerate(lines):
            out.append({"marker": marker if li == 0 else "", "text": ln, "indent": indent,
                        "gap_before": (st["foot_para_gap"] if (li == 0 and pi > 0) else 0.0)})
    return out


def _greedy(text, font, size, width_in):
    out = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split(" "):
            cand = (cur + " " + w) if cur else w
            if text_width_pt(cand, font, size) / 72.0 <= width_in or not cur:
                cur = cand
            else:
                out.append(cur)
                cur = w
        if cur:
            out.append(cur)
    return out


def measure_and_draw(fig_no, spec, data, meta, colors, warnings, canvas=None):
    """If canvas is None only measures; returns (width, height) in inches (unscaled)."""
    fmeta, st, items, mean_col = layout_figure(fig_no, spec, data, meta, colors, warnings)
    W = st["table_width"]
    pitch = st["line_pitch_pt"] / 72.0
    cap = lambda fs: st["cap_ratio"] * fs / 72.0  # noqa: E731
    title = fmeta.get("title", f"Figure {fig_no}.")

    # ---- vertical positions
    y = 0.0
    y_table_top = st["table_top_dy"]
    y = y_table_top + st["header_h"]
    geo = []
    for it in items:
        if it["kind"] == "section":
            geo.append((it, y, st["section_h"]))
            y += st["section_h"]
        else:
            n_lines = len(it["row"]["label_lines"])
            h = st["row_h"] + max(0, n_lines - 2) * st["row_h_extra_line"]
            geo.append((it, y, h))
            y += h
    y_table_bottom = y

    rows_any_na = any(it["kind"] == "row" and it["row"]["n"] < 11 and not it["row"]["mean_overridden"]
                      for it in items)
    paras = foot_paragraphs(fig_no, fmeta, rows_any_na, st)
    ncols = int(fmeta.get("footnote_columns", 1))
    col_w = W if ncols == 1 else (W - st["foot_col_gap"]) / 2
    flines = foot_lines(paras, st, col_w)
    fpitch = st["foot_pitch_pt"] / 72.0
    # split into columns
    cols = [flines]
    if ncols == 2 and len(flines) > 1:
        heights = [fpitch + l["gap_before"] for l in flines]
        total = sum(heights)
        acc, split = 0.0, len(flines)
        for i, h in enumerate(heights):
            acc += h
            if acc >= total / 2 - 1e-9:
                split = i + 1
                break
        cols = [flines[:split], flines[split:]]
        if cols[1]:
            cols[1][0] = dict(cols[1][0], gap_before=0.0)
    y_foot_rule = y_table_bottom + st["foot_gap_above"]
    col_heights = []
    for c in cols:
        hh = 0.0
        for i, l in enumerate(c):
            hh += (fpitch if i > 0 else 0.0) + l["gap_before"]
        col_heights.append(hh)
    first_base = y_foot_rule + st["foot_text_dy"] + cap(st["fs_foot"])
    if flines:
        y_foot_bottom = first_base + max(col_heights) + st["foot_bottom_dy"]
    else:
        y_foot_bottom = y_foot_rule
    H = y_foot_bottom + 0.01
    if canvas is None:
        return W, H

    cv = canvas
    ink = st["ink"]
    # ---- title block
    cv.hline(0, W, st["red_rule_lw"] / 72.0 / 2, st["red_rule_lw"], color=st["red"])
    cv.runs(0, st["title_base_dy"], [(title, st["font_title"], st["fs_title"], 0.0)])
    cv.hline(0, W, st["title_rule_dy"], st["lw_title_rule"])

    xs_cells = [st["label_col"] + i * st["cell_col"] for i in range(12)]  # left edges + mean left
    x_mean = xs_cells[11]

    # ---- header
    hb = y_table_top + (st["header_h"] + cap(st["fs_header"])) / 2
    cv.runs(st["pad_x"], hb, [(fmeta.get("header_label", "Rank (highest to lowest)"),
                                              st["font_bold"], st["fs_header"], 0.0)])
    for i in range(11):
        cx = xs_cells[i] + st["cell_col"] / 2
        cv.runs(cx, hb, [(str(i + 1), st["font_bold"], st["fs_header"], 0.0)], ha="center")
    cv.runs(x_mean + st["pad_x"] * 0.75, hb, [("Mean", st["font_bold"], st["fs_header"], 0.0)])

    # ---- body
    for it, y0, h in geo:
        if it["kind"] == "section":
            if st["section_band"]:
                cv.rect(0, y0, W, h, st["section_band"])
            base = y0 + (h + cap(st["fs_section"])) / 2
            cv.runs(st["pad_x"], base, marker_runs(it["text"], it["marker"], st["font_bold"], st["fs_section"], st))
            continue
        row = it["row"]
        b1 = y0 + st["pad_top"] + cap(st["fs_cell"])
        for i, d in enumerate(row["cells"]):
            x = xs_cells[i]
            cv.rect(x, y0, st["cell_col"], h, colors[d["country"]])
            cv.runs(x + st["pad_x"], b1, [(COUNTRY_LABELS[d["country"]], st["font_regular"], st["fs_cell"], 0.0)])
            if d["display"]:
                cv.runs(x + st["pad_x"], b1 + pitch,
                        marker_runs(d["display"], d["marker"], st["font_regular"], st["fs_cell"], st))
            elif d["marker"]:
                # marker attached to the country name when no value is displayed
                wname = text_width_pt(COUNTRY_LABELS[d["country"]], st["font_regular"], st["fs_cell"]) / 72.0
                cv.runs(x + st["pad_x"] + wname, b1,
                        [(d["marker"], st["font_regular"], st["fs_cell"] * st["marker_scale"],
                          st["fs_cell"] * st["marker_rise"])])
        # label
        lines = row["label_lines"]
        for li, ln in enumerate(lines):
            mk = row["label_marker"] if li == len(lines) - 1 else ""
            cv.runs(st["pad_x"], b1 + li * pitch, marker_runs(ln, mk, row["label_font"], st["fs_label"], st))
        # mean
        align = fmeta.get("mean_align", st["mean_align"])
        mx = x_mean + st["pad_x"] * 0.75 if align == "left" else W - st["pad_x"] * 0.75
        cv.runs(mx, b1, [(row["mean_disp"], st["font_regular"], st["fs_cell"], 0.0)], ha=align)
        if st["show_mean_n"] and row["n"] < 11 and row["n"] > 0 and not row["mean_overridden"]:
            cv.runs(mx, b1 + pitch, [(f"(n = {row['n']})", st["font_regular"], st["fs_mean_n"], 0.0)],
                    ha=align, color=st["mean_n_color"])

    # ---- rules
    cv.hline(0, W, y_table_top, st["lw_table_top"])
    cv.hline(0, W, y_table_top + st["header_h"], st["lw_header_bottom"])
    for k, (it, y0, h) in enumerate(geo):
        y1 = y0 + h
        nxt = geo[k + 1][0] if k + 1 < len(geo) else None
        if it["kind"] == "section":
            cv.hline(0, W, y1, st["lw_section_under"])
            continue
        if nxt is None:
            lw = st["lw_block_end"]
        elif nxt["kind"] == "section" or nxt.get("block_start"):
            lw = st["lw_block_end"]
        else:
            lw = st["lw_row"]
        cv.hline(0, W, y1, lw)
    # verticals: header
    yh0, yh1 = y_table_top, y_table_top + st["header_h"]
    cv.vline(0, yh0, y_table_bottom, st["lw_vert"])
    cv.vline(W, yh0, y_table_bottom, st["lw_vert"])
    cv.vline(st["label_col"], yh0, yh1, st["lw_vert_major"])
    cv.vline(x_mean, yh0, yh1, st["lw_vert_major"])
    for i in range(1, 11):
        cv.vline(xs_cells[i], yh0, yh1, st["lw_vert"])
    for it, y0, h in geo:
        if it["kind"] != "row":
            continue
        cv.vline(st["label_col"], y0, y0 + h, st["lw_vert_major"])
        cv.vline(x_mean, y0, y0 + h, st["lw_vert_major"])
        for i in range(1, 11):
            cv.vline(xs_cells[i], y0, y0 + h, st["lw_vert"])

    # ---- footnotes
    if flines:
        cv.hline(0, W, y_foot_rule, st["lw_foot_rule"])
        for ci, c in enumerate(cols):
            x0 = 0.0 if ci == 0 else col_w + st["foot_col_gap"]
            yb = first_base
            for i, l in enumerate(c):
                yb += (fpitch if i > 0 else 0.0) + l["gap_before"]
                if l["marker"]:
                    cv.runs(x0, yb, [(l["marker"], st["font_regular"], st["fs_foot"] * st["marker_scale"],
                                      st["fs_foot"] * st["marker_rise"])])
                cv.runs(x0 + l["indent"], yb, [(l["text"], st["font_regular"], st["fs_foot"], 0.0)])
        cv.hline(0, W, y_foot_bottom, st["lw_foot_rule"])
    return W, H


# --------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------
def new_fig(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    return fig, ax


PDF_META = {"Creator": "render_figures.py", "Producer": "matplotlib", "CreationDate": None, "ModDate": None}


def render_one(fig_no, spec, data, meta, colors, outdir, dpi, warnings):
    W, H = measure_and_draw(fig_no, spec, data, meta, colors, warnings)
    st = figure_style(meta, (meta.get("figures") or {}).get(str(fig_no), {}))
    m = st["margin"]
    fig, ax = new_fig(W + 2 * m, H + 2 * m)
    fig.patch.set_facecolor("white")
    measure_and_draw(fig_no, spec, data, meta, colors, [], Canvas(ax, m, m, 1.0, st))
    base = os.path.join(outdir, f"figure_{fig_no}")
    fig.savefig(base + ".png", dpi=dpi, facecolor="white", metadata={"Software": None})
    fig.savefig(base + ".svg", facecolor="white", metadata={"Date": None, "Creator": None})
    fig.savefig(base + ".pdf", facecolor="white", metadata=PDF_META)
    plt.close(fig)
    return base, (W, H)


def render_combined(figs, spec, data, meta, colors, path):
    page_w, page_h = 8.5, 11.0
    with PdfPages(path, metadata=PDF_META) as pdf:
        for fig_no in figs:
            W, H = measure_and_draw(fig_no, spec, data, meta, colors, [])
            st = figure_style(meta, (meta.get("figures") or {}).get(str(fig_no), {}))
            top, side = 0.75, (page_w - W) / 2
            scale = min(1.0, (page_h - 2 * top) / H, (page_w - 1.0) / W)
            fig, ax = new_fig(page_w, page_h)
            x0 = (page_w - W * scale) / 2
            measure_and_draw(fig_no, spec, data, meta, colors, [], Canvas(ax, x0, top, scale, st))
            del side
            pdf.savefig(fig, facecolor="white")
            plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--spec", default=os.path.join(ROOT, "spec", "indicators.csv"))
    ap.add_argument("--colors", default=os.path.join(ROOT, "spec", "country_colors.json"))
    ap.add_argument("--figures", default=",".join(map(str, FIGURE_ORDER)))
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--combined-name", default="figures_combined.pdf")
    ap.add_argument("--no-combined", action="store_true")
    args = ap.parse_args(argv)

    matplotlib.rcParams.update({"svg.hashsalt": "papanicolas2018", "pdf.fonttype": 42,
                                "svg.fonttype": "path", "path.simplify": False})
    spec = load_spec(args.spec)
    data = load_data(args.data)
    with open(args.meta, encoding="utf-8") as f:
        meta = json.load(f)
    colors = load_colors(args.colors)
    figs = [int(x) for x in args.figures.split(",") if x.strip()]
    figs = [f for f in FIGURE_ORDER if f in figs] + [f for f in figs if f not in FIGURE_ORDER]
    os.makedirs(args.outdir, exist_ok=True)
    known = {r["indicator_id"] for r in spec}
    extra = sorted({k[0] for k in data} - known)
    warnings: list = []
    if extra:
        warnings.append(f"data has indicator ids not in spec (ignored): {extra[:10]}{'...' if len(extra) > 10 else ''}")
    for f in figs:
        base, (W, H) = render_one(f, spec, data, meta, colors, args.outdir, args.dpi, warnings)
        print(f"figure {f}: {base}.png/.svg/.pdf  ({W:.2f} x {H:.2f} in table block)  QC ok")
    if not args.no_combined:
        p = os.path.join(args.outdir, args.combined_name)
        render_combined(figs, spec, data, meta, colors, p)
        print(f"combined: {p}")
    for w in dict.fromkeys(warnings):
        print("WARNING:", w, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
