import argparse
import geopandas as gpd
from core.io_utils import read_vector
from core.crs_utils import to_utm
from core.assigner import (
    Params, filter_oh_segments, restrict_to_hfra,
    ensure_elevation_fields, generate_candidates_one_to_many, select_best_match
)

def main():
    ap = argparse.ArgumentParser(description="Assign stations to OH distribution segments by distance & elevation rules.")
    ap.add_argument("--stations", required=True, help="Path to stations (vector). CSV requires lat/lon.")
    ap.add_argument("--segments", required=True, help="Path to segments (vector).")
    ap.add_argument("--station-id", default="station_id")
    ap.add_argument("--segment-id", default="segment_id")
    ap.add_argument("--oh-filter-expr", default=None, help="e.g., \"STRUCTURE == 'OH'\"")
    ap.add_argument("--hfra", default=None, help="Optional HFRA polygon path.")
    ap.add_argument("--dem", default=None, help="Optional DEM GeoTIFF if elevation fields missing.")
    ap.add_argument("--distance-miles", type=float, default=0.5)
    ap.add_argument("--elev-tol-ft", type=float, default=500.0)
    ap.add_argument("--out-candidates", default="candidates.csv")
    ap.add_argument("--out-best", default="best_match.csv")
    args = ap.parse_args()

    params = Params(
        distance_miles=args.distance_miles,
        elev_tol_ft=args.elev_tol_ft,
        station_id=args.station_id,
        segment_id=args.segment_id,
        oh_filter_expr=args.oh_filter_expr
    )

    print(f"Reading stations: {args.stations}")
    stations = read_vector(args.stations)
    print(f"Reading segments: {args.segments}")
    segments = read_vector(args.segments)

    segments_oh = filter_oh_segments(segments, params.oh_filter_expr)
    print(f"Segments after OH filter: {len(segments_oh)}")

    if args.hfra:
        print(f"Reading HFRA: {args.hfra}")
        hfra = read_vector(args.hfra)
        segments_oh = restrict_to_hfra(segments_oh, hfra)
        print(f"Segments after HFRA filter: {len(segments_oh)}")
    else:
        hfra = None

    # Ensure elevation fields exist (compute via DEM if absent)
    # Check if we need DEM
    print("Checking elevation fields...")
    stations, segments_oh = ensure_elevation_fields(stations, segments_oh, args.dem, params)

    # Project both to UTM (consistent planar distance)
    print("Projecting to UTM...")
    utm_epsg = None  # auto detect off stations
    stations_utm = to_utm(stations, utm_epsg)
    # Use same EPSG for segments
    utm_epsg = stations_utm.crs.to_epsg()
    segments_utm = to_utm(segments_oh, utm_epsg)

    # Build one-to-many candidates
    print("Generating candidates...")
    cand = generate_candidates_one_to_many(stations_utm, segments_utm, params)
    cand.to_csv(args.out_candidates, index=False)

    # Best per station
    print("Selecting best matches...")
    best = select_best_match(cand, params)
    best.to_csv(args.out_best, index=False)

    print(f"Saved one-to-many: {args.out_candidates}")
    print(f"Saved best-match:  {args.out_best}")

if __name__ == "__main__":
    main()
