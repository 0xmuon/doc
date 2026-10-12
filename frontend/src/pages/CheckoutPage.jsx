import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { placeOrder as checkoutOrder } from "../api/orderApi";
import { useAuth } from "../context/auth-context";
import { useCart } from "../context/cart-context";
import { inr } from "../utils/money";

export default function CheckoutPage() {
  const { token, user } = useAuth();
  const { cart, overStock, setCart, refreshCart } = useCart();
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
      setError(err.message);
      setBusy(false);
    }
  }

  if (!cart) return <p className="text-sm">{error || "Loading checkout..."}</p>;
  const total = cart.items.reduce((sum, item) => sum + Number(item.line_total), 0);

  return (
    <section className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-semibold">Checkout</h1>
      {cart.items.length === 0 ? <p className="mt-4 text-sm">Your cart is empty.</p> : null}
      <ul className="mt-4 divide-y">
        {cart.items.map((item) => (
          <li key={item.cart_item_id} className="flex justify-between py-3 text-sm">
            <span>{item.product_name} × {item.quantity}</span>
            <span>{inr(item.line_total)}</span>
          </li>
        ))}
      </ul>
      {cart.items.length > 0 ? <p className="mt-4 font-semibold">Total: {inr(total)}</p> : null}
      <form onSubmit={placeOrder} className="mt-6 space-y-4">
        <label className="block text-sm">
          Payment method
          <select value={method} onChange={(event) => setMethod(event.target.value)} className="mt-1 w-full rounded border px-3 py-2">
            <option value="CARD">Credit Card</option>
            <option value="COD">Cash on Delivery</option>
          </select>
        </label>
        {overStock ? <p className="text-sm text-red-700">Not available in this quantity. Update or remove that line before placing the order.</p> : null}
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <button
          type="submit"
          disabled={cart.items.length === 0 || overStock || busy}
          className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {busy ? "Placing order..." : "Place order"}
        </button>
      </form>
      <p className="mt-4 text-sm">
        <Link to="/orders" className="underline">View order history</Link>
      </p>
    </section>
  );
}
