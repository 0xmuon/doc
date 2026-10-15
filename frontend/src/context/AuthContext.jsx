/**
 * Who is logged in. Access and refresh tokens stay in localStorage.
 * A 401 in the API client refreshes the access token, or ends the session if that fails.
 */
import { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { fetchCurrentUser, loginUser, registerUser } from "../api/authApi";
import { setSessionExpiredHandler, setTokensRefreshedHandler, tokenStore } from "../api/client";
import { AuthContext } from "./auth-context";

const STORAGE_KEY = "abcshop_session";

function readSession() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function writeSession(next) {
  if (!next) {
    localStorage.removeItem(STORAGE_KEY);
    tokenStore.clear();
    return;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  tokenStore.save({ access_token: next.token, refresh_token: next.refreshToken });
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(readSession);
  const [ready, setReady] = useState(() => !readSession()?.token);
  const [sessionNotice, setSessionNotice] = useState("");

  useEffect(() => {
    setTokensRefreshedHandler((data) => {
      setSession((current) => {
        if (!current) return current;
        const next = { ...current, token: data.access_token, refreshToken: data.refresh_token || current.refreshToken };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        return next;
      });
    });
    setSessionExpiredHandler(() => {
      writeSession(null);
      setSession(null);
    });
  }, []);

  useEffect(() => {
    const saved = readSession();
    if (!saved?.token) return;
    tokenStore.save({ access_token: saved.token, refresh_token: saved.refreshToken });
    fetchCurrentUser(saved.token)
      .then((user) => {
        const next = { ...saved, token: tokenStore.getAccess() || saved.token, user };
        writeSession(next);
        setSession(next);
      })
      .catch(() => {
        writeSession(null);
        setSession(null);
        setSessionNotice("Your session ended. Please log in again.");
      })
      .finally(() => setReady(true));
  }, []);

  const value = useMemo(() => {
    return {
      ready,
      sessionNotice,
      clearSessionNotice() {
        setSessionNotice("");
      },
      token: session?.token ?? "",
      user: session?.user ?? null,
      async login(email, password) {
        const data = await loginUser({ email, password });
        const next = { token: data.access_token, refreshToken: data.refresh_token, user: data.user };
        writeSession(next);
        setSession(next);
      },
      async register(payload) {
        await registerUser(payload);
      },
      logout() {
        writeSession(null);
        setSession(null);
      },
    };
  }, [ready, session, sessionNotice]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired,
};
