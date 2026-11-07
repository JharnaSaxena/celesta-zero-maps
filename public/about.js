(() => {
  const $ = (s) => document.querySelector(s);
  const el = (tag, props = {}, ...kids) => {
    const n = document.createElement(tag);
    Object.assign(n, props);
    for (const k of kids) n.append(k);
    return n;
  };
  const safeUrl = (u) => (/^https?:\/\//i.test(u) ? u : '');

  async function loadTeam() {
    try {
      const r = await fetch('/api/team');
      if (!r.ok) throw new Error();
      const t = await r.json();
      $('#challenge').textContent = String(t.project.challenge || '').toUpperCase();
      $('#summary').textContent = t.project.summary;
      $('#companyName').textContent = t.company.name;
      $('#companyTagline').textContent = t.company.tagline;
      $('#companyAbout').textContent = t.company.about;
      const site = safeUrl(t.company.website);
      if (site) { const a = $('#companySite'); a.href = site; a.textContent = site.replace(/^https?:\/\//, ''); a.hidden = false; }

      const grid = $('#teamGrid');
      grid.replaceChildren(...t.team.map((m) => el('article', { className: 'card' },
        el('div', { className: 'avatar', textContent: (m.name || '?').trim().charAt(0).toUpperCase() }),
        el('h3', { textContent: m.name }),
        el('div', { className: 'role', textContent: m.role }),
        el('p', { textContent: m.bio }))));

      $('#credits').replaceChildren(...t.credits.map((c) => {
        const li = el('li');
        const u = safeUrl(c.url);
        if (u) li.append(el('a', { href: u, target: '_blank', rel: 'noreferrer', textContent: c.label }));
        else li.textContent = c.label;
        return li;
      }));
      $('#disclosures').replaceChildren(...t.disclosures.map((d) => el('li', { textContent: d })));
    } catch {
      $('#summary').textContent = 'Team information is unavailable right now.';
    }
  }

  async function loadDelay() {
    try {
      const r = await fetch('/api/mars/status', { cache: 'no-store' });
      const s = await r.json();
      $('#liveDelay').textContent =
        `Mars is ${s.earth.one_way_minutes} min from Earth one-way (${s.earth.distance_au} AU) · Jezero local time ${s.mars_time.lmst} LMST`;
    } catch { $('#liveDelay').textContent = 'Live Earth–Mars delay unavailable.'; }
  }

  $('#contactForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const f = e.target, status = $('#formStatus'), btn = f.querySelector('button');
    status.className = ''; status.textContent = 'Sending…'; btn.disabled = true;
    try {
      const body = Object.fromEntries(new FormData(f));
      const r = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'lifeline' },
        body: JSON.stringify(body),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.error || 'Could not send your message.');
      f.reset();
      status.textContent = 'Thanks. Your message has been received.';
    } catch (err) {
      status.className = 'err'; status.textContent = err.message;
    } finally { btn.disabled = false; }
  });

  loadTeam(); loadDelay(); setInterval(loadDelay, 60_000);
})();
