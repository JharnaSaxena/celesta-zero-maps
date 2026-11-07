import express from 'express';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import team from './data/team.json' with { type: 'json' };
import { db, statements, now, audit } from './db.js';
import {
  hashPassword, verifyPassword, burnTime, createSession, destroySession,
  loadUser, requireAuth, csrfGuard, clientIp,
} from './auth.js';
import { earthMars, marsTime } from './mars.js';
import { issPasses } from './satellites.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const publicDir = path.join(here, '..', 'public');

export const app = express();
if (process.env.VERCEL) app.set('trust proxy', 1);
else if (process.env.TRUST_PROXY) app.set('trust proxy', Number(process.env.TRUST_PROXY) || process.env.TRUST_PROXY);
app.disable('x-powered-by');

app.use(helmet({
  contentSecurityPolicy: {
    useDefaults: false,
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
      fontSrc: ["'self'", 'https://fonts.gstatic.com'],
      imgSrc: ["'self'", 'data:', 'blob:', 'https://trek.nasa.gov', 'https://server.arcgisonline.com'],
      connectSrc: ["'self'"],
      objectSrc: ["'none'"],
      baseUri: ["'self'"],
      formAction: ["'self'"],
      frameAncestors: ["'none'"],
    },
  },
  crossOriginEmbedderPolicy: false,
}));

app.use(express.json({ limit: '600kb' }));
app.use(loadUser);

// ---------- rate limits ----------
const mk = (windowMs, limit, message) => rateLimit({
  windowMs, limit, standardHeaders: 'draft-7', legacyHeaders: false,
  message: { error: message },
});
app.use('/api', mk(60_000, 240, 'Too many requests. Slow down.'));
const authLimiter = mk(15 * 60_000, 20, 'Too many sign-in attempts. Try again in 15 minutes.');
const contactLimiter = mk(60 * 60_000, 5, 'Too many messages. Try again later.');
const satelliteLimiter = mk(60_000, 20, 'ISS pass refresh limit reached. Wait a minute and retry.');
app.use('/api', csrfGuard);

// ---------- validation helpers ----------
const EMAIL_RE = /^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@]{2,}$/;
const clean = (s, max) => String(s ?? '').replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, max);
const bad = (res, msg, code = 400) => res.status(code).json({ error: msg });
const publicUser = (u) => ({ id: u.id, email: u.email, name: u.name });

// ---------- health & public info ----------
app.get('/api/health', (_req, res) => res.json({ ok: true, time: new Date().toISOString() }));
app.get('/api/team', (_req, res) => res.json(team));

app.get('/api/mars/earth-delay', (_req, res) => {
  res.set('Cache-Control', 'no-store');
  res.json(earthMars());
});
app.get('/api/mars/time', (req, res) => {
  const lon = Number(req.query.lon);
  res.set('Cache-Control', 'no-store');
  res.json(marsTime(Date.now(), Number.isFinite(lon) && Math.abs(lon) <= 360 ? lon : 77.58));
});
app.get('/api/mars/status', (_req, res) => {
  res.set('Cache-Control', 'no-store');
  res.json({ earth: earthMars(), mars_time: marsTime() });
});

app.get('/api/satellites/iss', satelliteLimiter, async (req, res) => {
  const latitude = Number(req.query.lat);
  const longitude = Number(req.query.lon);
  if (!Number.isFinite(latitude) || Math.abs(latitude) > 90 || !Number.isFinite(longitude) || Math.abs(longitude) > 180) {
    return bad(res, 'Provide a valid observer location using lat and lon.');
  }
  try {
    const result = await issPasses(latitude, longitude);
    res.set('Cache-Control', 'public, max-age=30, stale-while-revalidate=60');
    return res.json(result);
  } catch (error) {
    console.error('ISS pass prediction unavailable:', error.message);
    return bad(res, 'Live ISS elements are temporarily unavailable. Try again shortly.', 503);
  }
});

// ---------- auth ----------
app.post('/api/auth/register', authLimiter, async (req, res) => {
  const email = clean(req.body?.email, 320).toLowerCase();
  const name = clean(req.body?.name, 80);
  const password = String(req.body?.password ?? '');
  if (!EMAIL_RE.test(email)) return bad(res, 'Enter a valid email address.');
  if (name.length < 1) return bad(res, 'Enter your name.');
  if (password.length < 10 || password.length > 200) return bad(res, 'Password must be 10–200 characters.');
  if (await statements.get('SELECT 1 FROM users WHERE email = ?', email)) {
    // Same cost as a real registration, and a neutral message.
    await burnTime(password);
    return bad(res, 'Could not create that account. Try signing in instead.', 409);
  }
  const { salt, hash } = await hashPassword(password);
  let id;
  try {
    id = Number((await statements.run('INSERT INTO users (email, name, pw_salt, pw_hash, created_at) VALUES (?,?,?,?,?) RETURNING id',
      email, name, salt, hash, now())).lastInsertRowid);
  } catch {
    return bad(res, 'Could not create that account. Try signing in instead.', 409);
  }
  await audit(id, 'register', clientIp(req));
  await createSession(res, id, req.headers['user-agent']);
  res.status(201).json({ user: { id, email, name } });
});

app.post('/api/auth/login', authLimiter, async (req, res) => {
  const email = clean(req.body?.email, 320).toLowerCase();
  const password = String(req.body?.password ?? '').slice(0, 200);
  const row = await statements.get('SELECT * FROM users WHERE email = ?', email);
  let ok = false;
  if (row) ok = await verifyPassword(password, row.pw_salt, row.pw_hash);
  else await burnTime(password);
  if (!ok) {
    await audit(row?.id, 'login_failed', clientIp(req));
    return bad(res, 'Incorrect email or password.', 401);
  }
  await audit(row.id, 'login', clientIp(req));
  await createSession(res, row.id, req.headers['user-agent']);
  res.json({ user: publicUser(row) });
});

app.post('/api/auth/logout', async (req, res) => {
  if (req.user) await audit(req.user.id, 'logout', clientIp(req));
  await destroySession(req, res);
  res.json({ ok: true });
});

app.get('/api/auth/me', (req, res) => {
  res.set('Cache-Control', 'no-store');
  res.json({ user: req.user ? publicUser(req.user) : null });
});

// Privacy: download everything we hold, or delete it all.
app.get('/api/account/export', requireAuth, async (req, res) => {
  const id = req.user.id;
  const ws = await statements.get('SELECT data, rev, updated_at FROM workspaces WHERE user_id = ?', id);
  const briefings = await statements.all('SELECT id, title, payload, created_at FROM briefings WHERE user_id = ?', id);
  res.set('Content-Disposition', 'attachment; filename="zero-maps-account-export.json"');
  res.json({
    user: publicUser(req.user),
    workspace: ws ? { ...ws, data: JSON.parse(ws.data) } : null,
    briefings: briefings.map((b) => ({ ...b, payload: JSON.parse(b.payload) })),
  });
});
app.delete('/api/account', requireAuth, async (req, res) => {
  const row = await statements.get('SELECT * FROM users WHERE id = ?', req.user.id);
  const ok = await verifyPassword(String(req.body?.password ?? '').slice(0, 200), row.pw_salt, row.pw_hash);
  if (!ok) return bad(res, 'Password is incorrect.', 403);
  await audit(row.id, 'account_deleted', clientIp(req));
  await statements.run('DELETE FROM users WHERE id = ?', row.id); // cascades to sessions/workspace/briefings
  await destroySession(req, res);
  res.json({ ok: true });
});

// ---------- workspace sync (routes, notes, layer settings) ----------
const WS_KEYS = ['waypoints', 'route', 'name', 'savedRoutes', 'notes', 'layers', 'zoom', 'cx', 'cy',
  'mode', 'evaHour', 'crewDown', 'scienceWeight', 'marsGravity', 'observerLocation'];

function sanitizeWorkspace(d) {
  if (!d || typeof d !== 'object' || Array.isArray(d)) return null;
  const out = {};
  for (const k of WS_KEYS) if (k in d) out[k] = d[k];
  if ('savedRoutes' in out && (!Array.isArray(out.savedRoutes) || out.savedRoutes.length > 200)) return null;
  if ('notes' in out && (!Array.isArray(out.notes) || out.notes.length > 500)) return null;
  if ('waypoints' in out && (!Array.isArray(out.waypoints) || out.waypoints.length > 8)) return null;
  if ('route' in out && (!Array.isArray(out.route) || out.route.length > 20000)) return null;
  if ('name' in out) out.name = clean(out.name, 120);
  if ('observerLocation' in out && out.observerLocation !== null) {
    const loc = out.observerLocation;
    if (!loc || typeof loc !== 'object' || !Number.isFinite(loc.lat) || !Number.isFinite(loc.lon) || Math.abs(loc.lat) > 90 || Math.abs(loc.lon) > 180 || !Number.isFinite(loc.accuracyKm) || loc.accuracyKm < 0 || loc.accuracyKm > 10000) return null;
    out.observerLocation = { lat: +loc.lat.toFixed(2), lon: +loc.lon.toFixed(2), accuracyKm: Math.round(loc.accuracyKm) };
  }
  return out;
}

app.get('/api/workspace', requireAuth, async (req, res) => {
  res.set('Cache-Control', 'no-store');
  const row = await statements.get('SELECT data, rev, updated_at FROM workspaces WHERE user_id = ?', req.user.id);
  if (!row) return res.json({ rev: 0, data: null, updated_at: null });
  res.json({ rev: row.rev, data: JSON.parse(row.data), updated_at: row.updated_at });
});

app.put('/api/workspace', requireAuth, async (req, res) => {
  const data = sanitizeWorkspace(req.body?.data);
  const baseRev = Number(req.body?.baseRev);
  if (!data) return bad(res, 'Invalid workspace data.');
  if (!Number.isInteger(baseRev) || baseRev < 0) return bad(res, 'baseRev required.');
  const json = JSON.stringify(data);
  if (json.length > 500_000) return bad(res, 'Workspace too large.', 413);
  // One conditional upsert makes revision checks atomic across Vercel instances.
  const saved = await db.query(`
    INSERT INTO workspaces (user_id, data, rev, updated_at)
    SELECT $1,$2,1,$3 WHERE $4 = 0
    ON CONFLICT(user_id) DO UPDATE
      SET data = EXCLUDED.data, rev = workspaces.rev + 1, updated_at = EXCLUDED.updated_at
      WHERE workspaces.rev = $4
    RETURNING rev`, [req.user.id, json, now(), baseRev]);
  if (saved.rowCount) return res.json({ rev: saved.rows[0].rev });
  const row = await statements.get('SELECT data, rev, updated_at FROM workspaces WHERE user_id = ?', req.user.id);
  return res.status(409).json({ error: 'Newer version on server.', rev: row?.rev || 0, data: row ? JSON.parse(row.data) : null });
});

// ---------- briefings ----------
app.get('/api/briefings', requireAuth, async (req, res) => {
  const rows = await statements.all('SELECT id, title, created_at FROM briefings WHERE user_id = ? ORDER BY created_at DESC LIMIT 100', req.user.id);
  res.json({ briefings: rows });
});
app.get('/api/briefings/:id', requireAuth, async (req, res) => {
  const row = await statements.get('SELECT id, title, payload, created_at FROM briefings WHERE id = ? AND user_id = ?',
    Number(req.params.id), req.user.id);
  if (!row) return bad(res, 'Not found.', 404);
  res.json({ ...row, payload: JSON.parse(row.payload) });
});
app.post('/api/briefings', requireAuth, async (req, res) => {
  const p = req.body?.payload;
  if (!p || typeof p !== 'object' || Array.isArray(p)) return bad(res, 'payload object required.');
  const json = JSON.stringify(p);
  if (json.length > 100_000) return bad(res, 'Briefing too large.', 413);
  const count = Number((await statements.get('SELECT COUNT(*) AS n FROM briefings WHERE user_id = ?', req.user.id)).n);
  if (count >= 200) return bad(res, 'Briefing limit reached. Delete some first.', 409);
  const title = clean(req.body?.title, 120) || 'EVA briefing';
  const id = Number((await statements.run('INSERT INTO briefings (user_id, title, payload, created_at) VALUES (?,?,?,?) RETURNING id',
    req.user.id, title, json, now())).lastInsertRowid);
  res.status(201).json({ id });
});
app.delete('/api/briefings/:id', requireAuth, async (req, res) => {
  await statements.run('DELETE FROM briefings WHERE id = ? AND user_id = ?', Number(req.params.id), req.user.id);
  res.json({ ok: true });
});

// ---------- contact form (About page) ----------
app.post('/api/contact', contactLimiter, async (req, res) => {
  if (clean(req.body?.website, 100)) return res.json({ ok: true }); // honeypot: pretend success
  const name = clean(req.body?.name, 80), email = clean(req.body?.email, 320), message = clean(req.body?.message, 2000);
  if (!name || !EMAIL_RE.test(email) || message.length < 10) return bad(res, 'Please fill in name, a valid email and a message (10+ characters).');
  await statements.run('INSERT INTO contact_messages (name, email, message, created_at) VALUES (?,?,?,?)', name, email, message, now());
  res.status(201).json({ ok: true });
});

app.use('/api', (_req, res) => bad(res, 'Not found.', 404));

// ---------- static site ----------
// The planner page gets sync.js injected on the fly, so index.html needs no edits.
function servePlanner(_req, res, next) {
  const file = path.join(publicDir, 'index.html');
  fs.readFile(file, 'utf8', (err, html) => {
    if (err) return next();
    if (!html.includes('sync.js')) html = html.replace('</body>', '<script src="sync.js" defer></script></body>');
    res.type('html').send(html);
  });
}
app.get(['/', '/index.html'], servePlanner);
app.use(express.static(publicDir, { index: false, extensions: ['html'], maxAge: '1h', dotfiles: 'ignore' }));

app.use((err, _req, res, _next) => {
  if (err?.type === 'entity.too.large') return bad(res, 'Request too large.', 413);
  if (err instanceof SyntaxError) return bad(res, 'Invalid JSON.');
  console.error(err);
  res.status(500).json({ error: 'Something went wrong.' });
});

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT) || 3000;
  app.listen(port, () => console.log(`Zero Maps running at http://localhost:${port}`));
}
