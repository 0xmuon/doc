/** Low-stock urgency: shown when 5 or fewer items remain for this shopper. */

export const LOW_STOCK_THRESHOLD = 5;

/**
 * Items a shopper can still add: total stock minus what is already in
 * their cart. Adding to the cart does not lower backend stock until
 * checkout, so the subtraction happens here on the client.
 */
export function remainingStock(availableQuantity, cartQuantity) {
  return Math.max((availableQuantity || 0) - (cartQuantity || 0), 0);
}

/** Urgency line for a remaining count, or null when there is nothing to warn about. */
export function lowStockText(remaining) {
  if (remaining <= 0) return "All available stock is in your cart";
  if (remaining > LOW_STOCK_THRESHOLD) return null;
  return `Only ${remaining} ${remaining === 1 ? "item" : "items"} left — hurry!`;
}
