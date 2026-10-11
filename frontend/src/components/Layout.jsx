import { Link, NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const linkClass = ({ isActive }) =>
  `text-sm ${isActive ? "font-semibold text-blue-700 underline" : "text-slate-700 hover:text-blue-700"}`;

function Menu() {
  const { pathname } = useLocation();
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
        Cart
      </NavLink>
      <NavLink to="/orders" className={linkClass}>
        Orders
      </NavLink>
    </nav>
  );
}

function ProfileIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="8" r="3.2" />
      <path d="M5 19.2c1.4-3 3.8-4.4 7-4.4s5.6 1.4 7 4.4" strokeLinecap="round" />
    </svg>
  );
}

function Header() {
  const { user, logout } = useAuth();
  return (
    <header className="border-b border-rose-100 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4">
        <Link to="/home" className="text-lg font-semibold tracking-tight text-red-600">
          SwiftShop
        </Link>
        <Menu />
        <div className="flex items-center gap-3 text-sm">
          {user ? (
            <>
              <Link to="/profile" className="inline-flex items-center gap-1 text-slate-700 hover:text-blue-700" title={user.email}>
                <ProfileIcon />
                <span className="hidden sm:inline">{user.name}</span>
              </Link>
              <button type="button" className="rounded-full bg-red-600 px-3 py-1 text-white" onClick={logout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" aria-label="Profile" className="text-slate-700 hover:text-blue-700">
                <ProfileIcon />
              </Link>
              <Link to="/login" className="rounded bg-blue-600 px-3 py-1.5 text-white hover:bg-blue-700">
                Login
              </Link>
              <Link to="/register" className="rounded border border-slate-300 bg-white px-3 py-1.5 text-slate-800 hover:bg-slate-50">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="mt-auto border-t border-rose-100 bg-rose-50 text-slate-600">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:grid-cols-4">
        <div>
          <p className="font-semibold text-red-600">SwiftShop</p>
          <p className="mt-2 text-sm">Your shopping shop for the latest products and unbeatable deals. Fast shipping and 24/7 customer support.</p>
        </div>
        <div>
          <p className="font-semibold text-slate-900">Shop</p>
          <ul className="mt-2 space-y-1 text-sm">
            <li><Link to="/home" className="hover:text-blue-700">Home</Link></li>
            <li><Link to="/products" className="hover:text-blue-700">Category</Link></li>
            <li><Link to="/products" className="hover:text-blue-700">Deals</Link></li>
            <li><Link to="/products" className="hover:text-blue-700">New Arrivals</Link></li>
          </ul>
        </div>
        <div>
          <p className="font-semibold text-slate-900">Customer Service</p>
          <ul className="mt-2 space-y-1 text-sm">
            <li>Help Center</li>
            <li>Returns</li>
            <li>Shipping</li>
            <li>Contact Us</li>
          </ul>
        </div>
        <div>
          <p className="font-semibold text-slate-900">Connect</p>
          <ul className="mt-2 space-y-1 text-sm">
            <li><a href="mailto:support@swiftshop.com" className="hover:text-blue-700">support@swiftshop.com</a></li>
            <li><a href="tel:+919999999999" className="hover:text-blue-700">+91-9999999999</a></li>
          </ul>
        </div>
      </div>
    </footer>
  );
}

export default function Layout({ children }) {
  return (
    <div className="flex min-h-screen flex-col bg-rose-50/40 text-slate-900">
      <Header />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
      <Footer />
    </div>
  );
}
