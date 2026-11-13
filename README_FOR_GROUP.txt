========================================================================
  TERRASCOPE MARS — JEZERO CRATER FULL-STACK MISSION OPERATIONS
========================================================================

Hi Team! Here is the complete full-stack application for Jezero Crater & TerraScope.
The backend and frontend are now combined into ONE SINGLE SERVER on port 5000!

------------------------------------------------------------------------
HOW TO RUN ON LOCALHOST (1 SINGLE SERVER FOR EVERYTHING):
------------------------------------------------------------------------
Option A (Easiest - 1 Click on Windows):
  Double-click "start_all.bat".
  -> It starts the server and automatically opens http://localhost:5000 in your browser!

Option B (From Terminal / Command Prompt):
  python run_backend.py
  -> Then open your browser to: http://localhost:5000

------------------------------------------------------------------------
WHAT YOU GET ON HTTP://LOCALHOST:5000:
------------------------------------------------------------------------
1. http://localhost:5000
   -> The complete 3D Mars Jezero Crater Explorer!
      - Interactive 3D Mars orbital globe (drag to rotate, scroll to zoom)
      - Jezero Crater 3D terrain planner
      - Perseverance Rover Mastcam-Z 360° panorama viewer (Click the ◎ button)
      - Real-time Mars Sol clock, LMST solar time, and temperature badge
      - Directions & Pathfinding computed live by the backend
      - Candidate site intelligence with LIFELINE safety margins

2. http://localhost:5000/earth.html
   -> The Earth Field Explorer prototype (Nandi Hills terrain & danger zones).

3. http://localhost:5000/docs
   -> Interactive Swagger API Documentation Portal
      - Live API testing console for all endpoints
      - Perseverance rover telemetry & MOXIE oxygen generation counter
      - MEDA weather data & 7-Sol forecasts
      - Mars Sample Return tube cache

4. http://localhost:5000/api/health
   -> System health check and current Mars Sol counter.

------------------------------------------------------------------------
HOW TO RUN TESTS:
------------------------------------------------------------------------
python -m pytest tests/test_backend.py -v
(All 10 tests verify health, terrain, routing, lifeline, weather, telemetry, and database)

Enjoy exploring Jezero Crater!
========================================================================
