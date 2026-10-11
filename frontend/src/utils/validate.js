const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
// PDF: 8+ characters, one upper, one lower, one number, one special character.
const PASSWORD = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;

export function validateName(name) {
  const cleaned = name.trim();
  if (!cleaned) return "Name is required.";
  if (cleaned.length < 6) return "Name must be at least 6 characters.";
  if (!/^[A-Za-z ]+$/.test(cleaned)) return "Name must contain letters only.";
  return "";
}

export function validateEmail(email) {
  if (!email.trim()) return "Email is required.";
  if (!EMAIL.test(email.trim())) return "Enter a valid email address.";
  return "";
}

export function validatePassword(password) {
  if (!password) return "Password is required.";
  if (!PASSWORD.test(password)) {
    return "Password must be at least 8 characters and include an uppercase letter, a lowercase letter, a number, and a special character.";
  }
  return "";
}

export function validateMobile(mobile) {
  if (!/^\d{10}$/.test(mobile.trim())) return "Mobile must be 10 digits.";
  return "";
}

export function validateLoginPassword(password) {
  if (!password) return "Password is required.";
  return "";
}
