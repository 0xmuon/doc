/** Auth calls for this API. Login is JSON, and register includes mobile. */
import { api } from "./client";

export function loginUser({ email, password }) {
  return api("/api/auth/login", { method: "POST", body: { email, password } });
}

export function registerUser(payload) {
  return api("/api/users/register", { method: "POST", body: payload });
}

export function fetchCurrentUser(token) {
  return api("/api/auth/me", { token });
}
