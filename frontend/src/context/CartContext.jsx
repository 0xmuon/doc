/** Cart shared with the header count and the cart, product, and checkout pages. */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "./AuthContext";

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const { token, user, ready } = useAuth();
  const [cart, setCart] = useState(null);

  const refreshCart = useCallback(async () => {
    if (!token || !user) {
      setCart({ items: [] });
      return { items: [] };
    }
    const data = await api(`/api/cart/${user.user_id}`, { token });
    setCart(data);
    return data;
  }, [token, user]);

  useEffect(() => {
    if (!ready) return;
    refreshCart().catch(() => setCart({ items: [] }));
  }, [ready, refreshCart]);

  const value = useMemo(() => {
    const items = cart?.items ?? [];
    const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
    const overStock = items.some((item) => item.quantity > item.available_quantity);
    return { cart, items, itemCount, overStock, refreshCart, setCart };
  }, [cart, refreshCart]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  return useContext(CartContext);
}
