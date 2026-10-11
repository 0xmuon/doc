/**
 * Register. A duplicate email is shown under the email field.
 * Success goes to login with a confirmation message.
 */
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/auth-context";
import { useForm } from "../hooks/useForm";
import { validateEmail, validateMobile, validateName, validatePassword } from "../utils/validate";

const empty = { name: "", email: "", password: "", mobile: "" };

function validate(values) {
  return {
    name: validateName(values.name),
    email: validateEmail(values.email),
    password: validatePassword(values.password),
    mobile: validateMobile(values.mobile),
  };
}

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const form = useForm(empty, validate);
  const [serverError, setServerError] = useState("");
  const [emailTaken, setEmailTaken] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event) {
    event.preventDefault();
    form.touchAll();
    if (!form.isValid || busy) return;
    setBusy(true);
    setServerError("");
    setEmailTaken("");
    try {
      await register({
        name: form.values.name.trim(),
        email: form.values.email.trim(),
        password: form.values.password,
        mobile: form.values.mobile.trim(),
      });
      navigate("/login", { state: { message: "Registration successful. Please log in." } });
    } catch (error) {
      if (error.status === 409 || /email/i.test(error.message)) {
        setEmailTaken("This email is already registered");
      } else {
        setServerError(error.message);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-md space-y-4" noValidate>
      <h1 className="text-center text-2xl font-semibold">Register</h1>
      <label className="block text-sm">
        Full Name
        <input name="name" value={form.values.name} onChange={form.handleChange} onBlur={form.handleBlur} className="mt-1 w-full rounded border px-3 py-2" />
        {form.visibleError("name") ? <span className="text-red-700">{form.visibleError("name")}</span> : null}
      </label>
      <label className="block text-sm">
        Email address
        <input
          name="email"
          type="email"
          value={form.values.email}
          onChange={(event) => {
            setEmailTaken("");
            form.handleChange(event);
          }}
          onBlur={form.handleBlur}
          className="mt-1 w-full rounded border px-3 py-2"
        />
        {form.visibleError("email") || emailTaken ? <span className="text-red-700">{form.visibleError("email") || emailTaken}</span> : null}
      </label>
      <label className="block text-sm">
        Mobile
        <input name="mobile" inputMode="numeric" value={form.values.mobile} onChange={form.handleChange} onBlur={form.handleBlur} className="mt-1 w-full rounded border px-3 py-2" />
        {form.visibleError("mobile") ? <span className="text-red-700">{form.visibleError("mobile")}</span> : null}
      </label>
      <label className="block text-sm">
        Password
        <input name="password" type="password" value={form.values.password} onChange={form.handleChange} onBlur={form.handleBlur} className="mt-1 w-full rounded border px-3 py-2" />
        {form.visibleError("password") ? <span className="text-red-700">{form.visibleError("password")}</span> : null}
      </label>
      <p className="text-xs text-neutral-600">At least 8 characters with an uppercase letter, a lowercase letter, a number, and a special character.</p>
      {serverError ? <p className="text-sm text-red-700">{serverError}</p> : null}
      <button type="submit" disabled={!form.isValid || busy} className="w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-900 hover:bg-slate-50 disabled:opacity-50">
        {busy ? "Registering..." : "Register"}
      </button>
      <button type="button" className="w-full rounded bg-red-600 px-3 py-2 text-white hover:bg-red-700" onClick={() => { form.reset(); setServerError(""); setEmailTaken(""); }}>
        Reset
      </button>
      <p className="text-center text-sm">
        Already have an account? <Link to="/login" className="underline">Login</Link>
      </p>
    </form>
  );
}
