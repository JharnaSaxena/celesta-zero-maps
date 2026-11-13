/**
 * Sun-Centered Solar System & Interplanetary Distance Visualizer
 * Plots orbital paths and positions from JPL approximate planetary elements.
 * Displays real-time Earth-to-Mars distance with interactive date controls.
 */

export function createSolarSystemView(onClose) {
  let host = document.querySelector('#solar-system-dialog');
  if (!host) {
    host = document.createElement('dialog');
    host.id = 'solar-system-dialog';
    host.innerHTML = `
      <div class="ss-header">
        <div>
          <span class="ss-eyebrow">HELIOCENTRIC ORBITS · JPL KEPLERIAN ELEMENTS</span>
          <h2>Solar System & Interplanetary Distance</h2>
        </div>
        <button id="close-ss" class="close" aria-label="Close Solar System">×</button>
      </div>

      <div class="ss-distance-banner" id="ss-banner">
        <div class="ss-banner-item">
          <small>OBSERVER (EARTH)</small>
          <b id="ss-observer-label">Jaipur, India</b>
        </div>
        <div class="ss-banner-arrow">⇄</div>
        <div class="ss-banner-item">
          <small>TARGET (MARS)</small>
          <b>Jezero Crater</b>
        </div>
        <div class="ss-banner-metric">
          <small>INTERPLANETARY DISTANCE</small>
          <span id="ss-distance-km">198,649,085 km</span>
          <em id="ss-distance-au">(1.328 AU)</em>
        </div>
        <div class="ss-banner-metric">
          <small>ONE-WAY LIGHT TIME</small>
          <span id="ss-light-time">11m 02s</span>
          <em id="ss-round-trip">22m 04s round-trip</em>
        </div>
      </div>

      <div class="ss-canvas-host">
        <canvas id="ss-canvas"></canvas>
        <div class="ss-hud">
          <div class="ss-legend">
            <span><i style="background:#ffd000"></i>Sun</span>
            <span><i style="background:#4da6ff"></i>Earth (You)</span>
            <span><i style="background:#e06c4b"></i>Mars (Jezero)</span>
            <span><i style="background:#e0c068"></i>Venus</span>
            <span><i style="background:#c89462"></i>Jupiter</span>
          </div>
          <div class="ss-hint">Drag to pan · Scroll to zoom · Scrub date below</div>
        </div>
      </div>

      <div class="ss-controls">
        <div class="ss-date-group">
          <label>Ephemeris Date:</label>
          <input type="date" id="ss-date-input">
          <button id="ss-btn-today" class="ss-btn">Today</button>
        </div>
        <div class="ss-slider-group">
          <span>-1 Year</span>
          <input type="range" id="ss-slider" min="-365" max="365" value="0">
          <span>+1 Year</span>
        </div>
        <div id="ss-opposition-note">Scrub to view Earth-Mars orbital conjunction & opposition</div>
      </div>
    `;
    document.body.appendChild(host);
  }

  const canvas = host.querySelector('#ss-canvas');
  const ctx = canvas.getContext('2d');
  let w = 1, h = 1;
  let panX = 0, panY = 0;
  let zoom = 1.0;
  let isDragging = false, lastMouse = {x: 0, y: 0};
  let currentDate = new Date();
  let baseDate = new Date();
  let systemState = null;
  let activeObserver = {lat: 26.912434, lon: 75.787271, name: "Jaipur, India"};

  // Resize canvas
  function resize() {
    const parent = canvas.parentElement;
    w = parent.clientWidth || 800;
    h = parent.clientHeight || 500;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
  }

  // Fetch or calculate ephemeris state
  async function loadState(dateObj) {
    try {
      const iso = dateObj.toISOString();
      const res = await fetch(`/api/solar-system/positions?date=${encodeURIComponent(iso)}`);
      if (res.ok) {
        systemState = await res.json();
        updateBanner();
        draw();
        return;
      }
    } catch (e) {}

    // Client-side fallback calculation
    computeClientState(dateObj);
    updateBanner();
    draw();
  }

  function computeClientState(dt) {
    const jd = (dt.getTime() / 86400000.0) + 2440587.5;
    const T = (jd - 2451545.0) / 36525.0;

    const planets = [
      {name: "Mercury", a: 0.387, e: 0.2056, L: 252.25 + 149472.67 * T, color: "#9e9e9e", r: 4},
      {name: "Venus", a: 0.723, e: 0.0067, L: 181.98 + 58517.82 * T, color: "#e0c068", r: 7},
      {name: "Earth", a: 1.000, e: 0.0167, L: 100.46 + 35999.37 * T, color: "#4da6ff", r: 8},
      {name: "Mars", a: 1.524, e: 0.0934, L: -4.55 + 19140.30 * T, color: "#e06c4b", r: 6},
      {name: "Jupiter", a: 5.203, e: 0.0484, L: 34.40 + 3034.75 * T, color: "#c89462", r: 14}
    ];

    const computed = planets.map(p => {
      const rad = (p.L * Math.PI) / 180;
      const x = p.a * Math.cos(rad);
      const y = p.a * Math.sin(rad);
      // Orbit circle/ellipse points
      const orbit_path = [];
      for (let i = 0; i <= 64; i++) {
        const a = (i / 64) * Math.PI * 2;
        orbit_path.push({x: p.a * Math.cos(a), y: p.a * Math.sin(a)});
      }
      return {
        name: p.name,
        x_au: x,
        y_au: y,
        color: p.color,
        radius_scale: p.r,
        orbit_path
      };
    });

    const earth = computed.find(p => p.name === "Earth");
    const mars = computed.find(p => p.name === "Mars");
    const dx = mars.x_au - earth.x_au;
    const dy = mars.y_au - earth.y_au;
    const dist_au = Math.hypot(dx, dy);
    const dist_km = dist_au * 149597870.7;
    const light_sec = dist_km / 299792.458;

    systemState = {
      date_utc: dt.toISOString(),
      earth_mars_distance: {
        km: Math.round(dist_km),
        au: Number(dist_au.toFixed(4)),
        light_travel_time_formatted: `${Math.floor(light_sec / 60)}m ${Math.floor(light_sec % 60)}s`,
        round_trip_delay_formatted: `${Math.floor((light_sec * 2) / 60)}m ${Math.floor((light_sec * 2) % 60)}s`
      },
      planets: computed
    };
  }

  function updateBanner() {
    if (!systemState) return;
    const d = systemState.earth_mars_distance;
    host.querySelector('#ss-observer-label').textContent = activeObserver.name;
    host.querySelector('#ss-distance-km').textContent = `${d.km.toLocaleString()} km`;
    host.querySelector('#ss-distance-au').textContent = `(${d.au} AU)`;
    host.querySelector('#ss-light-time').textContent = d.light_travel_time_formatted;
    host.querySelector('#ss-round-trip').textContent = `${d.round_trip_delay_formatted} round-trip`;

    // Format date in input
    const dateInput = host.querySelector('#ss-date-input');
    const yyyy = currentDate.toISOString().split('T')[0];
    dateInput.value = yyyy;
  }

  // Draw Sun, Orbits, Planets, Distance vector
  function draw() {
    if (!w || !h) return;
    ctx.clearRect(0, 0, w, h);

    // Deep space background
    const bgGrad = ctx.createRadialGradient(w / 2 + panX, h / 2 + panY, 20, w / 2 + panX, h / 2 + panY, Math.max(w, h));
    bgGrad.addColorStop(0, '#131922');
    bgGrad.addColorStop(1, '#090c10');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    const centerX = w / 2 + panX;
    const centerY = h / 2 + panY;
    // Scale: 1 AU ~ 110 pixels at zoom 1.0
    const AU_PX = 110 * zoom;

    // Draw Sun
    ctx.beginPath();
    const sunGlow = ctx.createRadialGradient(centerX, centerY, 3, centerX, centerY, 32);
    sunGlow.addColorStop(0, '#fffbe6');
    sunGlow.addColorStop(0.3, '#ffcc00');
    sunGlow.addColorStop(0.7, '#ff880033');
    sunGlow.addColorStop(1, '#ff660000');
    ctx.fillStyle = sunGlow;
    ctx.arc(centerX, centerY, 32, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.arc(centerX, centerY, 9, 0, Math.PI * 2);
    ctx.fillStyle = '#ffea78';
    ctx.fill();

    if (!systemState || !systemState.planets) return;

    // Draw Orbit paths
    systemState.planets.forEach(p => {
      if (p.orbit_path && p.orbit_path.length) {
        ctx.beginPath();
        p.orbit_path.forEach((pt, idx) => {
          const px = centerX + pt.x * AU_PX;
          const py = centerY - pt.y * AU_PX;
          if (idx === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        });
        ctx.strokeStyle = p.name === 'Earth' ? '#4da6ff33' : p.name === 'Mars' ? '#e06c4b44' : '#ffffff14';
        ctx.lineWidth = p.name === 'Earth' || p.name === 'Mars' ? 1.5 : 1;
        ctx.setLineDash(p.name === 'Earth' || p.name === 'Mars' ? [4, 4] : []);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    });

    // Positions of Earth & Mars for distance vector
    const earth = systemState.planets.find(p => p.name === 'Earth');
    const mars = systemState.planets.find(p => p.name === 'Mars');

    if (earth && mars) {
      const ex = centerX + earth.x_au * AU_PX;
      const ey = centerY - earth.y_au * AU_PX;
      const mx = centerX + mars.x_au * AU_PX;
      const my = centerY - mars.y_au * AU_PX;

      // Draw Glowing Interplanetary Distance line
      ctx.beginPath();
      ctx.moveTo(ex, ey);
      ctx.lineTo(mx, my);
      ctx.strokeStyle = '#40e0d0';
      ctx.lineWidth = 2.5;
      ctx.setLineDash([6, 5]);
      ctx.shadowColor = '#40e0d0';
      ctx.shadowBlur = 10;
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.shadowBlur = 0;

      // Distance tag midway
      const midX = (ex + mx) / 2;
      const midY = (ey + my) / 2;
      const distStr = `${systemState.earth_mars_distance.km.toLocaleString()} km · ${systemState.earth_mars_distance.light_travel_time_formatted}`;

      ctx.font = '11px -apple-system, sans-serif';
      const tw = ctx.measureText(distStr).width;
      ctx.fillStyle = '#101720ee';
      ctx.strokeStyle = '#40e0d088';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(midX - tw / 2 - 8, midY - 14, tw + 16, 22, 6);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = '#e6f7ff';
      ctx.textAlign = 'center';
      ctx.fillText(distStr, midX, midY + 1);
      ctx.textAlign = 'start';
    }

    // Draw Planets
    systemState.planets.forEach(p => {
      const px = centerX + p.x_au * AU_PX;
      const py = centerY - p.y_au * AU_PX;
      const r = Math.max(4, (p.radius_scale || 5) * Math.sqrt(zoom));

      // Glow ring for Earth and Mars
      if (p.name === 'Earth' || p.name === 'Mars') {
        ctx.beginPath();
        ctx.arc(px, py, r + 5, 0, Math.PI * 2);
        ctx.strokeStyle = p.color;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();

      // Planet label
      ctx.font = '11px sans-serif';
      ctx.fillStyle = '#c5d1de';
      const label = p.name === 'Earth' ? `Earth (${activeObserver.name.split(',')[0]})` : (p.name === 'Mars' ? 'Mars (Jezero)' : p.name);
      ctx.fillText(label, px + r + 6, py + 4);
    });
  }

  // Mouse / Touch handlers for pan and zoom
  canvas.onpointerdown = e => {
    isDragging = true;
    lastMouse = {x: e.clientX, y: e.clientY};
    canvas.setPointerCapture(e.pointerId);
  };
  canvas.onpointermove = e => {
    if (!isDragging) return;
    panX += e.clientX - lastMouse.x;
    panY += e.clientY - lastMouse.y;
    lastMouse = {x: e.clientX, y: e.clientY};
    draw();
  };
  canvas.onpointerup = canvas.onpointercancel = () => {
    isDragging = false;
  };
  canvas.onwheel = e => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
    zoom = Math.max(0.3, Math.min(4.0, zoom * factor));
    draw();
  };

  // Date controls
  const dateInput = host.querySelector('#ss-date-input');
  const slider = host.querySelector('#ss-slider');
  const btnToday = host.querySelector('#ss-btn-today');

  dateInput.onchange = e => {
    const parsed = new Date(e.target.value);
    if (!isNaN(parsed.getTime())) {
      currentDate = parsed;
      slider.value = Math.round((currentDate - baseDate) / 86400000);
      loadState(currentDate);
    }
  };

  slider.oninput = e => {
    const offsetDays = parseInt(e.target.value, 10);
    currentDate = new Date(baseDate.getTime() + offsetDays * 86400000);
    loadState(currentDate);
  };

  btnToday.onclick = () => {
    baseDate = new Date();
    currentDate = new Date();
    slider.value = 0;
    loadState(currentDate);
  };

  // Close handler
  host.querySelector('#close-ss').onclick = () => {
    host.close();
    if (onClose) onClose();
  };

  return {
    open(observer = null) {
      if (observer) activeObserver = observer;
      host.showModal();
      setTimeout(() => {
        resize();
        loadState(currentDate);
      }, 50);
    },
    setObserver(obs) {
      activeObserver = obs;
      if (systemState) updateBanner();
    }
  };
}
