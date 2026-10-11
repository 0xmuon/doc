/**
 * One place that calls the shopping API.
 * In dev, Vite proxies /api to port 8000. A 401 retries once after POST /api/auth/refresh.
 */
const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

const ACCESS_KEY = "abcshop.accessToken";
const REFRESH_KEY = "abcshop.refreshToken";

export const tokenStore = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  save(data) {
    if (data.access_token) localStorage.setItem(ACCESS_KEY, data.access_token);
    if (data.refresh_token) localStorage.setItem(REFRESH_KEY, data.refresh_token);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

let onSessionExpired = () => {};
let onTokensRefreshed = () => {};

export function setSessionExpiredHandler(handler) {
  onSessionExpired = handler;
}

export function setTokensRefreshedHandler(handler) {
  onTokensRefreshed = handler;
}

export class ApiError extends Error {
  constructor(message, status, fieldErrors = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

function messageFrom(data, statusText) {
  const detail = data?.detail;
  const fieldErrors = {};
  if (Array.isArray(detail)) {
    for (const item of detail) {
      const field = item.loc?.[item.loc.length - 1];
      if (field) fieldErrors[field] = item.msg;
    }
    const message = detail.map((item) => item.msg).join(" ");
    return { message: message || statusText || "Request failed", fieldErrors };
  }
  if (typeof detail === "string" && detail) return { message: detail, fieldErrors };
  return { message: statusText || "Request failed", fieldErrors };
}

let refreshing = null;

async function refreshTokens() {
  const refreshToken = tokenStore.getRefresh();
  if (!refreshToken) return false;
  if (!refreshing) {
    refreshing = fetch(`${API_BASE}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
      .then(async (response) => {
        if (!response.ok) return false;
        const data = await response.json();
        tokenStore.save(data);
        onTokensRefreshed(data);
        return true;
      })
      .catch(() => false)
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
}

export async function api(path, { method = "GET", body, token } = {}, allowRefresh = true) {
  const headers = {};
  const access = token || tokenStore.getAccess();
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (access) headers.Authorization = `Bearer ${access}`;
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (response.status === 401 && allowRefresh && path !== "/api/auth/refresh") {
    const renewed = await refreshTokens();
    if (renewed) return api(path, { method, body, token: tokenStore.getAccess() }, false);
    tokenStore.clear();
    onSessionExpired();
  }
  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }
  if (!response.ok) {
    const parsed = messageFrom(data, response.statusText);
    throw new ApiError(parsed.message, response.status, parsed.fieldErrors);
  }
  return data;
}
