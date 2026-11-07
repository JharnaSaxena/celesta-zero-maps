# Jezero map data

- `perseverance-track.json`: rover positions and recorded elevations from the NASA Mars 2020 PLACES Bundle, Release 16 (through Sol 1896; source record retrieved November 2026). Coordinates are planetocentric latitude and east longitude. [PDS bundle](https://pds-geosciences.wustl.edu/missions/mars2020/places.htm).
- `jezero-geology.json`: representative locations and interpretations transcribed from Table 2 of the Mars 2020 Science Team photogeologic map. They are point anchors only; the app does not draw unit boundaries or imply exact mineral detections. [Map paper and GIS supplement](https://pmc.ncbi.nlm.nih.gov/articles/PMC7116714/).
- The raster base is the NASA Trek WMTS MRO CTX controlled Jezero mosaic, approximately 6 m/pixel where available. Tile requests are made directly to NASA Trek. [NASA Trek map services](https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars).

EVA margin, slope, route cost, and contour overlays remain a demonstration model on procedural terrain; they are not mission-grade safety or elevation products. The map's geographic imagery and sourced point layers are separate from that illustrative model.
