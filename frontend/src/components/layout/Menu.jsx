/** Top menu. Home, Products, Cart, and Orders. Cart shows how many items are in the cart. */
import { NavLink, useLocation } from "react-router-dom";
import { useCart } from "../../context/cart-context";

const linkClass = ({ isActive }) =>
  `text-sm ${isActive ? "font-semibold text-blue-700 underline" : "text-slate-700 hover:text-blue-700"}`;

export default function Menu() {
  const { pathname } = useLocation();
  const { itemCount } = useCart();
  const onHome = pathname === "/" || pathname === "/home";
  return (
    <nav className="flex flex-wrap items-center gap-4" aria-label="Shop">
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
