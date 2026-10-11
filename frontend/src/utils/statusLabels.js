/** Labels for this API's order and payment fields. */
export function statusLabels(order) {
  const labels = [];
  if (order.order_status === "CONFIRMED") labels.push("Confirmed");
  else if (order.order_status === "PAYMENT_FAILED") labels.push("Payment Failed");
  else labels.push("Pending Payment");

  if (order.payment_status === "PAID") labels.push("Paid");
  else if (order.payment_status === "FAILED" && !labels.includes("Payment Failed")) labels.push("Payment Failed");
  else if (order.payment_status === "PENDING" && !labels.includes("Pending Payment")) labels.push("Pending Payment");
  return labels;
}
