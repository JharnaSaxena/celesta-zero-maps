# Zero Maps

Zero Maps is an experimental Mars exploration and EVA planning interface centered on Jezero Crater. The current terrain, mineral overlays, route costs, and EVA resource margins are illustrative and are not safety guidance.

## Run locally

Requires Node.js 22.13 or newer and a PostgreSQL database URL.

```powershell
npm ci
npm start
```

Set `DATABASE_URL` to your PostgreSQL connection string, then open http://localhost:3000. The Express app serves the planner, Celesta/About page, and API from the same origin. For development, use `npm run dev`.

## Backend features

- Email and password accounts, password hashing with scrypt, and secure cookie sessions.
- Revisioned workspace sync for routes, field notes, map view, layers, and planner settings.
- Optional device location for Earth-side mission context; location is rounded to two decimals and only saved when the user opts in. It never changes Mars coordinates.
- Saved EVA briefing records and account data export/deletion.
- Live approximate Earth–Mars distance/light-time and Jezero local solar time endpoints.
- Celesta/About content served from `server/data/team.json`, plus a contact form stored in PostgreSQL.
- Helmet security headers, same-origin write protection, and API rate limits.

## Data and deployment

The PostgreSQL schema is created idempotently at server startup. Set `DATABASE_URL` (or `POSTGRES_URL`) to the pooled connection string from Neon or another Postgres provider. Never commit database credentials; `.env` is ignored by Git.

The project is configured for Vercel's Express deployment and Neon Postgres integration. The deployed project can be updated directly in Vercel; a GitHub connection is not required for direct deployments. The frontend lives in `public/` for Vercel's static asset serving; the server serves those same files for local development. Set `NODE_ENV=production` in Vercel so session cookies are Secure.

## Project files

- `public/` — Vercel-served planner frontend, About page, and cloud-sync client.
- `outputs/` — preserved frontend source and earlier working copy.
- `server/` — Express API, authentication/session handling, PostgreSQL schema, and Mars calculations.
- `server/data/team.json` — Celesta/project text, credits, and disclosures. Add real team member details before publishing; none were provided in the supplied archive.
- `test/smoke.mjs` — API smoke test; set `TEST_DATABASE_URL` to an isolated PostgreSQL database before running `npm test`.

## Before publishing

Review the Celesta description, add team names/bios, verify scientific citations, and update disclosures to reflect the team's actual work and AI assistance. The app is a prototype; do not present model outputs as flight-safety recommendations.

## Jezero map data

The map background streams NASA Trek MRO CTX Jezero mosaic tiles. Sourced data layers include the NASA Mars 2020 PLACES rover traverse (Release 16, through Sol 1896) and representative unit locations from the Mars 2020 Science Team photogeologic map. They are documented in [public/data/README.md](public/data/README.md). Geology markers are representative points, not polygon boundaries. The EVA margin, slope, and contour analysis remains an illustrative model and should not be used for real mission planning.

### ISS pass tracking

The Night Sky scene can request browser geolocation after the user presses “Set observer location.” The Express endpoint `/api/satellites/iss?lat=…&lon=…` obtains current ISS GP/TLE elements from CelesTrak, caches the element set in memory for 15 minutes, propagates the orbit with `satellite.js` SGP4, and estimates upcoming passes above 10° elevation for the next 48 hours. Pass results are shared only with the requesting browser and are not saved to the workspace. CelesTrak outages use the last in-memory element set when available; otherwise the endpoint returns 503.

Pass timing is approximate and not suitable for operational tracking or safety decisions. TLE/GP elements are predictions and their accuracy degrades as they age. The live ISS layer is hidden while the Time Machine date is shifted away from “Now.”


### Earth observer and Solar System view

The Earth scene retains the browser's reported latitude and longitude to six decimal places and displays the geolocation accuracy radius the browser reports. The point is centered on the globe for visibility. It remains in memory unless the user checks the save-location option; the ISS pass request sends coordinates to the Zero Maps API for that prediction. The Solar System scene plots Sun-centered positions and orbital paths from JPL's approximate planetary elements, with the existing date control changing the ephemeris date. Planet size is exaggerated; orbital distance is scaled.
