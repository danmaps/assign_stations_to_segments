# app_streamlit/app.py
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import tempfile
import shutil
import os
from pathlib import Path
import sys

# Add parent dir to path so we can import core
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

from core.io_utils import read_vector
from core.crs_utils import to_utm
from core.assigner import (
    Params, filter_oh_segments, restrict_to_hfra,
    ensure_elevation_fields, generate_candidates_one_to_many, select_best_match
)

def save_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return None
    # Create temp file with correct suffix
    suffix = Path(uploaded_file.name).suffix
    if suffix == "":
        suffix = ".tmp"
    
    # If zip, we keep .zip
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name

st.set_page_config(page_title="Point→Linear Feature Assignment", layout="wide")

st.title("Assign Points to Nearest Linear Features")
st.caption("Matches points to lines based on distance and optional elevation criteria.")

# Sidebar controls
distance_miles = st.sidebar.slider("Distance threshold (miles)", 0.1, 5.0, 0.5, 0.1)
elev_tol_ft = st.sidebar.slider("Elevation tolerance (feet)", 100, 2000, 500, 50)
station_id = st.sidebar.text_input("Point ID field", "station_id", help="Column name for unique ID in points dataset")
segment_id = st.sidebar.text_input("Line ID field", "segment_id", help="Column name for unique ID in lines dataset")
oh_filter_expr = st.sidebar.text_input("Line filter expression (optional)", "", help="Pandas query expression e.g., `STRUCTURE == 'OH'`")
line_sample_step_m = st.sidebar.slider("DEM sampling step along lines (m)", 25, 250, 100, 25)

if "run_analysis" not in st.session_state:
    st.session_state.run_analysis = True # Auto-run on first load

st.subheader("Data Input")

col1, col2 = st.columns(2)

# Check for sample data
sample_dir = os.path.join(root_dir, "sample_data")
sample_stations = os.path.join(sample_dir, "stations_sample.geojson")
sample_segments = os.path.join(sample_dir, "segments_sample.geojson")
has_sample = os.path.exists(sample_stations) and os.path.exists(sample_segments)

with col1:
    st.markdown("### Points (e.g., Stations)")
    # Default to Upload File if sample exists, else URL
    default_idx = 0 if has_sample else 1
    station_source_type = st.radio("Source", ["Upload File", "ArcGIS Service URL"], index=default_idx, key="st_source")
    stations_path = None
    
    if station_source_type == "Upload File":
        f = st.file_uploader("Upload Points (CSV/Shp/Zip/GPKG)", type=["gpkg","shp","json","geojson","csv","zip"], key="st_file")
        if f:
            stations_path = save_uploaded_file(f)
        elif has_sample:
            stations_path = sample_stations
            st.info("Using sample data (Santa Monica, CA)")
    else:
        stations_path = st.text_input("Points Service URL", value="https://services9.arcgis.com/RHVPKKiFTONKtxq3/arcgis/rest/services/NOAA_METAR_current_wind_speed_direction_v1/FeatureServer", key="st_url")

with col2:
    st.markdown("### Lines (e.g., Segments)")
    default_idx = 0 if has_sample else 1
    segment_source_type = st.radio("Source", ["Upload File", "ArcGIS Service URL"], index=default_idx, key="seg_source")
    segments_path = None
    
    if segment_source_type == "Upload File":
        f = st.file_uploader("Upload Lines (Shp/Zip/GPKG)", type=["gpkg","shp","json","geojson", "zip"], key="seg_file")
        if f:
            segments_path = save_uploaded_file(f)
        elif has_sample:
            segments_path = sample_segments
            st.info("Using sample data (Santa Monica, CA)")
    else:
        segments_path = st.text_input("Lines Service URL", value="https://services6.arcgis.com/Do88DoK2xjTUCXd1/arcgis/rest/services/OSM_NA_Highways/FeatureServer", key="seg_url")

st.markdown("### Optional Inputs")
hfra_file = st.file_uploader("Constraint Polygon (optional, e.g. HFRA)", type=["gpkg","shp","json","geojson","zip"], help="Only lines intersecting this polygon will be considered")
dem_file = st.file_uploader("DEM GeoTIFF (optional if elevevation fields exist)", type=["tif","tiff"])

# Button to trigger re-run
if st.button("Run assignment", type="primary"):
    st.session_state.run_analysis = True

if st.session_state.run_analysis:
    # Reset state so it doesn't run on every interaction unless button clicked or first load
    # actually, keeping it True might be annoying if inputs change. 
    # But usually we want it to run when inputs change? 
    # For now, let's just use the flag.
    st.session_state.run_analysis = False 
    
    if not stations_path or not segments_path:
        st.error("Please provide both Points and Lines.")
    else:
        stations = None
        segments = None
        hfra = None
        
        with st.spinner("Reading data..."):
            try:
                # Handle zip paths for geopandas
                # If path ends in .zip, prefix with zip://
                st_read_path = stations_path
                if str(stations_path).lower().endswith(".zip"):
                    st_read_path = f"zip://{stations_path}"
                
                seg_read_path = segments_path
                if str(segments_path).lower().endswith(".zip"):
                    seg_read_path = f"zip://{segments_path}"
                
                stations = read_vector(st_read_path)
                segments = read_vector(seg_read_path)
                
                if hfra_file:
                    hf_path = save_uploaded_file(hfra_file)
                    if hf_path.lower().endswith(".zip"):
                        hf_path = f"zip://{hf_path}"
                    hfra = read_vector(hf_path)
                
                st.success(f"Loaded {len(stations)} stations and {len(segments)} segments.")
            except Exception as e:
                st.error(f"Error reading data: {e}")
                # We stop later if data isn't loaded
        
        if stations is not None and segments is not None:
            with st.spinner("Processing..."):
                try:
                    params = Params(distance_miles=distance_miles, elev_tol_ft=elev_tol_ft,
                                    station_id=station_id, segment_id=segment_id,
                                    oh_filter_expr=oh_filter_expr if oh_filter_expr.strip() else None)

                    segments_oh = filter_oh_segments(segments, params.oh_filter_expr)
                    if hfra is not None:
                        segments_oh = restrict_to_hfra(segments_oh, hfra)

                    dem_path = None
                    if dem_file:
                        dem_path = save_uploaded_file(dem_file)

                    stations, segments_oh = ensure_elevation_fields(stations, segments_oh, dem_path, params,
                                                                    line_sample_step_m=line_sample_step_m)

                    utm_epsg = None
                    stations_utm = to_utm(stations, utm_epsg)
                    # Use same projection for consistency
                    if utm_epsg is None:
                        utm_epsg = stations_utm.crs.to_epsg()
                    segments_utm = to_utm(segments_oh, utm_epsg)

                    cand = generate_candidates_one_to_many(stations_utm, segments_utm, params)
                    best = select_best_match(cand, params)
                    
                    st.subheader("Results")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"One-to-many candidates ({len(cand)})")
                        st.dataframe(cand.head(100))
                        st.download_button("Download candidates CSV", data=cand.to_csv(index=False), file_name="candidates.csv")
                    with c2:
                        st.write(f"Best match per station ({len(best)})")
                        st.dataframe(best.head(100))
                        st.download_button("Download best-match CSV", data=best.to_csv(index=False), file_name="best_match.csv")

                    # Map preview (Folium)
                    st.subheader("Map preview")
                    
                    # Convert to WGS84 for mapping
                    # Handle empty results
                    if not stations.empty:
                         # Center map
                         center_lat = stations.to_crs(4326).geometry.y.mean()
                         center_lon = stations.to_crs(4326).geometry.x.mean()
                         m = folium.Map(tiles="cartodb-dark-matter", location=[center_lat, center_lon], zoom_start=10)
                    else:
                         m = folium.Map(tiles="cartodb-dark-matter", zoom_start=10)

                    # Add OH segments (simplify for display if needed)
                    # Filter OH segments for map
                    if not segments_oh.empty:
                        seg_geo = segments_oh.to_crs(4326)
                        if len(seg_geo) > 2000:
                             st.warning("Many segments. Mapping first 2000.")
                             seg_geo = seg_geo.iloc[:2000]

                        col_tooltip = [segment_id] if segment_id in seg_geo.columns else []
                        folium.GeoJson(
                            seg_geo,
                            name="OH segments",
                            style_function=lambda x: {"color": "#ffb703", "weight": 2},
                            tooltip=folium.GeoJsonTooltip(fields=col_tooltip) if col_tooltip else None
                        ).add_to(m)
                    
                    # Add stations
                    if not stations.empty:
                        stations_map = stations
                        if len(stations) > 1000:
                            st.warning("Large dataset detected. Mapping first 1000 stations.")
                            stations_map = stations.iloc[:1000]
                        
                        st_geo = stations_map.to_crs(4326)
                        for _, r in st_geo.iterrows():
                            # safely get id
                            s_id = r[station_id] if station_id in r else "Station"
                            folium.CircleMarker(
                                location=(r.geometry.y, r.geometry.x),
                                radius=4,
                                color="cyan",
                                fill=True,
                                tooltip=str(s_id)
                            ).add_to(m)

                    folium.LayerControl().add_to(m)
                    st_folium(m, height=600, width=None)
                    
                except Exception as e:
                    st.error(f"Error during processing: {e}")
                    import traceback
                    traceback.print_exc()
