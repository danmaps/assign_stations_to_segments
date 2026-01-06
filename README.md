# Assign Points to Linear Features

A tool to assign points (e.g., weather stations, assets) to the nearest linear features (e.g., distribution segments, roads) based on distance and elevation rules.

## Features
- **One-to-many** assignment: Finds all line segments within a configured distance (e.g., 0.5 miles).
- **Elevation check**: Validates if point elevation is within the line segment's elevation range ± tolerance.
- **Support for various inputs**: Shapefile, GeoJSON, GeoPackage, CSV (with lat/lon), and ArcGIS Service URLs.
- **Interactive UI**: Streamlit app for easy uploading, parameter tuning, and visualization.
- **CLI**: Command-line interface for batch processing.

## Setup

### Using uv (Recommended for speed)

1. **Create a virtual environment**:
   ```bash
   uv venv
   ```
2. **Activate the environment**:
   - Windows: `.venv\Scripts\activate`
   - Mac/Linux: `source .venv/bin/activate`
3. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```
   > **Note**: If you encounter SSL certificate errors (common in corporate environments), add the `--native-tls` flag:
   > ```bash
   > uv pip install --native-tls -r requirements.txt
   > ```

### Using standard pip

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Streamlit App
Run the interactive application:
```bash
streamlit run app_streamlit/app.py
```
- Upload **Points** (CSV, Shapefile, etc.) and **Lines** (Shapefile, GeoJSON, etc.). 
- Supports zipped Shapefiles.
- Or provide ArcGIS Feature Service URLs.
- Tune distance and elevation parameters.
- Visualize results on map and download CSVs.

### Command Line Interface (CLI)
```bash
python cli.py --stations path/to/points.shp --segments path/to/lines.shp --out-candidates cand.csv --out-best best.csv
```

Arguments:
- `--stations`: Path to points file (Note: argument name kept as `--stations` for backward compatibility).
- `--segments`: Path to lines file (Note: argument name kept as `--segments`).
- `--distance-miles`: Search radius (default 0.5).
- `--elev-tol-ft`: Elevation tolerance (default 500.0).
- `--dem`: Path to DEM GeoTIFF (optional if input files already have elevation fields).
- `--oh-filter-expr`: Query to filter lines (e.g. "STRUCTURE == 'OH'").

## Testing
Run unit tests:
```bash
pytest tests
```
