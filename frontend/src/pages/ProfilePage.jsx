import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchCurrentUser } from "../api/authApi";
import { fetchMyOrders } from "../api/orderApi";
import { EmptyState, ErrorState, LoadingState } from "../components/common/StatusMessage";
import OrderListItem from "../components/orders/OrderListItem";
import { useAuth } from "../context/auth-context";
import { describeLoadError } from "../utils/loadError";

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
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!ready) return undefined;
    if (!token) {
      navigate("/login");
      return undefined;
    }
    let ignore = false;
    Promise.all([fetchCurrentUser(token), fetchMyOrders(token)])
      .then(([me, history]) => {
        if (ignore) return;
        setProfile(me);
        setOrders(history.filter((order) => order.payment_status === "PAID"));
        setError(null);
      })
      .catch((err) => {
        if (!ignore) {
          setProfile(null);
          setOrders(null);
          setError(describeLoadError("profile data", err));
        }
      });
    return () => {
      ignore = true;
    };
  }, [ready, token, navigate, attempt]);

  if (error) {
    return (
      <section>
        <h1 className="page-title">Profile</h1>
        <ErrorState
          title={error.title}
          message={error.message}
          onRetry={() => { setError(null); setProfile(null); setOrders(null); setAttempt((value) => value + 1); }}
        />
      </section>
    );
  }
  if (!profile || !orders) return <LoadingState label="Loading profile..." />;

  return (
    <section>
      <h1 className="page-title">Profile</h1>
      <article className="panel mt-5 p-5">
        <h2 className="text-xl font-semibold text-slate-900">{profile.name}</h2>
        <dl className="mt-4 space-y-3 text-sm">
          <div className="flex flex-wrap gap-2">
            <dt className="w-28 text-slate-500">Email</dt>
            <dd className="font-medium text-slate-900">{profile.email}</dd>
          </div>
          <div className="flex flex-wrap gap-2">
            <dt className="w-28 text-slate-500">Phone</dt>
            <dd className="font-medium text-slate-900">{phoneLabel(profile.mobile)}</dd>
          </div>
        </dl>
      </article>
      <h2 className="mt-8 text-xl font-semibold tracking-tight text-slate-900">Placed orders</h2>
      {orders.length === 0 ? <EmptyState message="No placed orders yet." /> : null}
      {orders.length > 0 ? (
        <ul className="mt-4 space-y-4">
          {orders.map((order) => (
            <OrderListItem
              key={order.order_id}
              order={order}
              detail={PAYMENT_LABEL[order.payment_method] || order.payment_method}
            />
          ))}
        </ul>
      ) : null}
    </section>
  );
}
