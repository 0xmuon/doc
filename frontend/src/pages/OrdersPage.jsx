import { useEffect, useState } from "react";
import { fetchMyOrders } from "../api/orderApi";
import OrderListItem from "../components/orders/OrderListItem";
import { useAuth } from "../context/auth-context";

export default function OrdersPage() {
  const { token, ready } = useAuth();
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!ready || !token) return;
    fetchMyOrders(token)
      .then(setOrders)
      .catch((err) => setError(err.message));
  }, [ready, token]);

  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!orders) return <p className="text-sm">Loading orders...</p>;

  return (
    <section>
      <h1 className="text-2xl font-semibold">Order History</h1>
      {orders.length === 0 ? <p className="mt-6">No orders found.</p> : null}
      <ul className="mt-4 space-y-4">
        {orders.map((order) => (
          <OrderListItem key={order.order_id} order={order} />
        ))}
      </ul>
    </section>
  );
}
