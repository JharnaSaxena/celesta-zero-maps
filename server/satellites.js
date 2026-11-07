import {
  twoline2satrec, propagate, gstime, eciToGeodetic, eciToEcf,
  ecfToLookAngles, degreesToRadians, radiansToDegrees,
} from 'satellite.js';

const CATALOG = 25544;
const TLE_URL = `https://celestrak.org/NORAD/elements/gp.php?CATNR=${CATALOG}&FORMAT=TLE`;
const TLE_MAX_AGE = 15 * 60_000;
const PASS_ALTITUDE = degreesToRadians(10);
let tleCache = null;

async function getISSRecord() {
  if (tleCache && Date.now() - tleCache.fetchedAt < TLE_MAX_AGE) return tleCache;
  try {
    const response = await fetch(TLE_URL, {
      headers: { 'User-Agent': 'ZeroMaps/1.0 (public educational satellite tracker)' },
      signal: AbortSignal.timeout(8_000),
    });
    if (!response.ok) throw new Error(`CelesTrak responded ${response.status}`);
    const rows = (await response.text()).trim().split(/\r?\n/).map((row) => row.trim());
    const first = rows.findIndex((row) => row.startsWith('1 25544'));
    if (first < 0 || !rows[first + 1]?.startsWith('2 25544')) throw new Error('CelesTrak returned an invalid ISS element set');
    const [line1, line2] = [rows[first], rows[first + 1]];
    const satrec = twoline2satrec(line1, line2);
    if (satrec.error) throw new Error('ISS element set could not be initialized');
    tleCache = { name: rows[first - 1] || 'ISS (ZARYA)', line1, line2, epoch: satrec.jdsatepoch, fetchedAt: Date.now(), satrec, stale: false };
    return tleCache;
  } catch (error) {
    if (tleCache) return { ...tleCache, stale: true };
    throw error;
  }
}

function observerPosition(date, record, latitude, longitude) {
  const position = propagate(record.satrec, date)?.position;
  if (!position) return null;
  const gmst = gstime(date);
  const location = { latitude: degreesToRadians(latitude), longitude: degreesToRadians(longitude), height: 0.02 };
  const look = ecfToLookAngles(location, eciToEcf(position, gmst));
  const subpoint = eciToGeodetic(position, gmst);
  return {
    azimuth_deg: (radiansToDegrees(look.azimuth) + 360) % 360,
    elevation_deg: radiansToDegrees(look.elevation),
    range_km: look.rangeSat,
    altitude_km: subpoint.height,
    subpoint: { lat: radiansToDegrees(subpoint.latitude), lon: radiansToDegrees(subpoint.longitude) },
  };
}

function findPasses(record, latitude, longitude, now) {
  const stepMs = 60_000;
  const until = now.getTime() + 48 * 60 * 60_000;
  const passes = [];
  let previousTime = now.getTime();
  let previous = observerPosition(new Date(previousTime), record, latitude, longitude);
  let active = null;
  for (let time = previousTime + stepMs; time <= until && passes.length < 8; time += stepMs) {
    const current = observerPosition(new Date(time), record, latitude, longitude);
    if (!current) continue;
    const isAbove = current.elevation_deg >= 10;
    const wasAbove = previous && previous.elevation_deg >= 10;
    if (isAbove && !wasAbove) {
      const fraction = (10 - previous.elevation_deg) / (current.elevation_deg - previous.elevation_deg || 1);
      const aos = previousTime + Math.max(0, Math.min(1, fraction)) * stepMs;
      active = { aos, peakTime: time, peakElevation: current.elevation_deg, los: null };
    } else if (isAbove && active && current.elevation_deg > active.peakElevation) {
      active.peakElevation = current.elevation_deg;
      active.peakTime = time;
    } else if (!isAbove && wasAbove && active) {
      const fraction = (previous.elevation_deg - 10) / (previous.elevation_deg - current.elevation_deg || 1);
      active.los = previousTime + Math.max(0, Math.min(1, fraction)) * stepMs;
      if (active.aos > now.getTime() + 30_000) passes.push({
        aos: new Date(active.aos).toISOString(),
        peak: new Date(active.peakTime).toISOString(),
        los: new Date(active.los).toISOString(),
        max_elevation_deg: Math.round(active.peakElevation),
      });
      active = null;
    }
    previous = current;
    previousTime = time;
  }
  return passes;
}

export async function issPasses(latitude, longitude) {
  const record = await getISSRecord();
  const now = new Date();
  const position = observerPosition(now, record, latitude, longitude);
  if (!position) throw new Error('ISS position could not be propagated');
  return {
    satellite: record.name,
    norad_id: CATALOG,
    source: TLE_URL,
    fetched_at: new Date(record.fetchedAt).toISOString(),
    stale_element_set: record.stale,
    tle_epoch_jd: record.epoch,
    observer: { lat: latitude, lon: longitude },
    current: position,
    pass_threshold_deg: 10,
    prediction_window_hours: 48,
    passes: findPasses(record, latitude, longitude, now),
  };
}
