# TerraScope Mars — Jezero Explorer

## Assumptions and scope
This update implements Bunny's proposed 3D Mars exploration experience with mock data. The default screen is Mars; the prior Earth prototype remains at `/earth.html` with its original documentation in EARTH_README.md. No real Mars data, satellite imagery, or authoritative safety model is connected.

- A synthetic Jezero-inspired 50 × 50 km terrain, not a geographically accurate reconstruction.
- 65 × 65 vertices and 8,192 triangles. Fixed seed: 20261110.
- 8 fictional sites: 2 habitat candidates, 3 resource hubs, 3 science targets.
- Habitat candidates assume sealed, shielded installations; no naturally habitable Mars regions are claimed.
- Local X/Z coordinates and arbitrary model elevation in kilometers; these are not latitude/longitude or Mars-datum heights.

## Run on Windows, macOS or Linux
Install Node.js 22 LTS and npm. From the project directory:

```sh
npm install && npm run dev
```
Vite prints the actual preview URL, normally http://localhost:5173. Files hot-reload. On Windows PowerShell 5 run the two commands separately. Ctrl+C stops the server. `npm run build` produces both Mars and Earth static pages in `dist/`.

```sh
npm test
node scripts/generate-mars.js
npm run build
```
The Mars fixture is committed at `data/mock/mars.json`; the generator replaces it reproducibly. The original Earth generator and data remain separate.

## Interactions
- Drag or use arrow keys on the focused canvas to orbit and tilt. Scroll or use +/− buttons to zoom.
- Reset camera, overhead view, orbit tour, vertical exaggeration slider, and contour toggle.
- Toggle LIFELINE to color the actual terrain faces by mock margin.
- Filter site categories and select sites from the mesh or accessible sidebar.
- Click terrain to inspect the nearest projected grid sample; selection is approximate in this prototype.
- Select a destination, plan a weighted route from Aurora base, and replay its progression on the mesh.
- Mission notes explain the formula and data limitations.

## LIFELINE demonstration model
`margin = clamp(100 − 2 × slope_degrees − 0.32 × mock_dust_index − 1.1 × base_distance_km, 0, 100)`

Thresholds: Favorable ≥65; Caution 40–64; Critical <40. Coefficients and thresholds are illustrative, not validated. Radiation, life support, temperature, communications, equipment failures, supplies and many other relevant hazards are excluded. Do not use for mission decisions.

## Routing and rendering
Dijkstra on a 4-neighbor graph uses 3D segment length, the minimum margin of each edge, and elevation change. Critical cells carry a penalty rather than being impassable. The result warns if a route crosses critical or caution terrain. No travel time is claimed. Endpoints snap to the nearest grid node, so base-distance values can show small offsets.

The renderer projects actual X/Y/Z mesh vertices through a perspective camera into Canvas and sorts triangles by depth. It needs no WebGL, external assets, or tiles for Mars. This is a lightweight CPU-rendered mesh, not Google Earth, photogrammetry, or a high-fidelity scientific renderer. Labels and route lines are drawn as readable annotations above the surface; they do not have full terrain occlusion. No VR is implemented for Mars.

## Code
- `src/mars/model.js`: seed generation, illustrative score, graph routing.
- `src/mars/renderer.js`: perspective mesh, orbit/zoom, contours, markers and animated route.
- `src/mars/style.css`: responsive mission interface.
- `src/main.js`: Mars interface and state.
- `src/earth-main.js`, `earth.html`: previous Earth explorer.
- `src/algorithms/dijkstra.js`: shared heap-based pathfinding.
- `scripts/generate-mars.js`, `data/mock/mars.json`: reproducible fixture.
- `tests/mars.test.js`: reproducibility, bounds, route connectivity, score thresholds.
- `tests/dijkstra.test.js`: original four pathfinding cases.

## Future real-data integration
Replace the synthetic mesh with a georeferenced DEM; connect verified imagery, geology and mineral estimates; build and validate the safety model with domain experts; add barriers, uncertainty, engineering constraints and operational budgets. Keep provenance and confidence visible for every layer.

## Globe-first redesign
The current default interface replaces the terrain slab and permanent dashboards with a ray-cast spherical Mars globe, zoom/pan, search, place cards, compact layers and directions. Select Jezero to zoom to the synthetic crater, or a named place to open its card. Detailed text is behind Details and the mock-data information button. The globe texture is procedural, not satellite imagery. Close-up rendering is shaded surface texture on the sphere; terrain relief is visual shading rather than displaced geometry. The former mesh renderer remains in source only. The approximate Jezero anchor is used for navigation, not authoritative georeferencing. Seven data/routing tests remain available; browser checks cover globe navigation, search and directions.
