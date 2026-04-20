from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.ui_helpers import sort_age_groups

LIGHT_CATEGORY_COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
]
DARK_CATEGORY_COLORS = [
    "#6baed6",
    "#fdae6b",
    "#74c476",
    "#fb6a4a",
    "#bcbddc",
    "#c49c94",
]


def get_theme_tokens() -> dict[str, object]:
    base = st.get_option("theme.base") or "light"
    is_dark = str(base).lower() == "dark"

    if is_dark:
        return {
            "text": "#F3F4F6",
            "grid": "#374151",
            "border": "#4B5563",
            "background": "rgba(0,0,0,0)",
            "single": "#6baed6",
            "categories": DARK_CATEGORY_COLORS,
            "sequential": ["#3f001f", "#6a014d", "#8c1d6f", "#c51b8a", "#f768a1", "#fde0dd"],
        }

    return {
        "text": "#333333",
        "grid": "#f0f0f0",
        "border": "#E5E7EB",
        "background": "rgba(0,0,0,0)",
        "single": "#1f77b4",
        "categories": LIGHT_CATEGORY_COLORS,
        "sequential": ["#FFF7F3", "#FDE0DD", "#FCC5C0", "#FA9FB5", "#C51B8A", "#7A0177"],
    }


def apply_common_axis_style(chart: alt.Chart) -> alt.Chart:
    tokens = get_theme_tokens()
    return chart.configure_axis(
        labelColor=tokens["text"],
        titleColor=tokens["text"],
        gridColor=tokens["grid"],
        domainColor=tokens["border"],
        tickColor=tokens["border"],
    ).configure_view(
        stroke=None,
        fill=tokens["background"],
    ).configure_title(
        color=tokens["text"],
        anchor="start",
        fontSize=16,
    ).configure_legend(
        labelColor=tokens["text"],
        titleColor=tokens["text"],
    )


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
    tokens = get_theme_tokens()

    chart = (
        alt.Chart(plot_df)
        .mark_bar(color=tokens["single"])
        .encode(
            x=alt.X("value:Q", title="Value"),
            y=alt.Y(f"{category_col}:N", sort="-x", title=""),
            tooltip=[
                alt.Tooltip(f"{category_col}:N", title=category_col),
                alt.Tooltip("value:Q", title="Value", format=format_str),
            ],
        )
        .properties(height=380, title=title)
    )
    return apply_common_axis_style(chart)


def make_lollipop_chart(
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

    base = alt.Chart(plot_df).encode(
        y=alt.Y(f"{category_col}:N", sort="-x", title=""),
        x=alt.X("value:Q", title="Value"),
        tooltip=[
            alt.Tooltip(f"{category_col}:N", title=category_col),
            alt.Tooltip("value:Q", title="Value", format=format_str),
        ],
    )
    tokens = get_theme_tokens()

    rule = base.mark_rule(color=tokens["border"])
    point = base.mark_circle(size=90, color=tokens["single"])
    return apply_common_axis_style((rule + point).properties(height=380, title=title))


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
    tokens = get_theme_tokens()

    chart = (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X("value:Q", title="Value"),
            y=alt.Y(
                f"{category_col}:N",
                sort=None if "age" in category_col.lower() else top_categories,
                title="",
            ),
            color=alt.Color(f"{stack_col}:N", title=stack_col, scale=alt.Scale(range=tokens["categories"])),
            tooltip=[
                alt.Tooltip(f"{category_col}:N", title=category_col),
                alt.Tooltip(f"{stack_col}:N", title=stack_col),
                alt.Tooltip("value:Q", title="Value", format=format_str),
            ],
        )
        .properties(height=380, title=title)
    )
    return apply_common_axis_style(chart)


def make_normalized_stacked_bar(
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
    tokens = get_theme_tokens()

    chart = (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X("value:Q", stack="normalize", title="Share"),
            y=alt.Y(
                f"{category_col}:N",
                sort=None if "age" in category_col.lower() else top_categories,
                title="",
            ),
            color=alt.Color(f"{stack_col}:N", title=stack_col, scale=alt.Scale(range=tokens["categories"])),
            tooltip=[
                alt.Tooltip(f"{category_col}:N", title=category_col),
                alt.Tooltip(f"{stack_col}:N", title=stack_col),
                alt.Tooltip("value:Q", title="Value", format=format_str),
            ],
        )
        .properties(height=380, title=title)
    )
    return apply_common_axis_style(chart)


def make_heatmap(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    format_str: str = ",.2f",
) -> alt.Chart:
    if df.empty:
        empty_df = pd.DataFrame({x_col: [], y_col: [], "value": []})
        return apply_common_axis_style(
            alt.Chart(empty_df).mark_rect().properties(height=420, title=title)
        )
    tokens = get_theme_tokens()

    grouped = df.groupby([x_col, y_col], as_index=False)["value"].sum()

    if "age" in x_col.lower():
        grouped = sort_age_groups(grouped, x_col)

    chart = (
        alt.Chart(grouped)
        .mark_rect()
        .encode(
            x=alt.X(f"{x_col}:N", title=x_col, sort=None),
            y=alt.Y(f"{y_col}:N", title=y_col),
            color=alt.Color(
                "value:Q",
                title="Value",
                scale=alt.Scale(range=tokens["sequential"]),
            ),
            tooltip=[
                alt.Tooltip(f"{x_col}:N", title=x_col),
                alt.Tooltip(f"{y_col}:N", title=y_col),
                alt.Tooltip("value:Q", title="Value", format=format_str),
            ],
        )
        .properties(height=420, title=title)
    )
    return apply_common_axis_style(chart)


def make_line_chart(
    df: pd.DataFrame,
    time_col: str,
    group_col: str,
    title: str,
    format_str: str = ",.2f",
) -> alt.Chart:
    grouped = df.groupby([time_col, group_col], as_index=False)["value"].sum()
    tokens = get_theme_tokens()

    chart = (
        alt.Chart(grouped)
        .mark_line(point=True)
        .encode(
            x=alt.X(f"{time_col}:N", title=time_col),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color(f"{group_col}:N", title=group_col, scale=alt.Scale(range=tokens["categories"])),
            tooltip=[
                alt.Tooltip(f"{time_col}:N", title=time_col),
                alt.Tooltip(f"{group_col}:N", title=group_col),
                alt.Tooltip("value:Q", title="Value", format=format_str),
            ],
        )
        .properties(height=380, title=title)
    )
    return apply_common_axis_style(chart)


def make_line_with_latest_labels(
    df: pd.DataFrame,
    time_col: str,
    group_col: str,
    title: str,
    format_str: str = ",.2f",
    top_n: int = 5,
) -> alt.Chart:
    grouped = df.groupby([time_col, group_col], as_index=False)["value"].sum()
    top_groups = (
        grouped.groupby(group_col, as_index=False)["value"]
        .sum()
        .sort_values("value", ascending=False)
        .head(top_n)[group_col]
        .tolist()
    )
    grouped = grouped[grouped[group_col].isin(top_groups)].copy()
    grouped[time_col] = grouped[time_col].astype(str)

    line = (
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
    )

    latest_time = sorted(grouped[time_col].unique().tolist())[-1]
    latest = grouped[grouped[time_col] == latest_time]

    text = (
        alt.Chart(latest)
        .mark_text(align="left", dx=6)
        .encode(
            x=alt.X(f"{time_col}:N"),
            y=alt.Y("value:Q"),
            text=alt.Text(f"{group_col}:N"),
            color=alt.Color(f"{group_col}:N", legend=None),
        )
    )

    return apply_common_axis_style((line + text).properties(height=380, title=title))


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
    tokens = get_theme_tokens()

    chart = (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X(f"{x_col}:N", title=x_col, sort=None),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color(f"{color_col}:N", title=color_col, scale=alt.Scale(range=tokens["categories"])),
            tooltip=[
                alt.Tooltip(f"{x_col}:N", title=x_col),
                alt.Tooltip(f"{color_col}:N", title=color_col),
                alt.Tooltip("value:Q", title="Value", format=format_str),
            ],
        )
        .properties(height=380, title=title)
    )
    return apply_common_axis_style(chart)


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
        tokens = get_theme_tokens()
        chart = (
            alt.Chart(grouped)
            .mark_bar()
            .encode(
                x=alt.X("value:Q", title="Population"),
                y=alt.Y(f"{age_col}:N", sort=None, title=age_col),
                color=alt.Color(f"{sex_col}:N", title=sex_col, scale=alt.Scale(range=tokens["categories"])),
                tooltip=[
                    alt.Tooltip(f"{age_col}:N", title=age_col),
                    alt.Tooltip(f"{sex_col}:N", title=sex_col),
                    alt.Tooltip("value:Q", title="Population", format=",.0f"),
                ],
            )
            .properties(height=500, title=title)
        )
        return apply_common_axis_style(chart)

    first_sex = sex_values[0]
    grouped["pyramid_value"] = grouped["value"]
    grouped.loc[grouped[sex_col].astype(str) == first_sex, "pyramid_value"] *= -1
    tokens = get_theme_tokens()

    chart = (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X("pyramid_value:Q", title="Population"),
            y=alt.Y(f"{age_col}:N", sort=None, title=age_col),
            color=alt.Color(f"{sex_col}:N", title=sex_col, scale=alt.Scale(range=tokens["categories"])),
            tooltip=[
                alt.Tooltip(f"{age_col}:N", title=age_col),
                alt.Tooltip(f"{sex_col}:N", title=sex_col),
                alt.Tooltip("value:Q", title="Population", format=",.0f"),
            ],
        )
        .properties(height=500, title=title)
    )
    return apply_common_axis_style(chart)


def make_diverging_age_sex_chart(
    df: pd.DataFrame,
    age_col: str,
    sex_col: str,
    title: str,
    format_str: str = ",.0f",
) -> alt.Chart:
    grouped = df.groupby([age_col, sex_col], as_index=False)["value"].sum()
    grouped = sort_age_groups(grouped, age_col)

    sex_values = grouped[sex_col].astype(str).unique().tolist()
    if len(sex_values) >= 2:
        first_sex = sex_values[0]
        grouped["diverging_value"] = grouped["value"]
        grouped.loc[grouped[sex_col].astype(str) == first_sex, "diverging_value"] *= -1
    else:
        grouped["diverging_value"] = grouped["value"]
    tokens = get_theme_tokens()

    chart = (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X("diverging_value:Q", title="Population / count"),
            y=alt.Y(f"{age_col}:N", sort=None, title=age_col),
            color=alt.Color(f"{sex_col}:N", title=sex_col, scale=alt.Scale(range=tokens["categories"])),
            tooltip=[
                alt.Tooltip(f"{age_col}:N", title=age_col),
                alt.Tooltip(f"{sex_col}:N", title=sex_col),
                alt.Tooltip("value:Q", title="Value", format=format_str),
            ],
        )
        .properties(height=420, title=title)
    )
    return apply_common_axis_style(chart)


def make_region_dependency_scatter(
    population_df: pd.DataFrame,
    dependency_df: pd.DataFrame,
    region_col: str,
    title: str,
) -> alt.Chart:
    pop = population_df.groupby(region_col, as_index=False)["value"].sum().rename(columns={"value": "population_value"})
    dep = dependency_df.groupby(region_col, as_index=False)["value"].sum().rename(columns={"value": "dependency_value"})
    merged = pop.merge(dep, on=region_col, how="inner")
    tokens = get_theme_tokens()

    chart = (
        alt.Chart(merged)
        .mark_circle(size=180, opacity=0.8)
        .encode(
            x=alt.X("population_value:Q", title="Population"),
            y=alt.Y("dependency_value:Q", title="Old-age dependency ratio"),
            color=alt.Color(
                "dependency_value:Q",
                title="Dependency ratio",
                scale=alt.Scale(range=tokens["sequential"]),
            ),
            tooltip=[
                alt.Tooltip(f"{region_col}:N", title="Region"),
                alt.Tooltip("population_value:Q", title="Population", format=",.0f"),
                alt.Tooltip("dependency_value:Q", title="Dependency ratio", format=",.2f"),
            ],
        )
        .properties(height=380, title=title)
    )
    return apply_common_axis_style(chart)