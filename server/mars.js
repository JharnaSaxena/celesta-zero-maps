// Live Earth–Mars geometry. Uses JPL "Keplerian elements for approximate positions
// of the major planets" (Standish), valid 1800–2050 AD. Accuracy is good to roughly
// 0.01 AU, i.e. ~5 seconds of light time. Plenty for a planning display.

const AU_KM = 149597870.7;
const C_KM_S = 299792.458;
const rad = (d) => (d * Math.PI) / 180;

// [a, e, I, L, long.peri, long.node] and their rates per Julian century
const ELEMENTS = {
  earth: [1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0,
          0.00000562, -0.00004392, -0.01294668, 35999.37306329, 0.32327364, 0.0],
  mars:  [1.52371034, 0.0933941, 1.84969142, -4.55343205, -23.94362959, 49.55953891,
          0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343],
};

function helio(planet, T) {
  const el = ELEMENTS[planet];
  const a = el[0] + el[6] * T, e = el[1] + el[7] * T, I = rad(el[2] + el[8] * T);
  const L = el[3] + el[9] * T, w = el[4] + el[10] * T, O = rad(el[5] + el[11] * T);
  const omega = rad(w) - O;
  let M = (((L - w) % 360) + 540) % 360 - 180; // degrees, -180..180
  M = rad(M);
  let E = M + e * Math.sin(M);
  for (let i = 0; i < 12; i++) E -= (E - e * Math.sin(E) - M) / (1 - e * Math.cos(E));
  const xp = a * (Math.cos(E) - e), yp = a * Math.sqrt(1 - e * e) * Math.sin(E);
  const cw = Math.cos(omega), sw = Math.sin(omega), cO = Math.cos(O), sO = Math.sin(O);
  const cI = Math.cos(I), sI = Math.sin(I);
  return [
    (cw * cO - sw * sO * cI) * xp + (-sw * cO - cw * sO * cI) * yp,
    (cw * sO + sw * cO * cI) * xp + (-sw * sO + cw * cO * cI) * yp,
    (sw * sI) * xp + (cw * sI) * yp,
  ];
}

const julianDate = (ms) => ms / 86400000 + 2440587.5;

export function earthMars(ms = Date.now()) {
  const T = (julianDate(ms) - 2451545.0) / 36525;
  const e = helio('earth', T), m = helio('mars', T);
  const distAU = Math.hypot(e[0] - m[0], e[1] - m[1], e[2] - m[2]);
  const km = distAU * AU_KM;
  const oneWay = km / C_KM_S;
  return {
    at: new Date(ms).toISOString(),
    distance_au: +distAU.toFixed(4),
    distance_km: Math.round(km),
    one_way_seconds: Math.round(oneWay),
    one_way_minutes: +(oneWay / 60).toFixed(1),
    round_trip_minutes: +((2 * oneWay) / 60).toFixed(1),
    method: 'JPL approximate Keplerian elements (1800–2050); light-time = distance / c',
  };
}

// Mars Sol Date and local mean solar time at a given east longitude (Allison & McEwen / Mars24).
export function marsTime(ms = Date.now(), lonEast = 77.58) {
  const jdUT = julianDate(ms);
  const jdTT = jdUT + (37 + 32.184) / 86400; // TAI-UTC = 37 s since 2017
  const msd = (jdTT - 2405522.0028779) / 1.0274912517;
  const mtc = ((msd % 1) + 1) % 1 * 24; // hours at Mars prime meridian
  const lmst = (((mtc + lonEast / 15) % 24) + 24) % 24;
  const h = Math.floor(lmst), mnt = Math.floor((lmst - h) * 60);
  return {
    mars_sol_date: +msd.toFixed(4),
    sol_number: Math.floor(msd),
    lmst_hours: +lmst.toFixed(3),
    lmst: `${String(h).padStart(2, '0')}:${String(mnt).padStart(2, '0')}`,
    longitude_east: lonEast,
    note: 'Local mean solar time (LMST). Sunset in the model is nominal 18:00.',
  };
}
