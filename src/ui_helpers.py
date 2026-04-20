

from __future__ import annotations

import pandas as pd


def format_number(x: float | None) -> str:
    if x is None or pd.isna(x):
        return "—"
    if abs(x) >= 1000:
        return f"{x:,.0f}"
    return f"{x:,.2f}"


def top_group(df: pd.DataFrame, group_col: str | None) -> tuple[str, str]:
    if group_col is None or df.empty:
        return "—", "—"

    tmp = (
        df.groupby(group_col, as_index=False)["value"]
        .sum()
        .sort_values("value", ascending=False)
    )
    if tmp.empty:
        return "—", "—"

    return str(tmp.iloc[0][group_col]), format_number(tmp.iloc[0]["value"])


def latest_group(df: pd.DataFrame, time_col: str | None, group_col: str | None) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    out = df.copy()
    if time_col and time_col in out.columns:
        max_time = sorted(out[time_col].astype(str).unique().tolist())[-1]
        out = out[out[time_col].astype(str) == max_time].copy()

    if group_col and group_col in out.columns:
        return (
            out.groupby(group_col, as_index=False)["value"]
            .sum()
            .sort_values("value", ascending=False)
        )

    return out


def exclude_ireland(df: pd.DataFrame, region_col: str | None) -> pd.DataFrame:
    if region_col and region_col in df.columns:
        return df[
            ~df[region_col].astype(str).str.strip().str.lower().isin(["ireland"])
        ].copy()
    return df.copy()


def get_ireland_total(df: pd.DataFrame, region_col: str | None, time_col: str | None) -> float | None:
    if region_col is None or region_col not in df.columns or df.empty:
        return None

    tmp = df.copy()
    if time_col and time_col in tmp.columns:
        max_time = sorted(tmp[time_col].astype(str).unique().tolist())[-1]
        tmp = tmp[tmp[time_col].astype(str) == max_time].copy()

    ireland_df = tmp[tmp[region_col].astype(str).str.strip().str.lower() == "ireland"]
    if ireland_df.empty:
        return None

    return float(ireland_df["value"].sum())


def remove_all_ages(df: pd.DataFrame, age_col: str | None) -> pd.DataFrame:
    out = df.copy()
    if age_col and age_col in out.columns:
        out = out[
            ~out[age_col].astype(str).str.strip().str.lower().isin(["all ages"])
        ]
    return out.copy()


def remove_both_sexes(df: pd.DataFrame, sex_col: str | None) -> pd.DataFrame:
    out = df.copy()
    if sex_col and sex_col in out.columns:
        out = out[
            ~out[sex_col].astype(str).str.strip().str.lower().isin(["both sexes"])
        ]
    return out.copy()


def keep_only_both_sexes(df: pd.DataFrame, sex_col: str | None) -> pd.DataFrame:
    out = df.copy()
    if sex_col and sex_col in out.columns:
        out = out[
            out[sex_col].astype(str).str.strip().str.lower().isin(["both sexes"])
        ]
    return out.copy()


def sort_age_groups(df: pd.DataFrame, age_col: str) -> pd.DataFrame:
    df = df.copy()

    age_order = [
        "Under 5 years",
        "0 - 4 years",
        "5 - 9 years",
        "10 - 14 years",
        "15 - 19 years",
        "20 - 24 years",
        "25 - 29 years",
        "30 - 34 years",
        "35 - 39 years",
        "40 - 44 years",
        "45 - 49 years",
        "50 - 54 years",
        "55 - 59 years",
        "60 - 64 years",
        "65 - 69 years",
        "70 - 74 years",
        "75 - 79 years",
        "80 - 84 years",
        "85 years and over",
        "85 years and over ",
    ]

    df[age_col] = pd.Categorical(df[age_col], categories=age_order, ordered=True)
    return df.sort_values(age_col)


def create_region_insight_text(region_row: pd.Series | None) -> str:
    if region_row is None:
        return "Click a region on the map to see its profile and linked charts."

    region_name = str(region_row.get("region_name", "Selected region"))
    population = region_row.get("population_value")
    dependency = region_row.get("dependency_value")
    fertility = region_row.get("fertility_value")
    death = region_row.get("death_value")

    parts = [f"**{region_name}**"]
    if pd.notna(population):
        parts.append(f"Population: {format_number(population)}")
    if pd.notna(dependency):
        parts.append(f"Old-age dependency: {format_number(dependency)}")
    if pd.notna(fertility):
        parts.append(f"Fertility metric: {format_number(fertility)}")
    if pd.notna(death):
        parts.append(f"Death-rate metric: {format_number(death)}")

    return "  \n".join(parts)