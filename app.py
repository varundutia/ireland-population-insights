from __future__ import annotations
from pathlib import Path
import streamlit as st

import pandas as pd

from src.chart_builders import (
    make_line_chart,
    make_line_with_latest_labels,
    make_lollipop_chart,
    make_population_pyramid,
    make_region_dependency_scatter,
)
from src.data_loader import (
    build_filtered_datasets,
    detect_columns,
    load_csv,
    multiselect_filter,
)
from src.geo_utils import (
    make_hero_choropleth,
    add_normalized_region_column,
    build_latest_region_metrics,
    create_region_insight_text,
    load_geojson,
)
from src.ui_helpers import (
    exclude_ireland,
    format_number,
    get_ireland_total,
    latest_group,
    remove_all_ages,
    remove_both_sexes,
    top_group,
)


# ============================================================
# Page setup
# ============================================================
st.set_page_config(
    page_title="Ireland People & Society Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
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
# Sidebar filters
# ============================================================
st.sidebar.title("Controls")

hero_metric_label = st.sidebar.selectbox(
    "Hero map metric",
    [
        "Old-age dependency",
        "Population",
        "Fertility",
        "Death rate",
    ],
    index=0,
)

region_focus_mode = st.sidebar.radio(
    "Supporting charts",
    ["Clicked region", "Top 5 regions"],
    index=0,
)

show_data_preview = st.sidebar.checkbox("Show data preview", value=False)


# ============================================================
# Apply filters
# ============================================================
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
# Build region metrics for hero map and selection
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

metric_column_map = {
    "Old-age dependency": "dependency_value",
    "Population": "population_value",
    "Fertility": "fertility_value",
    "Death rate": "death_value",
}
hero_metric_column = metric_column_map[hero_metric_label]

if "selected_region" not in st.session_state:
    st.session_state["selected_region"] = None


# ============================================================
# App header
# ============================================================
st.title("Regional Demographic Pressure in Ireland")
st.caption(
    "A one-page explanatory view of population, ageing, fertility, and mortality across Irish regions. Use the hero map to select a region and read the linked insights below."
)


# ============================================================
# KPI row
# ============================================================
pop_top_name, pop_top_value = top_group(pea26_f, pea26_region)
dep_top_name, dep_top_value = top_group(pea29_f, pea29_region)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ireland total population", format_number(population_total_ireland))
c2.metric("Ireland old-age dependency", format_number(dependency_total_ireland))
c3.metric("Largest population region", pop_top_name, pop_top_value)
c4.metric("Highest dependency region", dep_top_name, dep_top_value)


# ============================================================
# Hero section
# ============================================================
hero_left, hero_right = st.columns([2.1, 1.0])

selected_region_row = None

with hero_left:
    st.subheader("Hero view: Ireland regional map")
    if region_metrics.empty:
        st.info("Regional metrics could not be built for the hero map.")
    else:
        hero_fig = make_hero_choropleth(
            region_metrics,
            ireland_geojson,
            hero_metric_column,
            hero_metric_label,
        )
        selection = st.plotly_chart(
            hero_fig,
            width="stretch",
            on_select="rerun",
            selection_mode="points",
        )

        if selection and selection.get("selection", {}).get("points"):
            point = selection["selection"]["points"][0]
            clicked_region = point.get("location")
            if clicked_region:
                st.session_state["selected_region"] = clicked_region

with hero_right:
    st.subheader("Selected region insights")
    if not region_metrics.empty and st.session_state.get("selected_region"):
        selected_match = region_metrics[
            region_metrics["normalized_region"] == st.session_state["selected_region"]
        ]
        if not selected_match.empty:
            selected_region_row = selected_match.iloc[0]
    st.markdown(create_region_insight_text(selected_region_row))


# ============================================================
# Supporting charts
# ============================================================
st.subheader("Supporting views")

support_left, support_right = st.columns(2)

with support_left:
    if not pea26_f.empty and not pea29_f.empty and pea26_region and pea29_region and pea26_region == pea29_region:
        st.altair_chart(
            make_region_dependency_scatter(
                pea26_f,
                pea29_f,
                pea26_region,
                "Population vs old-age dependency by region",
            ),
            width="stretch",
        )
    else:
        st.info("Population and dependency scatter could not be displayed.")

with support_right:
    if not pea29_f.empty and pea29_region:
        latest_dep = latest_group(pea29_f, pea29_time, pea29_region)
        st.altair_chart(
            make_lollipop_chart(
                latest_dep,
                pea29_region,
                "Ranked old-age dependency by region",
                top_n=12,
                format_str=",.2f",
            ),
            width="stretch",
        )
    else:
        st.info("Dependency ranking could not be displayed.")


trend_left, trend_right = st.columns(2)

selected_region_name = None
selected_region_normalized = st.session_state.get("selected_region")
if selected_region_row is not None:
    selected_region_name = selected_region_row.get("region_name")

with trend_left:
    if not vsa104_f.empty and vsa104_time and vsa104_region:
        fertility_trend_df = vsa104_f.copy()
        if region_focus_mode == "Clicked region" and selected_region_normalized:
            fertility_trend_df = fertility_trend_df[
                fertility_trend_df["normalized_region"] == selected_region_normalized
            ]
            title = f"Fertility trend: {selected_region_name}" if selected_region_name else "Fertility trend"
            if not fertility_trend_df.empty:
                st.altair_chart(
                    make_line_chart(
                        fertility_trend_df,
                        vsa104_time,
                        vsa104_region,
                        title,
                        format_str=",.2f",
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
                ),
                width="stretch",
            )
    else:
        st.info("Fertility trend could not be displayed.")

with trend_right:
    if not vsa108_f.empty and vsa108_time and vsa108_region:
        death_trend_df = vsa108_f.copy()
        if region_focus_mode == "Clicked region" and selected_region_normalized:
            death_trend_df = death_trend_df[
                death_trend_df["normalized_region"] == selected_region_normalized
            ]
            title = f"Death-rate trend: {selected_region_name}" if selected_region_name else "Death-rate trend"
            if not death_trend_df.empty:
                st.altair_chart(
                    make_line_chart(
                        death_trend_df,
                        vsa108_time,
                        vsa108_region,
                        title,
                        format_str=",.2f",
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
                ),
                width="stretch",
            )
    else:
        st.info("Death-rate trend could not be displayed.")


# ============================================================
# Optional detail view
# ============================================================
st.subheader("Age structure detail")
if not pea26_f.empty and pea26_age and pea26_sex:
    pyramid_df = pea26_f.copy()
    pyramid_df = remove_all_ages(pyramid_df, pea26_age)
    pyramid_df = remove_both_sexes(pyramid_df, pea26_sex)

    if selected_region_normalized:
        pyramid_df = pyramid_df[pyramid_df["normalized_region"] == selected_region_normalized]

    if pyramid_df.empty:
        st.info("Click a region on the map to inspect the age structure.")
    else:
        pyramid_title = f"Population pyramid: {selected_region_name}" if selected_region_name else "Population pyramid"
        st.altair_chart(
            make_population_pyramid(
                pyramid_df,
                pea26_age,
                pea26_sex,
                pyramid_title,
            ),
            width="stretch",
        )
else:
    st.info("Population pyramid could not be displayed.")


# ============================================================
# Data preview
# ============================================================
if show_data_preview:
    with st.expander("Preview processed datasets"):
        st.markdown("**Regional metrics for the map**")
        st.dataframe(region_metrics.head(20), use_container_width=True)

        st.markdown("**PEA26 Population**")
        st.dataframe(pea26_f.head(20), use_container_width=True)

        st.markdown("**PEA29 Old-age dependency**")
        st.dataframe(pea29_f.head(20), use_container_width=True)

        st.markdown("**VSA104 Fertility**")
        st.dataframe(vsa104_f.head(20), use_container_width=True)

        st.markdown("**VSA108 Death rate**")
        st.dataframe(vsa108_f.head(20), use_container_width=True)