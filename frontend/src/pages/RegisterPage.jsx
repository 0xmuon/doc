/**
 * Register. A duplicate email is shown under the email field.
 * Success opens a dialog, then the shopper is sent to login.
 */
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ErrorNote } from "../components/common/StatusMessage";
import { useAuth } from "../context/auth-context";
import { useForm } from "../hooks/useForm";
import { validateEmail, validateMobile, validateName, validatePassword } from "../utils/validate";

const empty = { name: "", email: "", password: "", mobile: "" };
const REDIRECT_SECONDS = 5;

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
  const [registeredEmail, setRegisteredEmail] = useState("");
  const [secondsLeft, setSecondsLeft] = useState(REDIRECT_SECONDS);
  const continueRef = useRef(null);

  function goToLogin() {
    if (!registeredEmail) return;
    navigate("/login", {
      replace: true,
      state: {
        message: "Registration successful. Please log in.",
        email: registeredEmail,
      },
    });
  }

  useEffect(() => {
    if (!registeredEmail) return undefined;
    continueRef.current?.focus();
    const timer = window.setInterval(() => {
      setSecondsLeft((current) => (current > 0 ? current - 1 : 0));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [registeredEmail]);

  useEffect(() => {
    if (!registeredEmail || secondsLeft > 0) return;
    navigate("/login", {
      replace: true,
      state: {
        message: "Registration successful. Please log in.",
        email: registeredEmail,
      },
    });
  }, [registeredEmail, secondsLeft, navigate]);

  async function onSubmit(event) {
    event.preventDefault();
    form.touchAll();
    if (!form.isValid || busy || registeredEmail) return;
    setBusy(true);
    setServerError("");
    setEmailTaken("");
    try {
      const email = form.values.email.trim();
      await register({
        name: form.values.name.trim(),
        email,
        password: form.values.password,
        mobile: form.values.mobile.trim(),
      });
      setSecondsLeft(REDIRECT_SECONDS);
      setRegisteredEmail(email);
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
    <>
      <form onSubmit={onSubmit} className="panel mx-auto max-w-md space-y-4 p-6 sm:p-8" noValidate>
        <div className="text-center">
          <p className="text-sm font-semibold tracking-wide text-red-600">ABC Shop</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">Create your account</h1>
          <p className="mt-2 text-sm text-slate-600">Register once, then sign in to shop, save a cart, and place orders.</p>
        </div>
        <label className="field-label">
          Full Name
          <input name="name" autoComplete="name" value={form.values.name} onChange={form.handleChange} onBlur={form.handleBlur} className="field" />
          {form.visibleError("name") ? <span className="field-error">{form.visibleError("name")}</span> : null}
        </label>
        <label className="field-label">
          Email address
          <input
            name="email"
            type="email"
            autoComplete="email"
            value={form.values.email}
            onChange={(event) => {
              setEmailTaken("");
              form.handleChange(event);
            }}
            onBlur={form.handleBlur}
            className="field"
          />
          {form.visibleError("email") || emailTaken ? <span className="field-error">{form.visibleError("email") || emailTaken}</span> : null}
        </label>
        <label className="field-label">
          Mobile
          <input name="mobile" inputMode="numeric" autoComplete="tel" value={form.values.mobile} onChange={form.handleChange} onBlur={form.handleBlur} className="field" />
          {form.visibleError("mobile") ? <span className="field-error">{form.visibleError("mobile")}</span> : null}
        </label>
        <label className="field-label">
          Password
          <input name="password" type="password" autoComplete="new-password" value={form.values.password} onChange={form.handleChange} onBlur={form.handleBlur} className="field" />
          {form.visibleError("password") ? <span className="field-error">{form.visibleError("password")}</span> : null}
        </label>
        <p className="text-xs leading-5 text-slate-500">At least 8 characters with an uppercase letter, a lowercase letter, a number, and a special character.</p>
        {serverError ? <ErrorNote message={serverError} /> : null}
        <button type="submit" disabled={!form.isValid || busy} className="btn-outline w-full">
          {busy ? "Registering..." : "Register"}
        </button>
        <button type="button" className="btn-danger w-full" onClick={() => { form.reset(); setServerError(""); setEmailTaken(""); }}>
          Reset
        </button>
        <p className="text-center text-sm text-slate-600">
          Already have an account? <Link to="/login" className="font-semibold text-blue-700 hover:underline">Login</Link>
        </p>
      </form>
      {registeredEmail ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="registered-title"
            aria-describedby="registered-text"
            className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl"
          >
            <p className="text-sm font-semibold tracking-wide text-blue-700">Registration complete</p>
            <h2 id="registered-title" className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">You are registered</h2>
            <p id="registered-text" className="mt-3 text-sm leading-6 text-slate-700">
              Your account for {registeredEmail} is ready. You are being taken to the login page so you can sign in.
            </p>
            <p className="mt-3 text-sm text-slate-500" aria-live="polite">
              Continuing to login in {secondsLeft} {secondsLeft === 1 ? "second" : "seconds"}.
            </p>
            <button ref={continueRef} type="button" className="btn-primary mt-5 w-full" onClick={goToLogin}>
              Go to login
            </button>
          </div>
        </div>
      ) : null}
    </>
  );
}
