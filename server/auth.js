import crypto from 'node:crypto';
import { promisify } from 'node:util';
import { statements, now, audit, sha256, purgeExpired } from './db.js';

const scrypt = promisify(crypto.scrypt);
const SCRYPT = { N: 2 ** 15, r: 8, p: 1, maxmem: 128 * 1024 * 1024 };
const KEYLEN = 64;
export const COOKIE = 'zero_maps_sid';
const SESSION_DAYS = 14;
const IS_PROD = process.env.NODE_ENV === 'production';

export async function hashPassword(password, salt = crypto.randomBytes(16)) {
  const hash = await scrypt(password, salt, KEYLEN, SCRYPT);
  return { salt, hash };
}

const DUMMY = await hashPassword('dummy-password-for-timing');
export async function verifyPassword(password, salt, hash) {
  const test = await scrypt(password, salt, KEYLEN, SCRYPT);
  return crypto.timingSafeEqual(test, hash);
}
export async function burnTime(password) {
  await verifyPassword(password, DUMMY.salt, DUMMY.hash).catch(() => {});
}

export function parseCookies(header = '') {
  const out = {};
  for (const part of header.split(';')) {
    const i = part.indexOf('=');
    if (i < 0) continue;
    try { out[part.slice(0, i).trim()] = decodeURIComponent(part.slice(i + 1).trim()); }
    catch { /* ignore malformed cookie */ }
  }
  return out;
}

export async function createSession(res, userId, userAgent) {
  await purgeExpired();
  const token = crypto.randomBytes(32).toString('base64url');
  const ttl = SESSION_DAYS * 86400;
  await statements.run(
    'INSERT INTO sessions (token_hash, user_id, created_at, expires_at, user_agent) VALUES (?,?,?,?,?)',
    sha256(token), userId, now(), now() + ttl, (userAgent || '').slice(0, 200),
  );
  res.setHeader('Set-Cookie',
    `${COOKIE}=${token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=${ttl}${IS_PROD ? '; Secure' : ''}`);
}

export async function destroySession(req, res) {
  const token = parseCookies(req.headers.cookie)[COOKIE];
  if (token) await statements.run('DELETE FROM sessions WHERE token_hash = ?', sha256(token));
  res.setHeader('Set-Cookie', `${COOKIE}=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0${IS_PROD ? '; Secure' : ''}`);
}

export async function loadUser(req, _res, next) {
  req.user = null;
  try {
    const token = parseCookies(req.headers.cookie)[COOKIE];
    if (token) {
      req.user = await statements.get(`
        SELECT u.id, u.email, u.name FROM sessions s JOIN users u ON u.id = s.user_id
        WHERE s.token_hash = ? AND s.expires_at > ?`, sha256(token), now()) || null;
    }
    next();
  } catch (error) { next(error); }
}

export function requireAuth(req, res, next) {
  if (!req.user) return res.status(401).json({ error: 'Sign in required.' });
  next();
}

// SameSite=Strict + a custom header + same-origin Origin check for cookie-authenticated writes.
export function csrfGuard(req, res, next) {
  if (['GET', 'HEAD', 'OPTIONS'].includes(req.method)) return next();
  if (req.headers['x-requested-with'] !== 'lifeline') {
    return res.status(403).json({ error: 'Missing request header.' });
  }
  const origin = req.headers.origin;
  if (origin) {
    let ok = false;
    try { ok = new URL(origin).host === req.headers.host; } catch { /* invalid */ }
    if (!ok) return res.status(403).json({ error: 'Cross-origin request blocked.' });
  }
  next();
}

export const clientIp = (req) => req.ip;
export { audit };
