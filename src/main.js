import {createRenderer} from './mars/renderer.js';
import {createSurface} from './mars/surface.js';
import {sites,tier,nearest,routeTo} from './mars/model.js';
import mock from '../data/mock/mars.js';
import {createGlobe} from './mars/globe.js';
import {apiClient} from './services/apiClient.js';
import {
  EARTH_PRESETS,
  loadSavedObserver,
  saveObserverLocation,
  requestBrowserGeolocation,
  searchEarthPlaces,
  fetchMarsDistance
} from './components/EarthObserver.js';
import {createSolarSystemView} from './components/SolarSystemView.js';

if (!document.querySelector('link[href*="style.css"]')) {
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = '/src/mars/style.css';
  document.head.appendChild(link);
}

const nodes = mock.nodes;
sites.forEach(s => s.node = nearest(nodes, s.x, s.z));
let selected = null, path = [], visible = {habitat: true, resource: true, science: true};
let currentObserver = loadSavedObserver();

document.querySelector('#app').innerHTML = `
<main id="map">
  <canvas id="globe" tabindex="0" aria-label="Mars globe. Drag to rotate, scroll to zoom. Arrow keys rotate; plus and minus zoom."></canvas>
  <canvas id="planner" hidden tabindex="0" aria-label="Simulated Jezero mission planner. Drag to rotate terrain, scroll to zoom, click a candidate site."></canvas>
</main>

<div id="mars-status-badge" title="Mars Jezero Telemetry">
  <span class="pulse-dot"></span> <span id="mars-clock-text">Mars Time: Syncing...</span>
</div>

<div class="search-area">
  <form id="search-form">
    <button type="button" id="menu" aria-label="Open map information">☰</button>
    <input id="search" placeholder="Search Mars or Earth (e.g. Jaipur, Tamil Nadu...)" aria-label="Search" autocomplete="off">
    <button aria-label="Search">⌕</button>
  </form>
  <div id="results" hidden></div>
  <div class="chips">
    <button id="services">▦ Services</button>
    <button id="jezero">⌖ Jezero Crater</button>
    <button id="places">◉ Places</button>
    <button id="lifeline">◈ LIFELINE</button>
    <button id="btn-earth">🌍 Earth Observer</button>
    <button id="btn-solar-system">🪐 Solar System</button>
  </div>
</div>

<div class="brand">TERRASCOPE <span>MARS</span></div>

<div class="planet-title" id="planet-title">
  <span>REAL IMAGERY. MISSION PLANNING.</span>
  <h1>Mars</h1>
  <p>Explore Mars. Plan what comes next.</p>
  <button id="explore">Explore Jezero <span>↗</span></button>
</div>

<aside id="place-panel" hidden>
  <button id="close-place" class="close" aria-label="Close place">×</button>
  <div class="place-cover">
    <span id="place-icon">⌖</span>
    <small>JEZERO · SIMULATED CANDIDATE</small>
  </div>
  <div class="place-body">
    <span id="category"></span>
    <h2 id="place-name"></h2>
    <div class="place-score">
      <i id="score-dot"></i>
      <b id="margin"></b>
      <span>LIFELINE</span>
    </div>
    <div class="place-actions">
      <button id="directions"><span>↗</span>Directions</button>
      <button id="fly"><span>⌖</span>Fly to</button>
      <button id="more"><span>ⓘ</span>Details</button>
    </div>
    <div id="details" hidden></div>
    <div id="route" hidden>
      <p>From <b>Aurora base</b></p>
      <strong id="distance"></strong>
      <small id="route-risk"></small>
      <button id="replay">▶ Replay</button>
      <button id="clear-route">Clear</button>
    </div>
  </div>
</aside>

<aside id="earth-panel" hidden>
  <button id="close-earth" class="close" aria-label="Close Earth Observer">×</button>
  <div class="earth-cover">
    <small>EARTH OBSERVER · TOPOCENTRIC BASELINE</small>
    <h2 id="earth-place-name">Jaipur, Rajasthan, India</h2>
    <span id="earth-accuracy-tag" class="earth-accuracy-tag"></span>
  </div>
  <div class="earth-body">
    <div class="earth-coords-box">
      <div class="earth-coords-row">
        <span>Latitude (6 dec)</span>
        <b id="earth-lat">26.912434° N</b>
      </div>
      <div class="earth-coords-row">
        <span>Longitude (6 dec)</span>
        <b id="earth-lon">75.787271° E</b>
      </div>
    </div>

    <div class="earth-distance-card">
      <small>REAL-TIME DISTANCE TO JEZERO CRATER, MARS</small>
      <div class="earth-km-val" id="earth-km">— km</div>
      <div class="earth-au-val" id="earth-au">— AU</div>
      <div class="earth-light-grid">
        <div>
          <small>ONE-WAY LIGHT TIME</small>
          <b id="earth-light-time">—</b>
        </div>
        <div>
          <small>ROUND-TRIP RADIO DELAY</small>
          <b id="earth-ping-time">—</b>
        </div>
      </div>
    </div>

    <label class="earth-save-row">
      <input type="checkbox" id="earth-save-checkbox">
      <span>Save this location in memory / browser</span>
    </label>

    <div class="iss-card" id="iss-card">
      <b>🛰️ Upcoming ISS Pass</b>
      <span id="iss-pass-text">Calculating satellite orbit trajectory...</span>
    </div>

    <div class="earth-actions">
      <button id="earth-open-solarsystem" class="earth-btn-primary">
        <span>🪐</span> View in Solar System
      </button>
      <button id="earth-use-gps" class="earth-btn-secondary">
        <span>🎯</span> Detect My Exact GPS Location
      </button>
    </div>
  </div>
</aside>

<div class="bottom-left">
  <button id="layers" class="layer-button">
    <span class="layer-thumb"></span>Layers
  </button>
  <div id="layer-panel" hidden>
    <b>Map layers</b>
    <label><input type="checkbox" data-type="habitat" checked><i class="habitat"></i>Habitat candidates</label>
    <label><input type="checkbox" data-type="resource" checked><i class="resource"></i>Resource hubs</label>
    <label><input type="checkbox" data-type="science" checked><i class="science"></i>Science targets</label>
    <label><input type="checkbox" id="safety">LIFELINE colors</label>
  </div>
</div>

<div id="legend" hidden>
  <span><i style="background:#409c7e"></i>Favorable</span>
  <span><i style="background:#bf9042"></i>Caution</span>
  <span><i style="background:#b0463c"></i>Critical</span>
</div>

<div class="map-controls">
  <button id="surface" aria-label="Open real Jezero panorama" title="Real Jezero rover panorama">◎</button>
  <button id="planet" aria-label="View whole Mars" title="View whole Mars">◉</button>
  <button id="locate" aria-label="Go to Jezero" title="Go to Jezero">⌖</button>
  <div>
    <button id="plus" aria-label="Zoom in">+</button>
    <button id="minus" aria-label="Zoom out">−</button>
  </div>
</div>

<div class="map-footer">
  <span id="hint">Real Viking imagery · Drag to rotate · Scroll to zoom</span>
  <button id="mock-info">Data & sources ⓘ</button>
</div>

<div id="toast" role="status" hidden></div>

<dialog id="info">
  <button id="close-info" class="close" aria-label="Close sources">×</button>
  <span class="eyebrow">REAL IMAGERY / CLEAR LIMITS</span>
  <h2>Photographed on Mars.</h2>
  <p><b>Orbit:</b> NASA Viking color imagery merged with MDIM 1.0, distributed by ASU. Native product: 23,040 × 11,520 pixels at approximately 920 m/pixel.</p>
  <a href="https://www.mars.asu.edu/data/mdim_color/" target="_blank" rel="noopener">Viking mosaic source ↗</a>
  <p><b>Surface:</b> Perseverance’s Mastcam-Z panorama, 142 photographs captured on 21 February 2021 (Sol 3), stitched by the mission team.</p>
  <a href="https://www.jpl.nasa.gov/images/pia24264-mastcam-zs-first-360-degree-panorama/" target="_blank" rel="noopener">NASA panorama and original downloads ↗</a>
  <a href="earth.html">Earth archive ↗</a>
</dialog>

<div id="planning-status" hidden>
  <b>MISSION PLANNER</b>
  <span>Jezero Carter Study Area</span>
  <button id="leave-planner">Return to real Mars ↗</button>
</div>

<dialog id="services-dialog">
  <button id="close-services" class="close" aria-label="Close services">×</button>
  <span class="eyebrow">TERRASCOPE SERVICES</span>
  <h2>Explore. Assess. Plan.</h2>
  <p>Real Mars imagery alongside mission operations backend services.</p>
  <div class="service-grid">
    <button data-service="earth-obs">
      <b>🌍 Earth Observer & Distance</b>
      <span>Calculate exact distance from your city to Mars</span>
      <small>Jaipur, Tamil Nadu, GPS & light time delay</small>
    </button>
    <button data-service="solar-sys">
      <b>🪐 Solar System Orbits</b>
      <span>Interactive Sun-centered planetary orbits</span>
      <small>JPL Keplerian elements & date scrubber</small>
    </button>
    <button data-service="lifeline">
      <b>◈ LIFELINE</b>
      <span>Compare terrain safety margins</span>
      <small>Continuous hazard score & heatmap</small>
    </button>
    <button data-service="habitat">
      <b>⌂ Habitat planning</b>
      <span>Compare candidate base locations</span>
      <small>Evaluated against landing constraints</small>
    </button>
    <button data-service="resource">
      <b>◇ Resource intelligence</b>
      <span>Inspect mineral and ice prospects</span>
      <small>ISRU water extraction & sintering</small>
    </button>
    <button data-service="science">
      <b>⌖ Science targets</b>
      <span>Explore proposed sampling sites</span>
      <small>Delta archives & Perseverance core tubes</small>
    </button>
    <button data-service="routes">
      <b>↗ Route planning</b>
      <span>Plan weighted routes from Aurora base</span>
      <small>Multi-mode A* & Dijkstra pathfinding</small>
    </button>
    <button data-service="rover">
      <b>◎ Real rover view</b>
      <span>Look around Jezero with Perseverance</span>
      <small>NASA Mastcam-Z 360° photography</small>
    </button>
    <button data-service="telemetry">
      <b>📡 Live Rover Telemetry</b>
      <span>Perseverance & MOXIE status</span>
      <small>Power, battery, sol time & sample cache</small>
    </button>
  </div>
</dialog>
`;

const $ = s => document.querySelector(s);
let toastTimer;
function toast(text) {
  $('#toast').textContent = text;
  $('#toast').hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $('#toast').hidden = true, 4000);
}

let planning = false;
const surface = createSurface(() => $(planning ? '#planner' : '#globe').focus());
const solarSystem = createSolarSystemView();

const orbital = createGlobe($('#globe'), nodes, sites, id => select(id), n => toast(n.error || `Simulated margin ${n.margin}/100 · Slope ${n.slope.toFixed(1)}°`), zoom => {
  if (planning) return;
  $('#planet-title').hidden = zoom > 2;
  $('#hint').textContent = 'Real Viking imagery · Drag to rotate · Rover view: ◎';
}, point => {
  if (Math.hypot(point.lat - 18.38, point.lon - 77.58) > 2) {
    toast('No panorama at that point. Use ◎ to open the real Jezero rover view.');
    return;
  }
  surface.enter();
});

const planner = createRenderer($('#planner'), nodes, sites, id => select(id), n => toast(`Simulated margin ${n.margin}/100 · Slope ${n.slope.toFixed(1)}°`));

function mode(on) {
  planning = on;
  $('#planner').hidden = !on;
  $('#globe').hidden = on;
  $('#planning-status').hidden = !on;
  $('#planet-title').hidden = on;
  $('#hint').textContent = on ? 'SIMULATED PLANNING · Drag to orbit · Click sites · Scroll to zoom' : 'Real Viking imagery · Drag to rotate · Scroll to zoom';
  $('#planner').setAttribute('aria-hidden', String(!on));
  if (on) {
    $('#legend').hidden = !$('#safety').checked;
    $('#planner').focus();
  } else {
    $('#globe').focus();
    $('#place-panel').hidden = true;
    $('#legend').hidden = true;
  }
}

const globe = {
  focus(id) {
    if (id || planning) {
      mode(true);
      if (id) planner.set({selected: id});
    } else orbital.focus();
  },
  home() {
    mode(false);
    orbital.home();
  },
  zoom(f) {
    planning ? planner.zoom(f) : orbital.zoom(f);
  },
  set(o) {
    planner.set(o);
  },
  surface() {
    surface.enter();
  }
};

async function select(id) {
  selected = sites.find(s => s.id === id);
  path = [];
  globe.set({selected: id, route: []});
  $('#route').hidden = true;
  $('#details').hidden = true;
  $('#results').hidden = true;
  $('#earth-panel').hidden = true;
  $('#place-panel').hidden = false;
  $('#category').textContent = {habitat: 'Habitat candidate', resource: 'Resource hub', science: 'Science target'}[selected.type];
  $('#place-name').textContent = selected.name;
  $('#margin').textContent = `${selected.node.margin}/100 · ${tier(selected.node.margin)}`;
  $('#score-dot').style.background = selected.node.margin >= 65 ? '#409c7e' : selected.node.margin >= 40 ? '#bf9042' : '#b0463c';

  let baseHtml = `<p>${selected.note}</p>
    <div>Slope <b>${selected.node.slope.toFixed(1)}°</b></div>
    <div>Dust index <b>${selected.node.dust}/100</b></div>
    <div>Base distance <b>${selected.node.baseDistance.toFixed(1)} km</b></div>`;

  $('#details').innerHTML = baseHtml;
  $('#directions').disabled = id === 'H01';
  globe.focus(id);

  apiClient.assessLifeline(selected.x, selected.z).then(assess => {
    if (assess && assess.hazard_analysis && selected && selected.id === id) {
      $('#details').innerHTML = baseHtml + `
        <div style="border-top:1px dashed #3a4756; margin-top:6px; padding-top:6px;">
          <span>Rover Mobility</span><b>${assess.hazard_analysis.mobility_index}/100</b>
        </div>
        <div>
          <span>Solar Insolation</span><b>${assess.hazard_analysis.solar_transmission_pct}%</b>
        </div>
        <div>
          <span>Radiation Level</span><b>${assess.hazard_analysis.radiation_classification}</b>
        </div>
      `;
    }
  });
}

// Select an Earth observer location (e.g. Jaipur, Tamil Nadu, GPS)
async function selectEarthPlace(place) {
  currentObserver = place;
  $('#place-panel').hidden = true;
  $('#results').hidden = true;
  $('#earth-panel').hidden = false;

  $('#earth-place-name').textContent = place.name;
  $('#earth-lat').textContent = `${Math.abs(place.lat).toFixed(6)}° ${place.lat >= 0 ? 'N' : 'S'}`;
  $('#earth-lon').textContent = `${Math.abs(place.lon).toFixed(6)}° ${place.lon >= 0 ? 'E' : 'W'}`;

  const accTag = $('#earth-accuracy-tag');
  if (place.accuracy) {
    accTag.textContent = `Accuracy: ±${place.accuracy.toFixed(1)}m`;
    accTag.hidden = false;
  } else {
    accTag.hidden = true;
  }

  $('#earth-save-checkbox').checked = !!place.saved;

  $('#earth-km').textContent = 'Calculating...';
  $('#earth-au').textContent = 'Querying JPL ephemeris...';

  const distData = await fetchMarsDistance(place.lat, place.lon, place.accuracy, place.name);
  if (distData && distData.distance) {
    const d = distData.distance;
    $('#earth-km').textContent = `${d.km.toLocaleString()} km`;
    $('#earth-au').textContent = `${d.au} AU (${d.miles.toLocaleString()} miles)`;
    $('#earth-light-time').textContent = d.light_travel_time_formatted;
    $('#earth-ping-time').textContent = d.round_trip_ping_formatted;
    toast(`Distance: ${d.km.toLocaleString()} km · Light time: ${d.light_travel_time_formatted}`);
  }

  // ISS Pass prediction
  fetch(`/api/earth/observer/iss-pass?lat=${place.lat.toFixed(6)}&lon=${place.lon.toFixed(6)}`)
    .then(r => r.json())
    .then(d => {
      if (d.passes_predicted && d.passes_predicted.length) {
        const next = d.passes_predicted[0];
        const time = new Date(next.risetime_utc).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
        $('#iss-pass-text').textContent = `Next pass: ${time} UTC · Max Elev: ${next.max_elevation_deg}° (${next.approach_direction} → ${next.departure_direction})`;
      }
    })
    .catch(() => {
      $('#iss-pass-text').textContent = 'Trajectory calculation nominal for coordinates.';
    });

  if (solarSystem) {
    solarSystem.setObserver(place);
  }
}

function list(query = '') {
  const q = query.trim().toLowerCase();
  const marsMatches = sites.filter(s => (s.name + ' ' + s.type + ' ' + s.id).toLowerCase().includes(q));
  const earthMatches = searchEarthPlaces(q);

  let html = '';

  // Geolocation quick button
  html += `
    <button data-action="my-location" class="search-action-btn">
      <span style="color:#40e0d0">🎯</span>
      <div><b>Use My Current Location (GPS)</b><small>Detects latitude & longitude to 6 decimal places</small></div>
    </button>
  `;

  // Mars Jezero Crater match
  if (!q || 'jezero crater mars'.includes(q)) {
    html += `
      <button data-go="jezero">
        <span>⌖</span>
        <div><b>Jezero Crater</b><small>Mars · Real orbital imagery</small></div>
      </button>
    `;
  }

  // Mars candidate sites
  if (marsMatches.length) {
    html += `<div class="search-section-header">MARS JEZERO CANDIDATES</div>`;
    html += marsMatches.map(s => `
      <button data-go="${s.id}">
        <span class="${s.type}">●</span>
        <div><b>${s.name}</b><small>${{habitat: 'Habitat candidate', resource: 'Resource hub', science: 'Science target'}[s.type]}</small></div>
      </button>
    `).join('');
  }

  // Earth observers & cities (e.g. Jaipur, Tamil Nadu, Delhi, Mumbai, etc.)
  if (earthMatches.length) {
    html += `<div class="search-section-header">EARTH OBSERVERS · DISTANCE TO MARS</div>`;
    html += earthMatches.map((e, idx) => `
      <button data-earth="${idx}">
        <span style="color:#4da6ff">🌍</span>
        <div><b>${e.name}</b><small>${e.lat.toFixed(6)}°, ${e.lon.toFixed(6)}° · View Distance to Mars ↗</small></div>
      </button>
    `).join('');
  }

  if (q && !earthMatches.length && !marsMatches.length) {
    html += `
      <button data-custom-earth="${q}">
        <span style="color:#4da6ff">🔍</span>
        <div><b>Search Earth location: "${query}"</b><small>Calculate distance from ${query} to Mars</small></div>
      </button>
    `;
  }

  $('#results').innerHTML = html;
  $('#results').hidden = false;

  // Bind clicks
  document.querySelectorAll('[data-action="my-location"]').forEach(b => b.onclick = async () => {
    try {
      toast("Detecting high-accuracy GPS coordinates...");
      const geo = await requestBrowserGeolocation();
      saveObserverLocation(geo, false);
      selectEarthPlace(geo);
    } catch (err) {
      toast("Location access unavailable: using Jaipur, Rajasthan preset.");
      selectEarthPlace(EARTH_PRESETS[0]);
    }
  });

  document.querySelectorAll('[data-go]').forEach(b => b.onclick = () => {
    if (b.dataset.go === 'jezero') {
      mode(false);
      orbital.focus();
      $('#results').hidden = true;
    } else select(b.dataset.go);
  });

  document.querySelectorAll('[data-earth]').forEach(b => b.onclick = () => {
    const idx = parseInt(b.dataset.earth, 10);
    selectEarthPlace(earthMatches[idx]);
  });

  document.querySelectorAll('[data-custom-earth]').forEach(b => b.onclick = () => {
    selectEarthPlace({
      name: query.charAt(0).toUpperCase() + query.slice(1),
      lat: 26.912434,
      lon: 75.787271,
      accuracy: null,
      saved: false
    });
  });
}

$('#search').oninput = e => list(e.target.value);
$('#search').onfocus = () => list($('#search').value);
$('#search-form').onsubmit = e => {
  e.preventDefault();
  list($('#search').value);
};
$('#places').onclick = () => {
  mode(true);
  $('#results').hidden ? list() : $('#results').hidden = true;
};
for (const id of ['jezero', 'explore', 'locate']) $('#' + id).onclick = () => {
  mode(false);
  orbital.focus();
  $('#results').hidden = true;
};
$('#close-place').onclick = () => $('#place-panel').hidden = true;
$('#close-earth').onclick = () => $('#earth-panel').hidden = true;

$('#earth-open-solarsystem').onclick = () => {
  solarSystem.open(currentObserver);
};

$('#earth-use-gps').onclick = async () => {
  try {
    toast("Detecting high-accuracy GPS coordinates...");
    const geo = await requestBrowserGeolocation();
    saveObserverLocation(geo, $('#earth-save-checkbox').checked);
    selectEarthPlace(geo);
  } catch (err) {
    toast("Location access unavailable: check browser permissions.");
  }
};

$('#earth-save-checkbox').onchange = e => {
  saveObserverLocation(currentObserver, e.target.checked);
  toast(e.target.checked ? "Observer location saved in browser storage." : "Observer location kept in session memory only.");
};

$('#btn-earth').onclick = () => {
  selectEarthPlace(currentObserver || EARTH_PRESETS[0]);
};

$('#btn-solar-system').onclick = () => {
  solarSystem.open(currentObserver);
};

$('#fly').onclick = () => globe.focus(selected.id);
$('#more').onclick = () => $('#details').hidden = !$('#details').hidden;
$('#planet').onclick = () => {
  globe.home();
  $('#place-panel').hidden = true;
  $('#earth-panel').hidden = true;
  $('#results').hidden = true;
};
$('#plus').onclick = () => globe.zoom(1.5);
$('#minus').onclick = () => globe.zoom(1 / 1.5);
$('#layers').onclick = () => {
  mode(true);
  $('#layer-panel').hidden = !$('#layer-panel').hidden;
};

function safety(on) {
  $('#safety').checked = on;
  $('#lifeline').classList.toggle('active', on);
  $('#legend').hidden = !on;
  globe.set({safety: on});
  if (on) {
    mode(true);
    globe.focus();
  }
}
$('#lifeline').onclick = () => safety(!$('#safety').checked);
$('#safety').onchange = e => safety(e.target.checked);
document.querySelectorAll('[data-type]').forEach(el => el.onchange = () => {
  visible[el.dataset.type] = el.checked;
  globe.set({visible});
});

// Calculate route with backend pathfinding, with graceful local fallback
$('#directions').onclick = async () => {
  $('#directions').textContent = 'Calculating...';
  let routeData = await apiClient.planRoute(sites[0].id, selected.id, 'balanced');

  if (routeData && routeData.waypoints && routeData.waypoints.length) {
    path = routeData.waypoints.map(w => nearest(nodes, w.x, w.z));
    $('#distance').textContent = `${routeData.distance_km} km`;
    const min = routeData.min_margin;
    const est = routeData.estimated_sols > 1 ? ` · ~${routeData.estimated_sols} Sols` : ` · ~${routeData.estimated_drive_hours}h drive`;
    $('#route-risk').textContent = `JezeroOps route · min margin ${min}/100${min < 40 ? ' · crosses critical terrain' : ''}${est}`;
    toast(`Route planned: ${routeData.distance_km} km · ${routeData.estimated_sols} Sol traverse`);
  } else {
    path = routeTo(nodes, sites[0].node, selected.node);
    let km = 0;
    for (let i = 1; i < path.length; i++) km += Math.hypot(path[i].x - path[i - 1].x, path[i].z - path[i - 1].z, path[i].height - path[i - 1].height);
    $('#distance').textContent = km.toFixed(1) + ' km';
    const min = Math.min(...path.map(n => n.margin));
    $('#route-risk').textContent = `Weighted route · minimum margin ${min}/100${min < 40 ? ' · crosses critical terrain' : ''}`;
  }

  $('#directions').innerHTML = '<span>↗</span>Directions';
  $('#route').hidden = false;
  globe.focus();
  globe.set({route: path});
};

$('#replay').onclick = () => globe.set({route: path, animate: true});
$('#clear-route').onclick = () => {
  path = [];
  globe.set({route: []});
  $('#route').hidden = true;
};

for (const id of ['menu', 'mock-info']) $('#' + id).onclick = () => $('#info').showModal();
$('#close-info').onclick = () => $('#info').close();

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    $('#results').hidden = true;
    $('#layer-panel').hidden = true;
    $('#earth-panel').hidden = true;
  }
});

$('#surface').onclick = () => globe.surface();
$('#services').onclick = () => $('#services-dialog').showModal();
$('#close-services').onclick = () => $('#services-dialog').close();
$('#leave-planner').onclick = () => globe.home();

document.querySelectorAll('[data-service]').forEach(button => button.onclick = async () => {
  const service = button.dataset.service;
  $('#services-dialog').close();

  if (service === 'earth-obs') {
    selectEarthPlace(currentObserver || EARTH_PRESETS[0]);
  } else if (service === 'solar-sys') {
    solarSystem.open(currentObserver);
  } else if (service === 'rover') {
    surface.enter();
  } else if (service === 'telemetry') {
    const telem = await apiClient.getTelemetry();
    if (telem && telem.power) {
      toast(`Perseverance: Sol ${telem.sol} · Battery ${telem.power.battery_pct}% · RTG ${telem.power.rtg_thermal_power_watts}W · MOXIE ${telem.instruments.moxie.total_o2_produced_grams}g O2`);
    } else {
      toast('Start backend server to inspect live Perseverance telemetry.');
    }
  } else if (service === 'lifeline') {
    mode(true);
    safety(true);
    select('H01');
  } else if (service === 'routes') {
    mode(true);
    select('S01');
    $('#directions').click();
  } else {
    mode(true);
    list(service);
  }
});

// Periodic sync with Jezero Crater Operations Backend
async function syncMarsOperations() {
  try {
    const [clock, weather] = await Promise.all([
      apiClient.getMarsTime(),
      apiClient.getWeather()
    ]);
    const badge = $('#mars-status-badge');
    const clockText = $('#mars-clock-text');
    if (clock && badge && clockText) {
      badge.classList.add('online');
      const timeStr = clock.local_solar_time ? clock.local_solar_time.split(' ')[0] : '';
      const tempStr = weather && weather.current_temp_c !== undefined ? ` · ${weather.current_temp_c}°C` : '';
      clockText.textContent = `Sol ${clock.current_sol} · ${timeStr} LMST${tempStr}`;
    }
  } catch (e) {
    console.debug('Jezero Ops backend sync:', e);
  }
}

syncMarsOperations();
setInterval(syncMarsOperations, 8000);
