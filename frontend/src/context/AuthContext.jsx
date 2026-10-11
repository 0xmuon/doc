import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../services/api";

const AuthContext = createContext(null);
const STORAGE_KEY = "swiftshop_session";

function readSession() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(readSession);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const saved = readSession();
    if (!saved?.token) {
      setReady(true);
      return;
    }
    api("/api/auth/me", { token: saved.token })
      .then((user) => {
        const next = { token: saved.token, user };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        setSession(next);
      })
      .catch(() => {
        localStorage.removeItem(STORAGE_KEY);
        setSession(null);
      })
      .finally(() => setReady(true));
  }, []);

  const value = useMemo(() => {
    return {
      ready,
      token: session?.token ?? "",
      user: session?.user ?? null,
      async login(email, password) {
        const data = await api("/api/auth/login", {
          method: "POST",
          body: { email, password },
        });
        const next = { token: data.access_token, user: data.user };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        setSession(next);
      },
      async register(payload) {
        await api("/api/users/register", { method: "POST", body: payload });
      },
      logout() {
        localStorage.removeItem(STORAGE_KEY);
        setSession(null);
      },
    };
  }, [ready, session]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
