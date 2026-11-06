<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Celesta · Zero Maps — Cosmic Explorer</title>
<meta name="description" content="Zoomable cosmic explorer: your live Earth location → Solar System → Mars Jezero Crater. Live night sky & ISS tracking." />
<meta property="og:title" content="Celesta · Zero Maps" />
<meta property="og:description" content="Earth → Solar System → Mars Jezero. Zoomable cosmic explorer with live ISS tracking." />
<meta property="og:type" content="website" />
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='40' fill='%23e07a3f'/><circle cx='68' cy='38' r='8' fill='%23f7d9b8' opacity='.55'/></svg>" />
<body>

<header class="topbar">
  <div class="wrap topbar-inner">
    <div class="brand">
      <span class="orb" aria-hidden="true"></span>
      Celesta <span class="sub">/ Zero Maps</span>
    </div>
    <nav class="nav">
      <a href="#features">Features</a>
      <a href="#data">Data</a>
      <a href="#run">Run</a>
      <a href="https://zero-maps.vercel.app" class="cta" target="_blank" rel="noopener">Open Live ↗</a>
    </nav>
  </div>
</header>

<main class="wrap">

  <!-- HERO -->
  <section class="hero" style="padding-top:96px">
    <span class="badge"><span class="dot"></span> Live deployment ready</span>
    <h1>From your doorstep<br /><span class="grad">to Jezero Crater.</span></h1>
    <p class="lead">
      A zoomable cosmic explorer. Start at your live Earth location, zoom out through the
      Solar System, then dive into a real Mars field map — with a live night sky, ISS passes,
      and 4D time control.
    </p>
    <div class="btns">
      <a href="https://zero-maps.vercel.app" class="btn btn-primary" target="_blank" rel="noopener">Launch Explorer ↗</a>
      <a href="https://github.com/YOUR_USERNAME/celesta-zero-maps" class="btn btn-ghost" target="_blank" rel="noopener">View Source</a>
    </div>

    <div class="journey" aria-label="Zoom journey">
      <b>You</b><span class="arrow">→</span>
      <b>Earth</b><span class="arrow">→</span>
      <b>Solar System</b><span class="arrow">→</span>
      <b>Mars</b><span class="arrow">→</span>
      <b>Jezero Crater</b>
    </div>
  </section>

  <!-- FEATURES -->
  <section id="features">
    <div class="sec-head">
      <h2>What's inside</h2>
      <p>Six interactive scenes stitched into one continuous zoom journey.</p>
    </div>
    <div class="grid">
      <div class="card">
        <div class="ico">📍</div>
        <h3>Live Earth location</h3>
        <p>Browser geolocation with accuracy radius, shown to six decimal places. Stays on your device — never sent to a server.</p>
      </div>
      <div class="card">
        <div class="ico">🌍</div>
        <h3>Seamless zoom</h3>
        <p>Your local map flows into the Earth globe, out to the Solar System, then into Mars — the way Google Maps zoom should feel.</p>
      </div>
      <div class="card">
        <div class="ico">🔴</div>
        <h3>Jezero field map</h3>
        <p>NASA CTX imagery, MOLA elevation relief, Perseverance PDS rover track & elevations, and mapped geology points.</p>
      </div>
      <div class="card">
        <div class="ico">✨</div>
        <h3>Night sky</h3>
        <p>Sun, Moon, planets and a curated named-star catalog rendered for your horizon and local time.</p>
      </div>
      <div class="card">
        <div class="ico">🛰️</div>
        <h3>ISS tracking</h3>
        <p>Live position plus passes above 10° for the next 48 hours, using CelesTrak TLEs and SGP4 propagation.</p>
      </div>
      <div class="card">
        <div class="ico">🪐</div>
        <h3>4D time control</h3>
        <p>Scrub across a year and watch the planets and sky rearrange. Positions follow JPL's approximate Keplerian model.</p>
      </div>
    </div>

    <div class="warn">
      <h3>⚠️ Known limitations — read before using</h3>
      <ul>
        <li>Terrain, EVA-margin and route-slope models are <b>illustrative</b>, not derived from a high-res DEM.</li>
        <li>Planet positions use JPL's <b>approximate</b> model — use <a href="https://ssd.jpl.nasa.gov/horizons/" target="_blank" rel="noopener">JPL Horizons</a> for precision.</li>
        <li>Earth surface is a stylised illustration, not satellite imagery.</li>
        <li>ISS pass times are estimates — <b>not operational guidance</b>.</li>
      </ul>
    </div>
  </section>

  <!-- DATA -->
  <section id="data">
    <div class="sec-head">
      <h2>Data sources</h2>
      <p>Everything is derived from public datasets. All credit to the original providers.</p>
    </div>
    <table class="data-table">
      <thead>
        <tr><th>Layer</th><th>Source</th><th>Notes</th></tr>
      </thead>
      <tbody>
        <tr><td>Mars surface</td><td><a href="https://www.nasa.gov" target="_blank" rel="noopener">NASA CTX</a></td><td>High-res orbital imagery</td></tr>
        <tr><td>Mars relief</td><td><a href="https://pds-geosciences.wustl.edu/" target="_blank" rel="noopener">NASA MOLA</a></td><td>Optional elevation layer</td></tr>
        <tr><td>Rover track</td><td><a href="https://pds.nasa.gov" target="_blank" rel="noopener">Perseverance PDS</a></td><td>Positions & elevations</td></tr>
        <tr><td>ISS orbits</td><td><a href="https://celestrak.org" target="_blank" rel="noopener">CelesTrak</a></td><td>TLE via SGP4</td></tr>
        <tr><td>Planets</td><td><a href="https://ssd.jpl.nasa.gov" target="_blank" rel="noopener">JPL SSD</a></td><td>Approximate Keplerian elements</td></tr>
        <tr><td>Earth tiles</td><td><a href="https://www.openstreetmap.org" target="_blank" rel="noopener">OpenStreetMap</a></td><td>© OSM contributors</td></tr>
      </tbody>
    </table>
  </section>

  <!-- RUN -->
  <section id="run">
    <div class="sec-head">
      <h2>Run it locally</h2>
      <p>Two commands and you're exploring.</p>
    </div>
<pre class="code"><span class="cm"># clone &amp; enter</span>
git clone https://github.com/YOUR_USERNAME/celesta-zero-maps
cd celesta-zero-maps

<span class="cm"># install &amp; serve</span>
npm install
npm run dev

<span class="cm"># → http://localhost:3000</span></pre>
  </section>

</main>

<footer>
  <div class="wrap">
    <div class="flinks">
      <a href="https://zero-maps.vercel.app" target="_blank" rel="noopener">Live site</a>
      <a href="https://github.com/YOUR_USERNAME/celesta-zero-maps" target="_blank" rel="noopener">GitHub</a>
      <a href="https://github.com/YOUR_USERNAME/celesta-zero-maps/releases" target="_blank" rel="noopener">Releases</a>
      <a href="https://github.com/YOUR_USERNAME/celesta-zero-maps/issues" target="_blank" rel="noopener">Issues</a>
    </div>
    <p>Celesta · Zero Maps — MIT licensed. Data © NASA, JPL, CelesTrak, OpenStreetMap contributors.</p>
  </div>
</footer>

</body>
</html>
