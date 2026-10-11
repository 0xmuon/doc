import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { inr } from "../utils/money";

export default function CartPage() {
  const { token, user, ready } = useAuth();
  const navigate = useNavigate();
  const [cart, setCart] = useState(null);
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [pendingId, setPendingId] = useState(0);
  const pendingRef = useRef(0);

  useEffect(() => {
    if (!ready) return;
    if (!token) {
      navigate("/login");
      return;
    }
    api(`/api/cart/${user.user_id}`, { token })
      .then(setCart)
      .catch((err) => setServerError(err.message));
  }, [ready, token, user, navigate]);

  async function changeQuantity(item, nextQuantity) {
    if (pendingRef.current) return;
    pendingRef.current = item.cart_item_id;
    if (nextQuantity > item.available_quantity) {
      pendingRef.current = 0;
      setErrors((current) => ({ ...current, [item.cart_item_id]: "Quantity cannot exceed available stock." }));
      return;
    }
    setErrors((current) => ({ ...current, [item.cart_item_id]: "" }));
    setServerError("");
    setPendingId(item.cart_item_id);
    try {
      if (nextQuantity < 1) {
        await api(`/api/cart/remove/${item.cart_item_id}`, { method: "DELETE", token });
      } else {
        await api(`/api/cart/update/${item.cart_item_id}`, {
          method: "PUT",
          token,
          body: { quantity: nextQuantity },
        });
      }
      setCart(await api(`/api/cart/${user.user_id}`, { token }));
    } catch (err) {
      setServerError(err.message);
    } finally {
      pendingRef.current = 0;
      setPendingId(0);
    }
  }

  async function removeItem(item) {
    await changeQuantity(item, 0);
  }

  if (!cart) return <p className="text-sm">{serverError || "Loading cart..."}</p>;
  const itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);
  const total = cart.items.reduce((sum, item) => sum + Number(item.line_total), 0);

  return (
    <section>
      <h1 className="text-2xl font-semibold">Your Cart</h1>
      {serverError ? <p className="mt-3 text-sm text-red-700">{serverError}</p> : null}
      {cart.items.length === 0 ? <p className="mt-6 text-sm">Your cart is empty.</p> : null}
      <ul className="mt-4 divide-y">
        {cart.items.map((item) => (
          <li key={item.cart_item_id} className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-medium">{item.product_name}</p>
              <p className="text-sm text-neutral-600">Price {inr(item.unit_price)}</p>
              <p className="text-sm">Subtotal {inr(item.line_total)}</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center rounded border border-slate-300 bg-white">
                <button
                  type="button"
                  aria-label={`Decrease quantity of ${item.product_name}`}
                  className="px-3 py-1 text-lg leading-none text-slate-800 hover:bg-slate-50 disabled:opacity-50"
                  onClick={() => changeQuantity(item, item.quantity - 1)}
                  disabled={pendingId === item.cart_item_id}
                >
                  −
                </button>
                <span className="min-w-8 text-center text-sm" aria-live="polite">{item.quantity}</span>
                <button
                  type="button"
                  aria-label={`Increase quantity of ${item.product_name}`}
                  className="px-3 py-1 text-lg leading-none text-slate-800 hover:bg-slate-50 disabled:opacity-50"
                  onClick={() => changeQuantity(item, item.quantity + 1)}
                  disabled={pendingId === item.cart_item_id || item.quantity >= item.available_quantity}
                >
                  +
                </button>
              </div>
              <button type="button" className="rounded bg-red-600 px-3 py-1 text-sm text-white hover:bg-red-700 disabled:opacity-50" onClick={() => removeItem(item)} disabled={pendingId === item.cart_item_id}>
                Remove
              </button>
            </div>
            {errors[item.cart_item_id] ? <p className="text-sm text-red-700">{errors[item.cart_item_id]}</p> : null}
          </li>
        ))}
      </ul>
      <div className="mt-6 flex items-center justify-between border-t pt-4">
        <p>Items: {itemCount}</p>
        <p className="font-semibold">Total: {inr(total)}</p>
      </div>
      <button
        type="button"
        disabled={cart.items.length === 0}
        onClick={() => navigate("/checkout")}
        className="mt-4 rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
      >
        Checkout
      </button>
      <p className="mt-3 text-sm">
        <Link to="/products" className="underline">Continue shopping</Link>
      </p>
    </section>
  );
}
