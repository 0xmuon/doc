import { useEffect, useState } from "react";
import { fetchMyOrders } from "../api/orderApi";
import { EmptyState, ErrorState, LoadingState } from "../components/common/StatusMessage";
import OrderListItem from "../components/orders/OrderListItem";
import { useAuth } from "../context/auth-context";
import { describeLoadError } from "../utils/loadError";

export default function OrdersPage() {
  const { token, ready } = useAuth();
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!ready || !token) return undefined;
    let ignore = false;
    fetchMyOrders(token)
      .then((rows) => {
        if (ignore) return;
        setOrders(rows);
        setError(null);
      })
      .catch((err) => {
        if (!ignore) {
          setOrders(null);
          setError(describeLoadError("order history", err));
        }
      });
    return () => {
      ignore = true;
    };
  }, [ready, token, attempt]);

  return (
    <section>
      <h1 className="page-title">Order History</h1>
      <p className="mt-2 text-sm text-slate-600">Every order you have placed, including payment that is still pending or failed.</p>
      {!orders && !error ? <LoadingState label="Loading orders..." /> : null}
      {error ? (
        <ErrorState
          title={error.title}
          message={error.message}
          onRetry={() => { setError(null); setOrders(null); setAttempt((value) => value + 1); }}
        />
      ) : null}
      {orders && orders.length === 0 ? <EmptyState message="No orders found." /> : null}
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
