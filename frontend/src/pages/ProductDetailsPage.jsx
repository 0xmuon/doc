/**
 * One product. Qty is how many to add. An invalid number is shown and is not sent.
 * The page stays here after a successful add.
 */
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { fetchProduct } from "../api/productApi";
import { useAuth } from "../context/auth-context";
import { useCart } from "../context/cart-context";
import { setCartQuantity } from "../utils/cartQuantity";
import { inr } from "../utils/money";
import { MAX_QUANTITY_PER_ITEM, validateQuantity } from "../utils/validate";

export default function ProductDetailsPage() {
  const { productId } = useParams();
  const { token, user } = useAuth();
  const { items, refreshCart } = useCart();
  const navigate = useNavigate();
  const location = useLocation();
  const [product, setProduct] = useState(null);
  const [loadedId, setLoadedId] = useState(null);
  const [quantity, setQuantity] = useState("1");
  const [quantityError, setQuantityError] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const pendingRef = useRef(false);
  const cartLine = items.find((item) => item.product_id === Number(productId)) || null;
  const current = loadedId === productId ? product : null;

  useEffect(() => {
    let ignore = false;
    fetchProduct(productId)
      .then((row) => {
        if (ignore) return;
        setProduct(row);
        setError("");
        setLoadedId(productId);
      })
      .catch((err) => {
        if (ignore) return;
        setProduct(null);
        setError(err.status === 404 ? "Product not found." : err.message);
        setLoadedId(productId);
      });
    return () => {
      ignore = true;
    };
  }, [productId]);

  async function addToCart() {
    if (pendingRef.current || !current) return;
    const inCart = cartLine?.quantity || 0;
    const typed = validateQuantity(quantity, current.available_quantity);
    const next = inCart + Number(quantity);
    const message = typed || validateQuantity(String(next), current.available_quantity);
    setQuantityError(message);
    if (message) return;
    if (!token || !user) {
      navigate("/login", { state: { from: location.pathname, message: "Please log in to add items to your cart." } });
      return;
    }
    pendingRef.current = true;
    setBusy(true);
    setError("");
    try {
      await setCartQuantity({
        token,
        userId: user.user_id,
        productId: current.product_id,
        nextQuantity: inCart + Number(quantity),
        available: current.available_quantity,
        line: cartLine,
      });
      await refreshCart();
      setQuantity("1");
    } catch (err) {
      setError(err.message);
    } finally {
      pendingRef.current = false;
      setBusy(false);
    }
  }

  if (loadedId === productId && error && !current) {
    return (
      <section>
        <p className="text-sm text-red-700">{error}</p>
        <Link to="/products" className="mt-3 inline-block text-sm underline">Back to products</Link>
      </section>
    );
  }
  if (!current) return <p className="text-sm">Loading product...</p>;
  const inStock = current.available_quantity > 0;

  return (
    <article className="mx-auto max-w-2xl">
      <Link to="/products" className="text-sm underline">Back to products</Link>
      <h1 className="mt-3 text-2xl font-semibold">{current.product_name}</h1>
      <p className="text-sm text-neutral-500">{current.category_name || "Uncategorised"}</p>
      {current.product_url ? (
        <img src={current.product_url} alt={current.product_name} className="mt-4 h-64 w-full object-contain" />
      ) : null}
      <p className="mt-4">{current.description || "No description available."}</p>
      <p className="mt-2 font-medium">{inr(current.price)}</p>
      <p className="text-sm text-neutral-600">SKU {current.sku}</p>
      <p className="text-sm text-neutral-600">{inStock ? `${current.available_quantity} in stock` : "Out of Stock"}</p>
      <p className="mt-1 text-sm text-slate-700">In cart: {cartLine?.quantity || 0}</p>
      {inStock ? (
        <div className="mt-4 flex flex-wrap items-end gap-2">
          <label className="text-sm">
            Qty
            <input
              type="number"
              min="1"
              value={quantity}
              onChange={(event) => {
                setQuantity(event.target.value);
                setQuantityError("");
              }}
              aria-label="Quantity"
              disabled={busy}
              className="mt-1 block w-20 rounded border px-2 py-2"
            />
          </label>
          <button
            type="button"
            disabled={busy || (cartLine?.quantity || 0) >= current.available_quantity || (cartLine?.quantity || 0) >= MAX_QUANTITY_PER_ITEM}
            onClick={addToCart}
            className="rounded bg-yellow-400 px-4 py-2 font-medium text-slate-900 hover:bg-yellow-300 disabled:opacity-50"
          >
            {busy ? "Adding..." : "Add to Cart"}
          </button>
        </div>
      ) : (
        <p className="mt-4 font-medium text-red-700">Out of Stock</p>
      )}
      {quantityError ? <p className="mt-2 text-sm text-red-700">{quantityError}</p> : null}
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
    </article>
  );
}
