/**
 * One product. Qty is how many to add. An invalid number is shown and is not sent.
 * The page stays here after a successful add.
 */
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { ErrorNote, ErrorState, LoadingState } from "../components/common/StatusMessage";
import { fetchProduct } from "../api/productApi";
import { useAuth } from "../context/auth-context";
import { useCart } from "../context/cart-context";
import { setCartQuantity } from "../utils/cartQuantity";
import { describeActionError, describeLoadError } from "../utils/loadError";
import { inr } from "../utils/money";
import { lowStockText, remainingStock } from "../utils/stock";
import { MAX_QUANTITY_PER_ITEM, validateQuantity } from "../utils/validate";

export default function ProductDetailsPage() {
  const { productId } = useParams();
  const { token, user } = useAuth();
  const { items, refreshCart, notifyAdded } = useCart();
  const navigate = useNavigate();
  const location = useLocation();
  const [product, setProduct] = useState(null);
  const [loadedId, setLoadedId] = useState(null);
  const [quantity, setQuantity] = useState("1");
  const [quantityError, setQuantityError] = useState("");
  const [loadError, setLoadError] = useState(null);
  const [actionError, setActionError] = useState("");
  const [attempt, setAttempt] = useState(0);
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
        setLoadError(null);
        setLoadedId(productId);
      })
      .catch((err) => {
        if (ignore) return;
        setProduct(null);
        setLoadError(describeLoadError("product data", err));
        setLoadedId(productId);
      });
    return () => {
      ignore = true;
    };
  }, [productId, attempt]);

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
    setActionError("");
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
      notifyAdded(current.product_name);
      setQuantity("1");
    } catch (err) {
      setActionError(describeActionError("Could not add to cart", err));
    } finally {
      pendingRef.current = false;
      setBusy(false);
    }
  }

  if (loadedId === productId && loadError && !current) {
    return (
      <section>
        <ErrorState
          title={loadError.title}
          message={loadError.message}
          onRetry={() => { setLoadError(null); setLoadedId(null); setAttempt((value) => value + 1); }}
        />
        <Link to="/products" className="btn-outline mt-4">Back to products</Link>
      </section>
    );
  }
  if (!current) return <LoadingState label="Loading product details..." />;
  const inStock = current.available_quantity > 0;
  const urgency = inStock ? lowStockText(remainingStock(current.available_quantity, cartLine?.quantity || 0)) : null;

  return (
    <article className="panel mx-auto grid max-w-4xl gap-6 p-5 sm:p-8 lg:grid-cols-2">
      <div>
        <Link to="/products" className="text-sm font-medium text-blue-700 hover:underline">Back to products</Link>
        {current.product_url ? (
          <img src={current.product_url} alt={current.product_name} className="mt-4 h-72 w-full border border-neutral-300 bg-neutral-50 object-contain p-4" />
        ) : (
          <div className="mt-4 flex h-72 items-center justify-center border border-neutral-300 bg-neutral-50 text-sm text-neutral-400">No image</div>
        )}
      </div>
      <div>
        <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">{current.category_name || "Uncategorised"}</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">{current.product_name}</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">{current.description || "No description available."}</p>
        <p className="mt-4 text-2xl font-semibold text-slate-900">{inr(current.price)}</p>
        <p className="mt-2 text-sm text-slate-500">SKU {current.sku}</p>
        <p className={`mt-1 text-sm font-medium ${inStock ? "text-slate-700" : "text-red-700"}`}>{inStock ? `${current.available_quantity} in stock` : "Out of Stock"}</p>
        {urgency ? <p className="mt-1 text-sm font-semibold text-red-700">{urgency}</p> : null}
        <p className="mt-1 text-sm text-slate-700">In cart: {cartLine?.quantity || 0}</p>
        {inStock ? (
          <div className="mt-5 flex flex-wrap items-end gap-3">
            <label className="field-label">
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
                className="field w-24"
              />
            </label>
            <button
              type="button"
              disabled={busy || (cartLine?.quantity || 0) >= current.available_quantity || (cartLine?.quantity || 0) >= MAX_QUANTITY_PER_ITEM}
              onClick={addToCart}
              className="btn-cart"
            >
              {busy ? "Adding..." : "Add to Cart"}
            </button>
          </div>
        ) : (
          <p className="mt-5 font-semibold text-red-700">Out of Stock</p>
        )}
        {quantityError ? <p className="mt-2 text-sm text-red-700">{quantityError}</p> : null}
        {actionError ? <div className="mt-3"><ErrorNote message={actionError} /></div> : null}
      </div>
    </article>
  );
}
