const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
// Letters only, with a single space between words.
const NAME_PATTERN = /^[A-Za-z]+( [A-Za-z]+)*$/;
// PDF: 8+ characters, one upper, one lower, one number, one special character.
const PASSWORD = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;

export const MAX_QUANTITY_PER_ITEM = Number(import.meta.env.VITE_MAX_QUANTITY_PER_ITEM) || 10;

export function validateName(name) {
  const cleaned = name.trim();
  if (!cleaned) return "Name is required.";
  if (cleaned.length < 6) return "Name must be at least 6 characters.";
  if (!NAME_PATTERN.test(cleaned)) return "Name can contain letters only.";
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

export function validateQuantity(value, stock) {
  const text = String(value).trim();
  if (!text) return "Quantity is required.";
  if (!/^\d+$/.test(text) || Number(text) < 1) return "Quantity must be a positive whole number.";
  const quantity = Number(text);
  if (quantity > stock) return "Quantity cannot exceed available stock.";
  if (quantity > MAX_QUANTITY_PER_ITEM) return `At most ${MAX_QUANTITY_PER_ITEM} per product.`;
  return "";
}
