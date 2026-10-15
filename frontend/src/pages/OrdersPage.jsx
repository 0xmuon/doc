import { useEffect, useState } from "react";
import { fetchMyOrders } from "../api/orderApi";
import { ErrorState, LoadingState } from "../components/common/StatusMessage";
import OrderListItem from "../components/orders/OrderListItem";
import { useAuth } from "../context/auth-context";

export default function OrdersPage() {
  const { token, ready } = useAuth();
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!ready || !token) return undefined;
    let ignore = false;
    fetchMyOrders(token)
      .then((rows) => {
        if (ignore) return;
        setOrders(rows);
        setError("");
      })
      .catch((err) => {
        if (!ignore) setError(err.message);
      });
    return () => {
      ignore = true;
    };
  }, [ready, token, attempt]);

  return (
    <section>
      <h1 className="page-title">Order History</h1>
      <p className="mt-2 text-sm text-slate-600">Every order you have placed, including payment that is still pending or failed.</p>
      {error ? <ErrorState message={error} onRetry={() => { setError(""); setOrders(null); setAttempt((value) => value + 1); }} /> : null}
      {!orders && !error ? <LoadingState label="Loading orders..." /> : null}
      {orders && orders.length === 0 ? <p className="panel mt-6 px-4 py-8 text-center text-sm text-slate-600">No orders found.</p> : null}
      {orders && orders.length > 0 ? (
        <ul className="mt-4 space-y-4">
          {orders.map((order) => (
            <OrderListItem key={order.order_id} order={order} />
          ))}
        </ul>
      ) : null}
    </section>
  );
}
