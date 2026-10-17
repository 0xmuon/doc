import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { EmptyState, ErrorNote, ErrorState, LoadingState } from "../components/common/StatusMessage";
import { placeOrder as checkoutOrder } from "../api/orderApi";
import { useAuth } from "../context/auth-context";
import { useCart } from "../context/cart-context";
import { describeActionError, describeLoadError } from "../utils/loadError";
import { inr } from "../utils/money";

export default function CheckoutPage() {
  const { token, user } = useAuth();
  const { cart, cartError, overStock, setCart, refreshCart } = useCart();
  const navigate = useNavigate();
  const [method, setMethod] = useState("CARD");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function placeOrder(event) {
    event.preventDefault();
    if (!cart?.items.length || overStock || busy) return;
    setBusy(true);
    setError("");
    try {
      const data = await checkoutOrder({ token, userId: user.user_id, paymentMethod: method });
      await refreshCart().catch(() => setCart({ user_id: user.user_id, items: [] }));
      const failed = data.order.payment_status === "FAILED";
      navigate(`/orders/${data.order.order_id}`, { state: failed ? undefined : { justPlaced: true } });
    } catch (err) {
      setError(describeActionError("Could not place order", err));
      setBusy(false);
    }
  }

  if (!cart && (error || cartError)) {
    const failed = describeLoadError("checkout data", { message: error || cartError });
    return (
      <section>
        <h1 className="page-title">Checkout</h1>
        <ErrorState
          title={failed.title}
          message={failed.message}
          onRetry={() => refreshCart().catch((err) => setError(describeLoadError("checkout data", err).message))}
        />
      </section>
    );
  }
  if (!cart) return <LoadingState label="Loading checkout..." />;
  const total = cart.items.reduce((sum, item) => sum + Number(item.line_total), 0);

  return (
    <section className="mx-auto max-w-2xl">
      <h1 className="page-title">Checkout</h1>
      <p className="mt-2 text-sm text-slate-600">Choose how you want to pay, then place the order.</p>
      {cart.items.length === 0 ? <EmptyState message="Your cart is empty." /> : null}
      {cart.items.length > 0 ? (
        <ul className="panel mt-5 divide-y divide-rose-100 px-4">
          {cart.items.map((item) => (
            <li key={item.cart_item_id} className="flex justify-between py-3 text-sm">
              <span className="text-slate-800">{item.product_name} × {item.quantity}</span>
              <span className="font-medium text-slate-900">{inr(item.line_total)}</span>
            </li>
          ))}
        </ul>
      ) : null}
      {cart.items.length > 0 ? <p className="mt-4 text-lg font-semibold text-slate-900">Total: {inr(total)}</p> : null}
      <form onSubmit={placeOrder} className="panel mt-6 space-y-4 p-5">
        <label className="field-label">
          Payment method
          <select value={method} onChange={(event) => setMethod(event.target.value)} className="field">
            <option value="CARD">Credit Card</option>
            <option value="COD">Cash on Delivery</option>
          </select>
        </label>
        {overStock ? <p className="text-sm text-red-700">Not available in this quantity. Update or remove that line before placing the order.</p> : null}
        {error ? <ErrorNote message={error} /> : null}
        <button
          type="submit"
          disabled={cart.items.length === 0 || overStock || busy}
          className="btn-primary"
        >
          {busy ? "Placing order..." : "Place order"}
        </button>
      </form>
      <p className="mt-4 text-sm">
        <Link to="/orders" className="font-medium text-blue-700 hover:underline">View order history</Link>
      </p>
    </section>
  );
}
