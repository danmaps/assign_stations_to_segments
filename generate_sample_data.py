import geopandas as gpd
from shapely.geometry import Point, LineString
import numpy as np
import os

# Create sample data in Santa Monica, CA area
# Approx bounds: Lon -118.50 to -118.48, Lat 34.00 to 34.02

# 1. Stations (Points)
# Create 5 stations
lons = [-118.495, -118.490, -118.485, -118.492, -118.488]
lats = [34.012, 34.015, 34.010, 34.008, 34.018]
ids = ["SM_01", "SM_02", "SM_03", "SM_04", "SM_05"]
elevs = [100.0, 150.0, 90.0, 110.0, 160.0]  # Feet

stations = gpd.GeoDataFrame({
    "station_id": ids,
    "elevation_ft": elevs,
    "type": ["Weather"] * 5
}, geometry=[Point(xy) for xy in zip(lons, lats)], crs="EPSG:4326")

# 2. Segments (Lines)
# Create a grid of lines
lines = []
seg_ids = []
min_zs = []
max_zs = []

# East-West lines
for i, lat in enumerate([34.010, 34.015, 34.020]):
    line = LineString([(-118.500, lat), (-118.480, lat)])
    lines.append(line)
    seg_ids.append(f"EW_{i}")
    min_zs.append(80 + i*20)
    max_zs.append(120 + i*20)

# North-South lines
for i, lon in enumerate([-118.495, -118.490, -118.485]):
    line = LineString([(lon, 34.005), (lon, 34.025)])
    lines.append(line)
    seg_ids.append(f"NS_{i}")
    min_zs.append(90 + i*10)
    max_zs.append(150 + i*10)

segments = gpd.GeoDataFrame({
    "segment_id": seg_ids,
    "min_elev_ft": min_zs,
    "max_elev_ft": max_zs,
    "STRUCTURE": ["OH"] * len(lines)  # Match default filter
}, geometry=lines, crs="EPSG:4326")

# Save
out_dir = "sample_data"
stations.to_file(os.path.join(out_dir, "stations_sample.geojson"), driver="GeoJSON")
segments.to_file(os.path.join(out_dir, "segments_sample.geojson"), driver="GeoJSON")

print("Sample data created in sample_data/")
