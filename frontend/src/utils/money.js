export function inr(amount) {
  const value = Number(amount);
  const text = Number.isInteger(value) ? String(value) : value.toFixed(2);
  return `INR ${text}`;
}
