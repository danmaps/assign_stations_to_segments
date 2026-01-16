# Product Requirements Document: Points-to-Lines Assignment Tool
## Alternative: React + Node.js + Leaflet/ESRI

---

## 1. Executive Summary

The **Points-to-Lines Assignment Tool** is a full-stack geospatial web application designed to identify and match points (e.g., weather stations, utility assets) to their closest linear features (e.g., distribution segments, roads) based on spatial distance and elevation constraints. Built with React frontend and Node.js backend, this modern architecture enables seamless user experience with real-time visualization and scalable server-side processing.

---

## 2. Product Overview

### 2.1 Purpose

Enable users to efficiently assign points to line segments with configurable spatial and elevation-based matching rules through an intuitive web interface, facilitating operations planning and asset management in utility, transportation, and environmental domains.

### 2.2 Key Use Cases

- **Utility Distribution**: Assign weather stations to overhead distribution segments for weather impact analysis
- **Asset Inventory**: Match field assets to network segments for maintenance planning
- **Environmental Monitoring**: Correlate monitoring stations with transportation corridors
- **Infrastructure Planning**: Support site selection and resource allocation decisions

---

## 3. Core Features

### 3.1 Point-to-Line Matching Engine

**Requirement**: Identify all candidate line segments within a configurable distance threshold for each input point.

- **Spatial Search**: Employ efficient spatial indexing (Turf.js, RBush) to find line segments within user-defined search radius (default: 0.5 miles)
- **Distance Calculation**: Compute perpendicular distance from point to line segment in projected coordinates (UTM via proj4js)
- **One-to-Many Matching**: Support multiple candidates per point with ranked distance metrics
- **Best Match Selection**: Automatically select top-N candidates or single best match based on user preference

### 3.2 Elevation Validation

**Requirement**: Filter matches based on elevation compatibility between points and line segments.

- **Point Elevation**: Extract or ingest point elevation data (feet)
- **Segment Elevation Range**: Compute minimum and maximum elevation along line segments
- **Elevation Tolerance**: Apply user-configurable tolerance (default: 500 feet) to validate matches
- **DEM Integration**: Optional Digital Elevation Model (GeoTIFF) support via backend for computing missing elevation data
- **Graceful Degradation**: Skip elevation checks if DEM unavailable and fields missing

### 3.3 Data Input & Format Support

**Requirement**: Accept multiple geospatial data formats and sources.

**Supported Input Formats**:
- Vector Files: Shapefile (via ZIP), GeoJSON, GeoPackage
- Tabular Data: CSV (with lat/lon columns)
- Remote Sources: ArcGIS Feature Service URLs, WFS endpoints

**Data Requirements**:
- Points: geometry, required ID field, optional elevation field
- Lines: geometry, required ID field, optional elevation range fields, optional filter attributes

### 3.4 Configurable Filtering

**Requirement**: Support attribute-based filtering to refine input datasets.

- **Segment Filtering**: Query expression syntax (e.g., `STRUCTURE == 'OH'`) to pre-filter segments
- **HFRA Boundary Filtering**: Restrict segments to High Fire Risk Area polygons
- **Custom ID Fields**: Support non-standard column names for point/segment identifiers

### 3.5 Interactive Web Interface

**Requirement**: Provide user-friendly React application with rich geospatial visualization.

**Frontend Capabilities**:
- Responsive web application (desktop, tablet, mobile support)
- File upload interface for points and lines (drag-and-drop support)
- Configurable parameter controls:
  - Search distance (miles)
  - Elevation tolerance (feet)
  - Filter expressions
  - DEM file upload
- Interactive map with Leaflet/ESRI integration
- Real-time visualization of matches with color-coded layers
- Data preview tables for input and output (sortable, filterable)
- CSV and GeoJSON export functionality
- Progress indicators and loading states
- Result statistics dashboard (match counts, distance ranges, elevation validation rates)

### 3.6 REST API Backend

**Requirement**: Enable programmatic access and support frontend processing requests.

**Core Endpoints**:
- `POST /api/upload` - Receive and validate geospatial files
- `POST /api/process/match` - Execute point-to-line matching
- `POST /api/process/candidates` - Generate full candidate list
- `POST /api/process/best-matches` - Generate best match results
- `POST /api/elevation/sample` - Extract elevation from DEM
- `GET /api/results/:id` - Retrieve cached results
- `POST /api/export/:format` - Export results in requested format

**Request/Response Format**: JSON with GeoJSON geometry support

---

## 4. Technical Architecture

### 4.1 Frontend Stack

| Technology | Purpose |
|-----------|---------|
| **React 18+** | UI framework with hooks and functional components |
| **TypeScript** | Type safety and developer experience |
| **Leaflet 1.9+** | Core mapping library |
| **ESRI Leaflet** | ArcGIS services integration (optional WMS/WFS layers) |
| **Turf.js** | Client-side geospatial analysis and calculations |
| **proj4js** | Coordinate system transformations |
| **Vite** | Build tool and dev server |
| **React Query** | Server state management and data fetching |
| **Redux Toolkit** | Client state management (if needed) |
| **Tailwind CSS** | Styling and responsive design |
| **React Hot Toast** | User notifications |
| **AG Grid Community** | Data table visualization |

### 4.2 Backend Stack

| Technology | Purpose |
|-----------|---------|
| **Node.js 18+** | Runtime environment |
| **Express.js** | Web framework |
| **TypeScript** | Type safety |
| **Turf.js** | Server-side geospatial analysis |
| **GeoTIFF** (geotiff.js) | DEM reading and sampling |
| **Mapbox GL JS Utils** / **turf** | Spatial indexing and distance calculations |
| **RBush** | Efficient spatial indexing |
| **proj4js** | Coordinate transformations |
| **Multer** | File upload handling |
| **Shapefile** (shapefile.js) | Shapefile parsing |
| **GDAL.js** (optional) | Advanced geospatial operations |
| **Jest** | Unit testing |
| **Supertest** | API testing |

### 4.3 Deployment Architecture

**Frontend**:
- Static build artifacts served via CDN or static web server
- Client-side bundling with Vite (tree-shaking, code splitting)
- Optional service worker for offline support

**Backend**:
- Node.js Express server deployed on:
  - Docker container (recommended)
  - AWS Lambda / Azure Functions (serverless option)
  - Traditional VM/server with PM2 process manager
- Horizontal scaling via load balancer
- File storage: Temporary disk cache or cloud storage (S3/Azure Blob)

**Database** (optional for result persistence):
- PostgreSQL with PostGIS extension
- MongoDB with Geospatial indexes

---

## 5. Functional Requirements

### 5.1 Frontend Workflow

1. **File Upload**
   - Drag-and-drop or file picker for points and lines
   - Multi-file upload support for Shapefile ZIPs
   - Real-time file validation with preview

2. **Parameter Configuration**
   - Interactive forms for search distance, elevation tolerance
   - Filter expression builder with syntax highlighting
   - DEM file upload with validation

3. **Process Initiation**
   - Submit matching job to backend API
   - Real-time progress updates via WebSocket or polling
   - Visual feedback during processing

4. **Results Visualization**
   - Interactive map with:
     - Point markers with popups
     - Line features with styling by match status
     - Match connections/arrows showing assignments
     - Color-coded layers (matched/unmatched/elevation fail)
   - Zoomable, pannable interface with layer controls
   - Result table with sorting and filtering

5. **Data Export**
   - CSV download of candidates
   - CSV download of best matches
   - GeoJSON download for further analysis
   - Shapefile download (via backend generation)

### 5.2 Backend Workflow

1. **File Reception**
   - Receive multipart form data from frontend
   - Validate file formats (ZIP, GeoJSON, CSV)
   - Parse Shapefile ZIPs using shapefile.js library
   - Validate coordinate reference systems

2. **Coordinate Transformation**
   - Detect or infer CRS from input files
   - Reproject to UTM zone for accurate distance calculations
   - Maintain original CRS for output if needed

3. **Elevation Data Resolution**
   - Use provided elevation fields if present
   - Sample DEM using geotiff.js if fields missing and DEM provided
   - Batch elevation queries for efficiency

4. **Spatial Indexing & Matching**
   - Build RBush spatial index on segments
   - Iterate through points using index for efficient candidate lookup
   - Compute precise perpendicular distances using Turf.js
   - Apply distance threshold filtering

5. **Elevation Filtering**
   - Validate point elevation within segment range ± tolerance
   - Flag elevation pass/fail status
   - Aggregate statistics

6. **Result Generation & Caching**
   - Generate full candidates list
   - Generate best matches (single or top-N per point)
   - Cache results with unique job ID
   - Format as JSON with GeoJSON geometries

### 5.3 Output Format

**Candidates Output** (JSON/GeoJSON):
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "station_id": "STN001",
        "segment_id": "SEG123",
        "distance_m": 425.3,
        "distance_miles": 0.264,
        "elev_pass": true,
        "rank": 1
      },
      "geometry": { "type": "Point", "coordinates": [...] }
    }
  ]
}
```

**Best Matches Output**: Same schema, filtered to top-N per point

---

## 6. Non-Functional Requirements

### 6.1 Performance

- **Frontend**:
  - Initial page load <3 seconds (with caching)
  - Map interaction responsiveness <100ms
  - Table rendering <1 second for 1,000 rows

- **Backend**:
  - Handle 1,000+ points and 10,000+ segments in <30 seconds
  - RBush spatial indexing for O(log n) lookups
  - Batch DEM sampling for efficiency
  - Memory usage <2GB for typical datasets
  - API response times <5 seconds for upload, <60 seconds for processing

### 6.2 Usability

- Intuitive React UI with minimal learning curve
- Responsive design supporting mobile devices (with limitations for large datasets)
- Clear error messages and input validation
- Interactive map with tooltips and legends
- Parameter preset templates for common workflows
- Undo/redo for parameter adjustments

### 6.3 Reliability

- Robust error handling for malformed geometry
- Input validation at frontend and backend
- Graceful degradation when optional data missing
- Comprehensive error logging and monitoring
- Result persistence (temporary storage minimum 24 hours)
- Automated backups for long-term result retention (optional)

### 6.4 Compatibility

- Cross-browser support (Chrome, Firefox, Safari, Edge)
- Responsive design for desktop, tablet, mobile
- Accessibility compliance (WCAG 2.1 AA)
- Support for different shapefile encodings
- CRS support for global datasets

### 6.5 Security

- HTTPS/TLS for all communications
- Input sanitization to prevent injection attacks
- File upload validation and virus scanning (optional)
- Rate limiting on API endpoints
- CORS configuration for specified domains
- Session management and optional authentication

---

## 7. Acceptance Criteria

### 7.1 Frontend Interface
- [ ] File upload accepts CSV, GeoJSON, Shapefile ZIP, GeoPackage
- [ ] Drag-and-drop functionality works smoothly
- [ ] Parameter controls update state without page reload
- [ ] Map renders with Leaflet and displays point/line layers
- [ ] Map markers and lines are interactive with popups
- [ ] Results table displays all required columns
- [ ] CSV and GeoJSON exports contain correct data
- [ ] UI is responsive on desktop, tablet, and mobile

### 7.2 Backend API
- [ ] Upload endpoint correctly parses multipart form data
- [ ] File validation rejects invalid formats
- [ ] Process endpoints return results within 60 seconds for typical datasets
- [ ] Coordinate transformations preserve accuracy
- [ ] Elevation sampling matches DEM values to expected precision
- [ ] Distance calculations match expected perpendicular distances
- [ ] Results caching works and serves cached results efficiently

### 7.3 Core Matching Logic
- [ ] Correctly identify all line segments within distance threshold
- [ ] Accurately compute perpendicular distances in UTM
- [ ] Elevation validation passes when point in range ± tolerance
- [ ] Elevation validation fails when exceeds threshold
- [ ] Results consistent across multiple runs
- [ ] Performance scales linearly with dataset size

### 7.4 Data Format Support
- [ ] Shapefile ZIP extraction and parsing correct
- [ ] GeoJSON read and parse correctly
- [ ] CSV with lat/lon auto-detected and projected
- [ ] GeoPackage read correctly
- [ ] ArcGIS service URL integration works
- [ ] Multiple CRS handling transparent to user

### 7.5 Filtering & Customization
- [ ] Filter expressions (e.g., `STRUCTURE == 'OH'`) work correctly
- [ ] HFRA boundary intersection removes out-of-area segments
- [ ] Custom ID column names propagated through results
- [ ] DEM integration optional and gracefully degrades

---

## 8. Success Metrics

- **User Adoption**: Initial beta user feedback positive (>4/5 stars)
- **Performance**: Processing time <30 seconds for 1,000 × 10,000 datasets
- **Reliability**: 99.5% API uptime
- **Accuracy**: Match results validated against ground truth (if available)
- **Accessibility**: WCAG 2.1 AA compliance achieved
- **Code Quality**: >80% test coverage for core modules
- **Load Time**: Lighthouse performance score >85

---

## 9. Development Roadmap

### Phase 1: MVP (Core Features)
- [ ] React frontend with file upload and parameters
- [ ] Leaflet map with point/line rendering
- [ ] Node.js backend with matching engine
- [ ] CSV export functionality
- [ ] Basic error handling

### Phase 2: Enhancement
- [ ] ESRI Leaflet integration for ArcGIS services
- [ ] Advanced visualization (heat maps, flow direction)
- [ ] DEM elevation sampling
- [ ] Results caching and persistence
- [ ] API documentation and Swagger/OpenAPI spec

### Phase 3: Production
- [ ] Authentication and user accounts
- [ ] Job history and saved analyses
- [ ] Batch processing queue for large datasets
- [ ] WebSocket real-time updates
- [ ] Performance optimization and load testing

---

## 10. Future Enhancements

- **Advanced Ranking**: Multi-criteria scoring (distance, elevation, attributes) with configurable weights
- **Batch Scheduling**: Background job queue for very large datasets
- **Network Analysis**: Consider segment connectivity and flow direction
- **Uncertainty Quantification**: Confidence scores based on data quality
- **Database Integration**: Direct PostGIS/enterprise geodatabase export
- **Mobile App**: React Native version for field data collection
- **Analytics Dashboard**: Aggregate statistics and reporting
- **Webhooks**: Notify external systems when jobs complete
- **Streaming Results**: Server-Sent Events (SSE) or WebSocket for large result sets
- **GraphQL API**: Alternative query interface for flexibility

---

## 11. Technology Justification

### Why React + Node.js?

**React Advantages**:
- Rich ecosystem for interactive geospatial UI
- Component reusability and maintainability
- Strong community and third-party library support
- Excellent developer experience with tools like Vite

**Node.js Advantages**:
- JavaScript across full stack (frontend and backend)
- Non-blocking I/O ideal for file processing
- Lightweight deployment footprint
- Excellent npm ecosystem for geospatial libraries

**Leaflet + ESRI Integration**:
- Leaflet: Open-source, lightweight, no licensing costs
- ESRI: Seamless ArcGIS service integration when needed
- Both are industry-standard for web mapping

---

## 12. Infrastructure & Deployment

### Development Environment
```
Frontend (port 5173):  localhost:5173
Backend (port 3000):   localhost:3000
```

### Production Deployment Options

**Option A: Docker Compose**
- Frontend: React build served by Nginx
- Backend: Node.js Express in Docker
- Single-machine or orchestrated via Docker Swarm

**Option B: Cloud Platform (AWS)**
- Frontend: S3 + CloudFront CDN
- Backend: EC2 with auto-scaling or ECS Fargate
- File storage: S3 buckets
- Optional: RDS for PostgreSQL/PostGIS

**Option C: Cloud Platform (Azure)**
- Frontend: Azure Static Web Apps
- Backend: App Service or Container Instances
- File storage: Blob Storage
- Optional: Azure Database for PostgreSQL

**Option D: Serverless (AWS Lambda)**
- Frontend: CloudFront + S3
- Backend: Lambda functions with API Gateway
- Limited to <15 minute execution time (consider async jobs)
- S3 for file storage and results

---

## 13. Appendix: Example Configuration

### 13.1 Upload Request
```bash
curl -X POST http://localhost:3000/api/process/match \
  -F "points=@stations.geojson" \
  -F "lines=@segments.shp" \
  -F "distance_miles=0.5" \
  -F "elev_tol_ft=500" \
  -F "oh_filter_expr=STRUCTURE == 'OH'"
```

### 13.2 Frontend Component Structure
```
src/
├── components/
│   ├── FileUploader.tsx
│   ├── ParameterForm.tsx
│   ├── Map.tsx
│   ├── ResultsTable.tsx
│   └── ExportButtons.tsx
├── hooks/
│   ├── useMapLayer.ts
│   ├── useMatchingAPI.ts
│   └── useResults.ts
├── services/
│   ├── api.ts
│   └── geoProcessing.ts
├── types/
│   └── index.ts
├── App.tsx
└── main.tsx
```

### 13.3 Backend Route Structure
```
src/
├── routes/
│   ├── upload.ts
│   ├── process.ts
│   └── export.ts
├── services/
│   ├── matching.ts
│   ├── elevation.ts
│   ├── fileParser.ts
│   └── crsTransform.ts
├── middleware/
│   ├── fileUpload.ts
│   ├── validation.ts
│   └── errorHandler.ts
├── types/
│   └── index.ts
└── app.ts
```

---

## 14. Dependencies Summary

### Frontend Dependencies
- react, react-dom
- typescript
- vite
- leaflet, leaflet-esri
- turf
- proj4js
- axios (or fetch)
- react-query
- tailwindcss
- ag-grid-react
- react-hot-toast

### Backend Dependencies
- express
- typescript
- multer
- turf
- geotiff
- shapefile
- rbush
- proj4js
- node-fetch
- cors
- dotenv

**Zero Python Dependencies** ✓

---

**Document Version**: 1.0 (React Alternative)  
**Last Updated**: January 2026  
**Owner**: Development Team
