# TerraScope — interactive terrain explorer

## Assumptions
- Study area: a roughly 11 × 11 km rectangle near Nandi Hills, Karnataka. Its data is entirely synthetic and is not an assessment of this location.
- No backend, API keys, geolocation, or real environmental data. Fixed seed: 20261104.
- Street and satellite basemaps are real external imagery, as requested; internet is required for those tiles and the optional Google font. Terrain mode and every analytical dataset work locally after installation.
- Routes follow a four-neighbor mock terrain grid, not roads. Risk is a soft penalty; routes can cross a hazard when necessary. Endpoints snap to the nearest grid node. Outside-area selections are rejected.
- Terrain is the locally generated elevation raster. 3D height is exaggerated; VR is an informational integration placeholder.

## Setup — Windows, macOS, Linux
Install Node.js 22 LTS with npm, then extract this project. In Windows PowerShell/Terminal, macOS Terminal, or a Linux shell, change to the extracted folder:

```sh
cd terrascope
npm install && npm run dev
```

For Windows PowerShell 5 (which does not accept `&&`), run `npm install` then `npm run dev` on separate lines. Vite prints the actual local URL in your terminal, normally **http://localhost:5173**. Open it in your browser. If 5173 is busy, use the next port printed by Vite. Saves hot-reload automatically. Stop with Ctrl+C. On a tablet on the same LAN, use the Network URL printed by Vite; permit the local development server through your firewall if required.

```sh
npm test       # Vitest, four pathfinding cases
npm run build # production static output in dist/
npm run generate # regenerate all four deterministic JSON files
```

## How to test
1. Pan/zoom and switch Street, Satellite, Terrain. Use the target button to fit the study area.
2. Click a point inside the dashed area: environmental metrics update from the nearest mock cell.
3. Toggle elevation, minerals, and danger layers. Click a diamond or danger polygon for details.
4. Choose Start Point, click the map, choose Destination, click again, then Calculate Route. Or click “Try a sample expedition”.
5. Toggle danger preference to recompute, inspect distance/time/exposure, and animate the route. Reset clears endpoints and animation.
6. Open 3D terrain and orbit/zoom; the computed path appears over the same grid. Close with × or Escape. VR explains the future integration point.

## Routing model
Dijkstra minimizes `horizontal meters + 8 × absolute elevation change + horizontal meters × risk`. Risk is 0/2/8/30 for none/Low/Medium/High, sampled at both edge endpoints and its midpoint. Danger preference removes only the risk term when disabled. Grid routing is an approximation: small future polygons could be missed by sampling, so production needs segment/polygon intersection and explicit impassable cells. Distance uses haversine; estimated walking time is distance at 4 km/h plus one hour per 600 m ascent. It does not model surface, fatigue, weather, or road access.

Dijkstra uses a binary heap: O((V+E) log V) time, O(V+E) space. Grid creation takes O(V Z P) for Z polygons averaging P vertices; space O(V+E). Algorithm source includes comments. Tests cover simple shortest path, avoidance on an actual risk-weighted grid, unreachable target, and identical endpoints.

## Mock versus future integrations
| Feature | Prototype | Production source/integration |
|---|---|---|
| Street / satellite | OSM / Esri live basemap tiles | Respect provider attribution, licensing, usage limits and caching policies |
| Elevation | Seeded 50 × 50 grid | DEM such as SRTM or Copernicus with vertical datum metadata |
| Environment | 25 seeded cells, nearest-cell lookup | Weather and air-quality observations with timestamps |
| Minerals | 10 synthetic sites, compositions total 100% | Verified geological surveys and sampling uncertainty |
| Hazards | 5 synthetic polygons | Authoritative alerts, closures, validity periods |
| Routing | Weighted grid | Traversable network, barriers, slope limits and calibrated travel times |
| 3D / VR | Working Three.js orbit view / VR note | WebXR headset session, controller navigation and accessibility |

No analytics or user data leaves the application; external tiles/fonts receive ordinary resource requests. This is a demonstration and is not suitable for navigation or safety decisions.

## File tree
```
terrascope/
├── index.html
├── package.json
├── vite.config.js
├── package-lock.json
├── README.md
├── .gitignore
├── .openai/hosting.json
├── scripts/generate-data.js
├── data/mock/
│   ├── elevation.json
│   ├── minerals.json
│   ├── dangerZones.json
│   └── environment.json
├── src/
│   ├── main.js
│   ├── components/
│   │   ├── MapView.js
│   │   ├── LayerSwitcher.js
│   │   ├── InfoPanel.js
│   │   ├── RoutePanel.js
│   │   └── View3D.js
│   ├── algorithms/
│   │   ├── dijkstra.js
│   │   └── graph.js
│   ├── data/loaders.js
│   └── styles/main.css
└── tests/dijkstra.test.js
```
All source and data are included in full. Vite bundles imported JSON, so no backend or public API is required. The optional 3D code loads only when opened. `.openai/hosting.json` is hosting metadata and is not needed for local execution.
