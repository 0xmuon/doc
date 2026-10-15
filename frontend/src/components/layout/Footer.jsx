/** Footer: shop links, contact, and the copyright line. */
import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="mt-auto border-t border-slate-800 bg-slate-900 text-slate-300">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:grid-cols-4 sm:px-6">
        <div>
          <p className="font-semibold text-white">ABC Shop</p>
          <p className="mt-2 text-sm leading-6 text-slate-400">Your shopping shop for the latest products and unbeatable deals. Fast shipping and 24/7 customer support.</p>
        </div>
        <div>
          <p className="font-semibold text-white">Shop</p>
          <ul className="mt-2 space-y-1.5 text-sm">
            <li><Link to="/home" className="hover:text-white">Home</Link></li>
            <li><Link to="/products" className="hover:text-white">Category</Link></li>
            <li><Link to="/products" className="hover:text-white">Deals</Link></li>
            <li><Link to="/products" className="hover:text-white">New Arrivals</Link></li>
          </ul>
        </div>
        <div>
          <p className="font-semibold text-white">Customer Service</p>
          <ul className="mt-2 space-y-1.5 text-sm text-slate-400">
            <li>Help Center</li>
            <li>Returns</li>
            <li>Shipping</li>
            <li>Contact Us</li>
          </ul>
        </div>
        <div>
          <p className="font-semibold text-white">Connect</p>
          <ul className="mt-2 space-y-1.5 text-sm">
            <li><a href="mailto:support@abcshop.example" className="hover:text-white">support@abcshop.example</a></li>
            <li><a href="tel:+1234567890" className="hover:text-white">+1 234 567 890</a></li>
          </ul>
        </div>
      </div>
      <p className="mx-auto max-w-6xl border-t border-slate-800 px-4 py-4 text-sm text-slate-400 sm:px-6">© 2026 ABC Shop. All Rights Reserved.</p>
    </footer>
  );
}
