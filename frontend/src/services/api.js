// Shopping API from week 3. The browser calls the process on port 8000.
const API_URL = "http://localhost:8000";

export function apiUrl() {
  return API_URL;
}

function messageFrom(data, statusText) {
  const detail = data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(" ");
  }
  if (typeof detail === "string" && detail) {
    return detail;
  }
  return statusText || "Request failed";
}

export async function api(path, { method = "GET", body, token } = {}) {
  const headers = {};
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(messageFrom(data, response.statusText));
  }
  return data;
}
