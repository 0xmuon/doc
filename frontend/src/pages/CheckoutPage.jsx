import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { inr } from "../utils/money";

export default function CheckoutPage() {
  const { token, user, ready } = useAuth();
  const navigate = useNavigate();
  const [cart, setCart] = useState(null);
  const [method, setMethod] = useState("CARD");
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!ready) return;
    if (!token) {
      navigate("/login");
      return;
    }
    api(`/api/cart/${user.user_id}`, { token })
      .then(setCart)
      .catch((err) => setError(err.message));
  }, [ready, token, user, navigate]);

  async function placeOrder(event) {
    event.preventDefault();
    if (!cart?.items.length || busy) return;
    setBusy(true);
    setError("");
    try {
      const data = await api("/api/orders/checkout", {
        method: "POST",
        token,
        body: { user_id: user.user_id, payment_method: method },
      });
      if (data.order.payment_status === "PAID") {
        navigate(`/orders/${data.order.order_id}`);
        return;
      }
      setResult(data);
      setCart({ user_id: user.user_id, items: [] });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!cart) return <p className="text-sm">{error || "Loading checkout..."}</p>;
  const total = cart.items.reduce((sum, item) => sum + Number(item.line_total), 0);

  return (
    <section className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-semibold">Checkout</h1>
      {cart.items.length === 0 && !result ? <p className="mt-4 text-sm">Your cart is empty.</p> : null}
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
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        {result ? (
          <p className="text-sm">
            {result.order.payment_status === "PAID"
              ? `Order placed. ${result.order.order_number}.`
              : `Payment was not completed. ${result.order.order_number} is on hold in your orders.`}
          </p>
        ) : null}
        <button
          type="submit"
          disabled={cart.items.length === 0 || busy}
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
