import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { validateEmail, validateLoginPassword } from "../utils/validate";

const empty = { email: "", password: "" };

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(empty);
  const [serverError, setServerError] = useState("");
  const [busy, setBusy] = useState(false);

  const errors = useMemo(
    () => ({
      email: validateEmail(form.email),
      password: validateLoginPassword(form.password),
    }),
    [form],
  );
  const valid = Object.values(errors).every((item) => item === "");

  function update(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function onSubmit(event) {
    event.preventDefault();
    if (!valid || busy) return;
    setBusy(true);
    setServerError("");
    try {
      await login(form.email.trim(), form.password);
      navigate("/products");
    } catch (error) {
      setServerError(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-md space-y-4" noValidate>
      <h1 className="text-center text-2xl font-semibold">Login</h1>
      <label className="block text-sm">
        Email address
        <input name="email" type="email" value={form.email} onChange={update} className="mt-1 w-full rounded border px-3 py-2" />
        {form.email && errors.email ? <span className="text-red-700">{errors.email}</span> : null}
      </label>
      <label className="block text-sm">
        Password
        <input name="password" type="password" value={form.password} onChange={update} className="mt-1 w-full rounded border px-3 py-2" />
        {form.password && errors.password ? <span className="text-red-700">{errors.password}</span> : null}
      </label>
      {serverError ? <p className="text-sm text-red-700">{serverError}</p> : null}
      <button type="submit" disabled={!valid || busy} className="w-full rounded bg-blue-600 px-3 py-2 text-white hover:bg-blue-700 disabled:opacity-50">
        {busy ? "Logging in..." : "Login"}
      </button>
      <button type="button" className="w-full rounded bg-red-600 px-3 py-2 text-white hover:bg-red-700" onClick={() => { setForm(empty); setServerError(""); }}>
        Reset
      </button>
      <p className="text-center text-sm">
        Don&apos;t have an account? <Link to="/register" className="underline">Register</Link>
      </p>
    </form>
  );
}
