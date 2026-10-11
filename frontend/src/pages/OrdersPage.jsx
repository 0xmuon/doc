import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { inr } from "../utils/money";

export default function OrdersPage() {
  const { token, ready } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!ready) return;
    if (!token) {
      navigate("/login");
      return;
    }
    api("/api/orders/me", { token })
      .then(setOrders)
      .catch((err) => setError(err.message));
  }, [ready, token, navigate]);

  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!orders) return <p className="text-sm">Loading orders...</p>;

  return (
    <section>
      <h1 className="text-2xl font-semibold">Order History</h1>
      {orders.length === 0 ? <p className="mt-6">No orders found.</p> : null}
      <ul className="mt-4 space-y-4">
        {orders.map((order) => (
          <li key={order.order_id} className="rounded border border-rose-100 bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-medium">{order.order_number}</p>
                <p className="text-sm text-neutral-600">{new Date(order.order_date).toLocaleString()}</p>
                <p className="text-sm">Total {inr(order.total_amount)}</p>
                <p className={`text-sm font-medium ${order.payment_status === "PAID" ? "text-blue-700" : "text-red-700"}`}>
                  {order.payment_status === "PAID" ? "Placed" : "On hold"}
                </p>
              </div>
              <Link to={`/orders/${order.order_id}`} className="rounded bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700">
                View details
              </Link>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
