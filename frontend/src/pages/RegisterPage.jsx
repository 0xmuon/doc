import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { validateEmail, validateMobile, validateName, validatePassword } from "../utils/validate";

const empty = { name: "", email: "", password: "", mobile: "" };

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(empty);
  const [serverError, setServerError] = useState("");
  const [busy, setBusy] = useState(false);

  const errors = useMemo(
    () => ({
      name: validateName(form.name),
      email: validateEmail(form.email),
      password: validatePassword(form.password),
      mobile: validateMobile(form.mobile),
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
      await register({
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
        mobile: form.mobile.trim(),
      });
      navigate("/login");
    } catch (error) {
      setServerError(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-md space-y-4" noValidate>
      <h1 className="text-center text-2xl font-semibold">Register</h1>
      <label className="block text-sm">
        Full Name
        <input name="name" value={form.name} onChange={update} className="mt-1 w-full rounded border px-3 py-2" />
        {form.name && errors.name ? <span className="text-red-700">{errors.name}</span> : null}
      </label>
      <label className="block text-sm">
        Email address
        <input name="email" type="email" value={form.email} onChange={update} className="mt-1 w-full rounded border px-3 py-2" />
        {form.email && errors.email ? <span className="text-red-700">{errors.email}</span> : null}
      </label>
      <label className="block text-sm">
        Mobile
        <input name="mobile" inputMode="numeric" value={form.mobile} onChange={update} className="mt-1 w-full rounded border px-3 py-2" />
        {form.mobile && errors.mobile ? <span className="text-red-700">{errors.mobile}</span> : null}
      </label>
      <label className="block text-sm">
        Password
        <input name="password" type="password" value={form.password} onChange={update} className="mt-1 w-full rounded border px-3 py-2" />
        {form.password && errors.password ? <span className="text-red-700">{errors.password}</span> : null}
      </label>
      {serverError ? <p className="text-sm text-red-700">{serverError}</p> : null}
      <button type="submit" disabled={!valid || busy} className="w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-900 hover:bg-slate-50 disabled:opacity-50">
        {busy ? "Registering..." : "Register"}
      </button>
      <button type="button" className="w-full rounded bg-red-600 px-3 py-2 text-white hover:bg-red-700" onClick={() => { setForm(empty); setServerError(""); }}>
        Reset
      </button>
      <p className="text-center text-sm">
        Already have an account? <Link to="/login" className="underline">Login</Link>
      </p>
    </form>
  );
}
