import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchCurrentUser } from "../api/authApi";
import { fetchMyOrders } from "../api/orderApi";
import OrderListItem from "../components/orders/OrderListItem";
import { useAuth } from "../context/auth-context";

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
    Promise.all([fetchCurrentUser(token), fetchMyOrders(token)])
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
          <OrderListItem
            key={order.order_id}
            order={order}
            detail={PAYMENT_LABEL[order.payment_method] || order.payment_method}
          />
        ))}
      </ul>
    </section>
  );
}
