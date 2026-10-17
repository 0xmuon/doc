/** Header: brand, menu, cart beside profile. */
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../context/auth-context";
import { useCart } from "../../context/cart-context";
import Menu from "./Menu";

function ProfileIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="8" r="3.2" />
      <path d="M5 19.2c1.4-3 3.8-4.4 7-4.4s5.6 1.4 7 4.4" strokeLinecap="round" />
    </svg>
  );
}

function CartIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M3.5 5h1.6l1.7 10.2a1.5 1.5 0 0 0 1.5 1.3h8.4a1.5 1.5 0 0 0 1.5-1.2L19.5 8H7" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="9.5" cy="19.5" r="1.2" />
      <circle cx="16.5" cy="19.5" r="1.2" />
    </svg>
  );
}

export default function Header() {
  const { user, logout } = useAuth();
  const { itemCount } = useCart();
  const { pathname } = useLocation();
  const cartActive = pathname === "/cart" || pathname === "/checkout";
  return (
    <header className="sticky top-0 z-40 border-b border-rose-100 bg-white/95 shadow-sm backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <Link to="/home" className="order-1 flex items-center gap-2 text-lg font-bold tracking-tight text-red-600">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-600 text-sm text-white">A</span>
          ABC Shop
        </Link>
        <Menu />
        <div className="order-2 flex items-center gap-2 text-sm md:order-3">
          <Link
            to="/cart"
            aria-label={itemCount > 0 ? `Cart, ${itemCount} items` : "Cart"}
            className={`relative inline-flex h-9 w-9 items-center justify-center rounded-full transition ${
              cartActive ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            <CartIcon />
            {itemCount > 0 ? (
              <span className="absolute -top-0.5 -right-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold leading-none text-white">
                {itemCount > 99 ? "99+" : itemCount}
              </span>
            ) : null}
          </Link>
          {user ? (
            <>
              <Link to="/profile" className="inline-flex items-center gap-2 rounded-full px-2 py-1 text-slate-700 hover:bg-slate-100 hover:text-blue-700" title={user.email}>
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-50 text-blue-700">
                  <ProfileIcon />
                </span>
                <span className="hidden font-medium sm:inline">{user.name}</span>
              </Link>
              <button type="button" className="btn-danger px-3 py-1.5" onClick={logout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" aria-label="Profile" className="flex h-9 w-9 items-center justify-center rounded-full text-slate-600 hover:bg-slate-100 hover:text-blue-700">
                <ProfileIcon />
              </Link>
              <Link to="/login" className="btn-primary px-3 py-1.5">
                Login
              </Link>
              <Link to="/register" className="btn-outline px-3 py-1.5">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
