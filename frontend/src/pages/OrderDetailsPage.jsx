import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { fetchOrder, retryPayment } from "../api/orderApi";
import StatusBadge from "../components/common/StatusBadge";
import { statusLabels } from "../utils/statusLabels";
import { useAuth } from "../context/auth-context";
import { inr } from "../utils/money";

export default function OrderDetailsPage() {
  const { orderId } = useParams();
  const location = useLocation();
  const { token, ready } = useAuth();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!ready || !token) return;
    fetchOrder(orderId, token)
      .then(setOrder)
      .catch((err) => {
        if (err.status === 403) setError("You can only view your own orders.");
        else if (err.status === 404) setError("Order not found.");
        else setError(err.message);
      });
  }, [ready, token, orderId]);

  async function payAgain() {
    setBusy(true);
    setError("");
    try {
      const updated = await retryPayment(order.order_id, token);
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
      {location.state?.justPlaced && order.payment_status !== "FAILED" ? (
        <p className="mt-3 text-sm text-blue-800">Thank you! Your order has been placed.</p>
      ) : null}
      <div className="mt-2 flex flex-wrap gap-2">
        {statusLabels(order).map((label) => (
          <StatusBadge key={label} status={label} />
        ))}
      </div>
      <p className="text-sm text-neutral-600">{new Date(order.order_date).toLocaleString()}</p>
      {order.payment_reference ? <p className="text-sm text-neutral-600">Reference {order.payment_reference}</p> : null}
      {order.payment_status !== "PAID" && order.failure_reason ? (
        <p className="mt-2 text-sm text-red-700">Payment failed: {order.failure_reason}</p>
      ) : null}
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
      {order.payment_status === "FAILED" ? (
        <button type="button" disabled={busy} onClick={payAgain} className="mt-4 rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50">
          {busy ? "Trying payment..." : "Pay again"}
        </button>
      ) : null}
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
    </section>
  );
}
