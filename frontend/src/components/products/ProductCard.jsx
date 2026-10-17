/** One product in the grid. Out of stock hides Add to Cart. Empty text uses a fallback. */
import PropTypes from "prop-types";
import { Link } from "react-router-dom";
import { inr } from "../../utils/money";
import { MAX_QUANTITY_PER_ITEM } from "../../utils/validate";

export default function ProductCard({ product, cartQuantity, onChange, busy, message }) {
  const inStock = product.available_quantity > 0;
  const quantity = cartQuantity || 0;
  return (
    <article className="panel flex flex-col overflow-hidden transition hover:-translate-y-0.5 hover:shadow-md">
      <Link to={`/products/${product.product_id}`} className="block">
        {product.product_url ? (
          <img src={product.product_url} alt={product.product_name} className="h-48 w-full bg-slate-50 object-contain p-4" />
        ) : (
          <div className="flex h-48 items-center justify-center bg-slate-50 text-sm text-slate-400">No image</div>
        )}
        <div className="px-4 pt-4">
          <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">{product.category_name || "Uncategorised"}</p>
          <h2 className="mt-1 text-base font-semibold text-slate-900">{product.product_name}</h2>
        </div>
      </Link>
      <div className="flex flex-1 flex-col px-4 pb-4">
        <p className="mt-2 truncate text-sm leading-6 text-slate-600" title={product.description || "No description available."}>
          {product.description || "No description available."}
        </p>
        <div className="mt-auto pt-3">
          <p className="text-lg font-semibold text-slate-900">{inr(product.price)}</p>
          <p className="mt-1 text-sm text-slate-600">In cart: {quantity}</p>
          {inStock ? (
            <button
              type="button"
              className="btn-cart mt-4 w-fit"
              onClick={() => onChange(product, quantity + 1)}
              disabled={busy || quantity >= product.available_quantity || quantity >= MAX_QUANTITY_PER_ITEM}
            >
              {busy ? "Updating..." : "Add to Cart"}
            </button>
          ) : (
            <p className="mt-4 text-sm font-semibold text-red-700">Out of Stock</p>
          )}
          {message ? <p className="mt-2 text-sm text-red-700">{message}</p> : null}
        </div>
      </div>
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
