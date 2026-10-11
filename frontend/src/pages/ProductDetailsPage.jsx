/**
 * One product. Qty is how many to add. An invalid number is shown and is not sent.
 * The page stays here after a successful add.
 */
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { setCartQuantity } from "../utils/cartQuantity";
import { inr } from "../utils/money";
import { validateQuantity } from "../utils/validate";

export default function ProductDetailsPage() {
  const { productId } = useParams();
  const { token, user } = useAuth();
  const { items, refreshCart } = useCart();
  const navigate = useNavigate();
  const location = useLocation();
  const [product, setProduct] = useState(null);
  const [quantity, setQuantity] = useState("1");
  const [quantityError, setQuantityError] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const pendingRef = useRef(false);
  const cartLine = items.find((item) => item.product_id === Number(productId)) || null;

  useEffect(() => {
    let ignore = false;
    setProduct(null);
    setError("");
    api(`/api/products/${productId}`)
      .then((row) => {
        if (!ignore) setProduct(row);
      })
      .catch((err) => {
        if (ignore) return;
        setError(err.status === 404 ? "Product not found." : err.message);
      });
    return () => {
      ignore = true;
    };
  }, [productId]);

  async function addToCart() {
    if (pendingRef.current || !product) return;
    const inCart = cartLine?.quantity || 0;
    const room = product.available_quantity - inCart;
    const message = validateQuantity(quantity, room);
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
        productId: product.product_id,
        nextQuantity: inCart + Number(quantity),
        available: product.available_quantity,
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

  if (error && !product) {
    return (
      <section>
        <p className="text-sm text-red-700">{error}</p>
        <Link to="/products" className="mt-3 inline-block text-sm underline">Back to products</Link>
      </section>
    );
  }
  if (!product) return <p className="text-sm">Loading product...</p>;
  const inStock = product.available_quantity > 0;

  return (
    <article className="mx-auto max-w-2xl">
      <Link to="/products" className="text-sm underline">Back to products</Link>
      <h1 className="mt-3 text-2xl font-semibold">{product.product_name}</h1>
      <p className="text-sm text-neutral-500">{product.category_name || "Uncategorised"}</p>
      {product.product_url ? (
        <img src={product.product_url} alt={product.product_name} className="mt-4 h-64 w-full object-contain" />
      ) : null}
      <p className="mt-4">{product.description || "No description available."}</p>
      <p className="mt-2 font-medium">{inr(product.price)}</p>
      <p className="text-sm text-neutral-600">SKU {product.sku}</p>
      <p className="text-sm text-neutral-600">{inStock ? `${product.available_quantity} in stock` : "Out of Stock"}</p>
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
            disabled={busy || (cartLine?.quantity || 0) >= product.available_quantity}
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
