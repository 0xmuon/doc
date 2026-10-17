/** Cart shared with the header count and the cart, product, and checkout pages. */
import { useCallback, useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { fetchCart } from "../api/cartApi";
import { useAuth } from "./auth-context";
import { CartContext } from "./cart-context";
import { MAX_QUANTITY_PER_ITEM } from "../utils/validate";

export function CartProvider({ children }) {
  const { token, user, ready } = useAuth();
  const [cartState, setCartState] = useState(null);
  const [cartError, setCartError] = useState("");
  const [addedNotice, setAddedNotice] = useState("");
  const userId = user?.user_id;

  const refreshCart = useCallback(async () => {
    if (!token || !userId) {
      setCartError("");
      return { items: [] };
    }
    try {
      const data = await fetchCart(userId, token);
      setCartState({ userId, cart: data });
      setCartError("");
      return data;
    } catch (err) {
      setCartError(err.message || "Error fetching cart data.");
      throw err;
    }
  }, [token, userId]);

  useEffect(() => {
    if (!ready || !token || !userId) return undefined;
    let ignore = false;
    fetchCart(userId, token)
      .then((data) => {
        if (ignore) return;
        setCartState({ userId, cart: data });
        setCartError("");
      })
      .catch((err) => {
        if (!ignore) setCartError(err.message || "Error fetching cart data.");
      });
    return () => {
      ignore = true;
    };
  }, [ready, token, userId]);

  const setCart = useCallback((next) => {
    setCartState((current) => {
      const previous = current?.userId === userId ? current.cart : { items: [] };
      const cart = typeof next === "function" ? next(previous) : next;
      return { userId, cart };
    });
    setCartError("");
  }, [userId]);

  const notifyAdded = useCallback((productName) => {
    const name = String(productName || "").trim();
    setAddedNotice(name ? `${name} was added to the cart.` : "Item was added to the cart.");
  }, []);

  const clearAddedNotice = useCallback(() => {
    setAddedNotice("");
  }, []);

  useEffect(() => {
    if (!addedNotice) return undefined;
    const timer = window.setTimeout(() => setAddedNotice(""), 5000);
    return () => window.clearTimeout(timer);
  }, [addedNotice]);

  const value = useMemo(() => {
    const signedIn = Boolean(token && userId);
    const mine = signedIn && cartState?.userId === userId ? cartState.cart : null;
    const visible = signedIn ? mine : { items: [] };
    const visibleError = signedIn ? cartError : "";
    const items = visible?.items ?? [];
    const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
    const overStock = items.some(
      (item) => item.quantity > item.available_quantity || item.quantity > MAX_QUANTITY_PER_ITEM,
    );
    return {
      cart: visible,
      cartError: visibleError,
      items,
      itemCount,
      overStock,
      addedNotice,
      notifyAdded,
      clearAddedNotice,
      refreshCart,
      setCart,
    };
  }, [addedNotice, cartError, cartState, clearAddedNotice, notifyAdded, refreshCart, setCart, token, userId]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

CartProvider.propTypes = {
  children: PropTypes.node.isRequired,
};
