/** Shell around every page: Header, main content, Footer. */
import { Outlet } from "react-router-dom";
import CartToast from "../common/CartToast";
import { useCart } from "../../context/cart-context";
import Footer from "./Footer";
import Header from "./Header";

export default function Layout() {
  const { addedNotice, clearAddedNotice } = useCart();
  return (
    <div className="flex min-h-screen flex-col bg-rose-50/60 text-slate-900">
      <Header />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
        <Outlet />
      </main>
      <Footer />
      <CartToast message={addedNotice} onClose={clearAddedNotice} />
    </div>
  );
}
