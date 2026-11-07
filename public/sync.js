/* Zero Maps cloud layer. Loaded automatically on the planner page by the server.
 * - Account dialog (register / sign in / sign out / export / delete)
 * - Syncs the planner's IndexedDB workspace with the backend (/api/workspace)
 * - Live Earth–Mars light-time in the header
 * - Saves a copy of each exported EVA briefing to the account
 * It talks to app.js only through the same IndexedDB record app.js already uses. */
(() => {
  'use strict';
  const DB_NAME = 'fieldwork-jezero', STORE = 'workspace', KEY = 'session';
  const SYNC_KEYS = ['waypoints', 'route', 'name', 'savedRoutes', 'notes', 'layers', 'zoom', 'cx', 'cy',
    'mode', 'evaHour', 'crewDown', 'scienceWeight', 'marsGravity', 'observerLocation'];
  const $ = (s, r = document) => r.querySelector(s);
  const h = (tag, props = {}, ...kids) => {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) k in n ? (n[k] = v) : n.setAttribute(k, v);
    for (const c of kids) n.append(c);
    return n;
  };

  let user = null, baseRev = 0, lastSent = '', busy = false, timer = null;

  // ---------- styles ----------
  document.head.append(h('style', { textContent: `
  .lf-chip{font:10px var(--mono,monospace);letter-spacing:.5px;color:#a5a79c;display:inline-flex;align-items:center;gap:7px}
  .lf-chip b{color:#f0c27e;font-weight:500}
  .lf-btn{height:30px;border:1px solid #393b34;background:#1c1f1b;color:#c6c7bc;border-radius:4px;padding:0 10px;font:10px var(--mono,monospace);letter-spacing:.4px;text-decoration:none;display:inline-flex;align-items:center;cursor:pointer}
  .lf-btn:hover{background:#292c26}
  .lf-btn.on{border-color:#a2ad73;color:#d7dfa6}
  #lfDialog{width:min(420px,calc(100% - 32px));border:1px solid #45473f;border-radius:5px;background:#1b1d1a;color:#f0eee7;padding:22px}
  #lfDialog::backdrop{background:#0b0c0acc}
  #lfDialog h2{font:600 20px var(--display,sans-serif);margin:6px 0 12px}
  #lfDialog label{display:grid;gap:5px;margin:0 0 12px;font:10px var(--mono,monospace);letter-spacing:.5px;color:#b9b9ac}
  #lfDialog input{background:#111312;border:1px solid #393b34;border-radius:3px;padding:10px;color:#f0eee7;font:13px var(--sans,sans-serif)}
  #lfDialog .row{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
  #lfDialog button.primary{background:#d87948;border:1px solid #d87948;color:#201812;border-radius:3px;padding:9px 13px;font:600 11px var(--mono,monospace);cursor:pointer}
  #lfDialog button.ghost{background:transparent;border:1px solid #45473f;color:#cfcdc2;border-radius:3px;padding:9px 13px;font:11px var(--mono,monospace);cursor:pointer}
  #lfDialog button.danger{background:#392720;border:1px solid #87573e;color:#ffb88f;border-radius:3px;padding:9px 13px;font:11px var(--mono,monospace);cursor:pointer}
  #lfDialog .msg{min-height:18px;font:11px var(--mono,monospace);color:#ff9d7a;margin:6px 0 0}
  #lfDialog .msg.ok{color:#b6c77f}
  #lfDialog p.hint{font-size:12px;color:#a6a69a;line-height:1.55;margin:0 0 12px}
  #lfDialog a{color:#e7aa70}
  ` }));

  // ---------- API ----------
  async function api(path, opts = {}) {
    const res = await fetch('/api' + path, {
      method: opts.method || 'GET',
      headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'lifeline' },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      credentials: 'same-origin',
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) { const e = new Error(json.error || `Request failed (${res.status})`); e.status = res.status; e.json = json; throw e; }
    return json;
  }
  const toast = (msg) => {
    const t = $('#toast'); if (!t) return;
    t.textContent = msg; t.classList.add('show');
    clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove('show'), 2600);
  };

  // ---------- IndexedDB bridge (same record app.js uses) ----------
  function openDb() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME);
      req.onupgradeneeded = () => { if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE); };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }
  async function readLocal() {
    const db = await openDb();
    try {
      if (!db.objectStoreNames.contains(STORE)) return null;
      return await new Promise((res, rej) => {
        const q = db.transaction(STORE).objectStore(STORE).get(KEY);
        q.onsuccess = () => res(q.result || null); q.onerror = () => rej(q.error);
      });
    } finally { db.close(); }
  }
  async function writeLocal(obj) {
    const db = await openDb();
    try {
      await new Promise((res, rej) => {
        const tx = db.transaction(STORE, 'readwrite');
        tx.objectStore(STORE).put(obj, KEY);
        tx.oncomplete = res; tx.onerror = () => rej(tx.error);
      });
    } finally { db.close(); }
  }
  const pick = (o) => { const out = {}; for (const k of SYNC_KEYS) if (o && k in o) out[k] = o[k]; return out; };
  const hasContent = (o) => !!o && ((o.savedRoutes?.length || 0) + (o.notes?.length || 0) + (o.waypoints?.length || 0) > 0);
  const revKey = () => `zero-maps-rev-${user?.id}`;
  const loadRev = () => { try { return Number(localStorage.getItem(revKey())) || 0; } catch { return 0; } };
  const saveRev = (r) => { baseRev = r; try { localStorage.setItem(revKey(), String(r)); } catch { /* ignore */ } };

  // ---------- sync ----------
  function setStatus() {
    const b = $('#lfAccountBtn'); if (!b) return;
    b.textContent = user ? `☁ ${user.name.split(' ')[0].slice(0, 14)}` : 'Sign in';
    b.classList.toggle('on', !!user);
    b.title = user ? 'Account & cloud sync' : 'Sign in to sync across devices';
  }

  async function pull(local, server) {
    await writeLocal({ ...(local || {}), ...server.data });
    saveRev(server.rev);
    location.reload();
  }

  async function initialSync() {
    const local = await readLocal();
    const server = await api('/workspace');
    const lr = loadRev();
    if (server.rev === 0 || !server.data) {            // nothing in the cloud yet
      saveRev(0);
      if (hasContent(local)) await push(local, true);
      return;
    }
    if (lr === server.rev) { saveRev(lr); lastSent = JSON.stringify(pick(local)); return; } // already in sync
    if (lr > 0) return pull(local, server);            // another device saved newer data
    // First time this device meets this account
    if (!hasContent(local)) return pull(local, server);
    const useCloud = confirm('Your account has a saved workspace.\n\nOK = load the cloud version on this device.\nCancel = replace the cloud version with this device\'s data.');
    if (useCloud) return pull(local, server);
    saveRev(server.rev);
    await push(local, true);
  }

  async function push(local, force = false) {
    if (busy || !user) return;
    const snap = pick(local || {});
    const s = JSON.stringify(snap);
    if (!force && s === lastSent) return;
    busy = true;
    try {
      const r = await api('/workspace', { method: 'PUT', body: { data: snap, baseRev } });
      saveRev(r.rev); lastSent = s;
    } catch (e) {
      if (e.status === 409) {
        const keep = confirm('Another device saved newer data.\n\nOK = load the newer cloud version here.\nCancel = overwrite the cloud with this device.');
        if (keep) { await writeLocal({ ...(local || {}), ...(e.json.data || {}) }); saveRev(e.json.rev); location.reload(); }
        else { saveRev(e.json.rev); busy = false; return push(local, true); }
      } else if (e.status === 401) { user = null; setStatus(); stopLoop(); }
      else if (e.status !== 413) console.warn('sync failed', e.message);
      else toast('Workspace is too large to sync.');
    } finally { busy = false; }
  }

  function startLoop() {
    stopLoop();
    timer = setInterval(async () => { try { await push(await readLocal()); } catch { /* ignore */ } }, 4000);
    document.addEventListener('visibilitychange', onVis);
  }
  function stopLoop() { clearInterval(timer); timer = null; document.removeEventListener('visibilitychange', onVis); }
  async function onVis() { if (document.visibilityState === 'hidden') { try { await push(await readLocal()); } catch { /* ignore */ } } }

  // ---------- briefing capture ----------
  let lastJsonBlob = null;
  const origCreate = URL.createObjectURL.bind(URL);
  URL.createObjectURL = (obj) => { if (obj instanceof Blob && obj.type === 'application/json') lastJsonBlob = obj; return origCreate(obj); };
  document.addEventListener('click', async (e) => {
    if (!e.target.closest('#briefingBtn') || !user || !lastJsonBlob) return;
    try {
      const payload = JSON.parse(await lastJsonBlob.text());
      if (payload.title !== 'Zero Maps EVA Field Briefing') return;
      await api('/briefings', { method: 'POST', body: { title: `EVA briefing · ${payload.bindingConstraint || 'limit'} · ${payload.estimatedReturnMarginMinutes} min`, payload } });
      toast('Briefing exported and saved to your account');
    } catch { /* download still worked */ }
  });

  // ---------- header UI ----------
  function mountHeader() {
    const actions = $('.top-actions'); if (!actions || $('#lfAccountBtn')) return;
    actions.prepend(
      h('a', { className: 'lf-btn', href: '/about.html', textContent: 'About' }),
      h('button', { id: 'lfAccountBtn', className: 'lf-btn', type: 'button', onclick: openDialog, textContent: 'Sign in' }));
    const center = $('.top-center');
    if (center) center.append(h('span', { className: 'top-divider', textContent: '/' }), h('span', { id: 'lfDelay', className: 'lf-chip', textContent: 'EARTH LINK …' }));
    setStatus(); refreshDelay(); setInterval(refreshDelay, 60_000);
  }
  async function refreshDelay() {
    const n = $('#lfDelay'); if (!n) return;
    try {
      const s = await (await fetch('/api/mars/status', { cache: 'no-store' })).json();
      n.replaceChildren('EARTH DELAY ', h('b', { textContent: `${s.earth.one_way_minutes} min` }), ` one-way · LMST ${s.mars_time.lmst}`);
      n.title = `Earth–Mars distance ${s.earth.distance_au} AU. Computed live on the server.`;
    } catch { n.textContent = 'EARTH DELAY n/a'; }
  }

  // ---------- account dialog ----------
  function openDialog() {
    let dlg = $('#lfDialog'); if (dlg) dlg.remove();
    dlg = h('dialog', { id: 'lfDialog' });
    document.body.append(dlg);
    (user ? renderAccount : renderAuth)(dlg, 'login');
    dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
    dlg.showModal();
  }

  function renderAuth(dlg, mode) {
    const reg = mode === 'register';
    const msg = h('p', { className: 'msg', role: 'alert' });
    const name = h('input', { name: 'name', maxLength: 80, autocomplete: 'name', required: true });
    const email = h('input', { name: 'email', type: 'email', maxLength: 320, autocomplete: 'email', required: true });
    const pw = h('input', { name: 'password', type: 'password', minLength: reg ? 10 : 1, maxLength: 200, autocomplete: reg ? 'new-password' : 'current-password', required: true });
    const submit = h('button', { className: 'primary', type: 'submit', textContent: reg ? 'Create account' : 'Sign in' });
    const form = h('form', { method: 'dialog' },
      ...(reg ? [h('label', {}, 'NAME', name)] : []),
      h('label', {}, 'EMAIL', email),
      h('label', {}, reg ? 'PASSWORD (10+ characters)' : 'PASSWORD', pw),
      msg,
      h('div', { className: 'row' }, submit,
        h('button', { className: 'ghost', type: 'button', textContent: reg ? 'I have an account' : 'Create account', onclick: () => renderAuth(dlg, reg ? 'login' : 'register') }),
        h('button', { className: 'ghost', type: 'button', textContent: 'Close', onclick: () => dlg.close() })));
    form.addEventListener('submit', async (e) => {
      e.preventDefault(); msg.textContent = ''; submit.disabled = true;
      try {
        const body = { email: email.value, password: pw.value, ...(reg ? { name: name.value } : {}) };
        const r = await api(reg ? '/auth/register' : '/auth/login', { method: 'POST', body });
        user = r.user; setStatus(); dlg.close();
        toast(`Signed in as ${user.name}`);
        await initialSync(); startLoop();
      } catch (err) { msg.textContent = err.message; } finally { submit.disabled = false; }
    });
    dlg.replaceChildren(
      h('div', { className: 'eyebrow', textContent: 'CLOUD SYNC' }),
      h('h2', { textContent: reg ? 'Create your account' : 'Sign in' }),
      h('p', { className: 'hint', textContent: 'Save routes and field notes to your account and open them on any device. An approximate Earth location is synced only if you choose Remember location. The planner still works without an account.' }),
      form);
    (reg ? name : email).focus();
  }

  function renderAccount(dlg) {
    const msg = h('p', { className: 'msg', role: 'status' });
    const out = h('button', { className: 'primary', type: 'button', textContent: 'Sign out', onclick: async () => {
      try { await api('/auth/logout', { method: 'POST' }); } catch { /* ignore */ }
      stopLoop(); user = null; setStatus(); dlg.close(); toast('Signed out');
    } });
    const del = h('button', { className: 'danger', type: 'button', textContent: 'Delete account', onclick: async () => {
      const p = prompt('This permanently deletes your account and cloud data.\nType your password to confirm:');
      if (!p) return;
      try { await api('/account', { method: 'DELETE', body: { password: p } }); stopLoop(); user = null; setStatus(); dlg.close(); toast('Account deleted'); }
      catch (e) { msg.className = 'msg'; msg.textContent = e.message; }
    } });
    dlg.replaceChildren(
      h('div', { className: 'eyebrow', textContent: 'SIGNED IN' }),
      h('h2', { textContent: user.name }),
      h('p', { className: 'hint', textContent: `${user.email} · Routes and field notes sync automatically every few seconds.` }),
      h('div', { className: 'row' },
        h('button', { className: 'ghost', type: 'button', textContent: 'Sync now', onclick: async () => {
          try { await push(await readLocal(), true); msg.className = 'msg ok'; msg.textContent = 'Synced.'; } catch (e) { msg.className = 'msg'; msg.textContent = e.message; }
        } }),
        h('a', { className: 'lf-btn', href: '/api/account/export', textContent: 'Download my data' }),
        out),
      msg,
      h('div', { className: 'row' }, del, h('button', { className: 'ghost', type: 'button', textContent: 'Close', onclick: () => dlg.close() })));
  }

  // ---------- boot ----------
  async function boot() {
    mountHeader();
    try {
      const r = await api('/auth/me');
      if (r.user) { user = r.user; baseRev = loadRev(); setStatus(); await initialSync(); startLoop(); }
    } catch { /* offline: planner keeps working locally */ }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
