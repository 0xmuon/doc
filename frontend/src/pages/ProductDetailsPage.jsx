import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import QuantityStepper from "../components/QuantityStepper";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { setCartQuantity } from "../utils/cartQuantity";
import { inr } from "../utils/money";

export default function ProductDetailsPage() {
  const { productId } = useParams();
  const { token, user, ready } = useAuth();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [cartLine, setCartLine] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const pendingRef = useRef(false);

  useEffect(() => {
    api(`/api/products/${productId}`)
      .then(setProduct)
      .catch((err) => setError(err.message));
  }, [productId]);

  useEffect(() => {
    if (!ready) return;
    if (!token || !user) {
      setCartLine(null);
      return;
    }
    api(`/api/cart/${user.user_id}`, { token })
      .then((data) => setCartLine(data.items.find((item) => item.product_id === Number(productId)) || null))
      .catch((err) => setError(err.message));
  }, [ready, token, user, productId]);

  async function changeQuantity(nextQuantity) {
    if (!token || !user) {
      navigate("/login");
      return;
    }
    if (pendingRef.current || !product) return;
    if ((cartLine?.quantity ?? 0) === nextQuantity) return;
    pendingRef.current = true;
    setBusy(true);
    setError("");
    try {
      await setCartQuantity({
        token,
        userId: user.user_id,
        productId: product.product_id,
        nextQuantity,
        available: product.available_quantity,
        line: cartLine,
      });
      const data = await api(`/api/cart/${user.user_id}`, { token });
      setCartLine(data.items.find((item) => item.product_id === product.product_id) || null);
    } catch (err) {
      setError(err.message);
    } finally {
      pendingRef.current = false;
      setBusy(false);
    }
  }

  if (error && !product) return <p className="text-sm text-red-700">{error}</p>;
  if (!product) return <p className="text-sm">Loading product...</p>;
  const inStock = product.available_quantity > 0;

  return (
    <article className="mx-auto max-w-2xl">
      <Link to="/products" className="text-sm underline">Back to products</Link>
      <h1 className="mt-3 text-2xl font-semibold">{product.product_name}</h1>
      <p className="text-sm text-neutral-500">{product.category_name}</p>
      {product.product_url ? (
        <img src={product.product_url} alt={product.product_name} className="mt-4 h-64 w-full object-contain" />
      ) : null}
      <p className="mt-4">{product.description}</p>
      <p className="mt-2 font-medium">{inr(product.price)}</p>
      <p className="text-sm text-neutral-600">Available: {product.available_quantity}</p>
      <p className="mt-1 text-sm text-slate-700">In cart: {cartLine?.quantity || 0}</p>
      {inStock ? (
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <QuantityStepper
            name={product.product_name}
            quantity={cartLine?.quantity || 0}
            max={product.available_quantity}
            busy={busy}
            onChange={changeQuantity}
          />
          <button
            type="button"
            disabled={busy || (cartLine?.quantity || 0) >= product.available_quantity}
            onClick={() => changeQuantity((cartLine?.quantity || 0) + 1)}
            className="rounded bg-yellow-400 px-4 py-2 font-medium text-slate-900 hover:bg-yellow-300 disabled:opacity-50"
          >
            {busy ? "Updating..." : "Add to Cart"}
          </button>
        </div>
      ) : (
        <p className="mt-4 font-medium text-red-700">Out of Stock</p>
      )}
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
    </article>
  );
}
