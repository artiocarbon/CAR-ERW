#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ERW CaR Viewer (Streamlit)

Loads CaR results saved as JSON files (single- or multi-CaR format) from a
`results/` folder and lets you interactively:

- Select one or more stones (compositions)
- Select one or more CaR levels (e.g., 95, 90, 85)
- Choose a visualization mode:
  * Stones per CaR (one figure per CaR; multiple stones overlaid)
  * CaR per stone (one figure per stone; multiple CaR lines)
  * Grid (subplots: rows = stones, columns = CaR)

Each plot includes, at the bottom-right, a composition legend for the stone(s).
You can also download each figure as a PNG.

Expected JSON schemas:

1) Multi-CaR (preferred):
{
  "time_years": [...],
  "curves": [
    {"car_level": 95.0, "percentile": 5.0, "guarantee_kg_per_t": [...]},
    {"car_level": 90.0, "percentile": 10.0, "guarantee_kg_per_t": [...]},
    ...
  ],
  "N": 100, "years": 150,
  "composition_name": "Basalt A",           # optional
  "composition": { "CaSiO3": 0.40, ... }    # optional (fractions summing ~1)
}

2) Single-CaR:
{
  "car_level": 90.0,
  "time_years": [...],
  "guarantee_kg_per_t": [...],
  "percentile": 10.0,
  "N": 100, "years": 150,
  "composition_name": "Basalt A",           # optional
  "composition": { "CaSiO3": 0.40, ... }    # optional
}

File naming is free-form, but something like `A_CAR.json` is convenient.
"""

import os, glob, json, io
from typing import Dict, List
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="ERW CaR Viewer", layout="wide")


# ---------------------- Loaders & helpers ---------------------- #

def load_all_results(results_dir: str) -> Dict[str, dict]:
    """
    Load all JSON files from `results_dir` and return a dictionary keyed by
    base filename (without suffix), each containing:
        {
          "name": <display name>,
          "time": np.ndarray,                 # time in years
          "curves": {car_level: np.ndarray}, # guarantee kg/t vs time
          "meta": {
            "path": str,
            "N": int or None,
            "years": int or None,
            "composition": dict or None,     # fractions 0..1
          }
        }
    """
    out = {}
    for path in sorted(glob.glob(os.path.join(results_dir, "*.json"))):
        base = os.path.basename(path)
        key = base.replace("_CAR.json", "").replace(".json", "")
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception as e:
            st.warning(f"Could not read {base}: {e}")
            continue

        curves_map = {}
        if "curves" in data and isinstance(data["curves"], list):
            # multi-CaR
            for c in data["curves"]:
                cl = float(c.get("car_level"))
                g = np.asarray(c.get("guarantee_kg_per_t", []), dtype=float)
                curves_map[cl] = g
            time = np.asarray(data.get("time_years", []), dtype=float)
        else:
            # single-CaR fallback
            cl = float(data.get("car_level"))
            g = np.asarray(data.get("guarantee_kg_per_t", []), dtype=float)
            time = np.asarray(data.get("time_years", []), dtype=float)
            curves_map[cl] = g

        nice = data.get("composition_name") or key
        out[key] = {
            "name": nice,
            "time": time,
            "curves": curves_map,
            "meta": {
                "path": path,
                "N": data.get("N"),
                "years": data.get("years"),
                "composition": data.get("composition"),
            },
        }
    return out


def union_car_levels(dataset: Dict[str, dict]) -> List[float]:
    """Return the union of CaR levels present in the dataset, sorted desc."""
    s = set()
    for payload in dataset.values():
        s |= set(float(k) for k in payload["curves"].keys())
    return sorted(s, reverse=True)


def fig_to_bytes(fig) -> bytes:
    """Serialize a Matplotlib figure into PNG bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()


def format_composition(comp: dict | None) -> str:
    """
    Return a compact, human-friendly composition string:
    "CaSiO3 40%, MgSiO3 30%, NaAlSi3O8 20%, KAlSi3O8 10%"
    If comp is None or empty, return "composition: n/a".
    """
    if not comp:
        return "composition: n/a"
    # keep a stable order for readability
    order = ["CaSiO3", "MgSiO3", "NaAlSi3O8", "KAlSi3O8"]
    parts = []
    s = sum(float(v) for v in comp.values()) or 1.0
    for k in order:
        if k in comp:
            pct = 100.0 * float(comp[k]) / s
            parts.append(f"{k} {pct:.0f}%")
    # include any extra keys if present
    for k, v in comp.items():
        if k not in order:
            pct = 100.0 * float(v) / s
            parts.append(f"{k} {pct:.0f}%")
    return ", ".join(parts)


def add_composition_legend(ax, items: List[str]):
    """
    Add a bottom-right legend-like box listing composition strings.
    Each item is one line.
    """
    if not items:
        items = ["composition: n/a"]
    text = "\n".join(items)
    # Place as anchored text box at lower right
    ax.text(
        1.0, 0.0, text,
        transform=ax.transAxes,
        ha="right", va="bottom",
        fontsize=9,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8, edgecolor="none", pad=0.4),
    )


# ---------------------- Sidebar ---------------------- #

st.sidebar.title("Options")

results_dir = st.sidebar.text_input("Results folder", value="results")
data = load_all_results(results_dir)

if not data:
    st.info("Put your JSON files in a `results/` folder (e.g., A_CAR.json, B_CAR.json, ...).")
    st.stop()

stone_keys = list(data.keys())
stone_labels = [f"{k} — {data[k]['name']}" for k in stone_keys]
label_to_key = dict(zip(stone_labels, stone_keys))

default_stones = stone_labels
selected_stones_labels = st.sidebar.multiselect("Stones", stone_labels, default=default_stones)
selected_stones = {label_to_key[l]: data[label_to_key[l]] for l in selected_stones_labels}

all_cars = union_car_levels(data)
default_cars = [c for c in [95.0, 90.0, 85.0, 80.0] if c in all_cars] or all_cars
selected_cars = st.sidebar.multiselect("CaR levels (%)", all_cars, default=default_cars)

mode = st.sidebar.selectbox(
    "View mode",
    ["Stones per CaR (one figure per CaR)", "CaR per stone (one figure per stone)", "Grid (subplots)"],
)

show_grid = st.sidebar.checkbox("Show grid", value=True)
run_btn = st.sidebar.button("Render plots")


# ---------------------- Main ---------------------- #

st.title("ERW CaR Viewer")
st.write(f"**Results folder:** `{results_dir}`")
st.write(f"Selected **{len(selected_stones)}** stone(s) and CaR levels **{selected_cars}**.")

if not selected_stones or not selected_cars:
    st.warning("Please select at least one stone and one CaR level.")
    st.stop()


# ---------------------- Plotters ---------------------- #

def plot_stones_per_car(stones: Dict[str, dict], car_level: float):
    """
    One figure for a single CaR. Multiple stones overlaid.
    The legend (lower-right) shows a composition line per stone.
    """
    # all stones should share same time length; take the first
    time = next(iter(stones.values()))["time"]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ymax = 1.0
    comp_lines = []
    for key, payload in stones.items():
        name = payload["name"]
        g = payload["curves"].get(car_level)
        if g is None or g.size == 0:
            continue
        ax.plot(time, g, label=name)
        ymax = max(ymax, float(np.nanmax(g)))
        comp = payload["meta"].get("composition")
        comp_lines.append(f"{name}: {format_composition(comp)}")

    ax.set_ylim(0, ymax * 1.05)
    ax.set_xlabel("Time (years)")
    ax.set_ylabel("Guarantee (kg CO$_2$ per tonne promised)")
    ax.set_title(f"CaR {int(car_level)}% — selected stones")
    if show_grid: ax.grid(True, alpha=0.3)
    # Regular legend for line labels (stone names)
    ax.legend(loc="upper left", framealpha=0.9)
    # Composition legend at bottom-right
    add_composition_legend(ax, comp_lines)
    plt.tight_layout()
    return fig


def plot_cars_per_stone(stone_key: str, payload: dict, car_levels: List[float]):
    """
    One figure per stone. Multiple CaR lines overlaid.
    Bottom-right legend shows the stone composition.
    """
    time = payload["time"]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ymax = 1.0
    for car in sorted(car_levels, reverse=True):
        g = payload["curves"].get(car)
        if g is None or g.size == 0:
            continue
        ax.plot(time, g, label=f"CaR {int(car)}%")
        ymax = max(ymax, float(np.nanmax(g)))

    ax.set_ylim(0, ymax * 1.05)
    ax.set_xlabel("Time (years)")
    ax.set_ylabel("Guarantee (kg CO$_2$ per tonne promised)")
    title = f"{payload['name']} ({stone_key})"
    ax.set_title(title)
    if show_grid: ax.grid(True, alpha=0.3)
    # CaR legend (lines)
    ax.legend(loc="upper left", framealpha=0.9)
    # Composition legend
    comp = payload["meta"].get("composition")
    add_composition_legend(ax, [format_composition(comp)])
    plt.tight_layout()
    return fig


def plot_grid(stones: Dict[str, dict], car_levels: List[float]):
    """
    Grid of subplots: rows = stones, columns = CaR.
    Each panel shows a single line and a small composition box.
    """
    rows, cols = len(stones), len(car_levels)
    fig, axs = plt.subplots(rows, cols, figsize=(4.8 * cols, 3.3 * rows), squeeze=False)
    for r, (key, payload) in enumerate(stones.items()):
        time = payload["time"]
        comp = payload["meta"].get("composition")
        comp_str = format_composition(comp)
        name = payload["name"]
        for c, car in enumerate(car_levels):
            ax = axs[r][c]
            g = payload["curves"].get(car, np.array([]))
            if g.size > 0:
                ax.plot(time, g)
                ymax = float(np.nanmax(g))
                ax.set_ylim(0, ymax * 1.05 if ymax > 0 else 1.0)
            ax.set_title(f"{name} — CaR {int(car)}%")
            ax.set_xlabel("Years")
            ax.set_ylabel("Guarantee (kg/t)")
            if show_grid: ax.grid(True, alpha=0.3)
            # Tiny composition box in each panel
            add_composition_legend(ax, [comp_str])
    plt.tight_layout()
    return fig


# ---------------------- Render ---------------------- #

if run_btn:
    if mode.startswith("Stones per CaR"):
        for car in selected_cars:
            fig = plot_stones_per_car(selected_stones, car)
            st.pyplot(fig)
            st.download_button(
                label=f"Download PNG — CaR {int(car)}%",
                data=fig_to_bytes(fig),
                file_name=f"stones_per_car_CaR{int(car)}.png",
                mime="image/png",
            )
            plt.close(fig)

    elif mode.startswith("CaR per stone"):
        for key, payload in selected_stones.items():
            fig = plot_cars_per_stone(key, payload, selected_cars)
            st.pyplot(fig)
            st.download_button(
                label=f"Download PNG — {payload['name']}",
                data=fig_to_bytes(fig),
                file_name=f"cars_per_stone_{key}.png",
                mime="image/png",
            )
            plt.close(fig)

    else:  # Grid
        fig = plot_grid(selected_stones, selected_cars)
        st.pyplot(fig)
        st.download_button(
            label="Download PNG — Grid",
            data=fig_to_bytes(fig),
            file_name=f"grid_{len(selected_stones)}x{len(selected_cars)}.png",
            mime="image/png",
        )
        plt.close(fig)

# ---------------------- Details footer ---------------------- #

with st.expander("Loaded files summary"):
    for k, p in data.items():
        comp = p["meta"].get("composition")
        st.write(f"**{k}** — {p['name']}")
        st.write(f"- File: {p['meta']['path']}")
        st.write(f"- CaR levels available: {sorted(p['curves'].keys(), reverse=True)}")
        st.write(f"- N={p['meta'].get('N')} | years={p['meta'].get('years')}")
        if comp:
            st.json(comp)
