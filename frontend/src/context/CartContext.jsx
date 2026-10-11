/** Cart shared with the header count and the cart, product, and checkout pages. */
import { useCallback, useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { fetchCart } from "../api/cartApi";
import { useAuth } from "./auth-context";
import { CartContext } from "./cart-context";
import { MAX_QUANTITY_PER_ITEM } from "../utils/validate";

export function CartProvider({ children }) {
  const { token, user, ready } = useAuth();
  const [cart, setCart] = useState(null);

  const refreshCart = useCallback(async () => {
    if (!token || !user) {
      setCart({ items: [] });
      return { items: [] };
    }
    const data = await fetchCart(user.user_id, token);
    setCart(data);
    return data;
  }, [token, user]);

  useEffect(() => {
    if (!ready || !token || !user) return undefined;
    let ignore = false;
    fetchCart(user.user_id, token)
      .then((data) => {
        if (!ignore) setCart(data);
      })
      .catch(() => {
        if (!ignore) setCart({ items: [] });
      });
    return () => {
      ignore = true;
    };
  }, [ready, token, user]);

  const value = useMemo(() => {
    const visible = token && user ? cart : { items: [] };
    const items = visible?.items ?? [];
    const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
    const overStock = items.some(
      (item) => item.quantity > item.available_quantity || item.quantity > MAX_QUANTITY_PER_ITEM,
    );
    return { cart: visible, items, itemCount, overStock, refreshCart, setCart };
  }, [cart, refreshCart, token, user]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

CartProvider.propTypes = {
  children: PropTypes.node.isRequired,
};
