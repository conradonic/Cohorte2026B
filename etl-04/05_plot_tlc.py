from __future__ import annotations

# Dependencias para correr la app:
#   conda install -c conda-forge streamlit pandas pyarrow pydeck geopandas pyogrio
#
# La app lee la capa gold (`etl-04/data/gold/tlc/trips_by_zone.parquet`), que genera el
# notebook `04b_aggregate_gold_tlc_2026.ipynb`. Ya no recorre los parquet de silver.
#
# El mapa coropletico usa `pydeck` para dibujar y `geopandas`/`pyogrio` para leer
# `etl-04/data/bronze/tlc/taxi_zones.zip`, el shapefile oficial de zonas TLC.

import json
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
BRONZE_DIR = APP_DIR / "data" / "bronze" / "tlc"
GOLD_DIR = APP_DIR / "data" / "gold" / "tlc"
ZONE_TRIPS_PATH = GOLD_DIR / "trips_by_zone.parquet"
ZONES_ZIP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip"
LOCAL_ZONES_ZIP = BRONZE_DIR / "taxi_zones.zip"


RECORD_TYPE_LABELS = {
    "fhv": "FHV",
    "fhvhv": "High Volume FHV",
    "green": "Green taxi",
    "yellow": "Yellow taxi",
}


@st.cache_data(show_spinner=False)
def load_zone_trips() -> pd.DataFrame:
    return pd.read_parquet(ZONE_TRIPS_PATH)


def cache_remote_file(url: str, local_path: Path) -> Path | None:
    if local_path.exists():
        return local_path

    try:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, local_path)
    except OSError:
        return None
    return local_path


@st.cache_data(show_spinner="Leyendo geometria de zonas TLC...")
def load_zone_shapes() -> pd.DataFrame | None:
    try:
        import geopandas as gpd
    except ModuleNotFoundError:
        return None

    source = cache_remote_file(ZONES_ZIP_URL, LOCAL_ZONES_ZIP)
    if source is None:
        return None

    try:
        zones = gpd.read_file(f"zip://{source}!taxi_zones/taxi_zones.shp")
    except (zipfile.BadZipFile, OSError, ValueError):
        return None

    zones = zones.rename(columns={"LocationID": "location_id", "LocationID ": "location_id"})
    if "location_id" not in zones.columns:
        for candidate in ["OBJECTID", "location_i"]:
            if candidate in zones.columns:
                zones = zones.rename(columns={candidate: "location_id"})
                break

    zones = zones.to_crs(epsg=4326)
    zones["location_id"] = zones["location_id"].astype("int64")
    return zones[["location_id", "geometry"]]


def render_map(data: pd.DataFrame) -> bool:
    try:
        import pydeck as pdk
    except ModuleNotFoundError:
        st.info(
            "El archivo de zonas puede estar descargado, pero falta `pydeck` para "
            "dibujar el mapa. Instala las dependencias con `conda install -c "
            "conda-forge pydeck geopandas`."
        )
        return False

    shapes = load_zone_shapes()
    if shapes is None:
        if LOCAL_ZONES_ZIP.exists():
            st.info(
                "`taxi_zones.zip` ya esta en `etl-04/data/bronze/tlc/`, pero falta `geopandas` "
                "o un lector de shapefiles (`fiona`/`pyogrio`) para convertirlo a "
                "geometrias de mapa. En el env de la clase podes instalarlo con "
                "`conda install -c conda-forge geopandas pyogrio`."
            )
        else:
            st.info(
                "No pude descargar `taxi_zones.zip`. Bajalo desde "
                "`https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip` y "
                "guardalo en `etl-04/data/bronze/tlc/`."
            )
        return False

    map_data = shapes.merge(data, on="location_id", how="left")
    map_data["trips"] = map_data["trips"].fillna(0)
    map_data["zone_label"] = map_data["zone_label"].fillna(
        "LocationID " + map_data["location_id"].astype(str)
    )
    max_trips = max(map_data["trips"].max(), 1)
    intensity = map_data["trips"] / max_trips
    map_data["fill_r"] = 255
    map_data["fill_g"] = (245 - 180 * intensity).astype("int64")
    map_data["fill_b"] = 80
    map_data["fill_a"] = 190
    geojson = json.loads(map_data.to_json())

    layer = pdk.Layer(
        "GeoJsonLayer",
        data=geojson,
        get_fill_color=[
            "properties.fill_r",
            "properties.fill_g",
            "properties.fill_b",
            "properties.fill_a",
        ],
        get_line_color=[45, 45, 45, 120],
        line_width_min_pixels=1,
        pickable=True,
    )
    view_state = pdk.ViewState(latitude=40.72, longitude=-73.93, zoom=9.6)
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="light",
        tooltip={
            "html": "<b>{zone_label}</b><br/>Viajes: {trips}",
            "style": {"backgroundColor": "white", "color": "black"},
        },
    )
    st.pydeck_chart(deck, use_container_width=True)
    return True


st.set_page_config(page_title="TLC 2026 por zona", layout="wide")
st.title("TLC 2026: pickups y dropoffs por zona")
st.caption(
    "Dependencias del mapa: `conda install -c conda-forge pydeck geopandas pyogrio`."
)

if not ZONE_TRIPS_PATH.exists():
    st.error(
        f"No encontre la tabla gold en {ZONE_TRIPS_PATH}. "
        "Corre antes el notebook `04b_aggregate_gold_tlc_2026.ipynb`."
    )
    st.stop()

gold = load_zone_trips()

with st.sidebar:
    st.header("Filtros")
    selected_record_types = st.multiselect(
        "Tipo de viaje",
        options=sorted(gold["record_type"].unique()),
        default=sorted(gold["record_type"].unique()),
        format_func=lambda value: RECORD_TYPE_LABELS.get(value, value),
    )
    selected_months = st.multiselect(
        "Mes",
        options=sorted(gold["year_month"].unique()),
        default=sorted(gold["year_month"].unique()),
    )
    location_kind = st.radio("Zona", ["Pickup", "Dropoff"], horizontal=True)
    top_n = st.slider("Top zonas", min_value=5, max_value=50, value=20, step=5)

selected = gold[
    gold["record_type"].isin(selected_record_types)
    & gold["year_month"].isin(selected_months)
    & gold["location_kind"].eq(location_kind.lower())
]

if selected.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

data = (
    selected.groupby(
        ["location_id", "borough", "zone", "service_zone", "zone_label"], as_index=False
    )["trips"]
    .sum()
    .sort_values("trips", ascending=False)
    .reset_index(drop=True)
)

total_trips = int(data["trips"].sum())
active_zones = int((data["trips"] > 0).sum())
months_included = selected["year_month"].nunique()

metric_total, metric_zones, metric_months = st.columns(3)
metric_total.metric("Viajes agregados", f"{total_trips:,}".replace(",", "."))
metric_zones.metric("Zonas con viajes", active_zones)
metric_months.metric("Meses incluidos", months_included)

tab_map, tab_bars, tab_table = st.tabs(["Mapa", "Rankings", "Tabla"])

with tab_map:
    if not render_map(data):
        st.bar_chart(data.head(top_n).set_index("zone_label")["trips"])

with tab_bars:
    top_zones = data.head(top_n).set_index("zone_label")["trips"]
    st.subheader(f"Top {top_n} zonas de {location_kind.lower()}")
    st.bar_chart(top_zones)

    borough_counts = (
        data.groupby("borough", as_index=False)["trips"]
        .sum()
        .sort_values("trips", ascending=False)
    )
    st.subheader("Viajes por borough")
    st.bar_chart(borough_counts.set_index("borough")["trips"])

with tab_table:
    st.dataframe(
        data[
            [
                "location_id",
                "borough",
                "zone",
                "service_zone",
                "trips",
            ]
        ].sort_values("trips", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
