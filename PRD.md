# Product Requirements Document: Points-to-Lines Assignment Tool

## 1. Executive Summary

The **Points-to-Lines Assignment Tool** is a geospatial analysis application designed to identify and match points (e.g., weather stations, utility assets) to their closest linear features (e.g., distribution segments, roads) based on spatial distance and elevation constraints. The tool provides both an interactive web interface and command-line interface for flexible deployment across different use cases.

---

## 2. Product Overview

### 2.1 Purpose

Enable users to efficiently assign points to line segments with configurable spatial and elevation-based matching rules, facilitating operations planning and asset management in utility, transportation, and environmental domains.

### 2.2 Key Use Cases

- **Utility Distribution**: Assign weather stations to overhead distribution segments for weather impact analysis
- **Asset Inventory**: Match field assets to network segments for maintenance planning
- **Environmental Monitoring**: Correlate monitoring stations with transportation corridors
- **Infrastructure Planning**: Support site selection and resource allocation decisions

---

## 3. Core Features

### 3.1 Point-to-Line Matching Engine

**Requirement**: Identify all candidate line segments within a configurable distance threshold for each input point.

- **Spatial Search**: Employ efficient R-tree spatial indexing to find line segments within user-defined search radius (default: 0.5 miles)
- **Distance Calculation**: Compute perpendicular distance from point to line segment in projected coordinates (UTM)
- **One-to-Many Matching**: Support multiple candidates per point with ranked distance metrics
- **Best Match Selection**: Automatically select top-N candidates or single best match based on user preference

### 3.2 Elevation Validation

**Requirement**: Filter matches based on elevation compatibility between points and line segments.

- **Point Elevation**: Extract or ingest point elevation data (feet)
- **Segment Elevation Range**: Compute minimum and maximum elevation along line segments
- **Elevation Tolerance**: Apply user-configurable tolerance (default: 500 feet) to validate matches
- **DEM Integration**: Optional Digital Elevation Model (GeoTIFF) support for computing missing elevation data
- **Graceful Degradation**: Skip elevation checks if DEM unavailable and fields missing

### 3.3 Data Input & Format Support

**Requirement**: Accept multiple geospatial data formats and sources.

**Supported Input Formats**:
- Vector Files: Shapefile, GeoJSON, GeoPackage
- Tabular Data: CSV (with lat/lon columns)
- Zipped Shapefiles: Direct upload of .zip archives
- Remote Sources: ArcGIS Feature Service URLs

**Data Requirements**:
- Points: geometry, required ID field, optional elevation field
- Lines: geometry, required ID field, optional elevation range fields, optional filter attributes

### 3.4 Configurable Filtering

**Requirement**: Support attribute-based filtering to refine input datasets.

- **Segment Filtering**: Query expression syntax (e.g., `STRUCTURE == 'OH'`) to pre-filter segments
- **HFRA Boundary Filtering**: Restrict segments to High Fire Risk Area polygons
- **Custom ID Fields**: Support non-standard column names for point/segment identifiers

### 3.5 Interactive Web Interface

**Requirement**: Provide user-friendly Streamlit application for ad-hoc analysis and parameter experimentation.

**Capabilities**:
- File upload interface for points and lines
- Configurable parameter controls:
  - Search distance (miles)
  - Elevation tolerance (feet)
  - Filter expressions
- Map visualization of results with matched pairs highlighted
- Data preview tables for input and output
- CSV export of candidates and best matches
- Support for Shapefile zip uploads

### 3.6 Command-Line Interface

**Requirement**: Enable batch processing and automation through CLI.

**Arguments**:
- `--stations`: Path to points file
- `--segments`: Path to lines file
- `--distance-miles`: Search radius (default 0.5)
- `--elev-tol-ft`: Elevation tolerance in feet (default 500.0)
- `--dem`: Optional DEM GeoTIFF for elevation sampling
- `--oh-filter-expr`: Optional segment filter query
- `--hfra`: Optional HFRA boundary polygon
- `--station-id` / `--segment-id`: Custom ID column names
- `--out-candidates`: Output path for all candidates
- `--out-best`: Output path for best matches

---

## 4. Technical Architecture

### 4.1 Core Components

| Component | Purpose |
|-----------|---------|
| `assigner.py` | Main matching logic, spatial indexing, distance/elevation calculations |
| `crs_utils.py` | Coordinate system transformations (geographic to UTM) |
| `elevation.py` | DEM sampling for points and line segments |
| `io_utils.py` | Multi-format vector file reading and writing |
| `app.py` | Streamlit web interface |
| `cli.py` | Command-line interface |

### 4.2 Dependencies

- **GeoPandas**: Geospatial data manipulation
- **Shapely**: Geometric operations and spatial predicates
- **Rasterio**: DEM GeoTIFF reading
- **Folium/Streamlit-Folium**: Interactive mapping
- **Pandas/NumPy**: Tabular data processing
- **Rtree**: Spatial indexing (STRtree)
- **PyOGRIO**: Vector file I/O
- **Pytest**: Unit testing

---

## 5. Functional Requirements

### 5.1 Data Processing Workflow

1. **Input Validation**
   - Verify file accessibility and format compatibility
   - Check for required geometry and ID columns
   - Validate coordinate reference systems

2. **Coordinate Transformation**
   - Reproject to UTM zone for accurate distance calculations
   - Maintain CRS throughout analysis

3. **Elevation Data Resolution**
   - Use provided elevation fields if present
   - Sample DEM if fields missing and DEM provided
   - Log warnings for missing elevation data

4. **Spatial Matching**
   - Build STRtree index on segments
   - Iterate through points, finding candidates within radius
   - Compute precise perpendicular distances

5. **Elevation Filtering**
   - Validate point elevation within segment range ± tolerance
   - Flag elevation pass/fail status in results

6. **Output Generation**
   - Full candidates list (all matches within distance)
   - Best matches (top-N or single best per point)
   - CSV export with distance and elevation metrics

### 5.2 Output Format

**Candidates Output**:
- `station_id`: Point identifier
- `segment_id`: Line identifier
- `distance_m`: Perpendicular distance in meters
- `elev_pass`: Boolean elevation validation result
- Additional attributes from input files as needed

**Best Matches Output**:
- Single row per point (or top-N variants)
- Same columns as candidates with ranking

---

## 6. Non-Functional Requirements

### 6.1 Performance

- Handle datasets with 1,000+ points and 10,000+ segments efficiently
- Spatial indexing for O(log n) candidate lookup
- Elevation sampling batched for large segments

### 6.2 Usability

- Streamlit app responsive and intuitive
- Clear error messages for invalid inputs
- Parameter tooltips and sensible defaults
- Progress indicators for long-running operations

### 6.3 Reliability

- Robust error handling for malformed geometry
- Graceful degradation when optional data missing
- Unit test coverage for core matching logic
- Input validation at multiple stages

### 6.4 Compatibility

- Cross-platform support (Windows, macOS, Linux)
- Support for different shapefile encodings and CRS
- Compatible with corporate network environments (SSL flag for package installation)

---

## 7. Acceptance Criteria

### 7.1 Core Matching Logic
- [ ] Correctly identify all line segments within specified distance threshold
- [ ] Accurately compute perpendicular distances in UTM coordinates
- [ ] Elevation validation passes when point is within segment range ± tolerance
- [ ] Elevation validation fails when point exceeds threshold
- [ ] Results consistent across multiple runs

### 7.2 Web Interface
- [ ] File uploads accepted for CSV, Shapefile, GeoJSON, GeoPackage
- [ ] Zipped Shapefile upload/extraction works correctly
- [ ] Parameter adjustments update results in real-time (or with minimal latency)
- [ ] Map visualization displays point-segment pairs
- [ ] CSV downloads include all required columns with correct data

### 7.3 CLI Interface
- [ ] All command-line arguments parsed correctly
- [ ] Output files generated with expected structure
- [ ] Batch processing completes without manual intervention
- [ ] Custom ID field names respected in output

### 7.4 Data Format Support
- [ ] Shapefile (.shp) input/output with multiple geometry types
- [ ] GeoJSON read and parse correctly
- [ ] CSV with lat/lon columns automatically detected and projected
- [ ] DEM GeoTIFF elevation sampling accurate to ±reasonable error

### 7.5 Filtering & Customization
- [ ] Segment filter expressions (e.g., `STRUCTURE == 'OH'`) filter correctly
- [ ] HFRA boundary intersection removes out-of-area segments
- [ ] Custom ID column names propagated through results

---

## 8. Success Metrics

- **Accuracy**: Match results validated against known associations (if available)
- **Performance**: Processing time <30 seconds for 1,000 points × 10,000 segments
- **Adoption**: User feedback on Streamlit interface usability
- **Reliability**: Zero data loss or corruption in output files
- **Maintainability**: Code test coverage >80% for core modules

---

## 9. Future Enhancements

- **Advanced Ranking**: Multi-criteria scoring (distance, elevation, attributes)
- **Batch Scheduling**: Background job processing for very large datasets
- **API Layer**: RESTful interface for integration with other systems
- **Reporting**: Auto-generated analysis reports with visualization
- **Caching**: Memoization of elevation sampling for repeated analysis
- **Database Export**: Direct output to PostGIS or enterprise geodatabases
- **Uncertainty Quantification**: Confidence scores for matches based on data quality
- **Network Analysis**: Consider connectivity and flow direction in segment assignment

---

## 10. Appendix: Configuration Examples

### 10.1 Weather Station to Overhead Segments
```bash
python cli.py \
  --stations weather_stations.shp \
  --segments distribution_network.shp \
  --oh-filter-expr "STRUCTURE == 'OH'" \
  --distance-miles 0.25 \
  --elev-tol-ft 300.0 \
  --dem dem_data.tif \
  --out-best weather_assigned.csv
```

### 10.2 Streamlit App Workflow
1. Open `streamlit run app_streamlit/app.py`
2. Upload stations CSV and segments Shapefile
3. Set distance = 0.5 miles, elevation tolerance = 500 ft
4. Apply filter: `STRUCTURE == 'OH'`
5. Review map and download results

---

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Owner**: Development Team
