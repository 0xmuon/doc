/**
 * Login. The button stays disabled until both fields are valid.
 * After a successful login the person returns to the page they came from.
 */
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ErrorNote } from "../components/common/StatusMessage";
import { safeReturnPath, useAuth } from "../context/auth-context";
import { useForm } from "../hooks/useForm";
import { validateEmail, validateLoginPassword } from "../utils/validate";

function validate(values) {
  return {
    email: validateEmail(values.email),
    password: validateLoginPassword(values.password),
  };
}

export default function LoginPage() {
  const { login, sessionNotice, clearSessionNotice } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const form = useForm({ email: location.state?.email || "", password: "" }, validate);
  const [serverError, setServerError] = useState("");
  const [busy, setBusy] = useState(false);
  const notice = location.state?.message || sessionNotice || "";

  async function onSubmit(event) {
    event.preventDefault();
    form.touchAll();
    if (!form.isValid || busy) return;
    setBusy(true);
    setServerError("");
    try {
      await login(form.values.email.trim(), form.values.password);
      clearSessionNotice();
      navigate(safeReturnPath(location.state?.from), { replace: true });
    } catch (error) {
      setServerError(error.status === 401 ? "Invalid email or password" : `Login failed: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="panel mx-auto max-w-md space-y-4 p-6 sm:p-8" noValidate>
      <div className="text-center">
        <p className="text-sm font-semibold tracking-wide text-red-600">ABC Shop</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">Welcome back</h1>
        <p className="mt-2 text-sm text-slate-600">Sign in with the email and password for your account.</p>
      </div>
      {notice && !serverError ? (
        <p className="rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-800">{notice}</p>
      ) : null}
      <label className="field-label">
        Email address
        <input name="email" type="email" autoComplete="email" value={form.values.email} onChange={form.handleChange} onBlur={form.handleBlur} className="field" />
        {form.visibleError("email") ? <span className="field-error">{form.visibleError("email")}</span> : null}
      </label>
      <label className="field-label">
        Password
        <input name="password" type="password" autoComplete="current-password" value={form.values.password} onChange={form.handleChange} onBlur={form.handleBlur} className="field" />
        {form.visibleError("password") ? <span className="field-error">{form.visibleError("password")}</span> : null}
      </label>
      {serverError ? <ErrorNote message={serverError} /> : null}
      <button type="submit" disabled={!form.isValid || busy} className="btn-primary w-full">
        {busy ? "Logging in..." : "Login"}
      </button>
      <button type="button" className="btn-danger w-full" onClick={() => { form.reset(); setServerError(""); }}>
        Reset
      </button>
      <p className="text-center text-sm text-slate-600">
        Don&apos;t have an account? <Link to="/register" className="font-semibold text-blue-700 hover:underline">Register</Link>
      </p>
    </form>
  );
}
