/**
 * Product list. Search waits 300 ms, and a slow older answer cannot replace a newer one.
 * Out-of-stock products stay at the end.
 */
import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import SearchBar from "../components/products/SearchBar";
import ProductCard from "../components/products/ProductCard";
import { fetchCategories, fetchProducts, searchProducts } from "../api/productApi";
import { useAuth } from "../context/auth-context";
import { useCart } from "../context/cart-context";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { setCartQuantity } from "../utils/cartQuantity";

/** Name matches the search route. A typed category is included too, because that route matches names only. */
async function loadProducts(name, category) {
  if (category) return searchProducts({ name, category });
  if (!name) return fetchProducts();
  const [byName, all] = await Promise.all([searchProducts({ name }), fetchProducts()]);
  const query = name.toLowerCase();
  const byCategory = all.filter((product) => (product.category_name || "").toLowerCase().includes(query));
  const seen = new Set();
  const merged = [];
  for (const product of [...byName, ...byCategory]) {
    if (seen.has(product.product_id)) continue;
    seen.add(product.product_id);
    merged.push(product);
  }
  return merged;
}

export default function ProductsPage() {
  const { token, user } = useAuth();
  const { items, refreshCart } = useCart();
  const navigate = useNavigate();
  const location = useLocation();
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [loadedKey, setLoadedKey] = useState(null);
  const [error, setError] = useState("");
  const [pendingId, setPendingId] = useState(0);
  const [stockError, setStockError] = useState({ id: 0, message: "" });
  const pendingRef = useRef(0);
  const debouncedName = useDebouncedValue(name.trim(), 300);
  const requestKey = `${debouncedName}|${category}`;
  const loaded = loadedKey === requestKey;

  useEffect(() => {
    fetchCategories()
      .then(setCategories)
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    let ignore = false;
    const key = `${debouncedName}|${category}`;
    loadProducts(debouncedName, category)
      .then((rows) => {
        if (ignore) return;
        const ordered = [...rows].sort(
          (a, b) => Number(a.available_quantity <= 0) - Number(b.available_quantity <= 0),
        );
        setProducts(ordered);
        setError("");
        setLoadedKey(key);
      })
      .catch((err) => {
        if (ignore) return;
        setError(err.message);
        setLoadedKey(key);
      });
    return () => {
      ignore = true;
    };
  }, [debouncedName, category]);

  async function changeQuantity(product, nextQuantity) {
    if (!token || !user) {
      navigate("/login", { state: { from: location.pathname, message: "Please log in to add items to your cart." } });
      return;
    }
    if (pendingRef.current) return;
    const line = items.find((item) => item.product_id === product.product_id) || null;
    if ((line?.quantity ?? 0) === nextQuantity) return;
    pendingRef.current = product.product_id;
    setPendingId(product.product_id);
    setStockError({ id: 0, message: "" });
    try {
      await setCartQuantity({
        token,
        userId: user.user_id,
        productId: product.product_id,
        nextQuantity,
        available: product.available_quantity,
        line,
      });
      await refreshCart();
    } catch (err) {
      setStockError({ id: product.product_id, message: err.message });
    } finally {
      pendingRef.current = 0;
      setPendingId(0);
    }
  }

  return (
    <section>
      <h1 className="text-2xl font-semibold">Products</h1>
      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <SearchBar value={name} onChange={setName} />
        <select
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          className="rounded border px-3 py-2"
          aria-label="Search by category"
        >
          <option value="">All categories</option>
          {categories.map((item) => (
            <option key={item.category_id} value={item.category_name}>
              {item.category_name}
            </option>
          ))}
        </select>
      </div>
      {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}
      {!loaded && !error ? <p className="mt-6 text-sm">Loading products...</p> : null}
      {loaded && !error && products.length === 0 ? <p className="mt-6 text-sm text-neutral-600">No products found.</p> : null}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {products.map((product) => (
          <ProductCard
            key={product.product_id}
            product={product}
            cartQuantity={items.find((item) => item.product_id === product.product_id)?.quantity || 0}
            onChange={changeQuantity}
            busy={pendingId === product.product_id}
            message={stockError.id === product.product_id ? stockError.message : ""}
          />
        ))}
      </div>
    </section>
  );
}
