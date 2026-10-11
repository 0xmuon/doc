/** Cart calls. Totals stay in the browser; these routes return the lines. */
import { api } from "./client";

export function fetchCart(userId, token) {
  return api(`/api/cart/${userId}`, { token });
}

export function addCartItem({ token, userId, productId, quantity }) {
  return api("/api/cart/add", {
    method: "POST",
    token,
    body: { user_id: userId, product_id: productId, quantity },
  });
}

export function updateCartItem(cartItemId, quantity, token) {
  return api(`/api/cart/update/${cartItemId}`, {
    method: "PUT",
    token,
    body: { quantity },
  });
}

export function removeCartItem(cartItemId, token) {
  return api(`/api/cart/remove/${cartItemId}`, { method: "DELETE", token });
}
