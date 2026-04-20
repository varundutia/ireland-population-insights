from __future__ import annotations

import itertools
import json
import re
import ssl
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================
# Configuration
# ============================================================
OUTPUT_DIR = Path("data_processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "vsa38_birth_rate": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/VSA38/JSON-stat/2.0/en",
    "vsa94_infant_mortality": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/VSA94/JSON-stat/2.0/en",
    "vsa104_fertility": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/VSA104/JSON-stat/2.0/en",
    "vsa108_death_rate": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/VSA108/JSON-stat/2.0/en",
    "pea26_population": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/PEA26/JSON-stat/2.0/en",
    "pea27_citizenship_non_eu": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/PEA27/JSON-stat/2.0/en",
    "pea28_birthplace_non_eu": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/PEA28/JSON-stat/2.0/en",
    "pea29_old_age_dependency": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/PEA29/JSON-stat/2.0/en",
    "eu_nuts3_geojson": "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson",
}


# ============================================================
# Fetch helpers
# ============================================================
def fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        msg = str(exc)
        if "CERTIFICATE_VERIFY_FAILED" not in msg and "certificate verify failed" not in msg:
            raise

        print("SSL verification failed. Retrying with unverified SSL context...")
        unverified_context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=60, context=unverified_context) as response:
            return json.loads(response.read().decode("utf-8"))


# ============================================================
# GeoJSON helpers
# ============================================================
def fetch_geojson(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        msg = str(exc)
        if "CERTIFICATE_VERIFY_FAILED" not in msg and "certificate verify failed" not in msg:
            raise

        print("SSL verification failed for GeoJSON download. Retrying with unverified SSL context...")
        unverified_context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=60, context=unverified_context) as response:
            return json.loads(response.read().decode("utf-8"))


# ============================================================
# JSON-stat helpers
# ============================================================
def safe_slug(text: str) -> str:
    text = str(text).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def extract_label_map(dimension_info: dict[str, Any]) -> dict[str, str]:
    category = dimension_info.get("category", {})
    index_obj = category.get("index", {})
    label_obj = category.get("label", {})

    if isinstance(index_obj, list):
        category_ids = [str(x) for x in index_obj]
    elif isinstance(index_obj, dict):
        category_ids = list(index_obj.keys())
    else:
        category_ids = []

    labels: dict[str, str] = {}
    for cat_id in category_ids:
        labels[str(cat_id)] = str(label_obj.get(cat_id, cat_id))

    if not labels and isinstance(label_obj, dict):
        for k, v in label_obj.items():
            labels[str(k)] = str(v)

    return labels


def jsonstat_to_dataframe(payload: dict[str, Any]) -> pd.DataFrame:
    if "id" not in payload or "dimension" not in payload:
        raise ValueError("This JSON does not look like a JSON-stat dataset payload.")

    dim_ids: list[str] = payload["id"]
    dimensions: dict[str, Any] = payload["dimension"]
    sizes: list[int] = payload.get("size", [])

    if sizes and len(sizes) != len(dim_ids):
        raise ValueError("Mismatch between payload['id'] and payload['size'].")

    dim_value_ids: list[list[str]] = []
    dim_value_labels: list[dict[str, str]] = []
    dim_labels: list[str] = []

    for dim_id in dim_ids:
        dim_info = dimensions[dim_id]
        dim_label = str(dim_info.get("label", dim_id))
        label_map = extract_label_map(dim_info)

        if label_map:
            ids_for_dim = list(label_map.keys())
        else:
            category = dim_info.get("category", {})
            index_obj = category.get("index", [])
            if isinstance(index_obj, list):
                ids_for_dim = [str(x) for x in index_obj]
            elif isinstance(index_obj, dict):
                ids_for_dim = list(index_obj.keys())
            else:
                ids_for_dim = []

            label_map = {x: x for x in ids_for_dim}

        dim_value_ids.append(ids_for_dim)
        dim_value_labels.append(label_map)
        dim_labels.append(dim_label)

    combinations = list(itertools.product(*dim_value_ids))
    values = payload.get("value")

    if values is None:
        raise ValueError("JSON-stat payload has no 'value' field.")

    records: list[dict[str, Any]] = []

    if isinstance(values, list):
        if len(values) != len(combinations):
            raise ValueError(f"Expected {len(combinations)} values but got {len(values)}.")

        for combo, value in zip(combinations, values):
            row: dict[str, Any] = {}
            for dim_id, dim_label, cat_id, label_map in zip(
                dim_ids, dim_labels, combo, dim_value_labels
            ):
                row[dim_id] = cat_id
                row[f"{dim_id}_label"] = label_map.get(cat_id, cat_id)
                row[safe_slug(dim_label)] = label_map.get(cat_id, cat_id)

            row["value"] = value
            records.append(row)

    elif isinstance(values, dict):
        for flat_idx_str, value in values.items():
            flat_idx = int(flat_idx_str)
            combo = combinations[flat_idx]

            row: dict[str, Any] = {}
            for dim_id, dim_label, cat_id, label_map in zip(
                dim_ids, dim_labels, combo, dim_value_labels
            ):
                row[dim_id] = cat_id
                row[f"{dim_id}_label"] = label_map.get(cat_id, cat_id)
                row[safe_slug(dim_label)] = label_map.get(cat_id, cat_id)

            row["value"] = value
            records.append(row)
    else:
        raise ValueError("Unsupported JSON-stat 'value' type.")

    return pd.DataFrame(records)


# ============================================================
# Cleaning helpers
# ============================================================
def normalise_common_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    for col in df.columns:
        if col != "value":
            df[col] = df[col].astype(str)

    df = df.dropna(subset=["value"]).reset_index(drop=True)
    return df


def find_first_matching_column(df: pd.DataFrame, contains_any: list[str]) -> str | None:
    lowered = {col: col.lower() for col in df.columns}
    for target in contains_any:
        target = target.lower()
        for original, low in lowered.items():
            if target in low:
                return original
    return None


def create_summary(df: pd.DataFrame, candidate_groups: list[list[str]]) -> pd.DataFrame:
    cleaned = normalise_common_columns(df)

    group_cols: list[str] = []
    seen: set[str] = set()

    for group in candidate_groups:
        col = find_first_matching_column(cleaned, group)
        if col and col not in seen:
            group_cols.append(col)
            seen.add(col)

    if not group_cols:
        return cleaned.copy()

    summary = (
        cleaned.groupby(group_cols, dropna=False, as_index=False)["value"]
        .sum()
        .sort_values("value", ascending=False)
        .reset_index(drop=True)
    )
    return summary


def save_csv(df: pd.DataFrame, filename: str) -> None:
    path = OUTPUT_DIR / filename
    df.to_csv(path, index=False)
    print(f"Saved: {path}")


def save_geojson(payload: dict[str, Any], filename: str) -> None:
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    print(f"Saved: {path}")


def create_ireland_nuts3_geojson() -> None:
    print("Fetching eu_nuts3_geojson...")
    geojson = fetch_geojson(DATASETS["eu_nuts3_geojson"])

    ireland_features: list[dict[str, Any]] = []
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        cntr_code = str(props.get("CNTR_CODE", "")).strip().upper()
        nuts_id = str(props.get("NUTS_ID", "")).strip().upper()

        if cntr_code == "IE" or nuts_id.startswith("IE"):
            ireland_features.append(feature)

    ireland_geojson = {
        "type": "FeatureCollection",
        "features": ireland_features,
    }

    save_geojson(ireland_geojson, "ireland_nuts3.geojson")


def process_dataset(
    dataset_key: str,
    raw_filename: str,
    summary_filename: str,
    candidate_groups: list[list[str]],
) -> None:
    print(f"Fetching {dataset_key}...")
    payload = fetch_json(DATASETS[dataset_key])
    raw_df = jsonstat_to_dataframe(payload)
    cleaned_df = normalise_common_columns(raw_df)
    summary_df = create_summary(cleaned_df, candidate_groups)

    save_csv(cleaned_df, raw_filename)
    save_csv(summary_df, summary_filename)


# ============================================================
# Main pipeline
# ============================================================
def main() -> None:
    print("Downloading and preparing CSO People and Society datasets...\n")

    # VSA38
    process_dataset(
        dataset_key="vsa38_birth_rate",
        raw_filename="vsa38_birth_rate_raw_cleaned.csv",
        summary_filename="vsa38_birth_rate_summary.csv",
        candidate_groups=[
            ["time", "year"],
            ["area_of_residence", "area", "region"],
            ["statistic"],
        ],
    )

    # VSA94
    process_dataset(
        dataset_key="vsa94_infant_mortality",
        raw_filename="vsa94_infant_mortality_raw_cleaned.csv",
        summary_filename="vsa94_infant_mortality_summary.csv",
        candidate_groups=[
            ["time", "year"],
            ["area_of_residence", "area", "region"],
            ["statistic"],
        ],
    )

    # VSA104
    process_dataset(
        dataset_key="vsa104_fertility",
        raw_filename="vsa104_fertility_raw_cleaned.csv",
        summary_filename="vsa104_fertility_summary.csv",
        candidate_groups=[
            ["time", "year"],
            ["mother_s_age_group", "age_group", "age group"],
            ["region", "nuts3"],
            ["statistic"],
        ],
    )

    # VSA108
    process_dataset(
        dataset_key="vsa108_death_rate",
        raw_filename="vsa108_death_rate_raw_cleaned.csv",
        summary_filename="vsa108_death_rate_summary.csv",
        candidate_groups=[
            ["time", "year"],
            ["region", "nuts3"],
            ["statistic"],
        ],
    )

    # PEA26
    process_dataset(
        dataset_key="pea26_population",
        raw_filename="pea26_population_raw_cleaned.csv",
        summary_filename="pea26_population_summary.csv",
        candidate_groups=[
            ["time", "year"],
            ["age_group", "age group"],
            ["sex"],
            ["region", "nuts3"],
            ["statistic"],
        ],
    )

    # PEA27
    process_dataset(
        dataset_key="pea27_citizenship_non_eu",
        raw_filename="pea27_citizenship_non_eu_raw_cleaned.csv",
        summary_filename="pea27_citizenship_non_eu_summary.csv",
        candidate_groups=[
            ["time", "year"],
            ["age_group", "age group"],
            ["sex"],
            ["human_development_index", "hdi"],
            ["statistic"],
        ],
    )

    # PEA28
    process_dataset(
        dataset_key="pea28_birthplace_non_eu",
        raw_filename="pea28_birthplace_non_eu_raw_cleaned.csv",
        summary_filename="pea28_birthplace_non_eu_summary.csv",
        candidate_groups=[
            ["time", "year"],
            ["age_group", "age group"],
            ["sex"],
            ["human_development_index", "hdi"],
            ["statistic"],
        ],
    )

    # PEA29
    process_dataset(
        dataset_key="pea29_old_age_dependency",
        raw_filename="pea29_old_age_dependency_raw_cleaned.csv",
        summary_filename="pea29_old_age_dependency_summary.csv",
        candidate_groups=[
            ["time", "year"],
            ["sex"],
            ["region", "nuts3"],
            ["statistic"],
        ],
    )

    create_ireland_nuts3_geojson()

    print("\nDone.")
    print("\nCreated files:")
    print("- data_processed/vsa38_birth_rate_raw_cleaned.csv")
    print("- data_processed/vsa38_birth_rate_summary.csv")
    print("- data_processed/vsa94_infant_mortality_raw_cleaned.csv")
    print("- data_processed/vsa94_infant_mortality_summary.csv")
    print("- data_processed/vsa104_fertility_raw_cleaned.csv")
    print("- data_processed/vsa104_fertility_summary.csv")
    print("- data_processed/vsa108_death_rate_raw_cleaned.csv")
    print("- data_processed/vsa108_death_rate_summary.csv")
    print("- data_processed/pea26_population_raw_cleaned.csv")
    print("- data_processed/pea26_population_summary.csv")
    print("- data_processed/pea27_citizenship_non_eu_raw_cleaned.csv")
    print("- data_processed/pea27_citizenship_non_eu_summary.csv")
    print("- data_processed/pea28_birthplace_non_eu_raw_cleaned.csv")
    print("- data_processed/pea28_birthplace_non_eu_summary.csv")
    print("- data_processed/pea29_old_age_dependency_raw_cleaned.csv")
    print("- data_processed/pea29_old_age_dependency_summary.csv")
    print("- data_processed/ireland_nuts3.geojson")


if __name__ == "__main__":
    main()