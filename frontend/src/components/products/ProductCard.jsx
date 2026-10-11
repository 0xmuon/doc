/** One product in the grid. Out of stock hides Add to Cart. Empty text uses a fallback. */
import PropTypes from "prop-types";
import { Link } from "react-router-dom";
import { inr } from "../../utils/money";
import { MAX_QUANTITY_PER_ITEM } from "../../utils/validate";

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
      <p className="text-sm text-neutral-500">{product.category_name || "Uncategorised"}</p>
      <p className="mt-2 line-clamp-3 text-sm text-neutral-700">{product.description || "No description available."}</p>
      <p className="mt-2 font-medium">{inr(product.price)}</p>
      <p className="mt-1 text-sm text-slate-700">In cart: {quantity}</p>
      {inStock ? (
        <button
          type="button"
          className="mt-3 w-fit rounded bg-yellow-400 px-3 py-2 text-sm font-medium text-slate-900 hover:bg-yellow-300 disabled:opacity-50"
          onClick={() => onChange(product, quantity + 1)}
          disabled={busy || quantity >= product.available_quantity || quantity >= MAX_QUANTITY_PER_ITEM}
        >
          {busy ? "Updating..." : "Add to Cart"}
        </button>
      ) : (
        <p className="mt-3 text-sm font-medium text-red-700">Out of Stock</p>
      )}
      {message ? <p className="mt-2 text-sm text-red-700">{message}</p> : null}
    </article>
  );
}

ProductCard.propTypes = {
  product: PropTypes.shape({
    product_id: PropTypes.number.isRequired,
    product_name: PropTypes.string.isRequired,
    product_url: PropTypes.string,
    category_name: PropTypes.string,
    description: PropTypes.string,
    price: PropTypes.number.isRequired,
    available_quantity: PropTypes.number.isRequired,
  }).isRequired,
  cartQuantity: PropTypes.number,
  onChange: PropTypes.func.isRequired,
  busy: PropTypes.bool,
  message: PropTypes.string,
};
