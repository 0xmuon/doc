/** Shell around every page: Header, main content, Footer. */
import { Outlet, useLocation } from "react-router-dom";
import CartToast from "../common/CartToast";
import { useCart } from "../../context/cart-context";
import Footer from "./Footer";
import Header from "./Header";

export default function Layout() {
  const { addedNotice, clearAddedNotice } = useCart();
  const { pathname } = useLocation();
  const isHome = pathname === "/" || pathname === "/home";

  return (
    <div className="flex min-h-screen flex-col text-stone-900">
      <Header />
      <main className={`mx-auto w-full flex-1 ${isHome ? "max-w-none px-0 py-0" : "max-w-6xl px-4 py-8 sm:px-6"}`}>
        <Outlet />
      </main>
      <Footer />
      <CartToast message={addedNotice} onClose={clearAddedNotice} />
    </div>
  );
}
