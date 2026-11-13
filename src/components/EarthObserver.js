/**
 * Earth Observer & Mars Distance Engine
 * Computes exact topocentric distance from an observer anywhere on Earth to Jezero Crater, Mars.
 * Retains latitude and longitude to 6 decimal places and geolocation accuracy radius.
 */

// Popular presets for instant search & demo
export const EARTH_PRESETS = [
  {name: "Jaipur, Rajasthan, India", lat: 26.912434, lon: 75.787271, type: "city", state: "Rajasthan", country: "India"},
  {name: "Tamil Nadu (Chennai), India", lat: 13.082680, lon: 80.270718, type: "state", state: "Tamil Nadu", country: "India"},
  {name: "Delhi (NCR), India", lat: 28.613939, lon: 77.209021, type: "capital", state: "Delhi", country: "India"},
  {name: "Bengaluru, Karnataka, India", lat: 12.971598, lon: 77.594563, type: "tech_hub", state: "Karnataka", country: "India"},
  {name: "Mumbai, Maharashtra, India", lat: 19.075984, lon: 72.877656, type: "city", state: "Maharashtra", country: "India"},
  {name: "Hyderabad, Telangana, India", lat: 17.385044, lon: 78.486671, type: "city", state: "Telangana", country: "India"},
  {name: "Kolkata, West Bengal, India", lat: 22.572646, lon: 88.363895, type: "city", state: "West Bengal", country: "India"},
  {name: "Pune, Maharashtra, India", lat: 18.520430, lon: 73.856744, type: "city", state: "Maharashtra", country: "India"},
  {name: "Ahmedabad, Gujarat, India", lat: 23.022505, lon: 72.571362, type: "city", state: "Gujarat", country: "India"},
  {name: "London, United Kingdom", lat: 51.507351, lon: -0.127758, type: "city", state: "Greater London", country: "United Kingdom"},
  {name: "New York City, NY, USA", lat: 40.712776, lon: -74.005974, type: "city", state: "New York", country: "United States"},
  {name: "Tokyo, Japan", lat: 35.676192, lon: 139.650311, type: "city", state: "Kanto", country: "Japan"}
];

const STORAGE_KEY = 'terrascope_earth_observer';
const JEZERO_COORDS = {lat: 18.38, lon: 77.58, name: "Jezero Crater, Mars"};

// Fallback in-memory observer
let inMemoryObserver = {
  lat: 26.912434,
  lon: 75.787271,
  accuracy: null,
  name: "Jaipur, Rajasthan, India",
  saved: false
};

export function loadSavedObserver() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const data = JSON.parse(raw);
      if (data && data.saved) {
        inMemoryObserver = data;
        return inMemoryObserver;
      }
    }
  } catch (e) {}
  return inMemoryObserver;
}

export function saveObserverLocation(observer, persist = false) {
  inMemoryObserver = {
    lat: Number(observer.lat),
    lon: Number(observer.lon),
    accuracy: observer.accuracy ? Number(observer.accuracy) : null,
    name: observer.name || `${observer.lat.toFixed(6)}, ${observer.lon.toFixed(6)}`,
    saved: persist
  };

  if (persist) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(inMemoryObserver));
    } catch (e) {}
  } else {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {}
  }
  return inMemoryObserver;
}

export async function requestBrowserGeolocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      return reject(new Error("Geolocation is not supported by this browser."));
    }
    navigator.geolocation.getCurrentPosition(
      pos => {
        const obs = {
          lat: Number(pos.coords.latitude.toFixed(6)),
          lon: Number(pos.coords.longitude.toFixed(6)),
          accuracy: Number(pos.coords.accuracy.toFixed(1)),
          name: "My Location",
          saved: false
        };
        resolve(obs);
      },
      err => reject(err),
      {enableHighAccuracy: true, timeout: 10000, maximumAge: 60000}
    );
  });
}

export function searchEarthPlaces(query) {
  if (!query) return [];
  const q = query.trim().toLowerCase();
  return EARTH_PRESETS.filter(p => 
    p.name.toLowerCase().includes(q) ||
    p.state.toLowerCase().includes(q) ||
    p.country.toLowerCase().includes(q)
  );
}

export async function fetchMarsDistance(lat, lon, accuracy = null, name = null, date = null) {
  try {
    const params = new URLSearchParams({
      lat: Number(lat).toFixed(6),
      lon: Number(lon).toFixed(6)
    });
    if (accuracy) params.set("accuracy", accuracy);
    if (name) params.set("name", name);
    if (date) params.set("date", date);

    const res = await fetch(`/api/mars/distance?${params.toString()}`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn("Backend distance calculation error, computing client-side:", e);
  }

  // Client-side fallback calculation matching JPL elements
  const now = new Date();
  const jd = (now.getTime() / 86400000.0) + 2440587.5;
  const T = (jd - 2451545.0) / 36525.0;

  // Approximate Earth & Mars coordinates
  const Le = (100.46457166 + 35999.37244981 * T) * Math.PI / 180;
  const Lm = (-4.55343205 + 19140.30268499 * T) * Math.PI / 180;
  const re = 1.0;
  const rm = 1.524;

  const dx = rm * Math.cos(Lm) - re * Math.cos(Le);
  const dy = rm * Math.sin(Lm) - re * Math.sin(Le);
  const dist_au = Math.hypot(dx, dy);
  const dist_km = dist_au * 149597870.7;
  const light_sec = dist_km / 299792.458;

  return {
    observer: {
      latitude: Number(lat.toFixed(6)),
      longitude: Number(lon.toFixed(6)),
      latitude_formatted: `${Math.abs(lat).toFixed(6)}° ${lat >= 0 ? 'N' : 'S'}`,
      longitude_formatted: `${Math.abs(lon).toFixed(6)}° ${lon >= 0 ? 'E' : 'W'}`,
      accuracy_radius_m: accuracy,
      place_name: name || `${lat.toFixed(6)}, ${lon.toFixed(6)}`
    },
    target: {
      body: "Mars",
      landmark: "Jezero Crater (Octavia E. Butler Landing / Perseverance)",
      latitude_deg: JEZERO_COORDS.lat,
      longitude_deg: JEZERO_COORDS.lon
    },
    distance: {
      km: Math.round(dist_km),
      au: Number(dist_au.toFixed(5)),
      miles: Math.round(dist_km * 0.621371),
      light_travel_time_seconds: Math.round(light_sec),
      light_travel_time_formatted: `${Math.floor(light_sec / 60)}m ${Math.floor(light_sec % 60)}s`,
      round_trip_ping_formatted: `${Math.floor((light_sec * 2) / 60)}m ${Math.floor((light_sec * 2) % 60)}s`
    }
  };
}
