from typing import Optional, Tuple
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.vrt import WarpedVRT

def sample_points_dem(gdf_pts: gpd.GeoDataFrame, dem_path: str, band: int = 1) -> np.ndarray:
    """
    Sample DEM at point locations. Returns elevation array in **feet**.
    Assumes DEM in meters; convert to feet (3.28084).
    """
    with rasterio.open(dem_path) as src:
        # Reproject points to DEM CRS for sampling
        pts = gdf_pts.to_crs(src.crs)
        coords = [(geom.x, geom.y) for geom in pts.geometry]
        
        # Sample
        # Note: src.sample returns a generator of arrays (one value per band)
        samples = np.array([val[0] for val in src.sample(coords, indexes=band)])
    
    return samples * 3.28084  # m->ft

def sample_line_minmax_dem(gdf_lines: gpd.GeoDataFrame, dem_path: str, band: int = 1,
                           step_m: float = 100.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Sample DEM along each line by densifying at ~step_m spacing (in meters).
    Returns (min_ft, max_ft) per line.
    """
    with rasterio.open(dem_path) as src:
        # Work in DEM CRS to measure meters
        lines = gdf_lines.to_crs(src.crs)
        min_list, max_list = [], []
        
        for geom in lines.geometry:
            if geom is None or geom.is_empty:
                min_list.append(np.nan)
                max_list.append(np.nan)
                continue
                
            # Handle MultiLineString
            geoms = [geom] if geom.geom_type == "LineString" else list(geom.geoms)
            zs = []
            
            for g in geoms:
                length = g.length
                # Ensure at least 2 samples per part
                if length == 0:
                    continue
                n = max(2, int(np.ceil(length / step_m)))
                ds = np.linspace(0, length, n)
                pts = [g.interpolate(d) for d in ds]
                coords = [(p.x, p.y) for p in pts]
                zvals = [v[0] for v in src.sample(coords, indexes=band)]
                zs.extend(zvals)
            
            if len(zs) == 0:
                min_list.append(np.nan)
                max_list.append(np.nan)
            else:
                zs = np.array(zs) * 3.28084  # meters->feet
                # Use nanmin/nanmax to ignore nodata if any
                min_list.append(np.nanmin(zs))
                max_list.append(np.nanmax(zs))
                
    return np.array(min_list), np.array(max_list)
