/** One product in the grid. Out of stock hides Add to Cart. Empty text uses a fallback. */
import PropTypes from "prop-types";
import { Link } from "react-router-dom";
import { inr } from "../../utils/money";
import { lowStockText, remainingStock } from "../../utils/stock";
import { MAX_QUANTITY_PER_ITEM } from "../../utils/validate";

export default function ProductCard({ product, cartQuantity, onChange, busy, message }) {
  const inStock = product.available_quantity > 0;
  const quantity = cartQuantity || 0;
  const urgency = inStock ? lowStockText(remainingStock(product.available_quantity, quantity)) : null;
  return (
    <article className="product-card flex flex-col">
      <Link to={`/products/${product.product_id}`} className="block">
        <div className="product-card__media">
          {product.product_url ? (
            <img src={product.product_url} alt={product.product_name} />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-neutral-400">No image</div>
          )}
          {!inStock ? (
            <span className="absolute top-2 left-2 bg-red-600 px-2 py-0.5 text-xs font-semibold text-white">
              Out of stock
            </span>
          ) : null}
        </div>
        <div className="px-4 pt-3">
          <p className="text-xs font-medium text-neutral-500">{product.category_name || "Uncategorised"}</p>
          <h2 className="mt-1 font-display text-base font-semibold leading-snug text-neutral-900">
            {product.product_name}
          </h2>
        </div>
      </Link>
      <div className="flex flex-1 flex-col px-4 pb-4">
        <p
          className="mt-1.5 line-clamp-2 text-sm leading-5 text-neutral-600"
          title={product.description || "No description available."}
        >
          {product.description || "No description available."}
        </p>
        <div className="mt-auto border-t border-neutral-200 pt-3">
          <div className="flex items-baseline justify-between gap-2">
            <p className="price-tag text-xl text-neutral-900">{inr(product.price)}</p>
            <p className="text-xs text-neutral-500">In cart: {quantity}</p>
          </div>
          {urgency ? <p className="mt-2 text-sm font-semibold text-red-700">{urgency}</p> : null}
          {inStock ? (
            <button
              type="button"
              className="btn-cart mt-3 w-full"
              onClick={() => onChange(product, quantity + 1)}
              disabled={busy || quantity >= product.available_quantity || quantity >= MAX_QUANTITY_PER_ITEM}
            >
              {busy ? "Updating..." : "Add to Cart"}
            </button>
          ) : (
            <p className="mt-3 text-sm font-semibold text-red-700">Currently unavailable</p>
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
