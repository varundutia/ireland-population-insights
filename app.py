from __future__ import annotations

from pathlib import Path
from typing import Iterable

import altair as alt
import pandas as pd
import streamlit as st


# ============================================================
# Page setup
# ============================================================
st.set_page_config(
    page_title="Ireland People & Society Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

alt.data_transformers.disable_max_rows()


# ============================================================
# Paths
# ============================================================
DATA_DIR = Path("data_processed")

FILES = {
    "vsa38": DATA_DIR / "vsa38_birth_rate_summary.csv",
    "vsa94": DATA_DIR / "vsa94_infant_mortality_summary.csv",
    "vsa104": DATA_DIR / "vsa104_fertility_summary.csv",
    "vsa108": DATA_DIR / "vsa108_death_rate_summary.csv",
    "pea26": DATA_DIR / "pea26_population_summary.csv",
    "pea27": DATA_DIR / "pea27_citizenship_non_eu_summary.csv",
    "pea28": DATA_DIR / "pea28_birthplace_non_eu_summary.csv",
    "pea29": DATA_DIR / "pea29_old_age_dependency_summary.csv",
}


# ============================================================
# Loading helpers
# ============================================================
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


# ============================================================
# Chart helpers
# ============================================================
def make_bar_chart(
    df: pd.DataFrame,
    category_col: str,
    title: str,
    top_n: int = 10,
    format_str: str = ",.2f",
) -> alt.Chart:
    plot_df = (
        df.groupby(category_col, as_index=False)["value"]
        .sum()
        .sort_values("value", ascending=False)
        .head(top_n)
    )

    return (
        alt.Chart(plot_df)
        .mark_bar()
        .encode(
            x=alt.X("value:Q", title="Value"),
            y=alt.Y(f"{category_col}:N", sort="-x", title=""),
            color=alt.Color("value:Q", title="Value"),
            tooltip=[
                alt.Tooltip(f"{category_col}:N", title=category_col),
                alt.Tooltip("value:Q", title="Value", format=format_str),
            ],
        )
        .properties(height=380, title=title)
    )


def make_stacked_bar(
    df: pd.DataFrame,
    category_col: str,
    stack_col: str,
    title: str,
    top_n: int = 10,
    format_str: str = ",.2f",
) -> alt.Chart:
    grouped = df.groupby([category_col, stack_col], as_index=False)["value"].sum()
    top_categories = (
        grouped.groupby(category_col, as_index=False)["value"]
        .sum()
        .sort_values("value", ascending=False)
        .head(top_n)[category_col]
        .tolist()
    )
    grouped = grouped[grouped[category_col].isin(top_categories)]

    if "age" in category_col.lower():
        grouped = sort_age_groups(grouped, category_col)

    return (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X("value:Q", title="Value"),
            y=alt.Y(
                f"{category_col}:N",
                sort=None if "age" in category_col.lower() else top_categories,
                title="",
            ),
            color=alt.Color(f"{stack_col}:N", title=stack_col),
            tooltip=[
                alt.Tooltip(f"{category_col}:N", title=category_col),
                alt.Tooltip(f"{stack_col}:N", title=stack_col),
                alt.Tooltip("value:Q", title="Value", format=format_str),
            ],
        )
        .properties(height=380, title=title)
    )


def make_heatmap(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    format_str: str = ",.2f",
) -> alt.Chart:
    if df.empty:
        empty_df = pd.DataFrame({x_col: [], y_col: [], "value": []})
        return (
            alt.Chart(empty_df)
            .mark_rect()
            .properties(height=420, title=title)
        )

    grouped = df.groupby([x_col, y_col], as_index=False)["value"].sum()

    if "age" in x_col.lower():
        grouped = sort_age_groups(grouped, x_col)

    return (
        alt.Chart(grouped)
        .mark_rect()
        .encode(
            x=alt.X(f"{x_col}:N", title=x_col, sort=None),
            y=alt.Y(f"{y_col}:N", title=y_col),
            color=alt.Color("value:Q", title="Value"),
            tooltip=[
                alt.Tooltip(f"{x_col}:N", title=x_col),
                alt.Tooltip(f"{y_col}:N", title=y_col),
                alt.Tooltip("value:Q", title="Value", format=format_str),
            ],
        )
        .properties(height=420, title=title)
    )


def make_line_chart(
    df: pd.DataFrame,
    time_col: str,
    group_col: str,
    title: str,
    format_str: str = ",.2f",
) -> alt.Chart:
    grouped = df.groupby([time_col, group_col], as_index=False)["value"].sum()

    return (
        alt.Chart(grouped)
        .mark_line(point=True)
        .encode(
            x=alt.X(f"{time_col}:N", title=time_col),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color(f"{group_col}:N", title=group_col),
            tooltip=[
                alt.Tooltip(f"{time_col}:N", title=time_col),
                alt.Tooltip(f"{group_col}:N", title=group_col),
                alt.Tooltip("value:Q", title="Value", format=format_str),
            ],
        )
        .properties(height=380, title=title)
    )


def make_grouped_bar(
    df: pd.DataFrame,
    x_col: str,
    color_col: str,
    title: str,
    format_str: str = ",.2f",
) -> alt.Chart:
    grouped = df.groupby([x_col, color_col], as_index=False)["value"].sum()

    if "age" in x_col.lower():
        grouped = sort_age_groups(grouped, x_col)

    return (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X(f"{x_col}:N", title=x_col, sort=None),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color(f"{color_col}:N", title=color_col),
            tooltip=[
                alt.Tooltip(f"{x_col}:N", title=x_col),
                alt.Tooltip(f"{color_col}:N", title=color_col),
                alt.Tooltip("value:Q", title="Value", format=format_str),
            ],
        )
        .properties(height=380, title=title)
    )


def make_population_pyramid(
    df: pd.DataFrame,
    age_col: str,
    sex_col: str,
    title: str,
) -> alt.Chart:
    grouped = df.groupby([age_col, sex_col], as_index=False)["value"].sum()
    grouped = sort_age_groups(grouped, age_col)

    sex_values = grouped[sex_col].astype(str).unique().tolist()
    if len(sex_values) < 2:
        return (
            alt.Chart(grouped)
            .mark_bar()
            .encode(
                x=alt.X("value:Q", title="Population"),
                y=alt.Y(f"{age_col}:N", sort=None, title=age_col),
                color=alt.Color(f"{sex_col}:N", title=sex_col),
                tooltip=[
                    alt.Tooltip(f"{age_col}:N", title=age_col),
                    alt.Tooltip(f"{sex_col}:N", title=sex_col),
                    alt.Tooltip("value:Q", title="Population", format=",.0f"),
                ],
            )
            .properties(height=500, title=title)
        )

    first_sex = sex_values[0]
    grouped["pyramid_value"] = grouped["value"]
    grouped.loc[grouped[sex_col].astype(str) == first_sex, "pyramid_value"] *= -1

    return (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X("pyramid_value:Q", title="Population"),
            y=alt.Y(f"{age_col}:N", sort=None, title=age_col),
            color=alt.Color(f"{sex_col}:N", title=sex_col),
            tooltip=[
                alt.Tooltip(f"{age_col}:N", title=age_col),
                alt.Tooltip(f"{sex_col}:N", title=sex_col),
                alt.Tooltip("value:Q", title="Population", format=",.0f"),
            ],
        )
        .properties(height=500, title=title)
    )


# ============================================================
# Load data
# ============================================================
try:
    vsa38 = load_csv(FILES["vsa38"])
    vsa94 = load_csv(FILES["vsa94"])
    vsa104 = load_csv(FILES["vsa104"])
    vsa108 = load_csv(FILES["vsa108"])
    pea26 = load_csv(FILES["pea26"])
    pea27 = load_csv(FILES["pea27"])
    pea28 = load_csv(FILES["pea28"])
    pea29 = load_csv(FILES["pea29"])
except Exception as e:
    st.error(str(e))
    st.stop()


# ============================================================
# Detect columns
# ============================================================
vsa38_time = pick_col(vsa38, [["time"], ["year"]])
vsa38_area = pick_col(vsa38, [["area_of_residence"], ["area"], ["region"]])

vsa94_time = pick_col(vsa94, [["time"], ["year"]])
vsa94_area = pick_col(vsa94, [["area_of_residence"], ["area"], ["region"]])

vsa104_time = pick_col(vsa104, [["time"], ["year"]])
vsa104_age = pick_col(vsa104, [["mother_s_age_group"], ["age_group"], ["age group"]])
vsa104_region = pick_col(vsa104, [["region"], ["nuts3"]])

vsa108_time = pick_col(vsa108, [["time"], ["year"]])
vsa108_region = pick_col(vsa108, [["region"], ["nuts3"]])

pea26_time = pick_col(pea26, [["time"], ["year"]])
pea26_age = pick_col(pea26, [["age_group"], ["age group"]])
pea26_sex = pick_col(pea26, [["sex"]])
pea26_region = pick_col(pea26, [["region"], ["nuts3"]])

pea27_time = pick_col(pea27, [["time"], ["year"]])
pea27_age = pick_col(pea27, [["age_group"], ["age group"]])
pea27_sex = pick_col(pea27, [["sex"]])
pea27_hdi = pick_col(pea27, [["human_development_index"], ["hdi"]])

pea28_time = pick_col(pea28, [["time"], ["year"]])
pea28_age = pick_col(pea28, [["age_group"], ["age group"]])
pea28_sex = pick_col(pea28, [["sex"]])
pea28_hdi = pick_col(pea28, [["human_development_index"], ["hdi"]])

pea29_time = pick_col(pea29, [["time"], ["year"]])
pea29_sex = pick_col(pea29, [["sex"]])
pea29_region = pick_col(pea29, [["region"], ["nuts3"]])


# ============================================================
# Sidebar filters
# ============================================================
st.sidebar.title("Filters")

pea26_region_selected = multiselect_filter("Population region", pea26, pea26_region)
pea26_sex_selected = multiselect_filter("Population sex", pea26, pea26_sex)

vsa104_region_selected = multiselect_filter("Fertility region", vsa104, vsa104_region)
vsa104_age_selected = multiselect_filter("Mother age group", vsa104, vsa104_age)

vsa108_region_selected = multiselect_filter("Death-rate region", vsa108, vsa108_region)

pea29_region_selected = multiselect_filter("Dependency region", pea29, pea29_region)
pea29_sex_selected = multiselect_filter("Dependency sex", pea29, pea29_sex)

vsa38_area_selected = multiselect_filter("Birth-rate area", vsa38, vsa38_area)
vsa94_area_selected = multiselect_filter("Infant mortality area", vsa94, vsa94_area)

pea27_sex_selected = multiselect_filter("Citizenship sex", pea27, pea27_sex)
pea27_hdi_selected = multiselect_filter("Citizenship HDI", pea27, pea27_hdi)

pea28_sex_selected = multiselect_filter("Birthplace sex", pea28, pea28_sex)
pea28_hdi_selected = multiselect_filter("Birthplace HDI", pea28, pea28_hdi)


# ============================================================
# Apply filters
# ============================================================
pea26_f = apply_filter(pea26, pea26_region, pea26_region_selected)
pea26_f = apply_filter(pea26_f, pea26_sex, pea26_sex_selected)

vsa104_f = apply_filter(vsa104, vsa104_region, vsa104_region_selected)
vsa104_f = apply_filter(vsa104_f, vsa104_age, vsa104_age_selected)

vsa108_f = apply_filter(vsa108, vsa108_region, vsa108_region_selected)

pea29_f = apply_filter(pea29, pea29_region, pea29_region_selected)
pea29_f = apply_filter(pea29_f, pea29_sex, pea29_sex_selected)

vsa38_f = apply_filter(vsa38, vsa38_area, vsa38_area_selected)
vsa94_f = apply_filter(vsa94, vsa94_area, vsa94_area_selected)

pea27_f = apply_filter(pea27, pea27_sex, pea27_sex_selected)
pea27_f = apply_filter(pea27_f, pea27_hdi, pea27_hdi_selected)

pea28_f = apply_filter(pea28, pea28_sex, pea28_sex_selected)
pea28_f = apply_filter(pea28_f, pea28_hdi, pea28_hdi_selected)


# ============================================================
# National totals before removing Ireland from charts
# ============================================================
population_total_ireland = get_ireland_total(pea26_f, pea26_region, pea26_time)
dependency_total_ireland = get_ireland_total(pea29_f, pea29_region, pea29_time)
death_total_ireland = get_ireland_total(vsa108_f, vsa108_region, vsa108_time)
fertility_total_ireland = get_ireland_total(vsa104_f, vsa104_region, vsa104_time)


# ============================================================
# Remove Ireland from regional comparison datasets
# ============================================================
pea26_f = exclude_ireland(pea26_f, pea26_region)
pea29_f = exclude_ireland(pea29_f, pea29_region)
vsa104_f = exclude_ireland(vsa104_f, vsa104_region)
vsa108_f = exclude_ireland(vsa108_f, vsa108_region)


# ============================================================
# App header
# ============================================================
st.title("Ireland People & Society Dashboard")
st.caption(
    "Exploring population structure, birth and fertility patterns, mortality, dependency, and diversity using CSO High Value Datasets."
)


# ============================================================
# KPI row
# ============================================================
pop_top_name, pop_top_value = top_group(pea26_f, pea26_region)
dep_top_name, dep_top_value = top_group(pea29_f, pea29_region)
death_top_name, death_top_value = top_group(vsa108_f, vsa108_region)
fert_top_name, fert_top_value = top_group(vsa104_f, vsa104_region)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ireland total population", format_number(population_total_ireland))
c2.metric("Ireland old-age dependency", format_number(dependency_total_ireland))
c3.metric("Largest population region", pop_top_name, pop_top_value)
c4.metric("Highest dependency region", dep_top_name, dep_top_value)


# ============================================================
# Tabs
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Population Structure",
        "Births & Fertility",
        "Mortality",
        "Citizenship & Birthplace",
    ]
)


# ============================================================
# Tab 1 - Population Structure
# ============================================================
with tab1:
    st.subheader("Population structure and old-age dependency")

    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        if not pea26_f.empty and pea26_region:
            latest_pop = latest_group(pea26_f, pea26_time, pea26_region)
            st.altair_chart(
                make_bar_chart(
                    latest_pop,
                    pea26_region,
                    "Latest population by region",
                    top_n=12,
                    format_str=",.0f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Population region column not detected or no data after filtering.")

    with row1_col2:
        if not pea29_f.empty and pea29_region:
            latest_dep = latest_group(pea29_f, pea29_time, pea29_region)
            st.altair_chart(
                make_bar_chart(
                    latest_dep,
                    pea29_region,
                    "Latest old-age dependency ratio by region",
                    top_n=12,
                    format_str=",.2f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Dependency region column not detected or no data after filtering.")

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        if not pea26_f.empty and pea26_age and pea26_region:
            heatmap_df = pea26_f.copy()
            heatmap_df = remove_all_ages(heatmap_df, pea26_age)
            heatmap_df = keep_only_both_sexes(heatmap_df, pea26_sex)

            if heatmap_df.empty:
                st.warning("No data available for the population heatmap after filtering.")
            else:
                st.altair_chart(
                    make_heatmap(
                        heatmap_df,
                        pea26_age,
                        pea26_region,
                        "Population heatmap: age group × region",
                        format_str=",.0f",
                    ),
                    use_container_width=True,
                )
        else:
            st.info("Population age or region column not detected.")

    with row2_col2:
        if not pea26_f.empty and pea26_age and pea26_sex:
            pyramid_df = pea26_f.copy()
            pyramid_df = remove_all_ages(pyramid_df, pea26_age)
            pyramid_df = remove_both_sexes(pyramid_df, pea26_sex)

            if pea26_region and pea26_region_selected:
                selected_non_ireland = [
                    x for x in pea26_region_selected
                    if str(x).strip().lower() != "ireland"
                ]
                if selected_non_ireland:
                    pyramid_df = pyramid_df[
                        pyramid_df[pea26_region].astype(str).isin(selected_non_ireland)
                    ]
            elif pea26_region:
                available_regions = safe_options(pea26_f, pea26_region)
                if available_regions:
                    pyramid_df = pyramid_df[
                        pyramid_df[pea26_region].astype(str) == available_regions[0]
                    ]

            if pyramid_df.empty:
                st.warning("No data available for the population pyramid after filtering.")
            else:
                st.altair_chart(
                    make_population_pyramid(
                        pyramid_df,
                        pea26_age,
                        pea26_sex,
                        "Population pyramid for selected/default region",
                    ),
                    use_container_width=True,
                )
        else:
            st.info("Population age or sex column not detected.")


# ============================================================
# Tab 2 - Births & Fertility
# ============================================================
with tab2:
    st.subheader("Birth rates and fertility patterns")

    top_row = st.columns(4)
    top_row[0].metric("Ireland fertility total", format_number(fertility_total_ireland))
    top_row[1].metric("Highest fertility region", fert_top_name, fert_top_value)
    top_row[2].metric("Ireland death total", format_number(death_total_ireland))
    top_row[3].metric("Highest death-rate region", death_top_name, death_top_value)

    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        if not vsa38_f.empty and vsa38_area:
            latest_birth = latest_group(vsa38_f, vsa38_time, vsa38_area)
            st.altair_chart(
                make_bar_chart(
                    latest_birth,
                    vsa38_area,
                    "Latest birth rate by area",
                    top_n=12,
                    format_str=",.2f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Birth-rate area column not detected or no data after filtering.")

    with row1_col2:
        if not vsa104_f.empty and vsa104_region and vsa104_age:
            fertility_heatmap_df = vsa104_f.copy()
            fertility_heatmap_df = remove_all_ages(fertility_heatmap_df, vsa104_age)
            st.altair_chart(
                make_heatmap(
                    fertility_heatmap_df,
                    vsa104_age,
                    vsa104_region,
                    "Fertility heatmap: mother's age group × region",
                    format_str=",.2f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Fertility age or region column not detected.")

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        if not vsa104_f.empty and vsa104_time and vsa104_region:
            top_regions = (
                vsa104_f.groupby(vsa104_region, as_index=False)["value"]
                .sum()
                .sort_values("value", ascending=False)
                .head(5)[vsa104_region]
                .tolist()
            )
            trend_df = vsa104_f[vsa104_f[vsa104_region].isin(top_regions)]
            st.altair_chart(
                make_line_chart(
                    trend_df,
                    vsa104_time,
                    vsa104_region,
                    "Fertility trend for top regions",
                    format_str=",.2f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Fertility time or region column not detected.")

    with row2_col2:
        if not vsa104_f.empty and vsa104_region and vsa104_age:
            fertility_stack_df = vsa104_f.copy()
            fertility_stack_df = remove_all_ages(fertility_stack_df, vsa104_age)
            st.altair_chart(
                make_stacked_bar(
                    fertility_stack_df,
                    vsa104_region,
                    vsa104_age,
                    "Fertility profile by region and mother's age group",
                    top_n=10,
                    format_str=",.2f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Fertility region or age-group column not detected.")


# ============================================================
# Tab 3 - Mortality
# ============================================================
with tab3:
    st.subheader("Death rates, stillbirths, and infant mortality")

    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        if not vsa108_f.empty and vsa108_region:
            latest_death = latest_group(vsa108_f, vsa108_time, vsa108_region)
            st.altair_chart(
                make_bar_chart(
                    latest_death,
                    vsa108_region,
                    "Latest death rate by region",
                    top_n=12,
                    format_str=",.2f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Death-rate region column not detected or no data after filtering.")

    with row1_col2:
        if not vsa94_f.empty and vsa94_area:
            latest_mortality = latest_group(vsa94_f, vsa94_time, vsa94_area)
            st.altair_chart(
                make_bar_chart(
                    latest_mortality,
                    vsa94_area,
                    "Latest stillbirth / infant mortality by area",
                    top_n=12,
                    format_str=",.2f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Infant mortality area column not detected or no data after filtering.")

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        if not vsa108_f.empty and vsa108_time and vsa108_region:
            top_regions = (
                vsa108_f.groupby(vsa108_region, as_index=False)["value"]
                .sum()
                .sort_values("value", ascending=False)
                .head(5)[vsa108_region]
                .tolist()
            )
            trend_df = vsa108_f[vsa108_f[vsa108_region].isin(top_regions)]
            st.altair_chart(
                make_line_chart(
                    trend_df,
                    vsa108_time,
                    vsa108_region,
                    "Death-rate trend for top regions",
                    format_str=",.2f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Death-rate time or region column not detected.")

    with row2_col2:
        if not vsa94_f.empty and vsa94_time and vsa94_area:
            top_areas = (
                vsa94_f.groupby(vsa94_area, as_index=False)["value"]
                .sum()
                .sort_values("value", ascending=False)
                .head(5)[vsa94_area]
                .tolist()
            )
            trend_df = vsa94_f[vsa94_f[vsa94_area].isin(top_areas)]
            st.altair_chart(
                make_line_chart(
                    trend_df,
                    vsa94_time,
                    vsa94_area,
                    "Stillbirth / infant mortality trend for top areas",
                    format_str=",.2f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Infant mortality time or area column not detected.")


# ============================================================
# Tab 4 - Citizenship & Birthplace
# ============================================================
with tab4:
    st.subheader("Citizenship and birthplace profiles outside the EU/EFTA/EU candidate groups")

    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        if not pea27_f.empty and pea27_hdi:
            latest_citizenship = latest_group(pea27_f, pea27_time, pea27_hdi)
            st.altair_chart(
                make_bar_chart(
                    latest_citizenship,
                    pea27_hdi,
                    "Latest citizenship profile by Human Development Index",
                    top_n=12,
                    format_str=",.0f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Citizenship HDI column not detected or no data after filtering.")

    with row1_col2:
        if not pea28_f.empty and pea28_hdi:
            latest_birthplace = latest_group(pea28_f, pea28_time, pea28_hdi)
            st.altair_chart(
                make_bar_chart(
                    latest_birthplace,
                    pea28_hdi,
                    "Latest birthplace profile by Human Development Index",
                    top_n=12,
                    format_str=",.0f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Birthplace HDI column not detected or no data after filtering.")

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        if not pea27_f.empty and pea27_age and pea27_sex:
            citizenship_plot_df = pea27_f.copy()
            citizenship_plot_df = remove_all_ages(citizenship_plot_df, pea27_age)
            citizenship_plot_df = remove_both_sexes(citizenship_plot_df, pea27_sex)

            st.altair_chart(
                make_grouped_bar(
                    citizenship_plot_df,
                    pea27_age,
                    pea27_sex,
                    "Citizenship profile by age group and sex",
                    format_str=",.0f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Citizenship age or sex column not detected.")

    with row2_col2:
        if not pea28_f.empty and pea28_age and pea28_sex:
            birthplace_plot_df = pea28_f.copy()
            birthplace_plot_df = remove_all_ages(birthplace_plot_df, pea28_age)
            birthplace_plot_df = remove_both_sexes(birthplace_plot_df, pea28_sex)

            st.altair_chart(
                make_grouped_bar(
                    birthplace_plot_df,
                    pea28_age,
                    pea28_sex,
                    "Birthplace profile by age group and sex",
                    format_str=",.0f",
                ),
                use_container_width=True,
            )
        else:
            st.info("Birthplace age or sex column not detected.")


# ============================================================
# Data preview
# ============================================================
with st.expander("Preview processed datasets"):
    st.markdown("**PEA26 Population**")
    st.dataframe(pea26_f.head(20), use_container_width=True)

    st.markdown("**PEA29 Old-age dependency**")
    st.dataframe(pea29_f.head(20), use_container_width=True)

    st.markdown("**VSA104 Fertility**")
    st.dataframe(vsa104_f.head(20), use_container_width=True)

    st.markdown("**VSA108 Death rate**")
    st.dataframe(vsa108_f.head(20), use_container_width=True)

    st.markdown("**VSA38 Birth rate**")
    st.dataframe(vsa38_f.head(20), use_container_width=True)

    st.markdown("**VSA94 Infant mortality**")
    st.dataframe(vsa94_f.head(20), use_container_width=True)

    st.markdown("**PEA27 Citizenship**")
    st.dataframe(pea27_f.head(20), use_container_width=True)

    st.markdown("**PEA28 Birthplace**")
    st.dataframe(pea28_f.head(20), use_container_width=True)