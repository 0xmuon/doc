import { useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import { Link, useNavigate } from "react-router-dom";
import { removeCartItem, updateCartItem } from "../api/cartApi";
import { useAuth } from "../context/auth-context";
import { useCart } from "../context/cart-context";
import { inr } from "../utils/money";
import { MAX_QUANTITY_PER_ITEM, validateQuantity } from "../utils/validate";

function CartQuantityInput({ item, disabled, onCommit }) {
  const [value, setValue] = useState(String(item.quantity));
  const [error, setError] = useState("");
  const inputRef = useRef(null);
  const timerRef = useRef(0);

  useEffect(() => {
    if (document.activeElement === inputRef.current) return;
    setValue(String(item.quantity));
    setError("");
  }, [item.quantity]);

  useEffect(() => () => window.clearTimeout(timerRef.current), []);

  function handleChange(event) {
    const next = event.target.value;
    setValue(next);
    const message = validateQuantity(next, item.available_quantity);
    setError(message);
    window.clearTimeout(timerRef.current);
    if (message || Number(next) === item.quantity) return;
    timerRef.current = window.setTimeout(() => onCommit(item, Number(next)), 500);
  }

  return (
    <div>
      <label className="text-sm">
        Qty
        <input
          ref={inputRef}
          type="number"
          min="1"
          max={Math.min(item.available_quantity, MAX_QUANTITY_PER_ITEM)}
          value={value}
          onChange={handleChange}
          disabled={disabled}
          aria-label={`Quantity of ${item.product_name}`}
          className="ml-2 w-20 rounded border px-2 py-1"
        />
      </label>
      {error ? <p className="mt-1 text-sm text-red-700">{error}</p> : null}
    </div>
  );
}

CartQuantityInput.propTypes = {
  item: PropTypes.shape({
    quantity: PropTypes.number.isRequired,
    available_quantity: PropTypes.number.isRequired,
    product_name: PropTypes.string.isRequired,
  }).isRequired,
  disabled: PropTypes.bool,
  onCommit: PropTypes.func.isRequired,
};

export default function CartPage() {
  const { token } = useAuth();
  const { cart, refreshCart, overStock } = useCart();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState("");
  const [pendingId, setPendingId] = useState(0);
  const pendingRef = useRef(0);

  async function changeQuantity(item, nextQuantity) {
    if (pendingRef.current) return;
    const message = nextQuantity < 1 ? "" : validateQuantity(nextQuantity, item.available_quantity);
    if (message) return;
    pendingRef.current = item.cart_item_id;
    setServerError("");
    setPendingId(item.cart_item_id);
    try {
      if (nextQuantity < 1) {
        await removeCartItem(item.cart_item_id, token);
      } else {
        await updateCartItem(item.cart_item_id, nextQuantity, token);
      }
      await refreshCart();
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
            <div className="flex items-start gap-2">
              <CartQuantityInput
                item={item}
                disabled={pendingId === item.cart_item_id}
                onCommit={changeQuantity}
              />
              <button type="button" className="mt-5 rounded bg-red-600 px-3 py-1 text-sm text-white hover:bg-red-700 disabled:opacity-50" onClick={() => removeItem(item)} disabled={pendingId === item.cart_item_id}>
                Remove
              </button>
            </div>
          </li>
        ))}
      </ul>
      <div className="mt-6 flex items-center justify-between border-t pt-4">
        <p>Items: {itemCount}</p>
        <p className="font-semibold">Total: {inr(total)}</p>
      </div>
      {overStock ? <p className="mt-4 text-sm text-red-700">Not available in this quantity. Update or remove that line to check out.</p> : null}
      <button
        type="button"
        disabled={cart.items.length === 0 || overStock}
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
