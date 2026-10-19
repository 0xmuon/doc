/** Footer: shop links, contact, and the copyright line. */
import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="mt-auto border-t border-neutral-300 bg-white text-neutral-700">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-8 sm:grid-cols-4 sm:px-6">
        <div>
          <p className="font-display text-base font-bold text-red-600">ABC Shop</p>
          <p className="mt-2 text-sm leading-6 text-neutral-600">
            Your shopping shop for the latest products and unbeatable deals. Fast shipping and 24/7 customer support.
          </p>
        </div>
        <div>
          <p className="text-sm font-semibold text-neutral-900">Shop</p>
          <ul className="mt-2 space-y-1.5 text-sm">
            <li>
              <Link to="/home" className="hover:text-red-600">
                Home
              </Link>
            </li>
            <li>
              <Link to="/products" className="hover:text-red-600">
                Category
              </Link>
            </li>
            <li>
              <Link to="/products" className="hover:text-red-600">
                Deals
              </Link>
            </li>
            <li>
              <Link to="/products" className="hover:text-red-600">
                New Arrivals
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="text-sm font-semibold text-neutral-900">Customer Service</p>
          <ul className="mt-2 space-y-1.5 text-sm">
            <li>
              <Link to="/help-center" className="hover:text-red-600">
                Help Center
              </Link>
            </li>
            <li>
              <Link to="/returns" className="hover:text-red-600">
                Returns
              </Link>
            </li>
            <li>
              <Link to="/shipping" className="hover:text-red-600">
                Shipping
              </Link>
            </li>
            <li>
              <Link to="/contact-us" className="hover:text-red-600">
                Contact Us
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="text-sm font-semibold text-neutral-900">Connect</p>
          <ul className="mt-2 space-y-1.5 text-sm">
            <li>
              <a href="mailto:support@abcshop.example" className="hover:text-red-600">
                support@abcshop.example
              </a>
            </li>
            <li>
              <a href="tel:+1234567890" className="hover:text-red-600">
                +1 234 567 890
              </a>
            </li>
          </ul>
        </div>
      </div>
      <p className="mx-auto max-w-6xl border-t border-neutral-200 px-4 py-3 text-sm text-neutral-500 sm:px-6">
        © 2026 ABC Shop. All Rights Reserved.
      </p>
    </footer>
  );
}
