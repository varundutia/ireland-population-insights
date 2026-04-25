import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


def normalize_region_name(name: str) -> str:
    text = str(name).strip().lower()
    text = text.replace("&", "and")
    text = text.replace("/", " ")
    text = text.replace("-", " ")
    text = " ".join(text.split())

    aliases = {
        "northern and western": "northern and western",
        "northern western": "northern and western",
        "southern": "southern",
        "eastern and midland": "eastern and midland",
        "eastern and midlands": "eastern and midland",
        "mid west": "mid west",
        "mid-west": "mid west",
        "mid east": "mid east",
        "mid-east": "mid east",
        "south east": "south east",
        "south-east": "south east",
        "south west": "south west",
        "south-west": "south west",
        "west": "west",
        "dublin": "dublin",
        "border": "border",
        "midland": "midland",
        "midlands": "midland",
    }
    return aliases.get(text, text)


@st.cache_data
def load_geojson(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing GeoJSON file: {path}. Add an Ireland NUTS3 GeoJSON at this path."
        )

    with open(path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    for feature in geojson.get("features", []):
        props = feature.setdefault("properties", {})
        candidate_name = (
            props.get("NUTS_NAME")
            or props.get("NAME_LATN")
            or props.get("name")
            or props.get("NAME")
            or feature.get("id")
            or ""
        )
        props["normalized_name"] = normalize_region_name(candidate_name)

    return geojson


def add_normalized_region_column(df: pd.DataFrame, region_col: str | None) -> pd.DataFrame:
    out = df.copy()
    if region_col and region_col in out.columns:
        out["normalized_region"] = out[region_col].astype(str).map(normalize_region_name)
    return out


def build_latest_region_metrics(
    pea26_df: pd.DataFrame,
    pea29_df: pd.DataFrame,
    vsa104_df: pd.DataFrame,
    vsa108_df: pd.DataFrame,
    pea26_region_col: str,
    pea29_region_col: str,
    vsa104_region_col: str,
    vsa108_region_col: str,
) -> pd.DataFrame:
    pea26_df = add_normalized_region_column(pea26_df, pea26_region_col)
    pea29_df = add_normalized_region_column(pea29_df, pea29_region_col)
    vsa104_df = add_normalized_region_column(vsa104_df, vsa104_region_col)
    vsa108_df = add_normalized_region_column(vsa108_df, vsa108_region_col)

    pop = (
        pea26_df.groupby(["normalized_region", pea26_region_col], as_index=False)["value"]
        .sum()
        .rename(columns={pea26_region_col: "region_name", "value": "population_value"})
    )
    dep = (
        pea29_df.groupby(["normalized_region", pea29_region_col], as_index=False)["value"]
        .sum()
        .rename(columns={pea29_region_col: "region_name_dep", "value": "dependency_value"})
    )
    fert = (
        vsa104_df.groupby(["normalized_region", vsa104_region_col], as_index=False)["value"]
        .sum()
        .rename(columns={vsa104_region_col: "region_name_fert", "value": "fertility_value"})
    )
    death = (
        vsa108_df.groupby(["normalized_region", vsa108_region_col], as_index=False)["value"]
        .sum()
        .rename(columns={vsa108_region_col: "region_name_death", "value": "death_value"})
    )

    merged = pop.merge(
        dep[["normalized_region", "dependency_value"]],
        on="normalized_region",
        how="outer",
    )
    merged = merged.merge(
        fert[["normalized_region", "fertility_value"]],
        on="normalized_region",
        how="outer",
    )
    merged = merged.merge(
        death[["normalized_region", "death_value"]],
        on="normalized_region",
        how="outer",
    )

    merged["region_name"] = merged["region_name"].fillna(
        merged["normalized_region"].str.title()
    )
    return merged


def make_hero_choropleth(
    region_metrics_df: pd.DataFrame,
    geojson: dict,
    metric_column: str,
    metric_label: str,
    theme_base: str = "light",
):
    plot_df = region_metrics_df.dropna(subset=[metric_column]).copy()

    is_dark = theme_base == "dark"
    text_color = "#FFFFFF" if is_dark else "#333333"
    bg_color = "rgba(0,0,0,0)"
    border_color = "#6B7280" if is_dark else "#E5E7EB"

    fig = px.choropleth(
        plot_df,
        geojson=geojson,
        locations="normalized_region",
        featureidkey="properties.normalized_name",
        color=metric_column,
        hover_name="region_name",
        hover_data={
            metric_column: ":,.2f",
            "population_value": ":,.0f",
            "dependency_value": ":,.2f",
            "fertility_value": ":,.2f",
            "death_value": ":,.2f",
            "normalized_region": False,
        },
        color_continuous_scale=[
            [0.0, "#FFF7F3"],
            [0.2, "#FDE0DD"],
            [0.4, "#FCC5C0"],
            [0.6, "#FA9FB5"],
            [0.8, "#C51B8A"],
            [1.0, "#7A0177"],
        ],
    )

    fig.update_traces(
        marker_line_color=border_color,
        marker_line_width=1.0,
    )
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor=bg_color,
        projection_type="mercator",
    )
    fig.update_layout(
        title=dict(
            text=f"Ireland NUTS3 regions by {metric_label}",
            font=dict(color=text_color, size=16),
        ),
        height=620,
        margin={"l": 0, "r": 0, "t": 50, "b": 0},
        coloraxis_colorbar=dict(
            title=metric_label,
            tickfont=dict(color=text_color),
            titlefont=dict(color=text_color),
        ),
        dragmode=False,
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(color=text_color),
    )
    return fig
