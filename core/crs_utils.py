from typing import Optional
import geopandas as gpd

def auto_utm_epsg_from_gdf(gdf: gpd.GeoDataFrame) -> int:
    """
    Choose UTM EPSG based on centroid longitude & hemisphere.
    Works for mixed SoCal extents (zones 11 or 10). Default N hemisphere.
    """
    # Use total_bounds for speed over unary_union
    minx, miny, maxx, maxy = gdf.to_crs(4326).total_bounds
    lon = (minx + maxx) / 2
    zone = int((lon + 180) // 6) + 1
    epsg = 32600 + zone  # WGS84 / UTM zone N
    return epsg

def to_utm(gdf: gpd.GeoDataFrame, epsg: Optional[int] = None) -> gpd.GeoDataFrame:
    if epsg is None:
        epsg = auto_utm_epsg_from_gdf(gdf)
    return gdf.to_crs(epsg=epsg)
