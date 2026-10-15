import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { fetchOrder, retryPayment, returnOrderToCart } from "../api/orderApi";
import StatusBadge from "../components/common/StatusBadge";
import { ErrorNote, ErrorState, LoadingState } from "../components/common/StatusMessage";
import { statusLabels } from "../utils/statusLabels";
import { useAuth } from "../context/auth-context";
import { useCart } from "../context/cart-context";
import { inr } from "../utils/money";

export default function OrderDetailsPage() {
  const { orderId } = useParams();
  const location = useLocation();
  const { token, ready } = useAuth();
  const { refreshCart } = useCart();
  const navigate = useNavigate();
  const [loaded, setLoaded] = useState({ id: "", order: null, error: "" });
  const [actionError, setActionError] = useState("");
  const [busy, setBusy] = useState("");
  const [attempt, setAttempt] = useState(0);
  const order = loaded.id === orderId ? loaded.order : null;
  const loadError = loaded.id === orderId ? loaded.error : "";

  useEffect(() => {
    if (!ready || !token) return undefined;
    let ignore = false;
    fetchOrder(orderId, token)
      .then((row) => {
        if (!ignore) setLoaded({ id: orderId, order: row, error: "" });
      })
      .catch((err) => {
        if (ignore) return;
        const message = err.status === 403
          ? "You can only view your own orders."
          : err.status === 404
            ? "Order not found."
            : err.message;
        setLoaded({ id: orderId, order: null, error: message });
      });
    return () => {
      ignore = true;
    };
  }, [ready, token, orderId, attempt]);

  async function payAgain() {
    setBusy("pay");
    setActionError("");
    try {
      const updated = await retryPayment(order.order_id, token);
      setLoaded({ id: orderId, order: updated, error: "" });
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusy("");
    }
  }

  async function returnToCart() {
    setBusy("cart");
    setActionError("");
    try {
      await returnOrderToCart(order.order_id, token);
      await refreshCart();
      navigate("/cart");
    } catch (err) {
      setActionError(err.message);
      setBusy("");
    }
  }

  if (!order && loadError) {
    return (
      <section>
        <Link to="/orders" className="text-sm font-medium text-blue-700 hover:underline">Back to order history</Link>
        <ErrorState message={loadError} onRetry={() => { setLoaded({ id: "", order: null, error: "" }); setAttempt((value) => value + 1); }} />
      </section>
    );
  }
  if (!order) return <LoadingState label="Loading order..." />;

  return (
    <section>
      <Link to="/orders" className="text-sm font-medium text-blue-700 hover:underline">Back to order history</Link>
      <h1 className="page-title mt-3">{order.order_number}</h1>
      {location.state?.justPlaced && order.payment_status !== "FAILED" ? (
        <p className="mt-4 rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-800">Thank you! Your order has been placed.</p>
      ) : null}
      <div className="mt-3 flex flex-wrap gap-2">
        {statusLabels(order).map((label) => (
          <StatusBadge key={label} status={label} />
        ))}
      </div>
      <p className="mt-2 text-sm text-slate-500">{new Date(order.order_date).toLocaleString()}</p>
      {order.payment_reference ? <p className="text-sm text-slate-500">Reference {order.payment_reference}</p> : null}
      {order.payment_status !== "PAID" && order.failure_reason ? (
        <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">Payment failed: {order.failure_reason}</p>
      ) : null}
      <div className="panel mt-5 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-rose-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Product</th>
              <th className="px-4 py-3 font-medium">Qty</th>
              <th className="px-4 py-3 font-medium">Price</th>
              <th className="px-4 py-3 font-medium">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((item) => (
              <tr key={item.order_detail_id} className="border-t border-rose-100">
                <td className="px-4 py-3 font-medium text-slate-900">{item.product_name}</td>
                <td className="px-4 py-3">{item.quantity}</td>
                <td className="px-4 py-3">{inr(item.price)}</td>
                <td className="px-4 py-3">{inr(item.line_total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-4 text-lg font-semibold text-slate-900">Total {inr(order.total_amount)}</p>
      {order.payment_status === "FAILED" ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {order.payment_method !== "COD" ? (
            <button type="button" disabled={busy !== ""} onClick={payAgain} className="btn-primary">
              {busy === "pay" ? "Trying payment..." : "Pay again"}
            </button>
          ) : null}
          <button type="button" disabled={busy !== ""} onClick={returnToCart} className="btn-outline-danger">
            {busy === "cart" ? "Returning to cart..." : "Return to cart"}
          </button>
        </div>
      ) : null}
      {actionError ? <div className="mt-3"><ErrorNote message={actionError} /></div> : null}
    </section>
  );
}
