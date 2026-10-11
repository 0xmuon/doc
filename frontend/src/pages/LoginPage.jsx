/**
 * Login. The button stays disabled until both fields are valid.
 * After a successful login the person returns to the page they came from.
 */
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { safeReturnPath, useAuth } from "../context/AuthContext";
import { useForm } from "../hooks/useForm";
import { validateEmail, validateLoginPassword } from "../utils/validate";

const empty = { email: "", password: "" };

function validate(values) {
  return {
    email: validateEmail(values.email),
    password: validateLoginPassword(values.password),
  };
}

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const form = useForm(empty, validate);
  const [serverError, setServerError] = useState("");
  const [busy, setBusy] = useState(false);
  const notice = location.state?.message || "";

  async function onSubmit(event) {
    event.preventDefault();
    form.touchAll();
    if (!form.isValid || busy) return;
    setBusy(true);
    setServerError("");
    try {
      await login(form.values.email.trim(), form.values.password);
      navigate(safeReturnPath(location.state?.from), { replace: true });
    } catch (error) {
      setServerError(error.status === 401 ? "Invalid email or password" : error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-md space-y-4" noValidate>
      <h1 className="text-center text-2xl font-semibold">Login</h1>
      {notice && !serverError ? <p className="text-sm text-blue-700">{notice}</p> : null}
      <label className="block text-sm">
        Email address
        <input name="email" type="email" value={form.values.email} onChange={form.handleChange} onBlur={form.handleBlur} className="mt-1 w-full rounded border px-3 py-2" />
        {form.visibleError("email") ? <span className="text-red-700">{form.visibleError("email")}</span> : null}
      </label>
      <label className="block text-sm">
        Password
        <input name="password" type="password" value={form.values.password} onChange={form.handleChange} onBlur={form.handleBlur} className="mt-1 w-full rounded border px-3 py-2" />
        {form.visibleError("password") ? <span className="text-red-700">{form.visibleError("password")}</span> : null}
      </label>
      {serverError ? <p className="text-sm text-red-700">{serverError}</p> : null}
      <button type="submit" disabled={!form.isValid || busy} className="w-full rounded bg-blue-600 px-3 py-2 text-white hover:bg-blue-700 disabled:opacity-50">
        {busy ? "Logging in..." : "Login"}
      </button>
      <button type="button" className="w-full rounded bg-red-600 px-3 py-2 text-white hover:bg-red-700" onClick={() => { form.reset(); setServerError(""); }}>
        Reset
      </button>
      <p className="text-center text-sm">
        Don&apos;t have an account? <Link to="/register" className="underline">Register</Link>
      </p>
    </form>
  );
}
