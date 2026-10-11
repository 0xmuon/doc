import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { inr } from "../utils/money";

const PAYMENT_LABEL = {
  CARD: "Credit Card",
  COD: "Cash on Delivery",
};

function phoneLabel(mobile) {
  const digits = String(mobile || "").replace(/\D/g, "");
  if (digits.length === 10) return `+91-${digits}`;
  return mobile || "";
}

export default function ProfilePage() {
  const { token, ready } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!ready) return;
    if (!token) {
      navigate("/login");
      return;
    }
    Promise.all([api("/api/auth/me", { token }), api("/api/orders/me", { token })])
      .then(([me, history]) => {
        setProfile(me);
        setOrders(history.filter((order) => order.payment_status === "PAID"));
        setError("");
      })
      .catch((err) => setError(err.message));
  }, [ready, token, navigate]);

  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!profile || !orders) return <p className="text-sm">Loading profile...</p>;

  return (
    <section>
      <h1 className="text-2xl font-semibold">Profile</h1>
      <article className="mt-4 rounded border border-rose-100 bg-white p-4 shadow-sm">
        <h2 className="text-base font-semibold">{profile.name}</h2>
        <dl className="mt-3 space-y-2 text-sm">
          <div className="flex flex-wrap gap-2">
            <dt className="w-28 text-neutral-500">Email</dt>
            <dd>{profile.email}</dd>
          </div>
          <div className="flex flex-wrap gap-2">
            <dt className="w-28 text-neutral-500">Phone</dt>
            <dd>{phoneLabel(profile.mobile)}</dd>
          </div>
        </dl>
      </article>
      <h2 className="mt-8 text-xl font-semibold">Placed orders</h2>
      {orders.length === 0 ? <p className="mt-4 text-sm">No placed orders yet.</p> : null}
      <ul className="mt-4 space-y-4">
        {orders.map((order) => (
          <li key={order.order_id} className="rounded border border-rose-100 bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-medium">{order.order_number}</p>
                <p className="text-sm text-neutral-600">{new Date(order.order_date).toLocaleString()}</p>
                <p className="text-sm">{PAYMENT_LABEL[order.payment_method] || order.payment_method}</p>
                <p className="text-sm">Total {inr(order.total_amount)}</p>
                <p className="text-sm font-medium text-blue-700">Placed</p>
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
