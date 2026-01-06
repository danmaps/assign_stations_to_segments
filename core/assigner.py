from dataclasses import dataclass
from typing import Optional, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.strtree import STRtree
from shapely import prepared
from .crs_utils import to_utm
from .elevation import sample_points_dem, sample_line_minmax_dem

FEET_TO_METERS = 0.3048
MILES_TO_METERS = 1609.344

@dataclass
class Params:
    distance_miles: float = 0.5
    elev_tol_ft: float = 500.0
    station_id: str = "station_id"
    segment_id: str = "segment_id"
    oh_filter_expr: Optional[str] = None  # e.g., "STRUCTURE == 'OH'"
    hfra_only: bool = False
    top_n: int = 1
    check_elevation: bool = True
    group_by_col: str = "segment" # 'segment' or 'station'

def filter_oh_segments(segments: gpd.GeoDataFrame, expr: Optional[str]) -> gpd.GeoDataFrame:
    if expr:
        return segments.query(expr).copy()
    return segments.copy()

def restrict_to_hfra(gdf: gpd.GeoDataFrame, hfra: Optional[gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    if hfra is None:
        return gdf
    # Intersect to keep only geometry inside HFRA
    # Using 'overlay' with intersection
    return gpd.overlay(gdf, hfra, how="intersection")

def ensure_elevation_fields(
    stations: gpd.GeoDataFrame,
    segments_oh: gpd.GeoDataFrame,
    dem_path: Optional[str],
    params: Params,
    line_sample_step_m: float = 100.0
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Populate elevation fields if missing. Station: 'station_elev_ft'
    Segments: 'seg_min_elev_ft', 'seg_max_elev_ft'
    """
    st = stations.copy()
    seg = segments_oh.copy()

    # Station elevation
    if "station_elev_ft" not in st.columns:
        if dem_path:
            st["station_elev_ft"] = sample_points_dem(st, dem_path)
        else:
            print("Warning: 'station_elev_ft' missing and no DEM provided. Elevation check will be skipped.")
            st["station_elev_ft"] = np.nan

    # Segment elevation range
    if not {"seg_min_elev_ft", "seg_max_elev_ft"}.issubset(seg.columns):
        if dem_path:
            mn, mx = sample_line_minmax_dem(seg, dem_path, step_m=line_sample_step_m)
            seg["seg_min_elev_ft"] = mn
            seg["seg_max_elev_ft"] = mx
        else:
            print("Warning: segment elevation fields missing and no DEM provided. Elevation check will be skipped.")
            if "seg_min_elev_ft" not in seg.columns: seg["seg_min_elev_ft"] = np.nan
            if "seg_max_elev_ft" not in seg.columns: seg["seg_max_elev_ft"] = np.nan

    return st, seg

def generate_candidates_one_to_many(
    stations_utm: gpd.GeoDataFrame,
    segments_utm: gpd.GeoDataFrame,
    params: Params
) -> gpd.GeoDataFrame:
    """
    Return a long-form GeoDataFrame where each row is a station-candidate segment pair
    within distance, with computed distance and elevation pass/fail.
    """
    if segments_utm.empty or stations_utm.empty:
        return gpd.GeoDataFrame(columns=[params.station_id, params.segment_id, "distance_m", "elev_pass"], crs=stations_utm.crs)

    radius_m = params.distance_miles * MILES_TO_METERS
    
    # Drop rows with invalid geometry
    segments_utm = segments_utm[segments_utm.geometry.notnull() & ~segments_utm.geometry.is_empty].copy()
    stations_utm = stations_utm[stations_utm.geometry.notnull() & ~stations_utm.geometry.is_empty].copy()

    if segments_utm.empty or stations_utm.empty:
        return gpd.GeoDataFrame(columns=[params.station_id, params.segment_id, "distance_m", "elev_pass"], crs=stations_utm.crs)

    # Build spatial index on segment geometries
    seg_geoms = list(segments_utm.geometry)
    tree = STRtree(seg_geoms)
    
    # Pre-prepare for faster precise distance (optional optimization)
    # prepared_segments = [prepared.prep(g) for g in seg_geoms] 
    # prepared.prep is for predicates like contains/intersects, not distance()

    rows = []
    # Map geometry index back to DataFrame index/row
    # We'll use iloc for lookup
    
    for i, strow in stations_utm.iterrows():
        # Buffer envelope for broad phase
        pt_buffer_env = strow.geometry.buffer(radius_m).envelope
        
        # Candidate indices from tree
        cand_indices = tree.query(pt_buffer_env)
        
        for j in cand_indices:
            # Precise distance to segment geometry
            dist_m = strow.geometry.distance(seg_geoms[j])
            
            if dist_m <= radius_m:
                segrow = segments_utm.iloc[j]
                
                # Elevation rule
                z = strow.get("station_elev_ft", np.nan)
                zmin = segrow.get("seg_min_elev_ft", np.nan)
                zmax = segrow.get("seg_max_elev_ft", np.nan)
                
                # Handle NaNs in elevation -> Fail or Pass? 
                # Strict rule: must be within range. If Null, check skipped (Analysis continues).
                # We categorize as PASS for the sake of not filtering them out, 
                # relying on downstream logic or users to see null elevation fields.
                if not params.check_elevation:
                    elev_pass = True
                elif pd.isna(z) or pd.isna(zmin) or pd.isna(zmax):
                    elev_pass = True
                else:
                    elev_pass = (z >= (zmin - params.elev_tol_ft)) and (z <= (zmax + params.elev_tol_ft))
                
                rows.append({
                    params.station_id: strow[params.station_id],
                    params.segment_id: segrow[params.segment_id],
                    "distance_m": float(dist_m),
                    "distance_ft": float(dist_m / FEET_TO_METERS),
                    "station_elev_ft": float(z) if not pd.isna(z) else None,
                    "seg_min_elev_ft": float(zmin) if not pd.isna(zmin) else None,
                    "seg_max_elev_ft": float(zmax) if not pd.isna(zmax) else None,
                    "elev_pass": bool(elev_pass)
                })
                
    cand = gpd.GeoDataFrame(rows, geometry=None) # No geometry column needed for CSV output usually
    return cand

def select_best_match(cand: gpd.GeoDataFrame, params: Params) -> gpd.GeoDataFrame:
    """
    Pick best per station: elevate pass first; sort by distance then elev delta.
    """
    if cand.empty:
        return cand.copy()

    # Calculate elev delta
    # If elev fields are None, delta is NaN
    
    # We need to fillna to calculate abs diff, or handle it.
    # If elev_pass is False, maybe we still want to rank them? Yes.
    
    def calc_delta(row):
        if pd.isna(row["station_elev_ft"]) or pd.isna(row["seg_min_elev_ft"]) or pd.isna(row["seg_max_elev_ft"]):
            return 999999.0
        return min(abs(row["station_elev_ft"] - row["seg_min_elev_ft"]), abs(row["station_elev_ft"] - row["seg_max_elev_ft"]))

    cand["elev_delta_abs_ft"] = cand.apply(calc_delta, axis=1)

    # Sort: elev_pass desc (True > False), distance asc, elev_delta asc, segment_id asc
    # If grouping by segment, we might want to prioritize station_id in sort for determinism
    sort_cols = ["elev_pass", "distance_m", "elev_delta_abs_ft", params.segment_id, params.station_id]
    asc_order = [False, True, True, True, True]
    
    cand_sorted = cand.sort_values(
        by=sort_cols,
        ascending=asc_order
    )
    
    # Determine grouping column
    group_col = params.segment_id if params.group_by_col == "segment" else params.station_id

    # Return top N per group
    if params.top_n == 1:
        best = cand_sorted.drop_duplicates(subset=[group_col], keep="first")
    else:
        best = cand_sorted.groupby(group_col).head(params.top_n)
    
    return best
