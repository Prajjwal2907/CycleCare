/* Shared CycleCare API client for the static frontend. */
const CycleCareAPI = (() => {
  const API_BASE = localStorage.getItem("cyclecare_api_base") || "http://localhost:8000/api";

  function getAccessToken() {
    return localStorage.getItem("cyclecare_access_token");
  }

  function setSession(data) {
    if (data.tokens) {
      localStorage.setItem("cyclecare_access_token", data.tokens.access);
      localStorage.setItem("cyclecare_refresh_token", data.tokens.refresh);
    }
    if (data.user) localStorage.setItem("cyclecare_user", JSON.stringify(data.user));
    if (data.profile) localStorage.setItem("cyclecare_profile", JSON.stringify(data.profile));
  }

  function clearSession() {
    ["cyclecare_access_token", "cyclecare_refresh_token", "cyclecare_user", "cyclecare_profile"].forEach((key) => localStorage.removeItem(key));
  }

  async function request(path, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (!(options.body instanceof FormData) && options.body !== undefined) headers.set("Content-Type", "application/json");

    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    let payload = null;
    try { payload = await response.json(); } catch (_) { payload = {}; }

    if (response.status === 401 && localStorage.getItem("cyclecare_refresh_token")) {
      const refreshed = await fetch(`${API_BASE}/accounts/token/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: localStorage.getItem("cyclecare_refresh_token") })
      });
      if (refreshed.ok) {
        const refreshData = await refreshed.json();
        localStorage.setItem("cyclecare_access_token", refreshData.access);
        return request(path, options);
      }
      clearSession();
    }

    if (!response.ok) {
      const detail = payload.detail || Object.values(payload).flat().join(" ") || `Request failed (${response.status})`;
      throw new Error(detail);
    }
    return payload;
  }

  function unwrap(payload) {
    return payload && Array.isArray(payload.results) ? payload.results : payload;
  }

  return {
    API_BASE,
    request,
    unwrap,
    setSession,
    clearSession,
    getUser: () => JSON.parse(localStorage.getItem("cyclecare_user") || "null"),
    getProfile: () => JSON.parse(localStorage.getItem("cyclecare_profile") || "null"),
    isAuthenticated: () => Boolean(getAccessToken()),
    register: (body) => request("/accounts/register/", { method: "POST", body: JSON.stringify(body) }),
    login: (body) => request("/accounts/login/", { method: "POST", body: JSON.stringify(body) }),
    profile: (body) => request("/accounts/profile/", { method: body ? "PATCH" : "GET", body: body ? JSON.stringify(body) : undefined }),
    cycles: () => request("/cycles/"),
    createCycle: (body) => request("/cycles/entries/", { method: "POST", body: JSON.stringify(body) }),
    cycleSummary: () => request("/cycles/summary/"),
    consents: () => request("/accounts/consent/"),
    grantConsent: (body) => request("/accounts/consent/grant/", { method: "POST", body: JSON.stringify(body) }),
    revokeConsent: (body) => request("/accounts/consent/revoke/", { method: "POST", body: JSON.stringify(body) }),
    craving: (craving) => request("/nutrition/craving/", { method: "POST", body: JSON.stringify({ craving }) }),
    suggestions: () => request("/suggestions/"),
    generateSuggestions: (patientId) => request("/suggestions/generate-ai/", { method: "POST", body: JSON.stringify(patientId ? { patient_id: patientId } : {}) }),
    pendingSuggestions: () => request("/suggestions/doctor/pending/"),
    reviewSuggestion: (id, body) => request(`/suggestions/${id}/review/`, { method: "PATCH", body: JSON.stringify(body) }),
    createSuggestion: (body) => request("/suggestions/doctor/create/", { method: "POST", body: JSON.stringify(body) }),
    doctorsPatients: () => request("/doctors/patients/"),
    patientDashboard: (id) => request(`/doctors/patients/${id}/dashboard/`),
    wearableConnect: (provider) => request(`/wearables/oauth/connect/?provider=${encodeURIComponent(provider)}`),
    wearableConnections: () => request("/wearables/connections/"),
    sleepTrends: () => request("/wearables/sleep/trends/"),
    exerciseTrends: () => request("/wearables/exercise/trends/"),
    logout: clearSession
  };
})();

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-logout]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      CycleCareAPI.logout();
      window.location.href = "index.html";
    });
  });
});
