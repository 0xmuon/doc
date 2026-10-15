/** Top menu. Home, Products, Cart, and Orders. Cart shows how many items are in the cart. */
import { NavLink, useLocation } from "react-router-dom";
import { useCart } from "../../context/cart-context";

const linkClass = ({ isActive }) =>
  `rounded-full px-3 py-1.5 text-sm transition ${isActive ? "bg-blue-50 font-semibold text-blue-700" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"}`;

export default function Menu() {
  const { pathname } = useLocation();
  const { itemCount } = useCart();
  const onHome = pathname === "/" || pathname === "/home";
  return (
    <nav className="order-3 flex w-full flex-wrap items-center gap-1 md:order-2 md:w-auto" aria-label="Shop">
      <NavLink to="/home" className={() => linkClass({ isActive: onHome })}>
        Home
      </NavLink>
      <NavLink to="/products" className={linkClass}>
        Products
      </NavLink>
      <NavLink to="/cart" className={linkClass}>
        Cart{itemCount > 0 ? ` (${itemCount})` : ""}
      </NavLink>
      <NavLink to="/orders" className={linkClass}>
        Orders
      </NavLink>
    </nav>
  );
}
