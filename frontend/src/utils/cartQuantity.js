import { api } from "../api/client";

export async function setCartQuantity({ token, userId, productId, nextQuantity, available, line }) {
  if (nextQuantity > available) {
    throw new Error("Quantity cannot exceed available stock.");
  }
  if (nextQuantity < 1) {
    if (line) {
      await api(`/api/cart/remove/${line.cart_item_id}`, { method: "DELETE", token });
    }
    return;
  }
  if (!line) {
    await api("/api/cart/add", {
      method: "POST",
      token,
      body: { user_id: userId, product_id: productId, quantity: nextQuantity },
    });
    return;
  }
  await api(`/api/cart/update/${line.cart_item_id}`, {
    method: "PUT",
    token,
    body: { quantity: nextQuantity },
  });
}
