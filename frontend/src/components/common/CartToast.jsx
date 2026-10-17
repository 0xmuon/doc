/** Short notice after an item is added to the cart. */
import PropTypes from "prop-types";
import { Link } from "react-router-dom";

export default function CartToast({ message, onClose }) {
  if (!message) return null;
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed right-4 bottom-4 z-50 w-[min(22rem,calc(100vw-2rem))] rounded-2xl border border-rose-100 bg-white p-4 shadow-xl"
    >
      <p className="text-sm font-semibold text-slate-900">Added to cart</p>
      <p className="mt-1 text-sm leading-6 text-slate-600">{message}</p>
      <div className="mt-3 flex items-center gap-3">
        <Link to="/cart" className="btn-primary px-3 py-1.5" onClick={onClose}>
          View cart
        </Link>
        <button type="button" className="text-sm font-medium text-slate-500 hover:text-slate-800" onClick={onClose}>
          Dismiss
        </button>
      </div>
    </div>
  );
}

CartToast.propTypes = {
  message: PropTypes.string,
  onClose: PropTypes.func.isRequired,
};
