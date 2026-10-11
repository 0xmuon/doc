import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { inr } from "../utils/money";

export default function OrderDetailsPage() {
  const { orderId } = useParams();
  const { token, ready } = useAuth();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!ready) return;
    if (!token) {
      navigate("/login");
      return;
    }
    api(`/api/orders/details/${orderId}`, { token })
      .then(setOrder)
      .catch((err) => setError(err.message));
  }, [ready, token, orderId, navigate]);

  async function payAgain() {
    setBusy(true);
    setError("");
    try {
      const updated = await api("/api/payments/process", {
        method: "POST",
        token,
        body: { order_id: order.order_id },
      });
      setOrder(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!order && error) return <p className="text-sm text-red-700">{error}</p>;
  if (!order) return <p className="text-sm">Loading order...</p>;

  return (
    <section>
      <Link to="/orders" className="text-sm underline">Back to order history</Link>
      <h1 className="mt-3 text-2xl font-semibold">{order.order_number}</h1>
      <p className={`text-sm font-medium ${order.payment_status === "PAID" ? "text-blue-700" : "text-red-700"}`}>
        {order.payment_status === "PAID" ? "Placed" : "On hold"}
      </p>
      <p className="text-sm text-neutral-600">{new Date(order.order_date).toLocaleString()}</p>
      <table className="mt-4 w-full text-left text-sm">
        <thead>
          <tr className="border-b">
            <th className="py-2">Product</th>
            <th className="py-2">Qty</th>
            <th className="py-2">Price</th>
            <th className="py-2">Subtotal</th>
          </tr>
        </thead>
        <tbody>
          {order.items.map((item) => (
            <tr key={item.order_detail_id} className="border-b">
              <td className="py-2">{item.product_name}</td>
              <td className="py-2">{item.quantity}</td>
              <td className="py-2">{inr(item.price)}</td>
              <td className="py-2">{inr(item.line_total)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-4 font-semibold">Total {inr(order.total_amount)}</p>
      {order.payment_status !== "PAID" ? (
        <button type="button" disabled={busy} onClick={payAgain} className="mt-4 rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50">
          {busy ? "Trying payment..." : "Pay again"}
        </button>
      ) : null}
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
    </section>
  );
}
