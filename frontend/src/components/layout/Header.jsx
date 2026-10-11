/** Header: brand, menu, and the profile icon. */
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import Menu from "./Menu";

function ProfileIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="8" r="3.2" />
      <path d="M5 19.2c1.4-3 3.8-4.4 7-4.4s5.6 1.4 7 4.4" strokeLinecap="round" />
    </svg>
  );
}

export default function Header() {
  const { user, logout } = useAuth();
  return (
    <header className="border-b border-rose-100 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4">
        <Link to="/home" className="text-lg font-semibold tracking-tight text-red-600">
          ABC Shop
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
