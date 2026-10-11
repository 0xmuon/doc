/** Footer: shop links, contact, and the copyright line. */
import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="mt-auto border-t border-rose-100 bg-rose-50 text-slate-600">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:grid-cols-4">
        <div>
          <p className="font-semibold text-red-600">ABC Shop</p>
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
            <li><a href="mailto:support@abcshop.example" className="hover:text-blue-700">support@abcshop.example</a></li>
            <li><a href="tel:+1234567890" className="hover:text-blue-700">+1 234 567 890</a></li>
          </ul>
        </div>
      </div>
      <p className="mx-auto max-w-6xl border-t border-rose-100 px-4 py-4 text-sm">© 2026 ABC Shop. All Rights Reserved.</p>
    </footer>
  );
}
