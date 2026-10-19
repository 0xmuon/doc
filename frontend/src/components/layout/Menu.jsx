/** Top menu. Home, Products, and Orders. */
import { NavLink, useLocation } from "react-router-dom";

const linkClass = ({ isActive }) =>
  `border-b-2 px-1 py-1 text-sm transition ${
    isActive
      ? "border-red-600 font-semibold text-neutral-900"
      : "border-transparent text-neutral-600 hover:border-neutral-300 hover:text-neutral-900"
  }`;

export default function Menu() {
  const { pathname } = useLocation();
  const onHome = pathname === "/" || pathname === "/home";
  return (
    <nav className="order-3 flex w-full items-center gap-4 md:order-none md:w-auto" aria-label="Shop">
      <NavLink to="/home" className={() => linkClass({ isActive: onHome })}>
        Home
      </NavLink>
      <NavLink to="/products" className={linkClass}>
        Products
      </NavLink>
      <NavLink to="/orders" className={linkClass}>
        Orders
      </NavLink>
    </nav>
  );
}
