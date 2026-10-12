/** Checkout, order history, one order, and pay again. */
import { api } from "./client";

export function placeOrder({ token, userId, paymentMethod }) {
  return api("/api/orders/checkout", {
    method: "POST",
    token,
    body: { user_id: userId, payment_method: paymentMethod },
  });
}

export function fetchMyOrders(token) {
  return api("/api/orders/me", { token });
}

export function fetchOrder(orderId, token) {
  return api(`/api/orders/details/${orderId}`, { token });
}

export function retryPayment(orderId, token) {
  return api("/api/payments/process", {
    method: "POST",
    token,
    body: { order_id: orderId },
  });
}

export function returnOrderToCart(orderId, token) {
  return api(`/api/orders/${orderId}/return-to-cart`, { method: "POST", token });
}
