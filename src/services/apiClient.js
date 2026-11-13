/**
 * Jezero Crater & TerraScope Operations API Client
 * Provides seamless communication with the backend server with graceful fallback.
 */

const API_BASE = '/api';

export const apiClient = {
  async getHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      return res.ok ? await res.json() : null;
    } catch (e) {
      return null;
    }
  },

  async getMarsTime() {
    try {
      const res = await fetch(`${API_BASE}/mars/telemetry/time`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn('API getMarsTime fallback:', e);
    }
    return null;
  },

  async getTelemetry(rover = 'Perseverance') {
    try {
      const res = await fetch(`${API_BASE}/mars/telemetry/current?rover=${encodeURIComponent(rover)}`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn('API getTelemetry fallback:', e);
    }
    return null;
  },

  async getWeather() {
    try {
      const res = await fetch(`${API_BASE}/mars/weather/current`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn('API getWeather fallback:', e);
    }
    return null;
  },

  async getSites(params = {}) {
    try {
      const query = new URLSearchParams(params).toString();
      const res = await fetch(`${API_BASE}/mars/sites${query ? `?${query}` : ''}`);
      if (res.ok) {
        const data = await res.json();
        return data.sites || [];
      }
    } catch (e) {
      console.warn('API getSites fallback:', e);
    }
    return null;
  },

  async assessLifeline(x, z) {
    try {
      const res = await fetch(`${API_BASE}/mars/lifeline/assess`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({x, z})
      });
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn('API assessLifeline fallback:', e);
    }
    return null;
  },

  async planRoute(fromSiteOrCoords, toSiteOrCoords, mode = 'balanced') {
    try {
      const payload = {mode};
      if (typeof fromSiteOrCoords === 'string') payload.from_site_id = fromSiteOrCoords;
      else { payload.from_x = fromSiteOrCoords.x; payload.from_z = fromSiteOrCoords.z; }

      if (typeof toSiteOrCoords === 'string') payload.to_site_id = toSiteOrCoords;
      else { payload.to_x = toSiteOrCoords.x; payload.to_z = toSiteOrCoords.z; }

      const res = await fetch(`${API_BASE}/mars/routes/plan`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn('API planRoute fallback:', e);
    }
    return null;
  },

  async dispatchRoverCommand(command, params = {}, roverId = 'Perseverance') {
    try {
      const res = await fetch(`${API_BASE}/mars/telemetry/command`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({rover_id: roverId, command, params})
      });
      return await res.json();
    } catch (e) {
      return {error: e.message};
    }
  },

  async getSampleCache() {
    try {
      const res = await fetch(`${API_BASE}/mars/telemetry/samples`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn('API getSampleCache fallback:', e);
    }
    return null;
  }
};
