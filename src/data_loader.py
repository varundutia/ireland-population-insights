from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st
from src.ui_helpers import sort_age_groups


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path)
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    return df.dropna(subset=["value"]).reset_index(drop=True)


def find_col(df: pd.DataFrame, keywords: Iterable[str]) -> str | None:
    lower_map = {col: col.lower() for col in df.columns}
    for keyword in keywords:
        keyword = keyword.lower()
        for col, low in lower_map.items():
            if keyword in low:
                return col
    return None


def pick_col(df: pd.DataFrame, candidate_groups: list[list[str]]) -> str | None:
    for group in candidate_groups:
        col = find_col(df, group)
        if col:
            return col
    return None


def apply_filter(df: pd.DataFrame, col: str | None, selected: list[str]) -> pd.DataFrame:
    if col and selected:
        return df[df[col].astype(str).isin(selected)].copy()
    return df.copy()


def safe_options(df: pd.DataFrame, col: str | None) -> list[str]:
    if not col or col not in df.columns:
        return []
    return sorted(df[col].dropna().astype(str).unique().tolist())


def multiselect_filter(label: str, df: pd.DataFrame, col: str | None) -> list[str]:
    opts = safe_options(df, col)
    if not opts:
        return []
    return st.sidebar.multiselect(label, opts)


def detect_columns(datasets: dict[str, pd.DataFrame]) -> dict[str, str | None]:
    vsa38 = datasets["vsa38"]
    vsa94 = datasets["vsa94"]
    vsa104 = datasets["vsa104"]
    vsa108 = datasets["vsa108"]
    pea26 = datasets["pea26"]
    pea27 = datasets["pea27"]
    pea28 = datasets["pea28"]
    pea29 = datasets["pea29"]

    return {
        "vsa38_time": pick_col(vsa38, [["time"], ["year"]]),
        "vsa38_area": pick_col(vsa38, [["area_of_residence"], ["area"], ["region"]]),
        "vsa94_time": pick_col(vsa94, [["time"], ["year"]]),
        "vsa94_area": pick_col(vsa94, [["area_of_residence"], ["area"], ["region"]]),
        "vsa104_time": pick_col(vsa104, [["time"], ["year"]]),
        "vsa104_age": pick_col(vsa104, [["mother_s_age_group"], ["age_group"], ["age group"]]),
        "vsa104_region": pick_col(vsa104, [["region"], ["nuts3"]]),
        "vsa108_time": pick_col(vsa108, [["time"], ["year"]]),
        "vsa108_region": pick_col(vsa108, [["region"], ["nuts3"]]),
        "pea26_time": pick_col(pea26, [["time"], ["year"]]),
        "pea26_age": pick_col(pea26, [["age_group"], ["age group"]]),
        "pea26_sex": pick_col(pea26, [["sex"]]),
        "pea26_region": pick_col(pea26, [["region"], ["nuts3"]]),
        "pea27_time": pick_col(pea27, [["time"], ["year"]]),
        "pea27_age": pick_col(pea27, [["age_group"], ["age group"]]),
        "pea27_sex": pick_col(pea27, [["sex"]]),
        "pea27_hdi": pick_col(pea27, [["human_development_index"], ["hdi"]]),
        "pea28_time": pick_col(pea28, [["time"], ["year"]]),
        "pea28_age": pick_col(pea28, [["age_group"], ["age group"]]),
        "pea28_sex": pick_col(pea28, [["sex"]]),
        "pea28_hdi": pick_col(pea28, [["human_development_index"], ["hdi"]]),
        "pea29_time": pick_col(pea29, [["time"], ["year"]]),
        "pea29_sex": pick_col(pea29, [["sex"]]),
        "pea29_region": pick_col(pea29, [["region"], ["nuts3"]]),
    }


def build_filtered_datasets(
    datasets: dict[str, pd.DataFrame],
    columns: dict[str, str | None],
    selections: dict[str, list[str]],
) -> dict[str, pd.DataFrame]:
    pea26_f = apply_filter(datasets["pea26"], columns["pea26_region"], selections.get("pea26_region_selected", []))
    pea26_f = apply_filter(pea26_f, columns["pea26_sex"], selections.get("pea26_sex_selected", []))

    vsa104_f = apply_filter(datasets["vsa104"], columns["vsa104_region"], selections.get("vsa104_region_selected", []))
    vsa104_f = apply_filter(vsa104_f, columns["vsa104_age"], selections.get("vsa104_age_selected", []))

    vsa108_f = apply_filter(datasets["vsa108"], columns["vsa108_region"], selections.get("vsa108_region_selected", []))

    pea29_f = apply_filter(datasets["pea29"], columns["pea29_region"], selections.get("pea29_region_selected", []))
    pea29_f = apply_filter(pea29_f, columns["pea29_sex"], selections.get("pea29_sex_selected", []))

    vsa38_f = apply_filter(datasets["vsa38"], columns["vsa38_area"], selections.get("vsa38_area_selected", []))
    vsa94_f = apply_filter(datasets["vsa94"], columns["vsa94_area"], selections.get("vsa94_area_selected", []))

    pea27_f = apply_filter(datasets["pea27"], columns["pea27_sex"], selections.get("pea27_sex_selected", []))
    pea27_f = apply_filter(pea27_f, columns["pea27_hdi"], selections.get("pea27_hdi_selected", []))

    pea28_f = apply_filter(datasets["pea28"], columns["pea28_sex"], selections.get("pea28_sex_selected", []))
    pea28_f = apply_filter(pea28_f, columns["pea28_hdi"], selections.get("pea28_hdi_selected", []))

    return {
        "pea26_f": pea26_f,
        "vsa104_f": vsa104_f,
        "vsa108_f": vsa108_f,
        "pea29_f": pea29_f,
        "vsa38_f": vsa38_f,
        "vsa94_f": vsa94_f,
        "pea27_f": pea27_f,
        "pea28_f": pea28_f,
    }
