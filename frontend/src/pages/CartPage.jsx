import { useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import { Link, useNavigate } from "react-router-dom";
import { removeCartItem, updateCartItem } from "../api/cartApi";
import { ErrorNote, ErrorState, LoadingState } from "../components/common/StatusMessage";
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
          className="field mt-0 ml-2 w-20"
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
  const { cart, cartError, refreshCart, overStock } = useCart();
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

  if (!cart && cartError) {
    return (
      <section>
        <h1 className="page-title">Your Cart</h1>
        <ErrorState message={serverError || cartError} onRetry={() => refreshCart().catch((err) => setServerError(err.message))} />
      </section>
    );
  }
  if (!cart) return <LoadingState label="Loading cart..." />;
  const itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);
  const total = cart.items.reduce((sum, item) => sum + Number(item.line_total), 0);

  return (
    <section>
      <h1 className="page-title">Your Cart</h1>
      <p className="mt-2 text-sm text-slate-600">Review quantities, then continue to checkout.</p>
      {serverError || cartError ? <div className="mt-3"><ErrorNote message={serverError || cartError} /></div> : null}
      {cart.items.length === 0 ? <p className="panel mt-6 px-4 py-8 text-center text-sm text-slate-600">Your cart is empty.</p> : null}
      <ul className="mt-4 space-y-3">
        {cart.items.map((item) => (
          <li key={item.cart_item_id} className="panel flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-semibold text-slate-900">{item.product_name}</p>
              <p className="text-sm text-slate-500">Price {inr(item.unit_price)}</p>
              <p className="text-sm font-medium text-slate-800">Subtotal {inr(item.line_total)}</p>
            </div>
            <div className="flex items-start gap-2">
              <CartQuantityInput
                item={item}
                disabled={pendingId === item.cart_item_id}
                onCommit={changeQuantity}
              />
              <button type="button" className="btn-danger mt-5 px-3 py-1.5" onClick={() => removeItem(item)} disabled={pendingId === item.cart_item_id}>
                Remove
              </button>
            </div>
          </li>
        ))}
      </ul>
      <div className="panel mt-6 flex items-center justify-between px-4 py-4">
        <p className="text-sm text-slate-600">Items: {itemCount}</p>
        <p className="text-lg font-semibold text-slate-900">Total: {inr(total)}</p>
      </div>
      {overStock ? <p className="mt-4 text-sm text-red-700">Not available in this quantity. Update or remove that line to check out.</p> : null}
      <button
        type="button"
        disabled={cart.items.length === 0 || overStock}
        onClick={() => navigate("/checkout")}
        className="btn-primary mt-4"
      >
        Checkout
      </button>
      <p className="mt-3 text-sm">
        <Link to="/products" className="font-medium text-blue-700 hover:underline">Continue shopping</Link>
      </p>
    </section>
  );
}
