// End-to-end smoke test: boots the server on a temp database and exercises the API.
import assert from 'node:assert/strict';

if (!process.env.TEST_DATABASE_URL) throw new Error('Set TEST_DATABASE_URL to an isolated disposable PostgreSQL database before running the smoke test.');
process.env.DATABASE_URL = process.env.TEST_DATABASE_URL;
const { app } = await import('../server/server.js');
const server = app.listen(0);
const base = `http://127.0.0.1:${server.address().port}`;

let cookie = '';
async function call(method, url, body, { csrf = true, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (csrf) headers['X-Requested-With'] = 'lifeline';
  if (auth && cookie) headers.Cookie = cookie;
  const res = await fetch(base + url, { method, headers, body: body ? JSON.stringify(body) : undefined });
  const sc = res.headers.get('set-cookie');
  if (sc) cookie = sc.split(';')[0].endsWith('=') ? '' : sc.split(';')[0];
  const text = await res.text();
  let json; try { json = JSON.parse(text); } catch { json = null; }
  return { status: res.status, json, text, headers: res.headers };
}
let n = 0;
const ok = (name) => console.log(`  ✓ ${++n}. ${name}`);

try {
  let r = await call('GET', '/api/health');
  assert.equal(r.status, 200); ok('health');

  r = await call('GET', '/api/mars/earth-delay');
  assert.ok(r.json.one_way_minutes > 2.5 && r.json.one_way_minutes < 24.5, `delay ${r.json.one_way_minutes}`);
  assert.ok(r.json.distance_au > 0.37 && r.json.distance_au < 2.7);
  ok(`earth delay plausible (${r.json.one_way_minutes} min, ${r.json.distance_au} AU)`);

  // Sanity check of the orbital maths against a known event: Mars opposition 2025-01-16, ~0.64 AU
  const { earthMars, marsTime } = await import('../server/mars.js');
  const opp = earthMars(Date.UTC(2025, 0, 16));
  assert.ok(Math.abs(opp.distance_au - 0.645) < 0.03, `opposition ${opp.distance_au}`);
  ok(`orbital maths vs 2025 opposition (${opp.distance_au} AU, expected ~0.64)`);
  const mt = marsTime(Date.UTC(2000, 0, 6, 0, 0, 0), 0);
  assert.ok(Math.abs(mt.mars_sol_date - 44796) < 0.1, `MSD ${mt.mars_sol_date}`);
  ok(`Mars Sol Date at 2000-01-06 = ${mt.mars_sol_date} (expected ~44796.0)`);

  r = await call('GET', '/api/mars/time?lon=77.58');
  assert.match(r.json.lmst, /^\d\d:\d\d$/); ok('LMST format');

  assert.match(r.headers.get('content-security-policy'), /default-src 'self'/);
  assert.equal(r.headers.get('x-powered-by'), null); ok('security headers (CSP on, x-powered-by off)');

  r = await call('POST', '/api/auth/register', { email: 'a@b.co', name: 'A', password: 'longenoughpw1' }, { csrf: false });
  assert.equal(r.status, 403); ok('CSRF header required on writes');

  r = await call('POST', '/api/auth/register', { email: 'bad', name: 'A', password: 'longenoughpw1' });
  assert.equal(r.status, 400); ok('rejects bad email');
  r = await call('POST', '/api/auth/register', { email: 'a@b.co', name: 'A', password: 'short' });
  assert.equal(r.status, 400); ok('rejects short password');

  r = await call('GET', '/api/workspace');
  assert.equal(r.status, 401); ok('workspace requires auth');

  r = await call('POST', '/api/auth/register', { email: 'Ada@Example.com', name: 'Ada', password: 'correct horse battery' });
  assert.equal(r.status, 201); assert.ok(cookie.startsWith('zero_maps_sid=')); ok('register + session cookie');

  r = await call('GET', '/api/auth/me');
  assert.equal(r.json.user.email, 'ada@example.com'); ok('me (email normalised)');

  const saved = cookie; cookie = '';
  r = await call('POST', '/api/auth/register', { email: 'ada@example.com', name: 'X', password: 'another long password' });
  assert.equal(r.status, 409); ok('duplicate email rejected');
  r = await call('POST', '/api/auth/login', { email: 'ada@example.com', password: 'wrong password!!' });
  assert.equal(r.status, 401); assert.equal(r.json.error, 'Incorrect email or password.');
  r = await call('POST', '/api/auth/login', { email: 'nobody@example.com', password: 'wrong password!!' });
  assert.equal(r.json.error, 'Incorrect email or password.'); ok('wrong password / unknown user give same error');
  r = await call('POST', '/api/auth/login', { email: 'ada@example.com', password: 'correct horse battery' });
  assert.equal(r.status, 200); ok('login');
  void saved;

  const ws = { name: 'Three Forks walk', savedRoutes: [{ name: 'R1', points: [{ x: 1, y: 2 }, { x: 3, y: 4 }] }], notes: [{ title: 'n', body: 'b' }], evaHour: 11, evil: '<script>' };
  r = await call('PUT', '/api/workspace', { data: ws, baseRev: 0 });
  assert.equal(r.status, 200); assert.equal(r.json.rev, 1); ok('workspace save (rev 1)');
  r = await call('GET', '/api/workspace');
  assert.equal(r.json.data.name, 'Three Forks walk'); assert.equal('evil' in r.json.data, false); ok('workspace load, unknown keys stripped');
  r = await call('PUT', '/api/workspace', { data: ws, baseRev: 0 });
  assert.equal(r.status, 409); assert.equal(r.json.rev, 1); ok('stale write → 409 conflict');
  r = await call('PUT', '/api/workspace', { data: { savedRoutes: 'nope' }, baseRev: 1 });
  assert.equal(r.status, 400); ok('invalid workspace shape rejected');
  r = await call('PUT', '/api/workspace', { data: { notes: [{ body: 'x'.repeat(600000) }] }, baseRev: 1 });
  assert.ok([400, 413].includes(r.status)); ok('oversized workspace rejected');

  r = await call('POST', '/api/briefings', { title: 'Brief 1', payload: { margin: 42 } });
  assert.equal(r.status, 201); const bid = r.json.id;
  r = await call('GET', '/api/briefings'); assert.equal(r.json.briefings.length, 1);
  r = await call('GET', `/api/briefings/${bid}`); assert.equal(r.json.payload.margin, 42); ok('briefings create/list/read');

  r = await call('POST', '/api/contact', { name: 'Bot', email: 'bot@x.io', message: 'hello there friend', website: 'spam.com' });
  assert.equal(r.status, 200);
  r = await call('POST', '/api/contact', { name: 'Real', email: 'real@x.io', message: 'hello there team' });
  assert.equal(r.status, 201); ok('contact form (honeypot + real)');

  r = await call('GET', '/api/team'); assert.equal(r.json.company.name, 'Celesta'); ok('team endpoint');

  r = await call('GET', '/api/account/export');
  assert.equal(r.json.briefings.length, 1); assert.equal(r.json.user.email, 'ada@example.com'); ok('account export');

  // Rate limiting on auth
  let limited = false;
  for (let i = 0; i < 25 && !limited; i++) {
    const x = await call('POST', '/api/auth/login', { email: 'ada@example.com', password: 'bad bad bad bad' }, { auth: false });
    if (x.status === 429) limited = true;
  }
  assert.ok(limited); ok('auth brute-force rate limit (429)');

  // Static: planner gets sync.js injected; about page served
  r = await call('GET', '/');
  assert.match(r.text, /<script src="\/?sync.js" defer><\/script>/); ok('sync.js is loaded by the planner page');
  r = await call('GET', '/about'); assert.equal(r.status, 200); assert.match(r.text, /Celesta|Zero Maps/); ok('/about served');
  r = await call('GET', '/server/data/team.json'); assert.equal(r.status, 404); ok('server files not exposed');
  r = await call('GET', '/../server/db.js'); assert.notEqual(r.status, 200); ok('path traversal blocked');

  // Delete account (rate limiter shared with login window is per-route; delete isn't limited by authLimiter)
  r = await call('DELETE', '/api/account', { password: 'wrong' }); assert.equal(r.status, 403);
  r = await call('DELETE', '/api/account', { password: 'correct horse battery' }); assert.equal(r.status, 200);
  r = await call('GET', '/api/auth/me'); assert.equal(r.json.user, null); ok('delete account wipes user + session');

  console.log(`\nAll ${n} checks passed.`);
} catch (e) {
  console.error('\nFAILED:', e.message);
  process.exitCode = 1;
} finally {
  server.close();
  setTimeout(() => process.exit(process.exitCode || 0), 100);
}
