import { Link } from "react-router-dom";
import { inr } from "../utils/money";
import QuantityStepper from "./QuantityStepper";

export default function ProductCard({ product, cartQuantity, onChange, busy, message }) {
  const inStock = product.available_quantity > 0;
  const quantity = cartQuantity || 0;
  return (
    <article className="flex flex-col rounded border border-rose-100 bg-white p-4 shadow-sm">
      <Link to={`/products/${product.product_id}`} className="block">
        {product.product_url ? (
          <img src={product.product_url} alt={product.product_name} className="h-40 w-full object-contain" />
        ) : (
          <div className="flex h-40 items-center justify-center bg-neutral-100 text-sm text-neutral-500">No image</div>
        )}
        <h2 className="mt-3 text-base font-semibold">{product.product_name}</h2>
      </Link>
      <p className="text-sm text-neutral-500">{product.category_name}</p>
      <p className="mt-2 line-clamp-3 text-sm text-neutral-700">{product.description}</p>
      <p className="mt-2 font-medium">{inr(product.price)}</p>
      <p className="mt-1 text-sm text-slate-700">In cart: {quantity}</p>
      {inStock ? (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {quantity >= 1 ? (
            <QuantityStepper
              name={product.product_name}
              quantity={quantity}
              max={product.available_quantity}
              busy={busy}
              onChange={(next) => onChange(product, next)}
            />
          ) : null}
          <button
            type="button"
            className="rounded bg-yellow-400 px-3 py-2 text-sm font-medium text-slate-900 hover:bg-yellow-300 disabled:opacity-50"
            onClick={() => onChange(product, quantity + 1)}
            disabled={busy || quantity >= product.available_quantity}
          >
            {busy ? "Updating..." : "Add to Cart"}
          </button>
        </div>
      ) : (
        <p className="mt-3 text-sm font-medium text-red-700">Out of Stock</p>
      )}
      {message ? <p className="mt-2 text-sm text-red-700">{message}</p> : null}
    </article>
  );
}
