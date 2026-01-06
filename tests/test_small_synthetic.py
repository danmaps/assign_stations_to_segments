import geopandas as gpd
from shapely.geometry import Point, LineString
import pandas as pd
import pytest
import sys
from pathlib import Path

# Add root to path for core import
root = Path(__file__).parent.parent
sys.path.append(str(root))

from core.assigner import Params, generate_candidates_one_to_many, select_best_match

def test_assignment_distance_and_elevation():
    # Station near a line, within 0.5mi, elevation in range
    st = gpd.GeoDataFrame(
        {"station_id": ["S1"], "station_elev_ft": [1500]},
        geometry=[Point(0, 0)], crs="EPSG:32611"
    )
    # Line starting at x=300m (well within 0.5 miles ~ 800m)
    # 0.5 miles = 804.672 meters
    seg = gpd.GeoDataFrame(
        {"segment_id": ["L1"], "seg_min_elev_ft": [1000], "seg_max_elev_ft": [2000]},
        geometry=[LineString([(300,0),(400,0)])], crs="EPSG:32611"
    )
    p = Params(distance_miles=0.5, elev_tol_ft=500)
    cand = generate_candidates_one_to_many(st, seg, p)
    
    assert len(cand) == 1
    assert cand.iloc[0]["elev_pass"] == True
    
    best = select_best_match(cand, p)
    assert len(best) == 1
    assert best.iloc[0]["segment_id"] == "L1"

def test_distance_fail():
    # Station far away (> 0.5 mi approx 805m)
    st = gpd.GeoDataFrame(
        {"station_id": ["S1"], "station_elev_ft": [1500]},
        geometry=[Point(0, 0)], crs="EPSG:32611"
    )
    # Line starts at 1000m
    seg = gpd.GeoDataFrame(
        {"segment_id": ["L1"], "seg_min_elev_ft": [1000], "seg_max_elev_ft": [2000]},
        geometry=[LineString([(1000,0),(1100,0)])], crs="EPSG:32611"
    )
    p = Params(distance_miles=0.5, elev_tol_ft=500)
    cand = generate_candidates_one_to_many(st, seg, p)
    assert len(cand) == 0

def test_elevation_fail():
    # Station near but too high
    st = gpd.GeoDataFrame(
        {"station_id": ["S1"], "station_elev_ft": [3000]},
        geometry=[Point(0, 0)], crs="EPSG:32611"
    )
    # Segment max is 2000. Tol is 500. Max valid is 2500. Station 3000 > 2500 -> Fail.
    seg = gpd.GeoDataFrame(
        {"segment_id": ["L1"], "seg_min_elev_ft": [1000], "seg_max_elev_ft": [2000]},
        geometry=[LineString([(300,0),(400,0)])], crs="EPSG:32611"
    )
    p = Params(distance_miles=0.5, elev_tol_ft=500)
    cand = generate_candidates_one_to_many(st, seg, p)
    
    # It should still be a candidate (distance pass), but elev_pass should be False
    assert len(cand) == 1
    assert cand.iloc[0]["elev_pass"] == False
