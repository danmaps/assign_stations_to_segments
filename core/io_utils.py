import geopandas as gpd
import pandas as pd
from pathlib import Path
import os
import requests

def read_vector(path: str) -> gpd.GeoDataFrame:
    """
    Reads a vector dataset from a file path or URL.
    Supports CSV with lat/lon columns.
    Supports ArcGIS Service URLs by attempting to fetch GeoJSON.
    """
    input_path = str(path).strip()
    
    # Check if URL
    if input_path.lower().startswith("http"):
        # Heuristic for ArcGIS Feature Server
        # e.g., .../FeatureServer/0
        lower_path = input_path.lower()
        if "featureserver" in lower_path or "mapserver" in lower_path:
            # If it looks like a layer URL (ends in digit) and doesn't have query params
            if not ("query" in lower_path or "f=" in lower_path) and lower_path[-1].isdigit():
                # Append standard query to get all features as GeoJSON
                query_url = f"{input_path}/query?where=1=1&outFields=*&f=geojson"
                try:
                    return gpd.read_file(query_url)
                except Exception as e:
                    print(f"Failed auto-query {query_url}: {e}. Trying raw URL...")
                    pass
        
        # Default read for URL
        return gpd.read_file(input_path)

    p = Path(input_path)
    
    # Handle CSV
    if p.suffix.lower() == ".csv":
        df = pd.read_csv(p)
        # Search for lat/lon columns
        cols = {c.lower(): c for c in df.columns}
        # Common variations
        lat_candidates = ["lat", "latitude", "y"]
        lon_candidates = ["lon", "long", "longitude", "x"]
        
        lat_col = None
        lon_col = None
        
        for cand in lat_candidates:
            if cand in cols:
                lat_col = cols[cand]
                break
        
        for cand in lon_candidates:
            if cand in cols:
                lon_col = cols[cand]
                break
        
        if lat_col and lon_col:
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
                crs="EPSG:4326"
            )
            return gdf
        else:
            raise ValueError(f"CSV must have lat/lon columns. Found: {list(df.columns)}")
            
    # Handle standard vector (Shapefile, GeoJSON, GeoPackage, etc.)
    # Geopandas handles zip:// internal schemas if needed, or just paths to .shp
    return gpd.read_file(p)
