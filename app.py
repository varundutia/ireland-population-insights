from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_theme import st_theme

from src.chart_builders import (
    make_bar_chart,
    make_line_chart,
    make_line_with_latest_labels,
    make_population_pyramid,
    make_region_dependency_scatter,
)
from src.data_loader import (
    build_filtered_datasets,
    detect_columns,
    load_csv,
)
from src.geo_utils import (
    add_normalized_region_column,
    build_latest_region_metrics,
    load_geojson,
    make_hero_choropleth,
)
from src.ui_helpers import (
    exclude_ireland,
    format_number,
    get_ireland_total,
    latest_group,
    remove_all_ages,
    remove_both_sexes,
)


# ============================================================
# Page setup
# ============================================================

st.set_page_config(
    page_title="Ireland People & Society Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

theme = st_theme(key="app_theme_detector")
theme_base = (theme or {}).get("base") or st.get_option("theme.base") or "light"

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1280px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .iv-kicker {
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.80rem;
            font-weight: 700;
            opacity: 0.75;
            margin-bottom: 0.35rem;
        }
        .iv-subtitle {
            font-size: 1.08rem;
            line-height: 1.55;
            max-width: 900px;
            margin-bottom: 0.4rem;
        }
        .iv-section-note {
            font-size: 0.95rem;
            opacity: 0.8;
            margin-top: -0.2rem;
            margin-bottom: 1rem;
        }
        .iv-divider {
            margin-top: 1.3rem;
            margin-bottom: 1.3rem;
            border-top: 1px solid rgba(128,128,128,0.18);
        }
        .iv-side-card {
            border: 1px solid rgba(128,128,128,0.18);
            border-radius: 16px;
            padding: 1rem;
            background: rgba(255,255,255,0.02);
        }
        .iv-overview {
            border: 1px solid rgba(128,128,128,0.18);
            border-radius: 16px;
            padding: 1.1rem 1.2rem;
            background: rgba(255,255,255,0.02);
            margin-bottom: 1rem;
        }
        .iv-overview h3 {
            margin: 0 0 0.45rem 0;
            font-size: 1.05rem;
        }
        .iv-overview p {
            margin: 0;
            line-height: 1.6;
            font-size: 0.98rem;
        }
        .iv-insight-card {
            border: 1px solid rgba(128,128,128,0.18);
            border-radius: 14px;
            padding: 0.95rem 1rem;
            background: rgba(255,255,255,0.02);
            height: 100%;
        }
        .iv-insight-label {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            opacity: 0.72;
            margin-bottom: 0.35rem;
            font-weight: 700;
        }
        .iv-insight-value {
            font-size: 1.35rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .iv-insight-text {
            font-size: 0.95rem;
            line-height: 1.55;
            opacity: 0.9;
        }
        .iv-region-header-card {
            border: 1px solid rgba(128,128,128,0.18);
            border-radius: 16px;
            padding: 1rem;
            background: rgba(255,255,255,0.02);
            margin-bottom: 0.85rem;
        }
        .iv-region-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 0.75rem;
        }
        .iv-metric-card {
            border: 1px solid rgba(128,128,128,0.18);
            border-radius: 14px;
            padding: 0.9rem 1rem;
            background: rgba(255,255,255,0.02);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


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
    "geojson": DATA_DIR / "ireland_nuts3.geojson",
}


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
    ireland_geojson = load_geojson(FILES["geojson"])
except Exception as e:
    st.error(str(e))
    st.stop()


# ============================================================
# Detect columns
# ============================================================
datasets = {
    "vsa38": vsa38,
    "vsa94": vsa94,
    "vsa104": vsa104,
    "vsa108": vsa108,
    "pea26": pea26,
    "pea27": pea27,
    "pea28": pea28,
    "pea29": pea29,
}

columns = detect_columns(datasets)

vsa38_time = columns["vsa38_time"]
vsa38_area = columns["vsa38_area"]
vsa94_time = columns["vsa94_time"]
vsa94_area = columns["vsa94_area"]
vsa104_time = columns["vsa104_time"]
vsa104_age = columns["vsa104_age"]
vsa104_region = columns["vsa104_region"]
vsa108_time = columns["vsa108_time"]
vsa108_region = columns["vsa108_region"]
pea26_time = columns["pea26_time"]
pea26_age = columns["pea26_age"]
pea26_sex = columns["pea26_sex"]
pea26_region = columns["pea26_region"]
pea27_time = columns["pea27_time"]
pea27_age = columns["pea27_age"]
pea27_sex = columns["pea27_sex"]
pea27_hdi = columns["pea27_hdi"]
pea28_time = columns["pea28_time"]
pea28_age = columns["pea28_age"]
pea28_sex = columns["pea28_sex"]
pea28_hdi = columns["pea28_hdi"]
pea29_time = columns["pea29_time"]
pea29_sex = columns["pea29_sex"]
pea29_region = columns["pea29_region"]


# ============================================================
# Fixed defaults (no sidebar controls)
# ============================================================
show_data_preview = False

pea26_region_selected: list[str] = []
pea26_sex_selected: list[str] = []
vsa104_region_selected: list[str] = []
vsa104_age_selected: list[str] = []
vsa108_region_selected: list[str] = []
pea29_region_selected: list[str] = []
pea29_sex_selected: list[str] = []
vsa38_area_selected: list[str] = []
vsa94_area_selected: list[str] = []
pea27_sex_selected: list[str] = []
pea27_hdi_selected: list[str] = []
pea28_sex_selected: list[str] = []
pea28_hdi_selected: list[str] = []


# ============================================================
# Apply filters
# ============================================================
filtered = build_filtered_datasets(
    datasets,
    columns,
    {
        "pea26_region_selected": pea26_region_selected,
        "pea26_sex_selected": pea26_sex_selected,
        "vsa104_region_selected": vsa104_region_selected,
        "vsa104_age_selected": vsa104_age_selected,
        "vsa108_region_selected": vsa108_region_selected,
        "pea29_region_selected": pea29_region_selected,
        "pea29_sex_selected": pea29_sex_selected,
        "vsa38_area_selected": vsa38_area_selected,
        "vsa94_area_selected": vsa94_area_selected,
        "pea27_sex_selected": pea27_sex_selected,
        "pea27_hdi_selected": pea27_hdi_selected,
        "pea28_sex_selected": pea28_sex_selected,
        "pea28_hdi_selected": pea28_hdi_selected,
    },
)

pea26_f = add_normalized_region_column(filtered["pea26_f"], pea26_region)
vsa104_f = add_normalized_region_column(filtered["vsa104_f"], vsa104_region)
vsa108_f = add_normalized_region_column(filtered["vsa108_f"], vsa108_region)
pea29_f = add_normalized_region_column(filtered["pea29_f"], pea29_region)
vsa38_f = filtered["vsa38_f"]
vsa94_f = filtered["vsa94_f"]
pea27_f = filtered["pea27_f"]
pea28_f = filtered["pea28_f"]


# ============================================================
# Analysis-ready measures
# ============================================================
def keep_latest_year(df: pd.DataFrame, time_col: str | None) -> pd.DataFrame:
    if not time_col or time_col not in df.columns or df.empty:
        return df.copy()
    years = pd.to_numeric(df[time_col], errors="coerce")
    latest = years.max()
    return df[years == latest].copy()


def keep_label(df: pd.DataFrame, col: str | None, label: str) -> pd.DataFrame:
    if not col or col not in df.columns:
        return df.copy()
    target = label.strip().lower()
    return df[df[col].astype(str).str.strip().str.lower() == target].copy()


def keep_statistic(df: pd.DataFrame, code: str) -> pd.DataFrame:
    if "STATISTIC" not in df.columns:
        return df.copy()
    return df[df["STATISTIC"].astype(str).str.strip() == code].copy()


def top_metric(metric_df: pd.DataFrame, metric_col: str) -> tuple[str, str]:
    if metric_df.empty or metric_col not in metric_df.columns:
        return "—", "—"
    tmp = metric_df.dropna(subset=[metric_col]).sort_values(metric_col, ascending=False)
    if tmp.empty:
        return "—", "—"
    return str(tmp.iloc[0]["region_name"]), format_number(tmp.iloc[0][metric_col])


def low_metric(metric_df: pd.DataFrame, metric_col: str) -> tuple[str, str]:
    if metric_df.empty or metric_col not in metric_df.columns:
        return "—", "—"
    tmp = metric_df.dropna(subset=[metric_col]).sort_values(metric_col, ascending=True)
    if tmp.empty:
        return "—", "—"
    return str(tmp.iloc[0]["region_name"]), format_number(tmp.iloc[0][metric_col])


# Counts and rates are filtered to one meaningful grain before aggregation:
# latest total population, both-sex dependency ratio, total fertility rate, and crude death rate.
pea26_population_measure = keep_label(keep_label(pea26_f, pea26_age, "All ages"), pea26_sex, "Both sexes")
pea29_dependency_measure = keep_label(pea29_f, pea29_sex, "Both sexes")
vsa104_fertility_measure = keep_label(keep_statistic(vsa104_f, "VSA104C01"), vsa104_age, "All ages")
vsa108_death_measure = vsa108_f.copy()


# ============================================================
# National totals before removing Ireland from charts
# ============================================================
population_total_ireland = get_ireland_total(pea26_population_measure, pea26_region, pea26_time)
dependency_total_ireland = get_ireland_total(pea29_dependency_measure, pea29_region, pea29_time)
death_total_ireland = get_ireland_total(vsa108_death_measure, vsa108_region, vsa108_time)
fertility_total_ireland = get_ireland_total(vsa104_fertility_measure, vsa104_region, vsa104_time)


# ============================================================
# Remove Ireland from regional comparison datasets
# ============================================================
pea26_age_structure_f = exclude_ireland(pea26_f, pea26_region)
pea26_f = exclude_ireland(pea26_population_measure, pea26_region)
pea29_f = exclude_ireland(pea29_dependency_measure, pea29_region)
vsa104_f = exclude_ireland(vsa104_fertility_measure, vsa104_region)
vsa108_f = exclude_ireland(vsa108_death_measure, vsa108_region)


# ============================================================
# Build region metrics for maps and selection
# ============================================================
region_metrics = pd.DataFrame()
if all([pea26_region, pea29_region, vsa104_region, vsa108_region]):
    region_metrics = build_latest_region_metrics(
        latest_group(pea26_f, pea26_time, pea26_region),
        latest_group(pea29_f, pea29_time, pea29_region),
        latest_group(vsa104_f, vsa104_time, vsa104_region),
        latest_group(vsa108_f, vsa108_time, vsa108_region),
        pea26_region,
        pea29_region,
        vsa104_region,
        vsa108_region,
    )

if "selected_region" not in st.session_state:
    st.session_state["selected_region"] = None


# ============================================================
# Helpers
# ============================================================
def get_selected_region_row(metric_df: pd.DataFrame) -> pd.Series | None:
    if metric_df.empty:
        return None
    selected_key = st.session_state.get("selected_region")
    if not selected_key:
        return None
    selected_match = metric_df[metric_df["normalized_region"] == selected_key]
    if selected_match.empty:
        return None
    return selected_match.iloc[0]


def render_selected_region_cards(region_row: pd.Series | None) -> None:
    if region_row is None:
        st.markdown(
            """
            <div class="iv-side-card">
                <div class="iv-insight-label">Selected region</div>
                <div class="iv-insight-text">
                    Click a region on the map to see its profile and linked charts. Click outside the selected region to clear it.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    region_name = str(region_row.get("region_name", "Selected region"))
    population = region_row.get("population_value")
    dependency = region_row.get("dependency_value")
    fertility = region_row.get("fertility_value")
    death = region_row.get("death_value")

    st.markdown(
        f"""
        <div class="iv-region-header-card">
            <div class="iv-insight-label">Selected region</div>
            <div class="iv-insight-value" style="font-size: 1.12rem;">{region_name}</div>
            <div class="iv-insight-text">
                The charts in this tab now follow this region where available.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cards = []
    if pd.notna(population):
        cards.append(
            f"""
            <div class="iv-metric-card">
                <div class="iv-insight-label">Population</div>
                <div class="iv-insight-value">{format_number(population)}</div>
            </div>
            """
        )
    if pd.notna(dependency):
        cards.append(
            f"""
            <div class="iv-metric-card">
                <div class="iv-insight-label">Old-age dependency</div>
                <div class="iv-insight-value">{format_number(dependency)}</div>
            </div>
            """
        )
    if pd.notna(fertility):
        cards.append(
            f"""
            <div class="iv-metric-card">
                <div class="iv-insight-label">Fertility</div>
                <div class="iv-insight-value">{format_number(fertility)}</div>
            </div>
            """
        )
    if pd.notna(death):
        cards.append(
            f"""
            <div class="iv-metric-card">
                <div class="iv-insight-label">Death rate</div>
                <div class="iv-insight-value">{format_number(death)}</div>
            </div>
            """
        )

    if cards:
        st.markdown(
            f"""
            <div class="iv-region-grid">
                {''.join(cards)}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_theme_header(metric_df: pd.DataFrame, metric_col: str, metric_label: str, map_title: str):
    tab_map_col, tab_info_col = st.columns([2.1, 1.0], gap="large")
    selected_row = None

    with tab_map_col:
        st.markdown(f"### {map_title}")
        if metric_df.empty:
            st.info("Regional metrics could not be built for this map.")
        else:
            theme_fig = make_hero_choropleth(
                metric_df,
                ireland_geojson,
                metric_col,
                metric_label,
                theme_base=theme_base,
            )
            theme_fig.update_layout(dragmode=False)
            theme_fig.update_geos(fitbounds="locations")
            theme_fig.update_xaxes(fixedrange=True)
            theme_fig.update_yaxes(fixedrange=True)

            selection = st.plotly_chart(
                theme_fig,
                width="stretch",
                on_select="rerun",
                selection_mode="points",
                key=f"map_{metric_label.lower().replace(' ', '_')}",
                config={
                    "displayModeBar": False,
                    "scrollZoom": False,
                    "doubleClick": False,
                    "doubleClickDelay": 1000,
                    "showTips": False,
                    "staticPlot": False,
                    "editable": False,
                    "modeBarButtonsToRemove": [
                        "zoom2d",
                        "pan2d",
                        "select2d",
                        "lasso2d",
                        "zoomIn2d",
                        "zoomOut2d",
                        "autoScale2d",
                        "resetScale2d",
                        "toImage",
                    ],
                },
            )

            points = (selection or {}).get("selection", {}).get("points", [])
            if points:
                clicked_region = points[0].get("location")
                if clicked_region:
                    st.session_state["selected_region"] = clicked_region
            else:
                st.session_state["selected_region"] = None

    with tab_info_col:
        st.markdown("### Selected region")
        selected_row = get_selected_region_row(metric_df)
        render_selected_region_cards(selected_row)

    return selected_row


# ============================================================
# App header
# ============================================================
st.markdown('<div class="iv-kicker">Ireland demographic overview</div>', unsafe_allow_html=True)
st.title("Regional demographic pressure in Ireland")
st.markdown(
    '<div class="iv-subtitle">Explore how Ireland\'s regions differ in population, ageing, fertility, and mortality through four focused thematic views.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="iv-section-note">Each tab starts with its own map and then explains that theme with supporting charts.</div>',
    unsafe_allow_html=True,
)


# ============================================================
# KPI row
# ============================================================
pop_top_name, pop_top_value = top_metric(region_metrics, "population_value")
dep_top_name, dep_top_value = top_metric(region_metrics, "dependency_value")
dep_low_name, dep_low_value = low_metric(region_metrics, "dependency_value")

st.markdown('<div class="iv-divider"></div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ireland population, 2024", format_number(population_total_ireland))
c2.metric("Ireland old-age dependency, 2024", format_number(dependency_total_ireland))
c3.metric("Largest region, 2024", pop_top_name, pop_top_value)
c4.metric("Highest ageing pressure, 2024", dep_top_name, dep_top_value)


# ============================================================
# Project overview
# ============================================================
st.markdown('<div class="iv-divider"></div>', unsafe_allow_html=True)
st.subheader("What this project is about")
st.markdown(
    """
    <div class="iv-overview">
        <p>
            This project explains how Ireland's regions differ demographically. It brings together population size,
            age structure, old-age dependency, fertility, and death-rate patterns so the viewer can compare regions,
            inspect individual regions, and understand where demographic pressure is strongest.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not region_metrics.empty:
    fert_top_name, fert_top_value = top_metric(region_metrics, "fertility_value")
    death_top_name, death_top_value = top_metric(region_metrics, "death_value")
    st.markdown("#### What to notice")
    i1, i2, i3 = st.columns(3)
    i1.markdown(
        f"""
        <div class="iv-insight-card">
            <div class="iv-insight-label">Size is not pressure</div>
            <div class="iv-insight-value">{pop_top_name}</div>
            <div class="iv-insight-text">
                The largest population region is also the lowest old-age dependency region ({dep_low_value}), so population size should not be read as ageing pressure.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    i2.markdown(
        f"""
        <div class="iv-insight-card">
            <div class="iv-insight-label">Ageing concentration</div>
            <div class="iv-insight-value">{dep_top_name}</div>
            <div class="iv-insight-text">
                The highest old-age dependency ratio is {dep_top_value}, which marks the region where the working-age support burden is greatest.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    i3.markdown(
        f"""
        <div class="iv-insight-card">
            <div class="iv-insight-label">Vital-rate contrast</div>
            <div class="iv-insight-value">{fert_top_name} / {death_top_name}</div>
            <div class="iv-insight-text">
                Fertility and crude death-rate leaders differ, so the dashboard separates birth dynamics from mortality instead of collapsing them into one demographic score.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Four thematic tabs with dedicated maps
# ============================================================
st.markdown('<div class="iv-divider"></div>', unsafe_allow_html=True)
st.subheader("Explore the story in four themes")
st.caption(
    "Each tab starts with its own thematic map and insight panel, followed by supporting charts for that topic."
)

population_tab, ageing_tab, fertility_tab, death_tab = st.tabs(
    [
        "Population",
        "Ageing",
        "Fertility",
        "Mortality",
    ]
)


with population_tab:
    population_selected_row = render_theme_header(
        region_metrics,
        "population_value",
        "Population",
        "Which regions are bigger or smaller?",
    )
    st.caption("Compare the relative size of regions and see whether larger population automatically aligns with higher demographic pressure.")
    pop_left, pop_right = st.columns(2)

    with pop_left:
        if not region_metrics.empty and {"region_name", "population_value"}.issubset(region_metrics.columns):
            population_rank_df = (
                region_metrics[["region_name", "population_value"]]
                .dropna()
                .rename(columns={"region_name": "Region", "population_value": "value"})
            )
            st.altair_chart(
                make_bar_chart(
                    population_rank_df,
                    "Region",
                    "Regional population ranking, 2024",
                    top_n=12,
                    format_str=",.0f",
                    value_title="Population",
                    theme_base=theme_base,
                ),
                width="stretch",
            )
        else:
            st.info("Population ranking could not be displayed.")

    with pop_right:
        if not pea26_f.empty and not pea29_f.empty and pea26_region and pea29_region and pea26_region == pea29_region:
            st.altair_chart(
                make_region_dependency_scatter(
                    pea26_f,
                    pea29_f,
                    pea26_region,
                    "Population size vs ageing pressure",
                    theme_base=theme_base,
                ),
                width="stretch",
            )
        else:
            st.info("Population comparison scatter could not be displayed.")


with ageing_tab:
    ageing_selected_row = render_theme_header(
        region_metrics,
        "dependency_value",
        "Old-age dependency",
        "Which regions are younger or older?",
    )
    ageing_selected_name = ageing_selected_row.get("region_name") if ageing_selected_row is not None else None
    ageing_selected_normalized = st.session_state.get("selected_region")
    st.caption("Use dependency ratio and age structure to understand which regions are ageing more and what that looks like underneath the summary numbers.")
    age_left, age_right = st.columns(2)

    with age_left:
        if not region_metrics.empty and {"region_name", "dependency_value"}.issubset(region_metrics.columns):
            dependency_rank_df = (
                region_metrics[["region_name", "dependency_value"]]
                .dropna()
                .rename(columns={"region_name": "Region", "dependency_value": "value"})
            )
            st.altair_chart(
                make_bar_chart(
                    dependency_rank_df,
                    "Region",
                    "Old-age dependency ranking, 2024",
                    top_n=12,
                    format_str=",.2f",
                    value_title="Old-age dependency ratio",
                    theme_base=theme_base,
                ),
                width="stretch",
            )
        else:
            st.info("Ageing ranking could not be displayed.")

    with age_right:
        if not pea29_f.empty and pea29_time and pea29_region:
            dependency_trend_df = pea29_f.copy()
            if ageing_selected_normalized:
                dependency_trend_df = dependency_trend_df[
                    dependency_trend_df["normalized_region"] == ageing_selected_normalized
                ]
                title = (
                    f"Old-age dependency trend: {ageing_selected_name}"
                    if ageing_selected_name
                    else "Old-age dependency trend"
                )
                if not dependency_trend_df.empty:
                    st.altair_chart(
                        make_line_chart(
                            dependency_trend_df,
                            pea29_time,
                            pea29_region,
                            title,
                            format_str=",.2f",
                            y_title="Old-age dependency ratio",
                            theme_base=theme_base,
                        ),
                        width="stretch",
                    )
                else:
                    st.info("Click a region on the map to view a linked ageing trend.")
            else:
                st.altair_chart(
                    make_line_with_latest_labels(
                        pea29_f,
                        pea29_time,
                        pea29_region,
                        "Old-age dependency trend with latest region labels",
                        format_str=",.2f",
                        top_n=5,
                        y_title="Old-age dependency ratio",
                        theme_base=theme_base,
                    ),
                    width="stretch",
                )
        else:
            st.info("Ageing trend could not be displayed.")

    st.markdown("#### Age structure detail")
    if not pea26_age_structure_f.empty and pea26_age and pea26_sex:
        pyramid_df = keep_latest_year(pea26_age_structure_f, pea26_time)
        pyramid_df = remove_all_ages(pyramid_df, pea26_age)
        pyramid_df = remove_both_sexes(pyramid_df, pea26_sex)
        if ageing_selected_normalized:
            pyramid_df = pyramid_df[pyramid_df["normalized_region"] == ageing_selected_normalized]
        if pyramid_df.empty:
            st.info("Click a region on the map to inspect the age structure.")
        else:
            pyramid_title = (
                f"Population pyramid: {ageing_selected_name}"
                if ageing_selected_name
                else "Population pyramid, 2024"
            )
            st.altair_chart(
                make_population_pyramid(
                    pyramid_df,
                    pea26_age,
                    pea26_sex,
                    pyramid_title,
                    theme_base=theme_base,
                ),
                width="stretch",
            )
    else:
        st.info("Population pyramid could not be displayed.")


with fertility_tab:
    fertility_selected_row = render_theme_header(
        region_metrics,
        "fertility_value",
        "Fertility",
        "Which regions have stronger or weaker fertility?",
    )
    fertility_selected_name = fertility_selected_row.get("region_name") if fertility_selected_row is not None else None
    fertility_selected_normalized = st.session_state.get("selected_region")
    st.caption("Compare the latest fertility levels across regions and then inspect how fertility changes over time for the selected region or leading regions.")
    fert_left, fert_right = st.columns(2)

    with fert_left:
        if not region_metrics.empty and {"region_name", "fertility_value"}.issubset(region_metrics.columns):
            fertility_rank_df = (
                region_metrics[["region_name", "fertility_value"]]
                .dropna()
                .rename(columns={"region_name": "Region", "fertility_value": "value"})
            )
            st.altair_chart(
                make_bar_chart(
                    fertility_rank_df,
                    "Region",
                    "Total fertility rate ranking by region, 2023",
                    top_n=12,
                    format_str=",.2f",
                    value_title="Total fertility rate",
                    theme_base=theme_base,
                ),
                width="stretch",
            )
        else:
            st.info("Fertility ranking could not be displayed.")

    with fert_right:
        if not vsa104_f.empty and vsa104_time and vsa104_region:
            fertility_trend_df = vsa104_f.copy()
            if fertility_selected_normalized:
                fertility_trend_df = fertility_trend_df[
                    fertility_trend_df["normalized_region"] == fertility_selected_normalized
                ]
                title = (
                    f"Fertility trend: {fertility_selected_name}"
                    if fertility_selected_name
                    else "Fertility trend"
                )
                if not fertility_trend_df.empty:
                    st.altair_chart(
                        make_line_chart(
                            fertility_trend_df,
                            vsa104_time,
                            vsa104_region,
                            title,
                            format_str=",.2f",
                            y_title="Total fertility rate",
                            theme_base=theme_base,
                        ),
                        width="stretch",
                    )
                else:
                    st.info("Click a region on the map to view a linked fertility trend.")
            else:
                st.altair_chart(
                    make_line_with_latest_labels(
                        vsa104_f,
                        vsa104_time,
                        vsa104_region,
                        "Fertility trend with latest region labels",
                        format_str=",.2f",
                        top_n=5,
                        y_title="Total fertility rate",
                        theme_base=theme_base,
                    ),
                    width="stretch",
                )
        else:
            st.info("Fertility trend could not be displayed.")


with death_tab:
    death_selected_row = render_theme_header(
        region_metrics,
        "death_value",
        "Death rate",
        "Which regions have higher or lower death rates?",
    )
    death_selected_name = death_selected_row.get("region_name") if death_selected_row is not None else None
    death_selected_normalized = st.session_state.get("selected_region")
    st.caption("Compare the latest regional death-rate levels and inspect how the pattern changes through time for the selected region or leading regions.")
    death_left, death_right = st.columns(2)

    with death_left:
        if not region_metrics.empty and {"region_name", "death_value"}.issubset(region_metrics.columns):
            death_rank_df = (
                region_metrics[["region_name", "death_value"]]
                .dropna()
                .rename(columns={"region_name": "Region", "death_value": "value"})
            )
            st.altair_chart(
                make_bar_chart(
                    death_rank_df,
                    "Region",
                    "Crude death-rate ranking by region, 2023",
                    top_n=12,
                    format_str=",.2f",
                    value_title="Crude death rate",
                    theme_base=theme_base,
                ),
                width="stretch",
            )
        else:
            st.info("Death-rate ranking could not be displayed.")

    with death_right:
        if not vsa108_f.empty and vsa108_time and vsa108_region:
            death_trend_df = vsa108_f.copy()
            if death_selected_normalized:
                death_trend_df = death_trend_df[
                    death_trend_df["normalized_region"] == death_selected_normalized
                ]
                title = (
                    f"Death-rate trend: {death_selected_name}"
                    if death_selected_name
                    else "Death-rate trend"
                )
                if not death_trend_df.empty:
                    st.altair_chart(
                        make_line_chart(
                            death_trend_df,
                            vsa108_time,
                            vsa108_region,
                            title,
                            format_str=",.2f",
                            y_title="Crude death rate",
                            theme_base=theme_base,
                        ),
                        width="stretch",
                    )
                else:
                    st.info("Click a region on the map to view a linked death-rate trend.")
            else:
                st.altair_chart(
                    make_line_with_latest_labels(
                        vsa108_f,
                        vsa108_time,
                        vsa108_region,
                        "Death-rate trend with latest region labels",
                        format_str=",.2f",
                        top_n=5,
                        y_title="Crude death rate",
                        theme_base=theme_base,
                    ),
                    width="stretch",
                )
        else:
            st.info("Death-rate trend could not be displayed.")


# ============================================================
# Data preview
# ============================================================
if show_data_preview:
    with st.expander("Preview processed datasets"):
        st.markdown("**Regional metrics for the map**")
        st.dataframe(region_metrics.head(20), width="stretch")

        st.markdown("**PEA26 Population**")
        st.dataframe(pea26_f.head(20), width="stretch")

        st.markdown("**PEA29 Old-age dependency**")
        st.dataframe(pea29_f.head(20), width="stretch")

        st.markdown("**VSA104 Fertility**")
        st.dataframe(vsa104_f.head(20), width="stretch")

        st.markdown("**VSA108 Death rate**")
        st.dataframe(vsa108_f.head(20), width="stretch")
