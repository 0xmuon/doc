/** Register and login: errors show after a field is left, and all of them if submit is attempted. */
import { useState } from "react";

export function useForm(initial, validate) {
  const [values, setValues] = useState(initial);
  const [touched, setTouched] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const errors = validate(values);
  const isValid = Object.values(errors).every((message) => message === "");

  function handleChange(event) {
    const { name, value } = event.target;
    setValues((current) => ({ ...current, [name]: value }));
  }

  function handleBlur(event) {
    setTouched((current) => ({ ...current, [event.target.name]: true }));
  }

  function touchAll() {
    setSubmitted(true);
  }

  function visibleError(name) {
    if (!touched[name] && !submitted) return "";
    return errors[name] || "";
  }

  function reset() {
    setValues(initial);
    setTouched({});
    setSubmitted(false);
  }

  return { values, errors, isValid, handleChange, handleBlur, touchAll, visibleError, reset };
}
