from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st


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


def detect_columns(datasets: dict[str, pd.DataFrame]) -> dict[str, str | None]:
    vsa104 = datasets["vsa104"]
    vsa108 = datasets["vsa108"]
    pea26 = datasets["pea26"]
    pea29 = datasets["pea29"]

    return {
        "vsa104_time": pick_col(vsa104, [["time"], ["year"]]),
        "vsa104_age": pick_col(vsa104, [["mother_s_age_group"], ["age_group"], ["age group"]]),
        "vsa104_region": pick_col(vsa104, [["region"], ["nuts3"]]),
        "vsa108_time": pick_col(vsa108, [["time"], ["year"]]),
        "vsa108_region": pick_col(vsa108, [["region"], ["nuts3"]]),
        "pea26_time": pick_col(pea26, [["time"], ["year"]]),
        "pea26_age": pick_col(pea26, [["age_group"], ["age group"]]),
        "pea26_sex": pick_col(pea26, [["sex"]]),
        "pea26_region": pick_col(pea26, [["region"], ["nuts3"]]),
        "pea29_time": pick_col(pea29, [["time"], ["year"]]),
        "pea29_sex": pick_col(pea29, [["sex"]]),
        "pea29_region": pick_col(pea29, [["region"], ["nuts3"]]),
    }
