import { addCartItem, removeCartItem, updateCartItem } from "../api/cartApi";
import { MAX_QUANTITY_PER_ITEM } from "./validate";

export async function setCartQuantity({ token, userId, productId, nextQuantity, available, line }) {
  if (nextQuantity > available) {
    throw new Error("Quantity cannot exceed available stock.");
  }
  if (nextQuantity > MAX_QUANTITY_PER_ITEM) {
    throw new Error(`At most ${MAX_QUANTITY_PER_ITEM} per product.`);
  }
  if (nextQuantity < 1) {
    if (line) await removeCartItem(line.cart_item_id, token);
    return;
  }
  if (!line) {
    await addCartItem({ token, userId, productId, quantity: nextQuantity });
    return;
  }
  await updateCartItem(line.cart_item_id, nextQuantity, token);
}
