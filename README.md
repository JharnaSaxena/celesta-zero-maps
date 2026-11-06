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
<style>
  :root{
    --bg:#080a12;
    --bg2:#0e1220;
    --card:#121829;
    --line:#222a3f;
    --txt:#e8edf7;
    --dim:#8f9ab5;
    --accent:#e07a3f;
    --accent2:#f0b27a;
    --blue:#5aa9e6;
    --radius:16px;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html{scroll-behavior:smooth}
  body{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    background:var(--bg);
    color:var(--txt);
    line-height:1.6;
    overflow-x:hidden;
    -webkit-font-smoothing:antialiased;
  }

  /* ---------- starfield ---------- */
  body::before{
    content:"";
    position:fixed;inset:0;z-index:-2;
    background:
      radial-gradient(1px 1px at 20% 30%, #fff 50%, transparent 51%),
      radial-gradient(1px 1px at 70% 15%, #cdd6ea 50%, transparent 51%),
      radial-gradient(1.5px 1.5px at 40% 80%, #fff 50%, transparent 51%),
      radial-gradient(1px 1px at 85% 60%, #aab6d0 50%, transparent 51%),
      radial-gradient(1px 1px at 15% 70%, #fff 50%, transparent 51%),
      radial-gradient(1.5px 1.5px at 60% 45%, #e8edf7 50%, transparent 51%),
      radial-gradient(1px 1px at 90% 25%, #fff 50%, transparent 51%),
      radial-gradient(1px 1px at 33% 12%, #cfd8ec 50%, transparent 51%),
      radial-gradient(1px 1px at 55% 90%, #fff 50%, transparent 51%),
      radial-gradient(1.5px 1.5px at 5% 45%, #e8edf7 50%, transparent 51%);
    background-size:100% 100%;
    opacity:.55;
  }
  body::after{
    content:"";
    position:fixed;inset:0;z-index:-1;
    background:radial-gradient(ellipse at 50% 0%, rgba(224,122,63,.10), transparent 55%),
               radial-gradient(ellipse at 80% 90%, rgba(90,169,230,.08), transparent 50%);
  }

  /* ---------- layout ---------- */
  .wrap{max-width:1080px;margin:0 auto;padding:0 24px}

  /* ---------- topbar ---------- */
  header.topbar{
    position:sticky;top:0;z-index:20;
    backdrop-filter:blur(10px);
    background:rgba(8,10,18,.72);
    border-bottom:1px solid var(--line);
  }
  .topbar-inner{
    display:flex;align-items:center;justify-content:space-between;
    height:64px;
  }
  .brand{display:flex;align-items:center;gap:11px;font-weight:700;font-size:17px;letter-spacing:.2px}
  .brand .orb{
    width:26px;height:26px;border-radius:50%;
    background:radial-gradient(circle at 32% 32%, var(--accent2), var(--accent) 55%, #7a3a17);
    box-shadow:0 0 18px rgba(224,122,63,.55);
    flex:none;
  }
  .brand span.sub{color:var(--dim);font-weight:400;font-size:14px}
  .nav{display:flex;gap:22px;align-items:center;font-size:14px}
  .nav a{color:var(--dim);text-decoration:none;transition:color .18s}
  .nav a:hover{color:var(--txt)}
  .nav a.cta{
    color:#170b04;background:linear-gradient(135deg,var(--accent2),var(--accent));
    padding:8px 16px;border-radius:999px;font-weight:600;
    box-shadow:0 4px 20px rgba(224,122,63,.28);
  }
  .nav a.cta:hover{filter:brightness(1.08);color:#170b04}

  /* ---------- hero ---------- */
  .hero{padding:96px 0 72px;text-align:center;position:relative}
  .hero .badge{
    display:inline-flex;align-items:center;gap:8px;
    font-size:12.5px;letter-spacing:.6px;text-transform:uppercase;
    color:var(--accent2);border:1px solid rgba(224,122,63,.35);
    background:rgba(224,122,63,.08);
    padding:6px 14px;border-radius:999px;margin-bottom:26px;
    font-weight:600;
  }
  .hero .badge .dot{width:7px;height:7px;border-radius:50%;background:#57d98a;box-shadow:0 0 8px #57d98a}
  .hero h1{
    font-size:clamp(38px,6vw,68px);
    line-height:1.05;font-weight:800;letter-spacing:-1.5px;
    margin-bottom:22px;
  }
  .hero h1 .grad{
    background:linear-gradient(100deg,var(--accent2),var(--accent) 45%,var(--blue));
    -webkit-background-clip:text;background-clip:text;color:transparent;
  }
  .hero p.lead{
    max-width:660px;margin:0 auto 36px;
    color:var(--dim);font-size:clamp(15px,1.7vw,18px);
  }
  .hero .btns{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
  .btn{
    display:inline-flex;align-items:center;gap:9px;
    padding:13px 26px;border-radius:12px;
    font-size:15px;font-weight:600;text-decoration:none;
    transition:transform .16s, box-shadow .2s, filter .2s;
  }
  .btn-primary{
    background:linear-gradient(135deg,var(--accent2),var(--accent));
    color:#170b04;box-shadow:0 8px 28px rgba(224,122,63,.35);
  }
  .btn-primary:hover{transform:translateY(-2px);filter:brightness(1.07)}
  .btn-ghost{
    border:1px solid var(--line);color:var(--txt);
    background:rgba(255,255,255,.02);
  }
  .btn-ghost:hover{border-color:#3a4767;transform:translateY(-2px)}

  /* ---------- journey strip ---------- */
  .journey{
    display:flex;align-items:center;justify-content:center;
    gap:10px;flex-wrap:wrap;
    margin-top:52px;font-size:13px;color:var(--dim);
    letter-spacing:.3px;
  }
  .journey b{color:var(--txt);font-weight:600}
  .journey .arrow{color:#3c4a6b}

  /* ---------- sections ---------- */
  section{padding:72px 0;position:relative}
  .sec-head{margin-bottom:38px;text-align:center}
  .sec-head h2{
    font-size:clamp(26px,3.4vw,36px);font-weight:750;letter-spacing:-.8px;margin-bottom:10px;
  }
  .sec-head p{color:var(--dim);font-size:15px;max-width:560px;margin:0 auto}

  /* ---------- cards ---------- */
  .grid{
    display:grid;gap:18px;
    grid-template-columns:repeat(auto-fit,minmax(250px,1fr));
  }
  .card{
    background:linear-gradient(160deg,var(--card),#0c1120);
    border:1px solid var(--line);
    border-radius:var(--radius);
    padding:24px 22px;
    transition:border-color .2s, transform .2s, box-shadow .2s;
  }
  .card:hover{
    border-color:#34405e;transform:translateY(-3px);
    box-shadow:0 14px 40px rgba(0,0,0,.35);
  }
  .card .ico{
    width:42px;height:42px;border-radius:11px;
    display:grid;place-items:center;font-size:20px;
    background:rgba(224,122,63,.12);
    border:1px solid rgba(224,122,63,.22);
    margin-bottom:16px;
  }
  .card h3{font-size:16.5px;font-weight:650;margin-bottom:7px;letter-spacing:-.2px}
  .card p{font-size:14px;color:var(--dim);line-height:1.55}

  /* ---------- warning panel ---------- */
  .warn{
    margin-top:18px;
    border:1px solid rgba(240,178,122,.28);
    background:rgba(240,178,122,.06);
    border-radius:var(--radius);
    padding:22px 24px;
  }
  .warn h3{font-size:15px;margin-bottom:10px;color:var(--accent2);display:flex;align-items:center;gap:8px}
  .warn ul{list-style:none;display:grid;gap:7px}
  .warn li{font-size:13.5px;color:var(--dim);padding-left:18px;position:relative}
  .warn li::before{content:"—";position:absolute;left:0;color:#4c5670}

  /* ---------- data table ---------- */
  .data-table{
    width:100%;border-collapse:collapse;font-size:14px;
    border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;
  }
  .data-table th,.data-table td{
    text-align:left;padding:13px 18px;
    border-bottom:1px solid var(--line);
  }
  .data-table th{
    font-size:12px;text-transform:uppercase;letter-spacing:.7px;
    color:var(--dim);font-weight:600;background:rgba(255,255,255,.025);
  }
  .data-table tr:last-child td{border-bottom:none}
  .data-table td{color:var(--dim)}
  .data-table td:first-child{color:var(--txt);font-weight:550}
  .data-table a{color:var(--blue);text-decoration:none}
  .data-table a:hover{text-decoration:underline}

  /* ---------- quickstart code ---------- */
  pre.code{
    background:#0a0e1a;border:1px solid var(--line);border-radius:12px;
    padding:20px 22px;overflow-x:auto;font-size:13.5px;line-height:1.7;
    font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    color:#c7d2e6;
  }
  pre.code .cm{color:#5b6883}

  /* ---------- footer ---------- */
  footer{
    border-top:1px solid var(--line);
    padding:44px 0 56px;margin-top:40px;
    text-align:center;color:var(--dim);font-size:13.5px;
  }
  footer .flinks{
    display:flex;gap:22px;justify-content:center;flex-wrap:wrap;margin-bottom:18px;
  }
  footer a{color:var(--dim);text-decoration:none;transition:color .18s}
  footer a:hover{color:var(--txt)}

  @media(max-width:640px){
    .nav a:not(.cta){display:none}
    .hero{padding:64px 0 48px}
    section{padding:52px 0}
  }
</style>
</head>
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
